# Competitive-Intelligence-HRbound-Estimator

A Claude Code skill that estimates **hazard ratio (HR) bounds** at interim analyses (IAs) and the final analysis (FA) for a survival endpoint in an oncology group sequential trial.

## What it does

- Walks you through study design inputs via structured questions
- Computes the required one-sided alpha for each (HR assumption × event rate) combination using the Schoenfeld formula at your chosen power level (default 90%)
- Calculates HR efficacy bounds at each analysis using O'Brien-Fleming, Pocock, or Hwang-Shih-DeCani (HSD) alpha spending via the `gsDesign` R package
- Summarises the range of HR bounds across all HR × event rate × information fraction scenarios
- Estimates conditional power (CP) at subsequent analyses under the **current trend** assumption

## Prerequisites

- R (≥ 4.0) with the [`gsDesign`](https://CRAN.R-project.org/package=gsDesign) and [`jsonlite`](https://CRAN.R-project.org/package=jsonlite) packages installed
- Claude Code CLI

Install R packages if needed:
```r
install.packages(c("gsDesign", "jsonlite"))
```

## Installation

Copy the skill into your Claude Code skills directory:

```bash
cp -r skills/Competitive-Intelligence-HRbound-Estimator ~/.claude/skills/
```

Or install as a plugin — see the [Claude Code plugin documentation](https://docs.anthropic.com/en/docs/claude-code/plugins).

## Usage

In a Claude Code session, trigger the skill by describing what you need:

> "Estimate the HR bound at IA1 for our survival trial"  
> "What HR do I need to observe at the interim to cross the OBF boundary?"  
> "Calculate HR bounds for a group sequential trial with 1 IA and 1 FA"

The skill will ask 8 questions and then print four tables:

| Table | Content |
|-------|---------|
| 1 | Required one-sided alpha per (HR, event rate) combination |
| 2 | HR bounds per information fraction scenario |
| 3 | HR bound range summary across all scenarios |
| 4 | Final summary with cumulative alpha and conditional power range |

## Inputs collected

| # | Input | Example |
|---|-------|---------|
| Q1 | Total N and randomization ratio | N = 600, 1:1 |
| Q2 | HR assumptions and FA event rate scenarios | HR 0.60–0.65; events 75%–80% of N |
| Q3 | Power level | 90% (default) |
| Q4 | Alpha selection: single value or full grid | Option B — keep all combinations |
| Q5 | Number of IAs and FA | 1 IA + FA |
| Q6 | Alpha spending function | OBF (default), Pocock, or HSD |
| Q7 | Information fraction scenarios | (0.75, 1.0), (0.80, 1.0) |
| Q8 | Current analysis | IA1 |

## Statistical methods

- **Alpha derivation**: Schoenfeld (1981) — `D = (z_α + z_β)² (1+r)² / [r (log HR)²]`
- **Boundary computation**: `gsDesign` R package (`sfLDOF` for OBF, `sfHSD` for HSD)
- **HR bound**: `HR_k = exp(−z_k (1+r) / √(D_k r))`
- **Conditional power**: current trend — `CP = 1 − Φ((c_j − z_k √(t_j/t_k)) / √(1 − t_k/t_j))`

All alphas are **one-sided**.
