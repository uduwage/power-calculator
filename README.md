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
  - allocation ratios:
    - `groups=2`: `control:treatment` (default `50:50`)
    - `groups>2`: explicit `control:t1:t2:...` (for example `40:60:60:60`)
- Optional duration estimate from:
  - daily users
  - eligible rate

## Project Structure

- `power_calculator/binary_power.py`: sample-size engine
- `power_calculator/duration.py`: consolidated duration calculations
- `power_calculator/cli.py`: command-line interface

## Repository Layout

```text
power-calculator/
|-- power_calculator/
|   |-- __init__.py         # Public package exports
|   |-- binary_power.py     # Binary metric sample-size calculations
|   |-- duration.py         # Duration estimators (total/equal-group/by-group)
|   |-- cli.py              # CLI entrypoint and argument parsing
|-- pyproject.toml          # Poetry config, dependencies, tool settings
|-- Makefile                # Format/lint/docker helper commands
|-- Dockerfile              # Container image definition
|-- .dockerignore           # Docker build context exclusions
|-- README.md               # Usage and setup documentation
|-- LICENSE                 # Project license
```

## Setup

### Prerequisites

- Python `>=3.10,<3.13`
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

Build image with explicit Python version:

```bash
docker build --build-arg PYTHON_VERSION=3.12-slim -t power-calculator:latest .
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
- `--allocation`:
  - for `--groups 2`: `control:treatment` (default: `50:50`)
  - for `--groups > 2`: `control:t1:t2:...` with exactly one value per group
  - note: although the CLI flag has default `50:50`, for `--groups > 2` you must
    explicitly pass a valid multi-group allocation
- `--daily-users`: average daily experiment users for duration estimate (optional)
- `--eligible-rate`: eligible share of daily users, accepts `90` or `0.9` (default: `1.0`)

### What `--correction` means

When `groups > 2`, you usually compare one control against multiple treatments (`groups - 1` comparisons).  
`--correction` adjusts alpha to control false positives across those multiple comparisons:

- `none`: no adjustment
- `bonferroni`: `adjusted_alpha = alpha / comparisons`
- `sidak`: `adjusted_alpha = 1 - (1 - alpha)^(1 / comparisons)`

For `groups = 2`, correction has no practical effect because there is only one comparison.

### Allocation format notes

- For `groups=2`, use two values like `50:50`.
- For `groups>2`, pass exactly one value per group, including control.
  - Example: `--groups 3 --allocation 50:25:25`
  - Example: `--groups 4 --allocation 40:20:20:20`
- Current engine behavior: treatment allocations must be equal across treatment
  arms for sample-size calculation.
  - Supported now (equal treatment arms): `34:33:33` for 3 groups.
  - Not supported yet (non-uniform treatment arms): `34:40:26` for 3 groups.
- Current CLI output shows `Allocation (control:treatment)` as the pairwise
  ratio used in sample-size formulas (control vs each treatment), not the full
  global traffic vector. For example, `34:33:33` prints approximately
  `50.75%:49.25%` in that pairwise line.

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
  --allocation 40:60:60:60
```

### Example: A/B/C with explicit split (supported)

```bash
python -m power_calculator.cli \
  --alternative two-sided \
  --confidence 95 \
  --power 80 \
  --groups 3 \
  --baseline-rate 10 \
  --mde 1 \
  --allocation 34:33:33
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

### Example: Set every input parameter (all non-default values)

```bash
python -m power_calculator.cli \
  --alternative one-sided \
  --confidence 92 \
  --power 85 \
  --groups 5 \
  --correction sidak \
  --baseline-rate 12.5 \
  --mde 1.8 \
  --allocation 45:55:55:55:55 \
  --daily-users 7500 \
  --eligible-rate 92
```

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
- allocation values must be positive
- for `groups=2`, allocation must have 2 values: `control:treatment`
- for `groups>2`, allocation must have exactly `groups` values: `control:t1:t2:...`
- treatment allocations must currently be uniform across treatment arms
- duration inputs require positive `daily_users`, and `eligible_rate` in `(0, 1]`

## References

- Casagrande, J. T., Pike, M. C., & Smith, P. G. (1978). *An improved approximate formula for calculating sample sizes for comparing two binomial distributions*. Biometrics, 34(3), 483-486. DOI: https://doi.org/10.2307/2530613
- Fleiss, J. L., Tytun, A., & Ury, H. K. (1980). *A simple approximation for calculating sample sizes for comparing independent proportions*. Biometrics, 36(2), 343-346. DOI: https://doi.org/10.2307/2529990
- Sidak, Z. (1967). *Rectangular confidence regions for the means of multivariate normal distributions*. Journal of the American Statistical Association, 62(318), 626-633. DOI: https://doi.org/10.1080/01621459.1967.10482935
- Dunn, O. J. (1961). *Multiple comparisons among means*. Journal of the American Statistical Association, 56(293), 52-64. DOI: https://doi.org/10.2307/2282330
- Kohavi, R., Tang, D., & Xu, Y. (2020). *Trustworthy Online Controlled Experiments: A Practical Guide to A/B Testing*. Cambridge University Press. DOI: https://doi.org/10.1017/9781108653985
- Acklam, P. J. (2000). *An algorithm for computing the inverse normal cumulative distribution function* (reference implementation note used for the normal quantile approximation). Archived source: http://web.archive.org/web/20151030215612/http://home.online.no/~pjacklam/notes/invnorm/

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

## Solving asdf or poetry issues

```bash
cd .../power-calculator

# 1) Install poetry version from .tool-versions
asdf install poetry 2.2.1
asdf reshim

# 2) Confirm poetry resolves from asdf
which poetry
poetry --version

# 3) Recreate project venv with current python 3.12.9
poetry env remove --all
poetry env use "$(asdf where python 3.12.9)/bin/python"

# 4) Install dependencies incl dev tools (ruff/black/mypy)
poetry install --with dev

# 5) Verify tools
poetry run ruff --version
poetry run black --version
poetry run mypy --version

# 6) Run format
make format
```

## License

MIT
