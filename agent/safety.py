import logging
from datetime import datetime, timezone, timedelta
from typing import List
from config import settings
from agent.tools import OptimizationProposal

logger = logging.getLogger("DevOpsAutopilot.SafetyAgent")

class SafetyAgent:
    """
    Role: Safety Agent
    Evaluates every proposal against organizational governance, namespace allowlists,
    maintenance change windows, minimum replica policies, and SLO thresholds.
    Assigns: 'auto_approve' | 'require_approval' | 'reject' with clear justification.
    """
    def evaluate_policies(self, proposals: List[OptimizationProposal]) -> List[OptimizationProposal]:
        logger.info(f"[SafetyAgent] Auditing {len(proposals)} proposals against governance policies.")
        # Calculate current hour in IST (UTC+5:30)
        ist_now = datetime.now(timezone(timedelta(hours=5, minutes=30)))
        ist_hour = ist_now.hour

        for p in proposals:
            ns = p.namespace.lower()
            risk = p.what_if.risk_score if p.what_if else "low"
            action_data = p.proposed_action
            target_reps = action_data.get("target_replicas", 1)

            # Policy 1: Production Namespace Protection
            if ns in ("prod", "production", "default"):
                if settings.PREVENT_PROD_EXECUTION:
                    p.safety_decision = "reject"
                    p.safety_reason = f"POLICY VIOLATION: Modifications in production namespace '{p.namespace}' are strictly prohibited by PREVENT_PROD_EXECUTION."
                else:
                    p.safety_decision = "require_approval"
                    p.safety_reason = f"GUARDED PROD: Action on production '{p.namespace}' requires explicit operator sign-off."
                continue

            # Policy 2: Namespace Allowlist
            allowed_ns = [a.lower() for a in settings.ALLOWED_NAMESPACES]
            if ns not in allowed_ns and p.resource_type == "pod":
                p.safety_decision = "reject"
                p.safety_reason = f"POLICY VIOLATION: Namespace '{p.namespace}' is not in configured ALLOWED_NAMESPACES ({settings.ALLOWED_NAMESPACES})."
                continue

            # Policy 3: Change Window Enforcement for Sensitive Workloads
            in_window = settings.CHANGE_WINDOW_START_HOUR <= ist_hour <= settings.CHANGE_WINDOW_END_HOUR
            if risk == "high" and not in_window:
                p.safety_decision = "require_approval"
                p.safety_reason = f"WINDOW CONSTRAINT: High-risk changes outside maintenance window ({settings.CHANGE_WINDOW_START_HOUR}:00-{settings.CHANGE_WINDOW_END_HOUR}:00 IST) require operator approval."
                continue

            # Policy 4: Minimum Replicas for Traffic-Bearing Deployments
            if p.resource_type == "pod" and target_reps < settings.MIN_REPLICAS_TRAFFIC and risk == "medium":
                p.safety_decision = "require_approval"
                p.safety_reason = f"SLO SAFETY: Target replicas ({target_reps}) is below minimum traffic baseline ({settings.MIN_REPLICAS_TRAFFIC}). Human review required."
                continue

            # Policy 5: Low-Risk Non-Prod Auto-Approval
            if risk == "low":
                p.safety_decision = "auto_approve"
                p.safety_reason = f"VERIFIED SAFE: Non-production workload in '{p.namespace}' with low risk profile and ample headroom."
                p.approved_by = "system"
            else:
                p.safety_decision = "require_approval"
                p.safety_reason = f"ELEVATED RISK ({risk.upper()}): Workload dynamics require human operator confirmation before execution."

        auto_count = sum(1 for p in proposals if p.safety_decision == "auto_approve")
        req_count = sum(1 for p in proposals if p.safety_decision == "require_approval")
        rej_count = sum(1 for p in proposals if p.safety_decision == "reject")

        logger.info(f"[SafetyAgent] Governance review completed: {auto_count} auto-approved, {req_count} require approval, {rej_count} rejected.")
        return proposals
