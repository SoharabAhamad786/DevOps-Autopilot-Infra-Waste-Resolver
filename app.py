import logging
import os
import sys

# Windows UTF-8 console output protection for emojis & INR symbol
if sys.platform.startswith("win") and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from sqlalchemy import func
from config import settings
from db.session import init_db, get_db, SessionLocal
from db.models import OptimizationRun, Finding, Resource
from agent.orchestrator import AgentOrchestrator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("DevOpsAutopilot.App")

app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)

orchestrator = AgentOrchestrator()

with app.app_context():
    init_db()
    logger.info("Database initialized successfully.")

@app.teardown_appcontext
def shutdown_session(exception=None):
    SessionLocal.remove()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/metrics", methods=["GET"])
def get_metrics_sample():
    """
    Returns the cluster metrics dataset used for live and 3D visualizer rendering.
    """
    import json
    path = settings.MOCK_METRICS_PATH
    if os.path.exists(path):
        with open(path, "r") as f:
            return jsonify(json.load(f)), 200
    return jsonify([]), 200

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "DevOps Autopilot – Multi-Agent Infra Waste Resolver",
        "agents": ["ObserverAgent", "OptimizerAgent", "SafetyAgent", "ExecutorAgent", "ReporterAgent"],
        "mode_default": "dry_run" if settings.DRY_RUN_DEFAULT else "live",
        "mock_metrics_active": settings.USE_MOCK_METRICS,
        "guardrails": {
            "allowed_namespaces": settings.ALLOWED_NAMESPACES,
            "max_actions_per_run": settings.MAX_ACTIONS_PER_RUN,
            "max_reduction_pct": settings.MAX_REPLICA_REDUCTION_PCT,
            "prevent_prod_execution": settings.PREVENT_PROD_EXECUTION,
            "slo_max_cpu_util_pct": settings.SLO_MAX_CPU_UTIL_PCT,
            "change_window_ist": f"{settings.CHANGE_WINDOW_START_HOUR}:00-{settings.CHANGE_WINDOW_END_HOUR}:00"
        }
    }), 200

@app.route("/api/optimize", methods=["POST"])
def trigger_optimization():
    """
    POST /api/optimize
    Triggers an autonomous multi-agent optimization cycle.
    """
    data = request.get_json() or {}
    mode = data.get("mode", "dry_run")
    scope = data.get("scope", "all")

    if mode not in ("dry_run", "live"):
        return jsonify({"error": "Invalid mode. Must be 'dry_run' or 'live'."}), 400

    try:
        result = orchestrator.run_optimization(mode=mode, scope=scope)
        return jsonify(result), 200
    except Exception as e:
        logger.exception("Error during multi-agent optimization run")
        return jsonify({"error": str(e)}), 500

@app.route("/api/runs", methods=["GET"])
def list_runs():
    limit = int(request.args.get("limit", 20))
    with get_db() as db:
        runs = db.query(OptimizationRun).order_by(OptimizationRun.triggered_at.desc()).limit(limit).all()
        return jsonify([run.to_dict() for run in runs]), 200

@app.route("/api/runs/<int:run_id>", methods=["GET"])
def get_run_detail(run_id: int):
    with get_db() as db:
        run = db.query(OptimizationRun).filter(OptimizationRun.id == run_id).first()
        if not run:
            return jsonify({"error": f"Run #{run_id} not found"}), 404

        findings = db.query(Finding).filter(Finding.run_id == run_id).all()
        run_data = run.to_dict()
        run_data["findings"] = [f.to_dict() for f in findings]
        return jsonify(run_data), 200

@app.route("/api/savings", methods=["GET"])
def get_aggregate_savings():
    with get_db() as db:
        total_savings = db.query(func.sum(OptimizationRun.savings_inr_month)).scalar() or 0.0
        total_runs = db.query(func.count(OptimizationRun.id)).scalar() or 0
        total_actions = db.query(func.sum(OptimizationRun.actions_count)).scalar() or 0
        total_findings = db.query(func.sum(OptimizationRun.findings_count)).scalar() or 0
        latest_run = db.query(OptimizationRun).order_by(OptimizationRun.triggered_at.desc()).first()

        # Waste trend across last 5 runs
        recent_runs = db.query(OptimizationRun).order_by(OptimizationRun.triggered_at.desc()).limit(5).all()
        waste_trend = [
            {"run_id": r.id, "before_pct": r.before_waste_pct, "after_pct": r.after_waste_pct}
            for r in reversed(recent_runs)
        ]

        return jsonify({
            "total_estimated_savings_inr_month": round(total_savings, 2),
            "total_runs_count": total_runs,
            "total_actions_count": total_actions,
            "total_findings_count": total_findings,
            "waste_trend": waste_trend,
            "latest_run": latest_run.to_dict() if latest_run else None,
            "currency": "INR",
            "currency_symbol": "₹"
        }), 200

@app.route("/api/waste-map", methods=["GET"])
def get_waste_map():
    """
    GET /api/waste-map
    Aggregates waste scores and estimated monthly waste by namespace and service.
    """
    with get_db() as db:
        resources = db.query(Resource).all()
        ns_map = {}
        for r in resources:
            ns = r.namespace or "default"
            if ns not in ns_map:
                ns_map[ns] = {
                    "namespace": ns,
                    "resource_count": 0,
                    "total_waste_score": 0.0,
                    "total_cost_month": 0.0,
                    "services": []
                }
            ns_map[ns]["resource_count"] += 1
            ns_map[ns]["total_waste_score"] += r.waste_score
            ns_map[ns]["total_cost_month"] += (r.cost_per_hour * 720.0)
            ns_map[ns]["services"].append({
                "resource_id": r.resource_id,
                "type": r.resource_type,
                "waste_score": r.waste_score,
                "cpu_util_pct": round((r.avg_cpu_usage / max(r.current_cpu_request, 0.001)) * 100, 1),
                "monthly_cost": round(r.cost_per_hour * 720.0, 2)
            })

        summary = []
        for ns, data in ns_map.items():
            count = data["resource_count"]
            avg_waste = round(data["total_waste_score"] / count, 1) if count else 0.0
            est_waste_inr = round(data["total_cost_month"] * (avg_waste / 100.0), 2)
            summary.append({
                "namespace": ns,
                "resource_count": count,
                "waste_score": avg_waste,
                "estimated_waste_inr_month": est_waste_inr,
                "services": data["services"]
            })

        summary.sort(key=lambda x: x["waste_score"], reverse=True)
        return jsonify(summary), 200

@app.route("/api/approve", methods=["POST"])
def approve_findings():
    """
    POST /api/approve
    Body: { "run_id": 1, "finding_ids": [1, 2] }
    Approves pending findings for live execution.
    """
    data = request.get_json() or {}
    run_id = data.get("run_id")
    finding_ids = data.get("finding_ids", [])

    if not run_id or not finding_ids:
        return jsonify({"error": "Missing run_id or finding_ids"}), 400

    try:
        result = orchestrator.approve_and_execute(run_id=int(run_id), finding_ids=[int(i) for i in finding_ids])
        return jsonify(result), 200
    except Exception as e:
        logger.exception("Error executing approvals")
        return jsonify({"error": str(e)}), 500

@app.route("/slack/commands", methods=["POST"])
def slack_chatops():
    """
    POST /slack/commands
    ChatOps interface for Slack slash command /autopilot
    Subcommands:
      /autopilot run <scope> <mode>
      /autopilot status
      /autopilot explain <run_id>
    """
    text = request.form.get("text", "").strip().lower()
    parts = text.split()
    cmd = parts[0] if parts else "status"

    if cmd == "run":
        scope = parts[1] if len(parts) > 1 else "all"
        mode = parts[2] if len(parts) > 2 else "dry_run"
        res = orchestrator.run_optimization(mode=mode, scope=scope)
        msg = f"🚀 *DevOps Autopilot Run #{res['run_id']} Triggered*\n" \
              f"• Mode: `{res['mode'].upper()}` | Scope: `{scope}`\n" \
              f"• Cluster Waste: *{res['before_waste_pct']}%* ➔ *{res['after_waste_pct']}%*\n" \
              f"• Monthly Savings Unlocked: `₹{res['savings_inr_month']:,.2f}/mo`\n" \
              f"• Actions Applied: {res['actions_count']} (Approved: {res['actions_approved']}, Pending: {res['actions_pending']}, Rejected: {res['actions_rejected']})"
        return jsonify({"response_type": "in_channel", "text": msg})

    elif cmd == "status":
        with get_db() as db:
            latest = db.query(OptimizationRun).order_by(OptimizationRun.triggered_at.desc()).first()
            if not latest:
                return jsonify({"response_type": "ephemeral", "text": "No optimization runs recorded yet. Use `/autopilot run` to start one."})
            msg = f"⚡ *DevOps Autopilot Status*\n" \
                  f"• Last Run: #{latest.id} ({latest.mode.upper()}) at {latest.triggered_at.strftime('%Y-%m-%d %H:%M:%S UTC')}\n" \
                  f"• Waste: *{latest.before_waste_pct}%* ➔ *{latest.after_waste_pct}%*\n" \
                  f"• Total ₹ Saved: `₹{latest.savings_inr_month:,.2f}/mo`\n" \
                  f"• Findings: {latest.findings_count} | Actions: {latest.actions_count}"
            return jsonify({"response_type": "in_channel", "text": msg})

    elif cmd == "explain":
        run_id = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
        with get_db() as db:
            run = db.query(OptimizationRun).filter(OptimizationRun.id == run_id).first() if run_id else \
                  db.query(OptimizationRun).order_by(OptimizationRun.triggered_at.desc()).first()
            if not run:
                return jsonify({"response_type": "ephemeral", "text": "Run not found."})
            findings = db.query(Finding).filter(Finding.run_id == run.id).limit(4).all()
            lines = [f"🔍 *Agent Reasoning Explanation for Run #{run.id}:*"]
            for f in findings:
                action = f.get_action_json()
                lines.append(f"• *{f.resource_id}* ({f.issue_type.upper()}): CPU={f.utilization_pct}%. What-If: {f.predicted_util_pct}% (Risk: {f.risk_score.upper()}). Safety: `{f.safety_decision}` -> {f.safety_reason}")
            return jsonify({"response_type": "in_channel", "text": "\n".join(lines)})

    else:
        help_msg = "ℹ️ *DevOps Autopilot ChatOps Commands:*\n" \
                   "• `/autopilot run <scope> <mode>` - Launch multi-agent optimization\n" \
                   "• `/autopilot status` - View latest cluster optimization summary\n" \
                   "• `/autopilot explain <run_id>` - Natural language explanation of agent reasoning"
        return jsonify({"response_type": "ephemeral", "text": help_msg})

if __name__ == "__main__":
    port = settings.PORT
    logger.info(f"Starting DevOps Autopilot server on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=(settings.FLASK_ENV == "development"))
