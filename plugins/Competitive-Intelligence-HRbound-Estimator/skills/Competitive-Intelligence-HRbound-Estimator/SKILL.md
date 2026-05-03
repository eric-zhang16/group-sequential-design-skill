---
name: Competitive-Intelligence-HRbound-Estimator
description: Estimate hazard ratio (HR) bounds at interim analyses (IAs) and final analysis (FA) for a survival endpoint in an oncology group sequential trial. Use this skill whenever a user wants to plan IA boundaries for a survival trial, calculate what HR needs to be observed at an interim, estimate conditional power at subsequent analyses, or evaluate alpha spending boundaries. Triggers on: "HR bound at IA", "interim analysis boundary", "conditional power survival", "OBF boundary", "alpha spending HR", "group sequential HR", "what HR do I need at interim", "HR bound for IA", "boundary at interim".
---

Walk the user through inputs via structured questions, compute HR bounds and conditional power using the bundled R script (`scripts/compute_hr_bounds.R`). Always use **one-sided alpha**. Default power is **90%**.

## Questions — ask in order, wait for each answer

### Q1 — Sample Size and Randomization Ratio
> "What is the total sample size (N) and randomization ratio (experimental : control)?
> Example: N = 400, ratio 1:1"

Record:
- `N` — total patients randomized
- `r` — ratio as decimal (1:1 → 1, 2:1 → 2)

---

### Q2 — HR Assumptions and Event Rate Scenarios
> "Please provide:
> 1. A list of HR assumptions (e.g., 0.60, 0.63, 0.65, 0.67)
> 2. A list of possible event rates as % of N (e.g., 70%, 75%, 80%)"

Record:
- `hr_list` — HR assumptions
- `event_rates` — as decimals (70% → 0.70)

---

### Q3 — Confirm Power
> "We will assume 90% power for all alpha calculations. Would you like to proceed, or specify a different power level?"

Record:
- `power` — default 0.90

---

### → Compute and display Table 1 (alpha grid) before asking Q4

---

### Q4 — Select Alpha
> "Based on the alpha grid above, please select a one-sided alpha. Two options:
>
> **Option A — Single alpha:** Pick one value. Suggestion: use the 80% event fraction column as the planning anchor (e.g., the alpha corresponding to your primary HR assumption at 80% events).
>
> **Option B — Keep all combinations:** Carry the full alpha range forward. Each (HR, event rate) combination uses its own alpha from the grid. This gives the widest possible range of HR bounds and CP across all design assumptions.
>
> Which would you prefer?"

Record:
- `use_alpha_grid` — `true` if Option B, `false` if Option A
- `alpha` — single value if Option A; omit if Option B (script computes per combination)

---

### Q5 — Number of Analyses
> "How many interim analyses (IAs) and a final analysis (FA) are planned?
> Example: '1 IA and 1 FA' or '2 IAs and 1 FA'"

Record:
- `n_IA` — number of interim analyses
- `k` = n_IA + 1 (total analyses including FA)

---

### Q6 — Spending Function
> "We will use the O'Brien-Fleming (OBF) alpha spending function by default. If you need a different spending function — Pocock or Hwang-Shih-DeCani (HSD) gamma family — please specify now. Otherwise just confirm OBF."

Record:
- `spending` — "OBF" (default), "Pocock", or "HSD"

---

### Q7 — Information Fraction Scenarios
> "Please provide possible information fraction (IF) scenarios. Each scenario is a tuple of length equal to total analyses (last value always 1.0).
>
> For 1 IA + FA, example:
>   (0.75, 1.0), (0.80, 1.0), (0.85, 1.0)
>
> For 2 IAs + FA, example:
>   (0.50, 0.75, 1.0), (0.60, 0.80, 1.0)"

Record:
- `if_scenarios` — list of vectors, each length k, last element = 1.0

---

### Q8 — Current Analysis
> "Which interim analysis are we currently preparing for? (e.g., IA1, IA2)"

Record:
- `current_ia` — 1-based index (IA1 = 1, IA2 = 2)

---

## Computation

Create output directory `output/hr-bound-estimator_<YYYYMMDD>/`, write input JSON, run script.

The script is at `<skill_base_dir>/scripts/compute_hr_bounds.R` where `<skill_base_dir>` is the
base directory shown in the skill context when this skill loads.

Locate `Rscript` for the current platform, then run:

```bash
# Auto-detect Rscript across platforms
RSCRIPT=$(command -v Rscript 2>/dev/null || \
  ls "/c/Program Files/R/R-"*/bin/Rscript.exe 2>/dev/null | sort -V | tail -1)

"$RSCRIPT" "<skill_base_dir>/scripts/compute_hr_bounds.R" "<path_to_input.json>"
```

On Windows the glob will find the newest R version automatically. On macOS/Linux `Rscript` is
normally on PATH. If neither works, ask the user for their Rscript path.

Input JSON — Option A (single alpha):
```json
{
  "N": 400, "r": 1,
  "hr_list": [0.60, 0.65, 0.70],
  "event_rates": [0.70, 0.75, 0.80],
  "power": 0.90,
  "use_alpha_grid": false,
  "alpha": 0.025,
  "k": 2, "spending": "OBF",
  "if_scenarios": [[0.75, 1.0], [0.80, 1.0], [0.85, 1.0]],
  "current_ia": 1
}
```

Input JSON — Option B (alpha grid, one per HR × event rate):
```json
{
  "N": 400, "r": 1,
  "hr_list": [0.60, 0.65, 0.70],
  "event_rates": [0.70, 0.75, 0.80],
  "power": 0.90,
  "use_alpha_grid": true,
  "alpha": null,
  "k": 2, "spending": "OBF",
  "if_scenarios": [[0.75, 1.0], [0.80, 1.0], [0.85, 1.0]],
  "current_ia": 1
}
```

Display all printed output to the user.

---

## Output Format Reference

**Table 1 — Required One-Sided Alpha** (displayed before Q4)
```
                  Event Rate (% of N)
               70%      75%      80%
            -------  -------  -------
HR = 0.60   0.0014   0.0008   0.0005
HR = 0.65   0.0101   0.0071   0.0051
Events (D)    280      300      320
```

**Table 2 — HR Bounds per IF Scenario** (one block per scenario)
```
IF Scenario: (0.80, 1.00)
Event Rate   D(total)  D(IA1)  HR(IA1)   D(FA)  HR(FA)
   70%          280      224    0.746      280    0.787
   75%          300      240    0.754      300    0.794
   80%          320      256    0.760      320    0.799
```

**Table 3 — HR Bound Range Summary**
```
Analysis          D Range        HR Bound Range
IA1 [current]   210 – 272       0.732 – 0.773
FA              280 – 320       0.787 – 0.800
```

**Table 4 — Final Summary**
```
Analysis          HR Bound Range     CP Range (current trend)
IA1 [current]     0.732 – 0.773      —
FA                0.787 – 0.800      xx% – xx%
```

CP logic:
- Computed only for analyses **after** `current_ia`
- Range comes from min/max HR bound scenarios at the current IA
- Method: current trend — observed HR at current IA projects forward to subsequent analyses
- Formula: `CP = 1 - Phi((c_j - z_k * sqrt(t_j/t_k)) / sqrt(1 - t_k/t_j))`
  where z_k and c_j are gsDesign boundaries, t_k and t_j are information fractions
