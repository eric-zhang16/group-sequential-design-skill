# KM Plot Digitizer & IPD Reconstruction

Extracts survival curve data from published Kaplan-Meier plot images and reconstructs individual patient-level time-to-event data (IPD), producing a Word report with KM comparison plots, survival statistics, and hazard rate curves.

## Plugin Structure

```
km-digitizer/                        # Plugin root
├── .claude-plugin/
│   └── plugin.json                  # Plugin metadata (name, description, author)
├── skills/
│   └── km-digitizer/                # Skill content
│       ├── SKILL.md                 # Skill instructions and workflow
│       ├── scripts/
│       │   ├── setup_wizard.py      # Interactive GUI to define axis boundaries and calibration points
│       │   ├── digitize_km.py       # Color-tracks curve pixels and calibrates pixel->data coordinates
│       │   ├── reconstruct_ipd.R    # Reconstructs individual patient TTE data via IPDfromKM
│       │   ├── plot_km_hazard.R     # KM comparison and B-spline hazard rate plots
│       │   ├── survival_stats.R     # Median and survival rates per arm
│       │   └── generate_report.py   # Assembles Word report from plots and statistics
│       └── evals/
│           └── evals.json           # Evaluation scenarios
└── README.md                        # This file
```

## Pipeline

```
PNG image
  → digitize_km.py       → km_digitized.json     (curve coordinates)
  → reconstruct_ipd.R    → ipd_combined.csv       (patient-level data)
  → generate_report.py   → reconstruction_report.docx
```

## Scripts

| Script | Language | Purpose |
|--------|----------|---------|
| `setup_wizard.py` | Python | Interactive GUI — click axis boundaries and calibration points to generate `config.json` |
| `digitize_km.py` | Python | Color-tracks curve pixels in the PNG; calibrates pixel→data coordinates; outputs digitized JSON |
| `reconstruct_ipd.R` | R | Reconstructs individual patient time-to-event data using `IPDfromKM::getIPD()` |
| `plot_km_hazard.R` | R | KM comparison plot (digitized vs reconstructed) and B-spline hazard rate curve |
| `survival_stats.R` | R | Median and survival rates per arm via `survival::survfit()` |
| `generate_report.py` | Python | Assembles Word report from R-generated plots and survival statistics table |

## Quick Start

### 1. Set up config

**Option A — Interactive wizard (recommended for new plots):**
```bash
python scripts/setup_wizard.py reference/KMPlot/<study>.png output/<study>/
```
The wizard opens a matplotlib window; click the axis boundaries and annotated calibration points, then enter number-at-risk values in the terminal.

**Option B — Automated (Claude does this when no display is available):** Claude reads the PNG to extract annotated values, runs a Python/OpenCV scan to find exact axis pixel positions, and writes `config.json` automatically. No user input required.

### 2. Digitize
```bash
python scripts/digitize_km.py output/<study>/config.json
```
Always inspect the `debug_image` output:
- **Green rectangle** — optimized plot region
- **Yellow dots** — tracked pixels for curve 0 (higher survival arm)
- **Magenta dots** — tracked pixels for curve 1 (lower survival arm)

### 3. Reconstruct IPD
```bash
Rscript scripts/reconstruct_ipd.R output/<study>/km_digitized.json output/<study>/
```

### 4. Generate report
```bash
python scripts/generate_report.py \
  output/<study>/km_digitized.json \
  output/<study>/ipd_combined.csv \
  output/<study>/
```

## Config Reference

```json
{
    "image_path": "reference/KMPlot/study_os.png",
    "plot_region": {"left": 219, "top": 98, "right": 1276, "bottom": 518},
    "x_range": [0, 72],
    "y_range": [0, 100],
    "x_label": "Time (months)",
    "y_label": "OS (%)",
    "calibration_points": [
        {"month": 12, "survival": 69.8, "curve": 0},
        {"month": 24, "survival": 45.7, "curve": 0},
        {"month": 36, "survival": 31.3, "curve": 0},
        {"month": 48, "survival": 23.6, "curve": 0},
        {"month": 60, "survival": 19.4, "curve": 0},
        {"month": 12, "survival": 48.0, "curve": 1},
        {"month": 24, "survival": 27.3, "curve": 1},
        {"month": 36, "survival": 17.4, "curve": 1},
        {"month": 48, "survival": 13.8, "curve": 1},
        {"month": 60, "survival": 11.3, "curve": 1}
    ],
    "number_at_risk": {
        "times": [0, 12, 24, 36, 48, 60, 72],
        "counts": {
            "Treatment arm": [410, 283, 184, 126, 95, 77, 0],
            "Control arm":   [206,  98,  55,  34, 27, 22, 0]
        }
    },
    "curve_names": ["Treatment arm", "Control arm"],
    "output_path": "output/study_os/km_digitized.json",
    "debug_image": "output/study_os/km_debug.png",
    "y_tolerance": 1.5
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `image_path` | Yes | Path to the KM plot PNG |
| `plot_region` | Yes | Pixel coordinates of the data area. Use the wizard or scan programmatically for dark axis lines — never visually estimate (causes systematic time shifts) |
| `x_range` | Yes | Data-space X-axis limits, e.g. `[0, 72]` |
| `y_range` | Yes | Data-space Y-axis limits, e.g. `[0, 100]` |
| `calibration_points` | Recommended | Known (month, survival%) pairs. `curve`: 0 = top arm, 1 = bottom arm. **Collect ALL labeled timepoints from BOTH curves** — not just 2. More points = better accuracy, especially in the early overlap zone |
| `number_at_risk` | For IPD | NaR table matching curve names. Required for `reconstruct_ipd.R` and for tail truncation |
| `curve_names` | Optional | Labels in survival-rank order (highest first). Must match `number_at_risk.counts` keys |
| `output_path` | Yes | Destination for digitized JSON |
| `debug_image` | Recommended | Destination for debug overlay PNG |
| `y_tolerance` | Optional | Min survival % change to register as a step (default: 1.0) |

## Report Contents

The generated `reconstruction_report.docx` contains:

1. **KM curve comparison** — digitized original (left) vs reconstructed from IPD (right)
2. **Survival statistics table** — N, Events n (%), median, and survival rates at NaR timepoints per arm
3. **Hazard rate plot** — B-spline smoothed hazard, truncated where any arm drops below 20% at risk
4. **Appendix** — original KM plot image

## Key Tips

- **Calibration is the biggest lever on accuracy** — use every annotated survival value printed on the plot, for both curves. RMSE < 1% is achievable with 5+ points per curve.
- **plot_region must come from pixel scanning**, not visual guessing — a few pixels of error in the left/right boundary translates to months of time shift.
- **number_at_risk keys must exactly match curve_names** — the reconstruction script matches by name.
- **Curves must be distinct colors** — the tracker cannot separate same-colored curves.

## Dependencies

**Python:** `opencv-python`, `numpy`, `python-docx`, `pandas`, `matplotlib`

**R packages:** `IPDfromKM`, `jsonlite`, `survival`, `survminer`, `bshazard`, `ggplot2`, `gridExtra`, `scales`
