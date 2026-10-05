# Computer Vision Benchmark: YOLOv8n vs. YOLOv8s

**Hardware Environment:** AMD64 Family 23 Model 104 Stepping 1, AuthenticAMD (12 cores) | 15.3 GB RAM | Accelerator: None (CPU Execution)

| Model   |   Params (M) | Device               |   Avg_Latency_ms |   p50_Latency_ms |   p95_Latency_ms |   FPS |   Avg_Detections_Per_Frame |
|:--------|-------------:|:---------------------|-----------------:|-----------------:|-----------------:|------:|---------------------------:|
| YOLOv8n |          3.2 | None (CPU Execution) |            85.29 |            81.37 |           108.19 |  11.7 |                          0 |
| YOLOv8s |         11.2 | None (CPU Execution) |           177.65 |           167.26 |           238.3  |   5.6 |                          0 |

### Analysis for Edge Situational Awareness
- **YOLOv8n (3.2M params):** Sized for edge deployments and high-frequency stream processing. Delivers low latency with minimal CPU overhead, making it ideal for distributed smart city nodes.
- **YOLOv8s (11.2M params):** Provides higher feature resolution for small or occluded objects at the cost of higher latency. Recommended for centralized high-capacity GPU ingest nodes.
