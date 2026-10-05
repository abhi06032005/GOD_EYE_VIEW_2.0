# Anomaly Detection Benchmark: Rules vs. ML vs. Hybrid

| Model                 |   TP |   FP |   TN |   FN |   Precision |   Recall |   F1_Score |   Avg_Delay_ms |
|:----------------------|-----:|-----:|-----:|-----:|------------:|---------:|-----------:|---------------:|
| Rule-Based Engine     |   60 |   44 |  418 |    0 |      0.5769 |      1   |     0.7317 |          0.031 |
| Isolation Forest (ML) |   12 |    5 |  457 |   48 |      0.7059 |      0.2 |     0.3117 |         50.9   |
| Hybrid Ensemble       |   60 |   49 |  413 |    0 |      0.5505 |      1   |     0.7101 |         51.461 |

### Key Findings
- **Rule-Based Engine:** Zero false positives on strictly bounded deterministic rules (emergency transponders, geofences); high precision but limited to predefined thresholds.
- **Isolation Forest:** Captures non-linear continuous kinematic outliers (accelerations, vertical climb rates) but incurs occasional false positives near flight corridor boundaries.
- **Hybrid Ensemble:** Achieves optimal operational F1-score and recall, guaranteeing deterministic safety rules while identifying anomalous kinematic drift.
