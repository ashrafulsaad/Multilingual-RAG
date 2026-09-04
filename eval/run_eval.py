"""Run JSONL evaluation cases against the live API."""

import argparse
import csv
import json
from pathlib import Path
from time import perf_counter

import httpx

from eval.metrics import hallucination_rate, keyword_overlap, percentile, recall_at_k


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8000")
    parser.add_argument("--dataset", type=Path, default=Path("eval/dataset.jsonl"))
    parser.add_argument("--output-dir", type=Path, default=Path("eval/results"))
    args = parser.parse_args()
    cases = [json.loads(line) for line in args.dataset.read_text(encoding="utf-8").splitlines() if line.strip()]
    results: list[dict] = []
    with httpx.Client(base_url=args.url, timeout=60) as client:
        for case in cases:
            started = perf_counter()
            response = client.post("/query", json={"question": case["question"], "top_k": case.get("top_k", 3)})
            elapsed = (perf_counter() - started) * 1000
            response.raise_for_status()
            payload = response.json()
            context = " ".join(source["text"] for source in payload["sources"])
            results.append({**case, **payload, "wall_latency_ms": elapsed, "correctness": keyword_overlap(payload["answer"], case["reference_answer"]), "supported": all(word.lower() in context.lower() for word in case.get("support_keywords", []))})
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    with (args.output_dir / "results.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["question", "answer", "correctness", "wall_latency_ms"])
        writer.writeheader()
        writer.writerows({key: row.get(key, "") for key in writer.fieldnames} for row in results)
    latencies = [row["latency_ms"]["total"] for row in results]
    print("Metric             Value")
    print(f"Recall@3           {recall_at_k(results, 3):.3f}")
    print(f"Correctness        {sum(row['correctness'] for row in results) / len(results):.3f}")
    print(f"Hallucination rate {hallucination_rate(results):.3f}")
    print(f"Latency p50 (ms)   {percentile(latencies, .50):.2f}")
    print(f"Latency p95 (ms)   {percentile(latencies, .95):.2f}")


if __name__ == "__main__":
    main()