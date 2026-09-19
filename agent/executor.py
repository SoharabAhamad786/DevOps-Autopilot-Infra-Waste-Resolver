import logging
from typing import List, Dict, Any
from config import settings
from integrations.k8s_client import K8sClient
from integrations.aws_client import AWSClient
from agent.tools import OptimizationProposal

logger = logging.getLogger("DevOpsAutopilot.ExecutorAgent")

class ExecutorAgent:
    """
    Role: Executor Agent
    Takes proposals vetted by the Safety Agent, strictly filters out rejected items,
    and applies scaling/shutdown operations in dry_run or live mode with rate-limiting.
    """
    def __init__(self):
        self.k8s_client = K8sClient()
        self.aws_client = AWSClient()

    def execute_plan(self, proposals: List[OptimizationProposal], dry_run: bool = True, force_execute_ids: List[str] = None) -> Dict[str, Any]:
        logger.info(f"[ExecutorAgent] Executing action plan (dry_run={dry_run}, total_proposals={len(proposals)}).")
        force_ids = set(force_execute_ids or [])

        actions_executed = 0
        actions_skipped = 0
        total_savings = 0.0
        details: List[str] = []
        action_limit = settings.MAX_ACTIONS_PER_RUN

        for p in proposals:
            # 1. Respect Safety Decisions
            if p.safety_decision == "reject":
                actions_skipped += 1
                details.append(f"[REJECTED] {p.resource_id} ({p.namespace}): {p.safety_reason}")
                continue

            if p.safety_decision == "require_approval" and p.resource_id not in force_ids:
                actions_skipped += 1
                details.append(f"[PENDING APPROVAL] {p.resource_id} ({p.namespace}): Awaiting operator review ({p.safety_reason})")
                continue

            # 2. Enforce Action Rate Cap
            if actions_executed >= action_limit:
                actions_skipped += 1
                details.append(f"[CAPPED] {p.resource_id}: Exceeded MAX_ACTIONS_PER_RUN limit of {action_limit}.")
                continue

            # 3. Apply Action
            try:
                action_data = p.proposed_action
                mode_tag = "[DRY RUN]" if dry_run else "[LIVE APPLIED]"

                if p.resource_type == "pod":
                    parent_wl = p.parent_workload or p.resource_id
                    target_reps = action_data.get("target_replicas", 1)
                    res = self.k8s_client.scale_deployment(
                        namespace=p.namespace,
                        deployment_name=parent_wl,
                        target_replicas=target_reps,
                        dry_run=dry_run
                    )
                    details.append(f"{mode_tag} Scaled deployment {p.namespace}/{parent_wl} from {action_data.get('current_replicas')} to {target_reps} replicas. Saved: ₹{p.estimated_savings_inr_month:,.2f}/mo")
                    actions_executed += 1
                    total_savings += p.estimated_savings_inr_month

                elif p.resource_type == "instance":
                    res = self.aws_client.stop_instance(instance_id=p.resource_id, dry_run=dry_run)
                    details.append(f"{mode_tag} Stopped idle instance {p.resource_id} ({action_data.get('instance_type', 'EC2')}). Saved: ₹{p.estimated_savings_inr_month:,.2f}/mo")
                    actions_executed += 1
                    total_savings += p.estimated_savings_inr_month

            except Exception as e:
                logger.error(f"[ExecutorAgent] Failed action on {p.resource_id}: {e}")
                actions_skipped += 1
                details.append(f"[FAILED] {p.resource_id}: {str(e)}")

        return {
            "mode": "dry_run" if dry_run else "live",
            "actions_executed": actions_executed,
            "actions_skipped": actions_skipped,
            "total_savings_inr_month": round(total_savings, 2),
            "details": details
        }
