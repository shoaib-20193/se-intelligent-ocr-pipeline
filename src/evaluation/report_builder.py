# src/evaluation/report_builder.py
# EvaluationReport assembly for M9
# See agents.md §DATA_MODEL → EvaluationReport
#
# Assembles final EvaluationReport from:
#   precision, recall, f1_score  <- metrics_engine
#   wer                          <- wer_calculator
#   latency_per_page             <- PipelineResult.stage_metrics (mean)
#   ram_usage_mb                 <- process RSS peak measurement
#
# Output: EvaluationReport { precision, recall, f1_score, wer, latency_per_page, ram_usage_mb }
