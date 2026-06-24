"""judge_runner.py

Execution runner for LLM-judges, aggregating and persisting scores side-by-side with Stage 16 metrics.
"""

import json
import os
from typing import Any, Dict
from agents.orchestrator_agent import OrchestratorAgent
from evaluation.datasets import SYNTHETIC_PROFILES
from evaluation.benchmarks import CRRABenchmarkRunner
from evaluation.llm_judges import (
    EvidenceJudge,
    ReasoningJudge,
    CounterfactualJudge,
    SkepticJudge,
    SafetyJudge,
    ReportClarityJudge,
)


class LLMJudgeRunner:
    """Runner class that executes both Stage 16 metrics and Stage 17 LLM judges."""

    def __init__(self) -> None:
        self.orchestrator = OrchestratorAgent()
        self.judges = [
            EvidenceJudge(),
            ReasoningJudge(),
            CounterfactualJudge(),
            SkepticJudge(),
            SafetyJudge(),
            ReportClarityJudge(),
        ]
        self.metrics_runner = CRRABenchmarkRunner()

    def run_evaluation_suite(self, results_json_path: str, report_md_path: str) -> Dict[str, Any]:
        """Runs the combined evaluation suite.

        Aggregates results and persists them to JSON and Markdown.
        """
        # 1. Run Stage 16 metrics benchmarks
        base_benchmarks = self.metrics_runner.run_benchmark()

        # 2. Run Stage 17 LLM Judges
        merged_results = {}
        for name, data in SYNTHETIC_PROFILES.items():
            profile = data["profile"]
            
            # Execute pipeline
            state = self.orchestrator.run(profile)

            # Score using judges
            judge_outputs = {}
            for judge in self.judges:
                res = judge.evaluate(state)
                judge_outputs[judge.category] = {
                    "score": res.score,
                    "reasoning": res.reasoning,
                    "passed": res.passed,
                }

            # Extract Stage 16 metric scores
            stage16_scores = base_benchmarks["results"][name]

            merged_results[name] = {
                "profile_session_id": profile.session_id,
                "stage16_metrics": stage16_scores,
                "stage17_judges": judge_outputs,
            }

        # Persist structured JSON log
        os.makedirs(os.path.dirname(results_json_path), exist_ok=True)
        with open(results_json_path, "w", encoding="utf-8") as f:
            json.dump(merged_results, f, indent=2)

        # Generate side-by-side Markdown report
        self.generate_markdown_report(merged_results, report_md_path)

        return merged_results

    def generate_markdown_report(self, results: Dict[str, Any], path: str) -> None:
        """Helper generating side-by-side evaluation table and reasoning breakdown."""
        md = []
        md.append("# LLM-Judge & Metric Side-by-Side Evaluation Report\n")
        md.append("This report presents a side-by-side comparison of deterministic Stage 16 metrics and Stage 17 LLM-judge scores.\n")
        
        md.append("## Case-by-Side Comparison Table\n")
        md.append("| Profile Name | Safety Metric | Safety Judge | Evidence Metric | Evidence Judge | Reasoning Metric | Reasoning Judge | Overall Judge Score |")
        md.append("|---|---|---|---|---|---|---|---|")
        
        for name, data in results.items():
            s16 = data["stage16_metrics"]
            s17 = data["stage17_judges"]
            
            s16_safety = s16["safety"]["overall_score"]
            s17_safety = s17["Safety Compliance"]["score"] / 5.0
            
            s16_evidence = s16["evidence"]["overall_score"]
            s17_evidence = s17["Evidence Quality"]["score"] / 5.0
            
            s16_reasoning = s16["reasoning"]["overall_score"]
            s17_reasoning = s17["Reasoning Quality"]["score"] / 5.0
            
            avg_judge = sum(j["score"] for j in s17.values()) / (len(s17) * 5.0)
            
            md.append(
                f"| `{name}` | {s16_safety:.0%} | {s17_safety:.0%} | {s16_evidence:.0%} | {s17_evidence:.0%} | {s16_reasoning:.0%} | {s17_reasoning:.0%} | {avg_judge:.2%} |"
            )
            
        md.append("\n## Detailed LLM-Judge Reasoning Logs\n")
        for name, data in results.items():
            md.append(f"### Profile: `{name}`\n")
            for cat, jdata in data["stage17_judges"].items():
                status = "PASS" if jdata["passed"] else "FAIL"
                md.append(f"- **{cat}**: Score `{jdata['score']}/5.0` | Status: `{status}`")
                md.append(f"  - *Reasoning*: {jdata['reasoning']}\n")

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(md))
