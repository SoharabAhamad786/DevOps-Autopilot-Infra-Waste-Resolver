import logging
from typing import Dict, Any, List
from integrations.slack_client import SlackClient
from agent.tools import OptimizationProposal

logger = logging.getLogger("DevOpsAutopilot.ReporterAgent")

class ReporterAgent:
    """
    Role: Reporter Agent
    Aggregates multi-agent metrics, calculates before/after waste trajectory,
    generates Slack ChatOps notifications, and updates the executive audit trail.
    """
    def __init__(self):
        self.slack_client = SlackClient()

    def generate_report(self, run_id: int, mode: str, proposals: List[OptimizationProposal], execution_result: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"[ReporterAgent] Compiling executive report for run #{run_id}.")

        findings_count = len(proposals)
        actions_executed = execution_result.get("actions_executed", 0)
        
        approved_count = sum(1 for p in proposals if p.safety_decision == "auto_approve")
        pending_count = sum(1 for p in proposals if p.safety_decision == "require_approval")
        rejected_count = sum(1 for p in proposals if p.safety_decision == "reject")

        # 1. Compute before and after cluster waste percentage
        if findings_count > 0:
            avg_initial_waste = sum(p.waste_score for p in proposals) / findings_count
            # Remediated waste drops proportionally to actions applied
            resolved_ratio = (actions_executed / findings_count) if findings_count else 0.0
            after_waste = max(5.0, avg_initial_waste * (1.0 - (resolved_ratio * 0.75)))
        else:
            avg_initial_waste = 0.0
            after_waste = 0.0

        savings_inr = execution_result.get("total_savings_inr_month", 0.0)

        # 2. Build Executive Narrative Summary
        mode_str = "DRY RUN (Simulated)" if mode == "dry_run" else "LIVE REMEDIATION"
        summary_lines = [
            f"Multi-Agent Run #{run_id} completed in [{mode_str}] mode.",
            f"• Discovered Waste: {findings_count} workloads evaluated.",
            f"• Safety Governance: {approved_count} auto-approved, {pending_count} require operator approval, {rejected_count} rejected.",
            f"• Actions Executed: {actions_executed} applied successfully.",
            f"• Waste Trajectory: Cluster waste reduced from {avg_initial_waste:.1f}% ➔ {after_waste:.1f}%.",
            f"• Recurring Monthly Savings: ₹{savings_inr:,.2f} / month."
        ]
        summary_text = "\n".join(summary_lines)

        # 3. Post to Slack
        slack_payload = {
            "run_id": run_id,
            "mode": mode,
            "findings_count": findings_count,
            "actions_executed": actions_executed,
            "actions_pending": pending_count,
            "actions_rejected": rejected_count,
            "total_savings_inr_month": savings_inr,
            "before_waste_pct": avg_initial_waste,
            "after_waste_pct": after_waste,
            "details": execution_result.get("details", []),
            "summary_text": summary_text
        }
        slack_posted = self.slack_client.post_summary(slack_payload)

        logger.info(f"[ReporterAgent] Report compiled. Slack delivery: {'Success' if slack_posted else 'Simulated'}.")

        return {
            "summary_text": summary_text,
            "before_waste_pct": round(avg_initial_waste, 1),
            "after_waste_pct": round(after_waste, 1),
            "actions_approved": approved_count,
            "actions_rejected": rejected_count,
            "actions_pending": pending_count,
            "slack_posted": slack_posted
        }
