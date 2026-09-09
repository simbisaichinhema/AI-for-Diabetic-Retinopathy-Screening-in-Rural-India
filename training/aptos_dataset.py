"""APTOS 2019 dataset loader and splitter.

Handles:
- Loading APTOS train.csv
- Resolving image paths
- Verifying missing/corrupt files
- Inspecting class distribution
- Clean train/validation/test split with stratification
- No data leakage
"""

import os
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Optional, List
from sklearn.model_selection import train_test_split
import yaml


class AptosDataLoader:
    """Load and validate APTOS 2019 blindness detection dataset."""

    def __init__(
        self,
        data_dir: str = "data/aptos",
        config_path: str = "configs/config.yaml",
    ):
        self.data_dir = Path(data_dir)
        self.config = self._load_config(config_path)
        self.df = None
        self.train_df = None
        self.val_df = None
        self.test_df = None

    def _load_config(self, config_path: str) -> dict:
        with open(config_path, "r") as f:
            return yaml.safe_load(f)

    def load_data(self, csv_name: str = "train.csv") -> pd.DataFrame:
        """Load APTOS train.csv and validate image paths.

        Returns:
            DataFrame with columns: id_code, diagnosis, image_path, valid
        """
        csv_path = self.data_dir / csv_name
        if not csv_path.exists():
            raise FileNotFoundError(
                f"APTOS CSV not found at {csv_path}. "
                f"Download from: https://www.kaggle.com/c/aptos2019-blindness-detection/data"
            )

        df = pd.read_csv(csv_path)

        # Validate expected columns
        required_cols = {"id_code", "diagnosis"}
        if not required_cols.issubset(df.columns):
            raise ValueError(f"CSV missing columns: {required_cols - set(df.columns)}")

        # Resolve image paths and check existence
        df["image_path"] = df["id_code"].apply(
            lambda x: str(self.data_dir / "train_images" / f"{x}.png")
        )

        # Also check for .jpg fallback
        for idx, row in df.iterrows():
            if not os.path.exists(row["image_path"]):
                jpg_path = str(self.data_dir / "train_images" / f"{row['id_code']}.jpg")
                if os.path.exists(jpg_path):
                    df.at[idx, "image_path"] = jpg_path

        df["valid"] = df["image_path"].apply(os.path.exists)

        self.df = df
        return df

    def validate(self) -> dict:
        """Validate dataset integrity.

        Returns:
            Dictionary with validation results.
        """
        if self.df is None:
            raise RuntimeError("Call load_data() first.")

        df = self.df
        total = len(df)
        valid = df["valid"].sum()
        missing = total - valid

        class_dist = df["diagnosis"].value_counts().sort_index()

        return {
            "total_images": total,
            "valid_images": int(valid),
            "missing_images": int(missing),
            "class_distribution": class_dist.to_dict(),
            "missing_files": df[~df["valid"]]["id_code"].tolist(),
        }

    def get_class_weights(self) -> dict:
        """Compute class weights for imbalanced dataset.

        Returns:
            Dictionary mapping class index to weight.
        """
        if self.df is None:
            raise RuntimeError("Call load_data() first.")

        counts = self.df["diagnosis"].value_counts().sort_index()
        total = len(self.df)
        n_classes = len(counts)

        weights = {}
        for cls, count in counts.items():
            weights[int(cls)] = total / (n_classes * count)

        return weights

    def split(
        self,
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
        seed: int = 42,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Split dataset into train/val/test with stratification.

        Prevents data leakage by using stratified split on diagnosis labels.

        Args:
            train_ratio: Fraction for training.
            val_ratio: Fraction for validation.
            test_ratio: Fraction for test.
            seed: Random seed for reproducibility.

        Returns:
            (train_df, val_df, test_df)
        """
        if self.df is None:
            raise RuntimeError("Call load_data() first.")

        df_valid = self.df[self.df["valid"]].copy()

        # First split: separate test set
        train_val, test = train_test_split(
            df_valid,
            test_size=test_ratio,
            stratify=df_valid["diagnosis"],
            random_state=seed,
        )

        # Second split: separate validation from train
        relative_val = val_ratio / (train_ratio + val_ratio)
        train, val = train_test_split(
            train_val,
            test_size=relative_val,
            stratify=train_val["diagnosis"],
            random_state=seed,
        )

        self.train_df = train.reset_index(drop=True)
        self.val_df = val.reset_index(drop=True)
        self.test_df = test.reset_index(drop=True)

        return self.train_df, self.val_df, self.test_df

    def get_split_summary(self) -> dict:
        """Get summary statistics of the current split."""
        if self.train_df is None:
            raise RuntimeError("Call split() first.")

        def split_stats(df, name):
            return {
                "name": name,
                "count": len(df),
                "class_distribution": df["diagnosis"].value_counts().sort_index().to_dict(),
            }

        return {
            "train": split_stats(self.train_df, "train"),
            "val": split_stats(self.val_df, "val"),
            "test": split_stats(self.test_df, "test"),
        }

    def save_split(self, output_dir: str = "data/aptos"):
        """Save split information to CSV files."""
        if self.train_df is None:
            raise RuntimeError("Call split() first.")

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        self.train_df.to_csv(output_path / "train_split.csv", index=False)
        self.val_df.to_csv(output_path / "val_split.csv", index=False)
        self.test_df.to_csv(output_path / "test_split.csv", index=False)

        # Save split metadata
        metadata = {
            "train_count": len(self.train_df),
            "val_count": len(self.val_df),
            "test_count": len(self.test_df),
            "split_seed": self.config["project"]["seed"],
            "class_distribution": self.get_split_summary(),
        }

        import json
        with open(output_path / "split_metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)


def load_and_split_aptos(
    data_dir: str = "data/aptos",
    config_path: str = "configs/config.yaml",
    seed: int = 42,
) -> Tuple[AptosDataLoader, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Convenience function to load and split APTOS dataset.

    Returns:
        (loader, train_df, val_df, test_df)
    """
    loader = AptosDataLoader(data_dir=data_dir, config_path=config_path)
    loader.load_data()
    validation = loader.validate()

    print(f"Loaded {validation['total_images']} images")
    print(f"Valid: {validation['valid_images']}, Missing: {validation['missing_images']}")
    print(f"Class distribution: {validation['class_distribution']}")

    if validation["missing_images"] > 0:
        print(f"WARNING: {validation['missing_images']} images missing!")
        print(f"Missing: {validation['missing_files'][:10]}...")

    train, val, test = loader.split(seed=seed)
    summary = loader.get_split_summary()

    print(f"\nSplit summary:")
    print(f"  Train: {summary['train']['count']} images")
    print(f"  Val:   {summary['val']['count']} images")
    print(f"  Test:  {summary['test']['count']} images")

    return loader, train, val, test
