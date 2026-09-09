"""EfficientNetB3 + CORAL ordinal regression model for DR grading.

Upgraded from our original EfficientNetB0 classifier to match the competitor's
stronger architecture while adding ordinal regression (CORAL) for better
alignment with the ordered nature of DR grades.
"""

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, Model
from typing import Tuple, Optional


def build_coral_model(
    num_grades: int = 5,
    input_shape: Tuple[int, int, int] = (512, 512, 3),
    dropout_rate: float = 0.4,
    freeze_backbone: bool = True,
    use_augmentation: bool = True,
) -> Model:
    """Build EfficientNetB3 + CORAL ordinal regression model.

    Architecture:
        Input -> In-model augmentation -> EfficientNetB3 (ImageNet pretrained)
        -> GlobalAvgPool -> Dropout -> Dense(K-1, no activation)

    The output has K-1 = 4 units (one per ordinal threshold).
    Each unit predicts P(grade > k) via CORAL loss.

    Args:
        num_grades: Number of DR grades (0-4 = 5).
        input_shape: Input image shape (H, W, 3).
        dropout_rate: Dropout rate for regularization.
        freeze_backbone: Whether to freeze pretrained backbone weights.
        use_augmentation: Whether to apply in-model augmentation.

    Returns:
        Compiled Keras Model.
    """
    inp = keras.Input(shape=input_shape, dtype=tf.float32, name="input_image")

    # In-model augmentation (lightweight, medical-appropriate)
    if use_augmentation:
        aug = keras.Sequential([
            layers.RandomFlip("horizontal"),
            layers.RandomRotation(0.05),
            layers.RandomZoom(0.10),
            layers.RandomContrast(0.10),
        ], name="augmentation")
        x = aug(inp)
    else:
        x = inp

    # Backbone: EfficientNetB3 (stronger than B0)
    base = keras.applications.EfficientNetB3(
        include_top=False,
        weights="imagenet",
        input_tensor=x,
        pooling="avg",
    )

    # Classification head
    x = base.output
    x = layers.BatchNormalization(name="bn")(x)
    x = layers.Dropout(dropout_rate, name="dropout")(x)

    # CORAL head: K-1 ordinal logits (no activation — raw logits for BCE)
    out = layers.Dense(num_grades - 1, activation=None, dtype="float32", name="coral_logits")(x)

    model = Model(inputs=inp, outputs=out, name="dr_coral_classifier")

    if freeze_backbone:
        base.trainable = False

    return model


def build_coral_model_with_augmentation(
    input_shape: Tuple[int, int, int] = (512, 512, 3),
    dropout_rate: float = 0.4,
) -> Model:
    """Convenience function for building the CORAL model."""
    return build_coral_model(
        input_shape=input_shape,
        dropout_rate=dropout_rate,
        freeze_backbone=True,
        use_augmentation=True,
    )


def compile_coral_model(
    model: Model,
    learning_rate: float = 3e-4,
    weight_decay: float = 1e-5,
):
    """Compile model with AdamW optimizer and CORAL loss.

    Args:
        model: Keras Model to compile.
        learning_rate: Learning rate.
        weight_decay: Weight decay for AdamW.
    """
    from training.coral import coral_loss_mean

    optimizer = tf.keras.optimizers.AdamW(
        learning_rate=learning_rate,
        weight_decay=weight_decay,
    )
    model.compile(optimizer=optimizer, loss=coral_loss_mean)
    return model


def predict_coral(
    model: Model,
    image,
    cutoffs: Tuple[float, float, float, float] = (0.8, 1.6, 2.4, 3.2),
):
    """Run CORAL inference: logits -> continuous score -> grade.

    Args:
        model: Trained CORAL model.
        image: Preprocessed image (1, H, W, 3).
        cutoffs: Decision thresholds for grade assignment.

    Returns:
        Dictionary with prediction results.
    """
    from training.coral import logits_to_prob, prob_to_continuous, apply_cutoffs

    logits = model.predict(image, verbose=0)
    probs = logits_to_prob(logits)
    continuous_score = prob_to_continuous(probs)
    grade = apply_cutoffs(continuous_score, cutoffs)[0]

    CLASS_NAMES = {
        0: "No DR", 1: "Mild DR", 2: "Moderate DR",
        3: "Severe DR", 4: "Proliferative DR",
    }

    # Compute per-threshold probabilities
    threshold_probs = {}
    for i in range(4):
        threshold_probs[f"severity_gt_{i}"] = float(probs[0, i])

    return {
        "grade": int(grade),
        "label": CLASS_NAMES[int(grade)],
        "continuous_score": float(continuous_score[0]),
        "threshold_probabilities": threshold_probs,
        "cutoffs": list(cutoffs),
    }
