"""
SHAP explanations for individual scoring decisions.

"""

import logging
from typing import Any, Dict, List

import numpy as np

from pipeline.preprocessing import add_derived_features

logger = logging.getLogger(__name__)


class Explainer:
    """Wraps a SHAP TreeExplainer around the fitted pipeline.

    The pipeline is (features -> classifier). SHAP needs the raw estimator and
    the TRANSFORMED matrix, so this class holds both halves and does the
    transformation itself. Handing the whole pipeline to shap and hoping is
    the usual mistake.
    """

    def __init__(self, pipeline: Any):
        self.pipeline = pipeline
        self.feature_step = pipeline.named_steps["features"]
        self.classifier = pipeline.named_steps["classifier"]
        self.feature_names = list(
            self.feature_step.named_steps["preprocess"].get_feature_names_out()
        )
        self._explainer = None

    def _ensure_explainer(self):
        """Build the explainer on first use.

        Lazily, because importing shap costs about a second and a container
        that is not asked for explanations should not pay it at startup.
        """
        if self._explainer is None:
            import shap

            self._explainer = shap.TreeExplainer(self.classifier)
        return self._explainer

    def explain(self, frame, top_n: int = 8) -> Dict[str, Any]:
        """Return the features that moved this one score, largest first.

        TASK 10:
          - Transform the frame with self.feature_step, then call
            shap_values on self.classifier's explainer.
          - Depending on the model, shap returns (n, features) or
            (n, features, classes). Normalise to the positive class.
          - expected_value may be a scalar or an array; normalise it too.
          - Sort by ABSOLUTE contribution and keep the top n.
          - Report the applicant's OWN value for each feature, not the
            standardised one. add_derived_features(frame) gives you the
            derived ones; one-hot columns have no counterpart in the
            application and fall back to the transformed value. An adverse
            action notice quoting "your PAY_0 was 2.16" cannot be reconciled
            with the application form by anyone outside the ML team.
        """
        explainer = self._ensure_explainer()

        # Transform the frame using the feature pipeline step
        X_transformed = self.feature_step.transform(frame)

        # Compute SHAP values
        shap_values = explainer.shap_values(X_transformed)

        # Normalise to positive class (class 1):
        # shap may return (n, features) for binary or (n, features, classes)
        if isinstance(shap_values, list):
            # List of arrays: one per class — take class 1 if present, else 0
            sv = np.array(shap_values[1])[0] if len(shap_values) > 1 else np.array(shap_values[0])[0]
        elif len(np.array(shap_values).shape) == 3:
            # (n, features, classes) — take class 1 if present
            arr = np.array(shap_values)
            sv = arr[0, :, 1] if arr.shape[2] > 1 else arr[0, :, 0]
        else:
            # (n, features) — already positive class
            sv = np.array(shap_values)[0]

        # Normalise expected_value to positive class scalar
        expected_value = explainer.expected_value
        if hasattr(expected_value, "__len__"):
            base_value = float(expected_value[1]) if len(expected_value) > 1 else float(expected_value[0])
        else:
            base_value = float(expected_value)

        # Build a rich frame with derived features for raw value lookup
        enriched = add_derived_features(frame)
        enriched_row = enriched.iloc[0]

        # Map transformed feature names to raw applicant values
        contributions: List[Dict[str, Any]] = []
        for i, feat_name in enumerate(self.feature_names):
            contribution = float(sv[i])
            # Try to get the raw value from the enriched frame; fall back to transformed
            if feat_name in enriched_row.index:
                raw_value = float(enriched_row[feat_name])
            else:
                raw_value = float(X_transformed[0, i])

            contributions.append({
                "feature": feat_name,
                "value": raw_value,
                "contribution": contribution,
                "direction": "increases risk" if contribution > 0 else "reduces risk",
            })

        # Sort by absolute contribution, keep top_n
        contributions.sort(key=lambda c: abs(c["contribution"]), reverse=True)
        contributions = contributions[:top_n]

        return {
            "base_value": base_value,
            "contributions": contributions,
            "note": (
                "SHAP values are in log-odds. Positive = increases default probability."
            ),
        }
