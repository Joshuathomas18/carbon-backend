"""XGBoost carbon sequestration prediction model."""

import json
import logging
import pickle
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

MODEL_PATH = Path(__file__).parent.parent.parent / "models" / "carbon_regressor.pkl"
VERRA_DATA_PATH = (
    Path(__file__).parent.parent / "data" / "verra_training_data.csv"
)


class CarbonModel:
    """XGBoost model for carbon sequestration prediction."""

    def __init__(self):
        """Initialize carbon model."""
        self.model = None
        self.feature_names = None
        self.load_or_train()

    def load_or_train(self):
        """Load existing model or train new one."""
        if MODEL_PATH.exists():
            self.load_model()
            logger.info("✓ Loaded pre-trained carbon model")
        else:
            logger.info("Training new carbon model...")
            self.train_model()
            self.save_model()

    def train_model(self):
        """Train XGBoost on Verra data."""
        try:
            import xgboost as xgb
            from sklearn.preprocessing import StandardScaler
        except ImportError:
            logger.error("xgboost not installed, using mock model")
            self._create_mock_model()
            return

        # Load training data
        try:
            df = pd.read_csv(VERRA_DATA_PATH)
            logger.info(f"Loaded {len(df)} Verra projects for training")
        except Exception as e:
            logger.error(f"Could not load training data: {e}")
            self._create_mock_model()
            return

        # Feature engineering
        # Encode categorical features
        state_map = {
            state: i
            for i, state in enumerate(df["state"].unique())
        }
        crop_map = {
            crop: i
            for i, crop in enumerate(df["crop_type"].unique())
        }

        X = pd.DataFrame({
            "state_code": df["state"].map(state_map),
            "crop_code": df["crop_type"].map(crop_map),
            "soil_clay": df["soil_clay_percent"],
            "soil_org_carbon": df["soil_organic_carbon"],
            "burning_history": (~df["practice_burning"].astype(bool)).astype(int),
            "residue_retained": df["practice_residue"],
            "cover_crop": df["practice_cover_crop"],
            "years_since_baseline": df["years_since_baseline"],
        })

        y = df["verified_tonnes_co2_per_hectare"]

        # Train XGBoost
        self.model = xgb.XGBRegressor(
            max_depth=5,
            learning_rate=0.1,
            n_estimators=100,
            random_state=42,
            verbosity=0,
        )
        self.model.fit(X, y)
        self.feature_names = X.columns.tolist()

        # Model performance
        train_score = self.model.score(X, y)
        logger.info(f"✓ Model trained. R² = {train_score:.3f}")

        # Feature importance
        importance = dict(zip(self.feature_names, self.model.feature_importances_))
        logger.info(f"✓ Feature importance: {json.dumps(importance, indent=2)}")

    def _create_mock_model(self):
        """Create mock model (when xgboost not available)."""
        logger.warning("Creating mock model for MVP")
        self.feature_names = [
            "state_code",
            "crop_code",
            "soil_clay",
            "soil_org_carbon",
            "burning_history",
            "residue_retained",
            "cover_crop",
            "years_since_baseline",
        ]
        self.model = "mock"

    def predict(
        self,
        state_code: int,
        crop_code: int,
        soil_clay: float,
        soil_org_carbon: float,
        burning_history: int,
        residue_retained: int,
        cover_crop: int = 0,
        years_since_baseline: int = 2,
    ) -> Tuple[float, float]:
        """
        Predict carbon sequestration.

        Returns:
            (predicted_tonnes_co2_per_hectare, confidence_score)
        """
        if self.model == "mock":
            # Mock prediction: base + adjustments
            base = 1.5
            base += soil_org_carbon * 0.5
            base += (soil_clay / 30) * 0.3
            base += burning_history * 0.2
            base += residue_retained * 0.15
            base += cover_crop * 0.12
            base += years_since_baseline * 0.05

            return round(max(0.5, base), 2), 0.75

        try:
            import xgboost as xgb

            features = np.array(
                [
                    [
                        state_code,
                        crop_code,
                        soil_clay,
                        soil_org_carbon,
                        burning_history,
                        residue_retained,
                        cover_crop,
                        years_since_baseline,
                    ]
                ]
            )

            prediction = self.model.predict(features)[0]
            confidence = 0.82  # Base confidence, could be improved with variance

            return round(max(0.5, prediction), 2), round(confidence, 2)

        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return 1.5, 0.50

    def save_model(self):
        """Save model to disk."""
        try:
            MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(MODEL_PATH, "wb") as f:
                pickle.dump(
                    {"model": self.model, "features": self.feature_names}, f
                )
            logger.info(f"✓ Model saved to {MODEL_PATH}")
        except Exception as e:
            logger.error(f"Error saving model: {e}")

    def load_model(self):
        """Load model from disk."""
        try:
            with open(MODEL_PATH, "rb") as f:
                data = pickle.load(f)
                self.model = data["model"]
                self.feature_names = data["features"]
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            self.train_model()


# Global model instance
_carbon_model = None


def get_carbon_model() -> CarbonModel:
    """Get or create global carbon model instance."""
    global _carbon_model
    if _carbon_model is None:
        _carbon_model = CarbonModel()
    return _carbon_model
