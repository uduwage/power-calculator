"""Shared helpers for experiment allocation parsing and normalization."""

from __future__ import annotations


def _parse_allocation(allocation: str, groups: int) -> list[float]:
    """Parse allocation into normalized per-group shares.

    Supported input forms:
    - groups=2: `control:treatment` (e.g. `50:50`)
    - groups>2: explicit `control:t1:t2:...` with exactly `groups` values
      (e.g. `50:25:25` for 3 groups).

    Args:
        allocation: Allocation text separated by `:`.
        groups: Total number of experiment groups, including control.

    Returns:
        Normalized per-group shares as `[control, treatment_1, ...]`.

    Raises:
        ValueError: If parsing fails, count does not match allowed formats,
            or any value is non-positive.
    """
    try:
        weights = [float(part.strip()) for part in allocation.split(":")]
    except (AttributeError, ValueError) as exc:
        raise ValueError(
            "Allocation must be in 'control:treatment' or "
            "'control:t1:t2:...' format (i.e. 50:50 or 33:33:34)."
        ) from exc

    if len(weights) < 2:
        raise ValueError("Allocation must include at least control and one treatment.")
    if any(weight <= 0 for weight in weights):
        raise ValueError("Allocation values must all be positive.")

    if len(weights) == 2 and groups == 2 or len(weights) == groups:
        expanded = weights
    else:
        if groups == 2:
            guidance = (
                "For 2 groups, provide exactly two values like "
                "'control:treatment' (e.g. 50:50)."
            )
        else:
            guidance = (
                "For groups > 2, provide exactly one value per group "
                "(e.g. 50:25:25)."
            )
        raise ValueError(
            f"Allocation has {len(weights)} values but groups={groups}. " + guidance
        )
    total = sum(expanded)
    return [weight / total for weight in expanded]


__all__ = ["_parse_allocation"]
