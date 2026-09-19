import math
import logging
from typing import List
from config import settings
from agent.tools import ResourceMetric, OptimizationProposal, WhatIfSimulation

logger = logging.getLogger("DevOpsAutopilot.OptimizerAgent")

class OptimizerAgent:
    """
    Role: Optimizer Agent
    Analyzes telemetry from the Observer Agent, identifies waste, designs right-sizing/stop actions,
    and runs a What-If predictive simulation assessing SLO breach risks.
    """
    def generate_proposals(self, metrics: List[ResourceMetric]) -> List[OptimizationProposal]:
        logger.info(f"[OptimizerAgent] Evaluating waste across {len(metrics)} observed metrics.")
        proposals: List[OptimizationProposal] = []

        for m in metrics:
            cpu_util = m.avg_cpu_usage / m.current_cpu_request
            util_pct = round(cpu_util * 100.0, 2)

            # Classify issue
            issue_type = None
            if cpu_util < 0.05:
                issue_type = "idle"
            elif cpu_util < 0.30 and (m.current_cpu_request >= (m.avg_cpu_usage * 2.5)):
                issue_type = "overprovisioned"

            if not issue_type:
                continue

            savings_inr = 0.0
            action_payload = {}
            what_if = None

            if m.resource_type == "pod":
                parent_workload = m.parent_workload or m.resource_id
                old_reps = max(m.replicas, 1)
                
                # Maximum 50% scale-down rule
                max_reduction = max(1, math.floor(old_reps * settings.MAX_REPLICA_REDUCTION_PCT))
                target_reps = max(1, old_reps - max_reduction)
                reduced_reps = old_reps - target_reps

                # Calculate pod cost
                pod_cost_month = (m.current_cpu_request * settings.PRICE_PER_CORE_MONTH_INR) + \
                                 ((m.current_mem_request / 1024.0) * settings.PRICE_PER_GB_MEM_MONTH_INR)
                if pod_cost_month <= 0:
                    pod_cost_month = settings.DEFAULT_POD_COST_MONTH_INR
                
                savings_inr = round(reduced_reps * pod_cost_month, 2)

                action_payload = {
                    "action": "scale_down" if issue_type == "idle" else "right_size",
                    "parent_workload": parent_workload,
                    "namespace": m.namespace,
                    "current_replicas": old_reps,
                    "target_replicas": target_reps,
                    "cpu_reduction_cores": round(reduced_reps * m.current_cpu_request, 2),
                    "memory_reduction_mb": round(reduced_reps * m.current_mem_request, 2)
                }

                # What-If Simulation:
                # When replicas decrease, remaining replicas absorb traffic:
                # new_util = old_util * (old_reps / target_reps)
                predicted_util = min(100.0, util_pct * (old_reps / target_reps))
                
                risk_score = "low"
                risk_reasons = []

                if predicted_util > settings.SLO_MAX_CPU_UTIL_PCT:
                    risk_score = "high"
                    risk_reasons.append(f"Predicted CPU ({predicted_util:.1f}%) exceeds SLO ceiling ({settings.SLO_MAX_CPU_UTIL_PCT}%).")
                elif predicted_util > 55.0 or m.has_traffic:
                    risk_score = "medium"
                    risk_reasons.append(f"Workload handles live traffic; predicted util is {predicted_util:.1f}%.")
                else:
                    risk_reasons.append(f"Safe headroom: predicted CPU is {predicted_util:.1f}%. No traffic spikes detected.")

                what_if = WhatIfSimulation(
                    predicted_util_pct=round(predicted_util, 1),
                    risk_score=risk_score,
                    risk_reason=" ".join(risk_reasons)
                )

            elif m.resource_type == "instance":
                if m.cost_per_hour > 0:
                    savings_inr = round(m.cost_per_hour * 24 * 30, 2)
                else:
                    savings_inr = round((m.current_cpu_request * settings.PRICE_PER_CORE_MONTH_INR) + \
                                        ((m.current_mem_request / 1024.0) * settings.PRICE_PER_GB_MEM_MONTH_INR), 2)

                action_payload = {
                    "action": "stop",
                    "instance_id": m.resource_id,
                    "namespace": m.namespace,
                    "instance_type": m.tags.get("instance_type", "EC2"),
                    "estimated_monthly_hours": 720
                }

                # What-if simulation for stopping instance
                what_if = WhatIfSimulation(
                    predicted_util_pct=0.0,
                    risk_score="low" if m.namespace.lower() != "prod" else "high",
                    risk_reason=f"Instance {m.resource_id} has near-zero network activity ({m.network_rx_kbps + m.network_tx_kbps:.1f} kbps). Safe to shut down."
                )

            proposal = OptimizationProposal(
                resource_id=m.resource_id,
                resource_type=m.resource_type,
                namespace=m.namespace,
                parent_workload=m.parent_workload,
                issue_type=issue_type,
                utilization_pct=util_pct,
                waste_score=m.waste_score,
                proposed_action=action_payload,
                estimated_savings_inr_month=savings_inr,
                what_if=what_if
            )
            proposals.append(proposal)

        logger.info(f"[OptimizerAgent] Generated {len(proposals)} optimization proposals with What-If simulations.")
        return proposals
