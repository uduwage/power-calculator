"""Shared interfaces for metric-family implementations."""

from __future__ import annotations

from typing import Protocol, TypeVar, runtime_checkable

from .models import DesignRequest, DesignSampleSizeResult

MetricFamilyDesignInputsType = TypeVar("MetricFamilyDesignInputsType")


@runtime_checkable
class MetricFamilyDesignCalculator(Protocol[MetricFamilyDesignInputsType]):
    """Shared contract for metric-family design calculators.

    Notes:
        The first shared capability is sample-size calculation. Additional
        design and evaluation methods can be added later as the architecture
        expands.
    """

    def calculate_sample_size(
        self,
        request: DesignRequest[MetricFamilyDesignInputsType],
    ) -> DesignSampleSizeResult:
        """Calculate sample size for the given metric-family design request."""
        ...


__all__ = ["MetricFamilyDesignCalculator"]
