import os
os.environ["KERAS_BACKEND"] = "torch"
os.environ["TORCHDYNAMO_DISABLE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "0"

import cv2
import numpy as np
import gradio as gr
import spaces  # ZeroGPU free tier

MODEL_ID = "Aldahmashi/DR-EfficientNetB0"
MODEL_FILE = "final_model.keras"
CLASS_NAMES = ["No DR", "Mild DR", "Moderate DR", "Severe DR", "Proliferative DR"]

_classifier = None

def get_model():
    global _classifier
    if _classifier is not None:
        return _classifier
    from huggingface_hub import hf_hub_download
    import keras
    path = hf_hub_download(repo_id=MODEL_ID, filename=MODEL_FILE)
    _classifier = keras.saving.load_model(path)
    print(f"Loaded {MODEL_ID}: in={_classifier.input_shape} out={_classifier.output_shape}")
    return _classifier

def quality_score(img_rgb):
    gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
    lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    focus = min(1.0, float(lap_var) / 400.0)
    mean_b = float(np.mean(gray))
    bright = 1.0 if 30 <= mean_b <= 220 else max(0.0, 1.0 - abs(mean_b - 125) / 125)
    _, binary = cv2.threshold(gray, 20, 255, cv2.THRESH_BINARY)
    fov = min(1.0, float((binary > 0).mean()) / 0.4)
    overall = round(0.4 * focus + 0.3 * bright + 0.3 * fov, 3)
    usable = overall >= 0.35 and focus >= 0.25 and fov >= 0.30
    return usable, overall, focus, bright, fov

def preprocess(img_rgb):
    img = cv2.resize(img_rgb, (224, 224)).astype(np.float32) / 255.0
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    return np.expand_dims((img - mean) / std, axis=0)

@spaces.GPU(duration=60)
def predict(image):
    if image is None:
        return "Please upload a fundus image.", None
    img_rgb = np.array(image.convert("RGB"))
    usable, overall, focus, bright, fov = quality_score(img_rgb)
    try:
        model = get_model()
    except Exception as e:
        return f"Model failed to load (needs internet on first run): {e}", None
    probs = np.array(model.predict(preprocess(img_rgb), verbose=0)[0], dtype=float)
    probs = np.clip(probs, 0, None)
    probs = probs / probs.sum() if probs.sum() > 0 else np.ones(5) / 5
    pred = int(np.argmax(probs))
    referable = float(probs[2] + probs[3] + probs[4])
    lines = [
        f"### {CLASS_NAMES[pred]} (grade {pred})",
        f"Confidence: {probs[pred]*100:.1f}%",
        f"Referable (mod+): {'YES - refer' if pred >= 2 else 'NO'} ({referable*100:.1f}%)",
        f"",
        f"Quality usable: {usable} (overall {overall}, focus {focus:.2f}, illum {bright:.2f}, fov {fov:.2f})",
    ]
    if not usable:
        lines.append("Warning: low quality - consider recapture.")
    return "\n".join(lines), {CLASS_NAMES[i]: float(probs[i]) for i in range(5)}

demo = gr.Interface(
    fn=predict,
    inputs=gr.Image(type="pil", label="Fundus photo"),
    outputs=[gr.Markdown(label="Result"), gr.Label(label="Probabilities")],
    title="AI Diabetic Retinopathy Screening (Rural India)",
    description="EfficientNetB0 5-grade DR classifier. Model downloads at runtime from Aldahmashi/DR-EfficientNetB0 - no weights bundled, keeps Space small. Runs on ZeroGPU free tier. Not a medical device.",
    examples=None,
    allow_flagging="never",
)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", "7860")))
