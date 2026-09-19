import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from db.session import get_db
from db.models import OptimizationRun, Finding, Resource
from agent.observer import ObserverAgent
from agent.optimizer import OptimizerAgent
from agent.safety import SafetyAgent
from agent.executor import ExecutorAgent
from agent.reporter import ReporterAgent
from agent.llm_client import LLMClient

logger = logging.getLogger("DevOpsAutopilot.Orchestrator")

class AgentOrchestrator:
    """
    Coordinates the multi-agent system:
    Observer ➔ Optimizer (What-If) ➔ Safety Agent (SLO/Windows) ➔ Executor ➔ Reporter.
    Maintains a visible natural-language reasoning stream and audit trail.
    """
    def __init__(self):
        self.observer = ObserverAgent()
        self.optimizer = OptimizerAgent()
        self.safety = SafetyAgent()
        self.executor = ExecutorAgent()
        self.reporter = ReporterAgent()
        self.llm = LLMClient()

    def run_optimization(self, mode: str = "dry_run", scope: str = "all") -> Dict[str, Any]:
        start_time = datetime.now(timezone.utc)
        logger.info(f"=== [MULTI-AGENT CYCLE STARTED] Mode='{mode}', Scope='{scope}' ===")
        reasoning_trail: List[Dict[str, str]] = []

        # 1. Initialize Run in Database
        with get_db() as db:
            run_record = OptimizationRun(
                triggered_at=start_time,
                mode=mode,
                findings_count=0,
                actions_count=0,
                actions_approved=0,
                actions_rejected=0,
                savings_inr_month=0.0,
                before_waste_pct=0.0,
                after_waste_pct=0.0,
                slack_posted=False,
                summary_text="Multi-agent optimization cycle running..."
            )
            db.add(run_record)
            db.flush()
            run_id = run_record.id

        # Phase 1: Observer Agent
        reasoning_trail.append({
            "agent": "Observer Agent",
            "message": f"Ingesting metrics from Kubernetes Metrics Server and AWS CloudWatch (Scope: '{scope}')."
        })
        metrics = self.observer.observe_cluster(scope=scope)
        self._persist_resource_snapshots(metrics)
        reasoning_trail.append({
            "agent": "Observer Agent",
            "message": f"Telemetry normalized for {len(metrics)} workloads. Average cluster waste baseline detected."
        })

        # Phase 2: Optimizer Agent (with What-If Simulator)
        reasoning_trail.append({
            "agent": "Optimizer Agent",
            "message": "Analyzing utilization curves (<5% Idle, <30% Oversized) and executing What-If simulations."
        })
        proposals = self.optimizer.generate_proposals(metrics)
        for p in proposals[:3]:
            reasoning_trail.append({
                "agent": "Optimizer Agent",
                "message": f"Workload '{p.resource_id}' ({p.issue_type}): CPU={p.utilization_pct}%. What-If predicts {p.what_if.predicted_util_pct}% post-action. Risk: {p.what_if.risk_score.upper()}."
            })
        if len(proposals) > 3:
            reasoning_trail.append({
                "agent": "Optimizer Agent",
                "message": f"...and {len(proposals) - 3} more workload proposals calculated."
            })

        # Phase 3: Safety Agent (Policy & Governance)
        reasoning_trail.append({
            "agent": "Safety Agent",
            "message": "Auditing proposals against namespace allowlists, maintenance windows, and SLO minimum replicas."
        })
        proposals = self.safety.evaluate_policies(proposals)
        for p in proposals:
            if p.safety_decision == "reject":
                reasoning_trail.append({
                    "agent": "Safety Agent",
                    "message": f"🛡️ REJECTED '{p.resource_id}': {p.safety_reason}"
                })
            elif p.safety_decision == "require_approval":
                reasoning_trail.append({
                    "agent": "Safety Agent",
                    "message": f"⏳ PENDING APPROVAL '{p.resource_id}': {p.safety_reason}"
                })

        # Phase 4: Executor Agent
        is_dry_run = (mode == "dry_run")
        reasoning_trail.append({
            "agent": "Executor Agent",
            "message": f"Enforcing policy outcomes. Executing auto-approved actions in {'DRY RUN' if is_dry_run else 'LIVE'} mode."
        })
        exec_result = self.executor.execute_plan(proposals, dry_run=is_dry_run)
        reasoning_trail.append({
            "agent": "Executor Agent",
            "message": f"Execution finished. Applied {exec_result.get('actions_executed')} actions. ₹{exec_result.get('total_savings_inr_month'):,.2f}/mo recovered."
        })

        # Phase 5: Reporter Agent
        report = self.reporter.generate_report(run_id, mode, proposals, exec_result)
        reasoning_trail.append({
            "agent": "Reporter Agent",
            "message": f"Waste reduced: {report['before_waste_pct']}% ➔ {report['after_waste_pct']}%. Executive Slack notification sent."
        })

        # Persist Findings and update OptimizationRun record in DB
        with get_db() as db:
            run_record = db.query(OptimizationRun).filter(OptimizationRun.id == run_id).first()
            if run_record:
                run_record.findings_count = len(proposals)
                run_record.actions_count = exec_result.get("actions_executed", 0)
                run_record.actions_approved = report["actions_approved"]
                run_record.actions_rejected = report["actions_rejected"]
                run_record.savings_inr_month = exec_result.get("total_savings_inr_month", 0.0)
                run_record.before_waste_pct = report["before_waste_pct"]
                run_record.after_waste_pct = report["after_waste_pct"]
                run_record.slack_posted = report["slack_posted"]
                run_record.summary_text = report["summary_text"]

            for p in proposals:
                is_executed = (p.safety_decision == "auto_approve") and (exec_result.get("actions_executed", 0) > 0)
                finding = Finding(
                    run_id=run_id,
                    resource_id=p.resource_id,
                    resource_type=p.resource_type,
                    issue_type=p.issue_type,
                    utilization_pct=p.utilization_pct,
                    proposed_action=json.dumps(p.proposed_action),
                    estimated_savings_inr_month=p.estimated_savings_inr_month,
                    predicted_util_pct=p.what_if.predicted_util_pct if p.what_if else 0.0,
                    risk_score=p.what_if.risk_score if p.what_if else "low",
                    risk_reason=p.what_if.risk_reason if p.what_if else None,
                    safety_decision=p.safety_decision,
                    safety_reason=p.safety_reason,
                    executed=is_executed,
                    executed_at=datetime.now(timezone.utc) if is_executed else None,
                    approved_by=p.approved_by
                )
                db.add(finding)

        elapsed = round((datetime.now(timezone.utc) - start_time).total_seconds(), 2)
        logger.info(f"=== [MULTI-AGENT CYCLE FINISHED] Run #{run_id} in {elapsed}s ===")

        return {
            "status": "success",
            "run_id": run_id,
            "mode": mode,
            "findings_count": len(proposals),
            "actions_count": exec_result.get("actions_executed", 0),
            "actions_approved": report["actions_approved"],
            "actions_rejected": report["actions_rejected"],
            "actions_pending": report["actions_pending"],
            "savings_inr_month": exec_result.get("total_savings_inr_month", 0.0),
            "before_waste_pct": report["before_waste_pct"],
            "after_waste_pct": report["after_waste_pct"],
            "slack_posted": report["slack_posted"],
            "summary_text": report["summary_text"],
            "reasoning_trail": reasoning_trail,
            "elapsed_seconds": elapsed
        }

    def approve_and_execute(self, run_id: int, finding_ids: List[int]) -> Dict[str, Any]:
        """
        Operator Human-in-the-loop: approves specific findings and executes them in live mode.
        """
        logger.info(f"[Orchestrator] Human approval received for run #{run_id}, findings={finding_ids}.")
        executed_findings = []
        with get_db() as db:
            findings = db.query(Finding).filter(Finding.run_id == run_id, Finding.id.in_(finding_ids)).all()
            if not findings:
                return {"error": "No matching findings found", "executed": 0}

            for f in findings:
                action_data = f.get_action_json()
                try:
                    if f.resource_type == "pod":
                        wl = action_data.get("parent_workload", f.resource_id)
                        ns = action_data.get("namespace", "default")
                        target = action_data.get("target_replicas", 1)
                        self.executor.k8s_client.scale_deployment(ns, wl, target, dry_run=False)
                    elif f.resource_type == "instance":
                        self.executor.aws_client.stop_instance(f.resource_id, dry_run=False)

                    f.executed = True
                    f.executed_at = datetime.now(timezone.utc)
                    f.approved_by = "operator"
                    f.safety_decision = "approved_by_operator"
                    executed_findings.append(f.resource_id)
                except Exception as e:
                    logger.error(f"Error executing approved finding {f.resource_id}: {e}")

            # Update run totals
            run = db.query(OptimizationRun).filter(OptimizationRun.id == run_id).first()
            if run:
                run.actions_count += len(executed_findings)

        return {
            "status": "success",
            "run_id": run_id,
            "approved_count": len(executed_findings),
            "executed_resources": executed_findings
        }

    def _persist_resource_snapshots(self, metrics: list):
        try:
            with get_db() as db:
                for m in metrics:
                    r_id = m.resource_id
                    existing = db.query(Resource).filter(Resource.resource_id == r_id).first()
                    if not existing:
                        existing = Resource(
                            resource_type=m.resource_type,
                            resource_id=r_id,
                            namespace=m.namespace,
                            current_cpu_request=m.current_cpu_request,
                            current_mem_request=m.current_mem_request,
                            avg_cpu_usage=m.avg_cpu_usage,
                            avg_mem_usage=m.avg_mem_usage,
                            cost_per_hour=m.cost_per_hour,
                            waste_score=m.waste_score
                        )
                        db.add(existing)
                    else:
                        existing.avg_cpu_usage = m.avg_cpu_usage
                        existing.avg_mem_usage = m.avg_mem_usage
                        existing.waste_score = m.waste_score
                        existing.updated_at = datetime.now(timezone.utc)
        except Exception as e:
            logger.warning(f"Error saving resource snapshots: {e}")
