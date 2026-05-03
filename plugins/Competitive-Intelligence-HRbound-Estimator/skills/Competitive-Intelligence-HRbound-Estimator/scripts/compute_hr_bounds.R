#!/usr/bin/env Rscript
# compute_hr_bounds.R
# HR bounds and conditional power for group sequential survival trial
# Usage: Rscript compute_hr_bounds.R <input.json>

suppressPackageStartupMessages({
  for (pkg in c("gsDesign", "jsonlite")) {
    if (!requireNamespace(pkg, quietly = TRUE))
      install.packages(pkg, repos = "https://cran.r-project.org")
    library(pkg, character.only = TRUE)
  }
})

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 1) stop("Usage: Rscript compute_hr_bounds.R <input.json>")
inp <- fromJSON(args[1])

N           <- inp$N
r           <- inp$r
hr_list     <- as.numeric(inp$hr_list)
event_rates <- as.numeric(inp$event_rates)
power       <- inp$power
alpha       <- inp$alpha
k           <- inp$k
spending    <- inp$spending
current_ia  <- inp$current_ia

# if_scenarios: may come in as a matrix or list depending on jsonlite
if (is.matrix(inp$if_scenarios)) {
  if_scenarios <- lapply(seq_len(nrow(inp$if_scenarios)),
                         function(i) as.numeric(inp$if_scenarios[i, ]))
} else {
  if_scenarios <- lapply(inp$if_scenarios, as.numeric)
}

z_beta         <- qnorm(power)
use_alpha_grid <- isTRUE(inp$use_alpha_grid)
D_values       <- round(event_rates * N)
er_labels      <- paste0(round(event_rates * 100), "%")

# Pre-compute alpha grid (used for display and optionally for per-combination alpha)
alpha_grid <- outer(seq_along(hr_list), seq_along(event_rates), Vectorize(function(i, j) {
  za <- abs(log(hr_list[i])) * sqrt(D_values[j] * r / (1 + r)^2) - z_beta
  1 - pnorm(za)
}))

sfu_fn <- switch(spending,
  "OBF"    = sfLDOF,
  "Pocock" = sfLDPocock,
  "HSD"    = sfHSD,
  sfLDOF
)

analysis_labels <- c(if (k > 1) paste0("IA", seq_len(k - 1)), "FA")

# ================================================================
# TABLE 1: Required One-Sided Alpha (Schoenfeld)
# ================================================================
cat("\n====== Required One-Sided Alpha ======\n")
cat(sprintf("N = %d | Randomization %g:1 | Power = %.0f%%\n\n", N, r, power * 100))

col_w <- 10
cat(sprintf("%-12s", ""))
for (er in er_labels) cat(sprintf("%*s", col_w, er))
cat("\n")
cat(strrep("-", 12 + col_w * length(er_labels)), "\n")

for (i in seq_along(hr_list)) {
  cat(sprintf("HR = %-6.2f", hr_list[i]))
  for (j in seq_along(event_rates)) {
    za  <- abs(log(hr_list[i])) * sqrt(D_values[j] * r / (1 + r)^2) - z_beta
    cat(sprintf("%*s", col_w, sprintf("%.4f", 1 - pnorm(za))))
  }
  cat("\n")
}
cat(sprintf("\n%-12s", "Events (D)"))
for (D in D_values) cat(sprintf("%*d", col_w, D))
cat("\n")

# ================================================================
# Compute all (IF scenario × event rate) combinations
# ================================================================
results <- list()

for (si in seq_along(if_scenarios)) {
  timing <- if_scenarios[[si]]

  for (ej in seq_along(event_rates)) {
    D_total <- D_values[ej]

    for (hi in seq_along(hr_list)) {
      alpha_use <- if (use_alpha_grid) alpha_grid[hi, ej] else inp$alpha

      gsd      <- gsDesign(k = k, test.type = 1, alpha = alpha_use, beta = 1 - power,
                           sfu = sfu_fn, timing = timing)
      z_bounds <- gsd$upper$bound

      D_k  <- round(timing * D_total)
      hr_b <- exp(-z_bounds * (1 + r) / sqrt(D_k * r))

    # Conditional power for analyses after current_ia (current trend)
    cp <- rep(NA_real_, k)
    t_cur <- timing[current_ia]
    z_cur <- z_bounds[current_ia]

    for (ji in seq_len(k)) {
      if (ji > current_ia) {
        t_j   <- timing[ji]
        c_j   <- z_bounds[ji]
        ratio <- t_cur / t_j
        cp[ji] <- 1 - pnorm((c_j - z_cur * sqrt(t_j / t_cur)) / sqrt(1 - ratio))
      }
    }

      results[[length(results) + 1]] <- list(
        timing      = timing,
        hr_assumed  = hr_list[hi],
        alpha_use   = alpha_use,
        event_rate  = event_rates[ej],
        D_total     = D_total,
        D_k         = D_k,
        z_bounds    = z_bounds,
        hr_bounds   = hr_b,
        cp          = cp,
        cum_alpha   = cumsum(gsd$upper$spend)
      )
    }  # end hi loop
  }    # end ej loop
}      # end si loop

# ================================================================
# TABLE 2: HR Bounds per IF Scenario
# ================================================================
cat("\n\n====== HR Bounds at Each Analysis — Per IF Scenario ======\n")
cat(sprintf("alpha = %.4f (one-sided) | %s spending | Power = %.0f%%\n",
            alpha, spending, power * 100))

unique_timings <- unique(lapply(results, function(x) x$timing))

for (timing in unique_timings) {
  sc <- Filter(function(x) isTRUE(all.equal(x$timing, timing)), results)

  t_str <- paste(sprintf("%.2f", timing), collapse = ", ")
  cat(sprintf("\nIF Scenario: (%s)\n", t_str))

  # Header
  hdr_parts <- c(sprintf("%-12s %9s", "Event Rate", "D(total)"))
  for (ai in seq_len(k)) {
    hdr_parts <- c(hdr_parts,
                   sprintf("%9s %10s",
                           paste0("D(", analysis_labels[ai], ")"),
                           paste0("HR(", analysis_labels[ai], ")")))
  }
  hdr <- paste(hdr_parts, collapse = "")
  cat(hdr, "\n")
  cat(strrep("-", nchar(hdr)), "\n")

  for (res in sc) {
    row <- sprintf("%-12s %9d", paste0(res$event_rate * 100, "%"), res$D_total)
    for (ai in seq_len(k))
      row <- paste0(row, sprintf(" %9d %10.3f", res$D_k[ai], res$hr_bounds[ai]))
    cat(row, "\n")
  }
}

# ================================================================
# TABLE 3: HR Bound Range Summary
# ================================================================
cat("\n\n====== HR Bound Range Summary — All Scenarios ======\n")
cat(sprintf("%-22s %15s %20s\n", "Analysis", "D Range", "HR Bound Range"))
cat(strrep("-", 59), "\n")

for (ai in seq_len(k)) {
  all_d  <- sapply(results, function(x) x$D_k[ai])
  all_hr <- sapply(results, function(x) x$hr_bounds[ai])
  lbl    <- if (ai == current_ia) paste0(analysis_labels[ai], " [current]")
            else analysis_labels[ai]
  cat(sprintf("%-22s %5d – %5d     %.3f – %.3f\n",
              lbl, min(all_d), max(all_d), min(all_hr), max(all_hr)))
}

# ================================================================
# TABLE 4: Final Summary — HR Bound Range + CP Range
# ================================================================
cat("\n\n====== Final Summary ======\n")
cat(sprintf("Current analysis: IA%d\n", current_ia))
cat("CP method: current trend\n\n")

cat(sprintf("%-24s %-22s %-24s %-28s\n",
            "Analysis", "HR Bound Range", "Cumul. Alpha Range", "CP Range (current trend)"))
cat(strrep("-", 100), "\n")

for (ai in seq_len(k)) {
  all_hr    <- sapply(results, function(x) x$hr_bounds[ai])
  all_calpha <- sapply(results, function(x) x$cum_alpha[ai])
  lbl       <- if (ai == current_ia) paste0(analysis_labels[ai], " [current]")
               else analysis_labels[ai]
  hr_str    <- sprintf("%.3f – %.3f", min(all_hr), max(all_hr))
  calpha_str <- if (min(all_calpha) == max(all_calpha))
                  sprintf("%.4f", min(all_calpha))
                else
                  sprintf("%.4f – %.4f", min(all_calpha), max(all_calpha))

  if (ai <= current_ia) {
    cp_str <- "—"
  } else {
    all_cp <- na.omit(sapply(results, function(x) x$cp[ai]))
    cp_str <- sprintf("%.1f%% – %.1f%%", min(all_cp) * 100, max(all_cp) * 100)
  }

  cat(sprintf("%-24s %-22s %-24s %s\n", lbl, hr_str, calpha_str, cp_str))
}
cat("\n")
