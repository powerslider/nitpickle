# Validation log

The Phase 0 gate. One line per pre-flight run. The number that matters is the
last column: findings you fixed that you would otherwise have shipped. If after
~5 branches that stays near zero, the proof loop is noise - stop and fix review
quality before building anything else (see docs/ROADMAP.md).

| Date | Branch | Proven blocking | Important | Fixed-would-have-shipped |
| --- | --- | --- | --- | --- |
| _example_ | _feature/sync-cache_ | _1_ | _2_ | _1_ |
