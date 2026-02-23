# power-calculator

`power-calculator` is a Python tool for planning A/B(/n) experiments with **binary metrics** (for example: conversion, click-through, subscribe/not-subscribe).

It helps you answer:
- How many users do I need per group?
- How many total users do I need for A/B/n?
- How many days will it likely take given my traffic?

## Features

- Binary metric sample size calculation using normal approximation of two proportions.
- Supports:
  - one-sided and two-sided alternative hypotheses
  - confidence level `(1 - alpha)`
  - power `(1 - beta)`
  - number of groups (A/B or A/B/n)
  - multiple testing correction: `none`, `bonferroni`, `sidak`
  - baseline metric rate (%)
  - MDE (`Y_t - Y_c`) in percentage points
  - control:treatment allocation ratio (default `50:50`)
- Optional duration estimate from:
  - daily users
  - eligible rate

## Project Structure

- `power_calculator/binary_power.py`: sample-size engine
- `power_calculator/duration.py`: consolidated duration calculations
- `power_calculator/cli.py`: command-line interface

## Setup

### Prerequisites

- Python `>= 3.8`
- `pip` or `poetry`

### Option 1: Poetry (recommended)

```bash
git clone git@github.com:uduwage/power-calculator.git
cd power-calculator
poetry install
poetry run power-calculator --help
```

### Option 2: pip (editable install)

```bash
git clone git@github.com:uduwage/power-calculator.git
cd power-calculator
python -m venv .venv
source .venv/bin/activate
pip install -e .
power-calculator --help
```

### Run without installing entrypoint

```bash
python -m power_calculator.cli --help
```

### Option 3: Docker

Build image:

```bash
docker build -t power-calculator:latest .
```

Run help:

```bash
docker run --rm power-calculator:latest --help
```

Run a sample calculation:

```bash
docker run --rm power-calculator:latest \
  --baseline-rate 10 \
  --mde 2 \
  --daily-users 5000 \
  --eligible-rate 90
```

## CLI Usage

### Minimal required command

```bash
python -m power_calculator.cli --baseline-rate 10 --mde 2
```

### Main arguments

- `--alternative`: `one-sided` or `two-sided` (default: `two-sided`)
- `--confidence`: confidence level, accepts `95` or `0.95` (default: `95`)
- `--power`: statistical power, accepts `80` or `0.8` (default: `80`)
- `--groups`: total groups including control (default: `2`)
- `--correction`: `none`, `bonferroni`, `sidak` (default: `none`)
- `--baseline-rate`: baseline binary rate in percent (required)
- `--mde`: minimum detectable effect in percentage points (required)
- `--allocation`: `control:treatment` ratio (default: `50:50`)
- `--daily-users`: average daily experiment users for duration estimate (optional)
- `--eligible-rate`: eligible share of daily users, accepts `90` or `0.9` (default: `100`)

### Example: Two-sided A/B

```bash
python -m power_calculator.cli \
  --alternative two-sided \
  --confidence 95 \
  --power 80 \
  --groups 2 \
  --baseline-rate 10 \
  --mde 2 \
  --allocation 50:50
```

### Example: A/B/n with correction and uneven allocation

```bash
python -m power_calculator.cli \
  --alternative one-sided \
  --confidence 95 \
  --power 80 \
  --groups 4 \
  --correction bonferroni \
  --baseline-rate 10 \
  --mde 2 \
  --allocation 40:60
```

### Example: Include duration estimate

```bash
python -m power_calculator.cli \
  --baseline-rate 10 \
  --mde 2 \
  --daily-users 5000 \
  --eligible-rate 90
```

This prints a `Duration Estimate` section with:
- expected daily eligible users
- estimated duration in days
- bottleneck group (for multi-group/custom allocation cases)

## Python API Usage

### Sample size

```python
from power_calculator import SampleSizeInput, calculate_sample_size

result = calculate_sample_size(
    SampleSizeInput(
        alternative="two-sided",
        confidence_level=0.95,
        power=0.80,
        groups=2,
        correction="none",
        baseline_rate_pct=10.0,
        mde_pct=2.0,
        allocation="50:50",
    )
)

print(result.control_sample_size)
print(result.treatment_sample_size)
print(result.overall_total)
```

### Duration: total sample size

```python
from power_calculator import estimate_duration

d = estimate_duration(
    total_sample_size=7682,
    daily_users=5000,
    eligible_rate=0.9,
)
print(d.days_required)
```

### Duration: by group (advanced)

```python
from power_calculator import estimate_duration_by_group

d = estimate_duration_by_group(
    group_sample_sizes={"control": 3186, "treatment_1": 4779, "treatment_2": 4779},
    daily_users=12000,
    traffic_shares={"control": 0.4, "treatment_1": 0.3, "treatment_2": 0.3},
    eligible_rate=0.8,
)
print(d.days_per_group)
print(d.days_required)
```

## Assumptions

- Binary outcome is modeled as Bernoulli (success/fail per user).
- For `groups > 2`, the calculator assumes one control compared pairwise with each treatment.
- Multiple-testing correction is applied across `(groups - 1)` comparisons.
- `MDE` is interpreted as absolute percentage-point lift (`variant = baseline + MDE`).

## Validation Rules

Common input checks include:
- confidence and power must be in `(0, 1)` (or `%` form in CLI)
- baseline rate and MDE must be valid percentages
- `groups >= 2`
- allocation values must be positive and in `control:treatment` format
- duration inputs require positive `daily_users`, and `eligible_rate` in `(0, 1]`

## Development

Install dev dependencies:

```bash
poetry install
```

Run tests:

```bash
poetry run pytest
```

Build container with Make:

```bash
make docker.build
make docker.run
```

## License

MIT
