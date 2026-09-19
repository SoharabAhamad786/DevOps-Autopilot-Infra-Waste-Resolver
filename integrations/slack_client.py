import logging
import requests
from typing import Dict, Any, Optional
from config import settings

logger = logging.getLogger("DevOpsAutopilot.SlackClient")

class SlackClient:
    """
    Handles Slack incoming webhook notifications with rich block formatting
    and provides payload builders for ChatOps slash commands.
    """
    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or settings.SLACK_WEBHOOK_URL

    def post_summary(self, summary_data: Dict[str, Any]) -> bool:
        mode = summary_data.get("mode", "dry_run")
        mode_text = "DRY-RUN (Simulated)" if mode == "dry_run" else "LIVE EXECUTION"
        mode_emoji = "🔍" if mode == "dry_run" else "⚡"
        savings_inr = summary_data.get("total_savings_inr_month", 0.0)
        findings_count = summary_data.get("findings_count", 0)
        actions_count = summary_data.get("actions_executed", 0)
        pending_count = summary_data.get("actions_pending", 0)
        rejected_count = summary_data.get("actions_rejected", 0)
        before_waste = summary_data.get("before_waste_pct", 0.0)
        after_waste = summary_data.get("after_waste_pct", 0.0)

        details_list = summary_data.get("details", [])
        details_preview = "\n".join([f"• {d}" for d in details_list[:5]])
        if len(details_list) > 5:
            details_preview += f"\n• ...and {len(details_list) - 5} more actions."

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{mode_emoji} DevOps Autopilot – Multi-Agent Optimization Report",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Run ID:*\n#{summary_data.get('run_id', 'N/A')}"},
                    {"type": "mrkdwn", "text": f"*Mode:*\n`{mode_text}`"},
                    {"type": "mrkdwn", "text": f"*Cluster Waste:*\n*{before_waste:.1f}%* ➔ *{after_waste:.1f}%*"},
                    {"type": "mrkdwn", "text": f"*Monthly Savings:*\n`₹{savings_inr:,.2f} / mo`"}
                ]
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"✅ *Actions Applied:* {actions_count}"},
                    {"type": "mrkdwn", "text": f"⏳ *Pending Approval:* {pending_count}"},
                    {"type": "mrkdwn", "text": f"🛡️ *Policy Rejections:* {rejected_count}"},
                    {"type": "mrkdwn", "text": f"📊 *Total Evaluated:* {findings_count}"}
                ]
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Top Actions & Reasoning:*\n{details_preview}"}
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "🛡️ *Multi-Agent Flow:* Observer ➔ Optimizer (What-If) ➔ Safety Agent (SLO/Windows) ➔ Executor ➔ Reporter"
                    }
                ]
            }
        ]

        payload = {
            "text": f"DevOps Autopilot Run #{summary_data.get('run_id')} completed. Waste: {before_waste:.1f}% -> {after_waste:.1f}%. Savings: ₹{savings_inr:,.2f}/mo",
            "blocks": blocks
        }

        if not self.webhook_url or "XXXXX" in self.webhook_url:
            logger.info("================ SLACK NOTIFICATION SIMULATION ================")
            logger.info(f"Target Mode: {mode_text}")
            logger.info(f"Cluster Waste: {before_waste:.1f}% -> {after_waste:.1f}%")
            logger.info(f"Savings: INR {savings_inr:,.2f}/month")
            logger.info(f"Summary: {summary_data.get('summary_text', '')}")
            logger.info("================================================================")
            return True

        try:
            resp = requests.post(self.webhook_url, json=payload, timeout=8)
            return resp.status_code == 200
        except Exception as e:
            logger.error(f"Failed to deliver Slack webhook: {e}")
            return False

    def build_chatops_response(self, text: str, attachments: list = None) -> Dict[str, Any]:
        """
        Builds immediate response payloads for Slack slash commands (/autopilot).
        """
        res = {
            "response_type": "in_channel",
            "text": text
        }
        if attachments:
            res["attachments"] = attachments
        return res
