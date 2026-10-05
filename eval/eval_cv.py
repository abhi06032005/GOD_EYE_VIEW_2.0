#!/usr/bin/env python3
"""
SentinelAI Computer Vision Evaluation Harness
Benchmarks Ultralytics YOLOv8n vs. YOLOv8s on traffic camera frames.
Measures: Latency (ms), FPS, Parameter Count, Object Count Consistency, and Hardware Specs.
Outputs: eval/results/cv_benchmark.csv, eval/results/cv_benchmark.md, eval/results/cv_latency_fps.png.
"""
import os
import sys
import time
import platform
import psutil
import torch
import cv2
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from ultralytics import YOLO

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE_VIDEO = os.path.join(BASE_DIR, "data", "sample", "traffic_sample.mp4")
RESULTS_DIR = os.path.join(BASE_DIR, "eval", "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

def get_hardware_info():
    cpu_name = platform.processor() or "x86_64 CPU"
    cpu_cores = psutil.cpu_count(logical=True)
    ram_gb = round(psutil.virtual_memory().total / (1024 ** 3), 1)
    cuda_avail = torch.cuda.is_available()
    gpu_name = torch.cuda.get_device_name(0) if cuda_avail else "None (CPU Execution)"
    return {
        "Platform": platform.system() + " " + platform.release(),
        "CPU": f"{cpu_name} ({cpu_cores} cores)",
        "RAM_GB": f"{ram_gb} GB",
        "Accelerator": gpu_name,
        "Device": "cuda:0" if cuda_avail else "cpu"
    }

def evaluate_cv():
    hw = get_hardware_info()
    print("[Eval: CV] Detected Hardware:", hw)

    # Load 100 frames from the sample video
    cap = cv2.VideoCapture(SAMPLE_VIDEO)
    frames = []
    while len(frames) < 100:
        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = cap.read()
            if not ret:
                break
        frames.append(frame)
    cap.release()
    print(f"[Eval: CV] Loaded {len(frames)} test frames for benchmarking.")

    models_to_test = [
        {"name": "YOLOv8n", "weights": "yolov8n.pt", "params_m": 3.2},
        {"name": "YOLOv8s", "weights": "yolov8s.pt", "params_m": 11.2}
    ]

    results = []

    for m in models_to_test:
        print(f"[Eval: CV] Benchmarking {m['name']} on {hw['Device']}...")
        model = YOLO(m["weights"])
        
        # Warmup
        for w in range(5):
            _ = model.predict(frames[w % len(frames)], verbose=False, device=hw['Device'])

        latencies_ms = []
        counts_list = []

        for frame in frames:
            t0 = time.time()
            res = model.predict(frame, conf=0.35, verbose=False, device=hw['Device'])
            dt_ms = (time.time() - t0) * 1000.0
            latencies_ms.append(dt_ms)

            # Extract count of vehicles
            boxes = res[0].boxes if res else []
            v_count = sum(1 for b in boxes if int(b.cls[0].item()) in [0, 2, 3, 5, 7])
            counts_list.append(v_count)

        avg_lat = np.mean(latencies_ms)
        p50_lat = np.percentile(latencies_ms, 50)
        p95_lat = np.percentile(latencies_ms, 95)
        p99_lat = np.percentile(latencies_ms, 99)
        fps = 1000.0 / avg_lat if avg_lat > 0 else 0.0

        results.append({
            "Model": m["name"],
            "Params (M)": m["params_m"],
            "Device": hw["Accelerator"],
            "Avg_Latency_ms": round(avg_lat, 2),
            "p50_Latency_ms": round(p50_lat, 2),
            "p95_Latency_ms": round(p95_lat, 2),
            "FPS": round(fps, 1),
            "Avg_Detections_Per_Frame": round(float(np.mean(counts_list)), 2)
        })

    df = pd.DataFrame(results)
    csv_path = os.path.join(RESULTS_DIR, "cv_benchmark.csv")
    df.to_csv(csv_path, index=False)
    print(f"[Eval: CV] Benchmark CSV saved to {csv_path}")

    # Generate Markdown Table
    md_path = os.path.join(RESULTS_DIR, "cv_benchmark.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Computer Vision Benchmark: YOLOv8n vs. YOLOv8s\n\n")
        f.write(f"**Hardware Environment:** {hw['CPU']} | {hw['RAM_GB']} RAM | Accelerator: {hw['Accelerator']}\n\n")
        f.write(df.to_markdown(index=False))
        f.write("\n\n### Analysis for Edge Situational Awareness\n")
        f.write("- **YOLOv8n (3.2M params):** Sized for edge deployments and high-frequency stream processing. Delivers low latency with minimal CPU overhead, making it ideal for distributed smart city nodes.\n")
        f.write("- **YOLOv8s (11.2M params):** Provides higher feature resolution for small or occluded objects at the cost of higher latency. Recommended for centralized high-capacity GPU ingest nodes.\n")

    # Plot Latency vs FPS
    plt.figure(figsize=(9, 4.5))
    x = np.arange(len(results))
    width = 0.35

    ax1 = plt.subplot(1, 2, 1)
    bars1 = ax1.bar([r["Model"] for r in results], [r["Avg_Latency_ms"] for r in results], color=["#38bdf8", "#818cf8"])
    ax1.set_ylabel("Inference Latency (ms)")
    ax1.set_title("Mean Inference Latency (Lower is Better)")
    ax1.grid(axis='y', linestyle='--', alpha=0.5)
    for bar in bars1:
        yval = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2, yval + 1, f"{yval:.1f} ms", ha='center', va='bottom', fontsize=9)

    ax2 = plt.subplot(1, 2, 2)
    bars2 = ax2.bar([r["Model"] for r in results], [r["FPS"] for r in results], color=["#34d399", "#f43f5e"])
    ax2.set_ylabel("Frames Per Second (FPS)")
    ax2.set_title("Throughput (Higher is Better)")
    ax2.grid(axis='y', linestyle='--', alpha=0.5)
    for bar in bars2:
        yval = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2, yval + 0.5, f"{yval:.1f} FPS", ha='center', va='bottom', fontsize=9)

    plt.suptitle(f"Ultralytics YOLO Benchmark on {hw['Accelerator']}", fontsize=11, fontweight='bold')
    plt.tight_layout()
    plot_path = os.path.join(RESULTS_DIR, "cv_latency_fps.png")
    plt.savefig(plot_path, dpi=200)
    plt.close()
    print(f"[Eval: CV] Benchmark chart saved to {plot_path}")

    return df

if __name__ == "__main__":
    evaluate_cv()
