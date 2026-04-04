from __future__ import annotations
from typing import Literal

MetricFamily = Literal[
    "binary",
    "continuous_mean",
    "count_mean",
    "ratio_mean",
]

Alternative = Literal["one-sided", "two-sided"]
Correction = Literal["none", "bonferroni", "sidak"]
DesignMode = Literal["sample_size", "power", "mde", "duration"]

EvaluationMode = Literal[
    "analyze",
    "confidence_interval",
    "significance_test",
]

__all__ = [
    "MetricFamily",
    "Alternative",
    "Correction",
    "DesignMode",
    "EvaluationMode",
]
