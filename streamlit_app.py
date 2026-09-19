import streamlit as st
import pandas as pd
import requests
from config import settings

st.set_page_config(
    page_title="DevOps Autopilot – Multi-Agent Infra Waste Resolver",
    page_icon="⚡",
    layout="wide"
)

API_BASE = f"http://127.0.0.1:{settings.PORT}"

st.title("⚡ DevOps Autopilot – Multi-Agent Infra Waste Resolver")
st.caption("Collaborative Agentic Swarm: Observer ➔ Optimizer (What-If) ➔ Safety Agent ➔ Executor ➔ Reporter")

# Sidebar - Safety Policies
st.sidebar.header("🛡️ Safety & Governance Policies")
st.sidebar.info(f"**Allowed Namespaces:** {', '.join(settings.ALLOWED_NAMESPACES)}")
st.sidebar.info(f"**Max Scale-down:** {int(settings.MAX_REPLICA_REDUCTION_PCT * 100)}%")
st.sidebar.info(f"**Max Actions/Run:** {settings.MAX_ACTIONS_PER_RUN}")
st.sidebar.info(f"**SLO Ceiling:** {settings.SLO_MAX_CPU_UTIL_PCT}% CPU")
st.sidebar.info(f"**Change Window:** {settings.CHANGE_WINDOW_START_HOUR}:00-{settings.CHANGE_WINDOW_END_HOUR}:00 IST")

scope = st.sidebar.selectbox("Scope Filter", ["all", "staging", "dev", "demo"])
col_btn1, col_btn2 = st.sidebar.columns(2)
run_dry = col_btn1.button("🔍 Run Dry-Run", use_container_width=True)
run_live = col_btn2.button("⚡ Run Live", use_container_width=True, type="primary")

if run_dry or run_live:
    mode = "live" if run_live else "dry_run"
    with st.spinner(f"Multi-agent swarm collaborating in {mode.upper()} mode..."):
        try:
            resp = requests.post(f"{API_BASE}/api/optimize", json={"mode": mode, "scope": scope}, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                st.success(f"Run #{data.get('run_id')} complete! Waste reduced {data.get('before_waste_pct')}% ➔ {data.get('after_waste_pct')}%. Unlocked ₹{data.get('savings_inr_month'):,.2f}/mo.")
            else:
                st.error(f"Error: {resp.text}")
        except Exception as e:
            st.error(f"Failed to connect to backend: {e}")

# Fetch Aggregate Stats
try:
    savings_resp = requests.get(f"{API_BASE}/api/savings", timeout=5).json()
    total_savings = savings_resp.get("total_estimated_savings_inr_month", 0.0)
    total_actions = savings_resp.get("total_actions_count", 0)
    latest_run = savings_resp.get("latest_run")
except Exception:
    total_savings = 0.0
    total_actions = 0
    latest_run = None

# Top Metrics Row
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("Estimated Monthly Savings", f"₹{total_savings:,.2f} / mo")
with m2:
    if latest_run:
        st.metric("Cluster Waste Trajectory", f"{latest_run.get('before_waste_pct', 0)}% ➔ {latest_run.get('after_waste_pct', 0)}%")
    else:
        st.metric("Cluster Waste Trajectory", "0.0% ➔ 0.0%")
with m3:
    st.metric("Actions Executed", f"{total_actions} applied")
with m4:
    status_label = "Active" if latest_run and latest_run.get("slack_posted") else "Simulated"
    st.metric("Slack ChatOps", status_label)

# Streamlit Tabs
tab_overview, tab_waste_map, tab_what_if, tab_audit = st.tabs([
    "📊 Swarm Overview", "🗺️ Waste Map", "🔮 Run Details & What-If", "📜 Audit Trail"
])

with tab_overview:
    if latest_run:
        st.markdown("### 📋 Latest Executive Summary")
        st.info(latest_run.get("summary_text", ""))
    else:
        st.write("Trigger an optimization run to view multi-agent results.")

with tab_waste_map:
    st.markdown("### 🗺️ Capacity Waste Map by Namespace")
    try:
        wm_resp = requests.get(f"{API_BASE}/api/waste-map", timeout=5).json()
        if wm_resp:
            wm_df = pd.DataFrame([
                {
                    "Namespace": w["namespace"],
                    "Workloads": w["resource_count"],
                    "Average Waste Score": f"{w['waste_score']}%",
                    "Monthly Waste Leakage": f"₹{w['estimated_waste_inr_month']:,.2f}"
                }
                for w in wm_resp
            ])
            st.dataframe(wm_df, use_container_width=True)
    except Exception as e:
        st.warning(f"Could not load waste map: {e}")

with tab_what_if:
    st.markdown("### 🔮 Workload Optimization & What-If Simulation")
    if latest_run:
        try:
            run_detail = requests.get(f"{API_BASE}/api/runs/{latest_run['id']}", timeout=5).json()
            findings = run_detail.get("findings", [])
            if findings:
                table_rows = []
                for f in findings:
                    action = f.get("proposed_action", {})
                    action_str = f"Scale {action.get('current_replicas')} ➔ {action.get('target_replicas')}" if f["resource_type"] == "pod" else "Stop Instance"
                    table_rows.append({
                        "Resource": f["resource_id"],
                        "Type": f["resource_type"].upper(),
                        "Issue": f["issue_type"].upper(),
                        "Current Util": f"{f['utilization_pct']}%",
                        "Proposed Action": action_str,
                        "What-If (Predicted)": f"{f.get('predicted_util_pct', 0)}%",
                        "SLO Risk": f.get("risk_score", "low").upper(),
                        "Safety Decision": f.get("safety_decision", "auto_approve").upper(),
                        "Est. Savings": f"₹{f['estimated_savings_inr_month']:,.2f}",
                        "Executed?": "✅ Yes" if f["executed"] else "🔍 Simulated"
                    })
                st.dataframe(pd.DataFrame(table_rows), use_container_width=True)
        except Exception as e:
            st.warning(f"Error loading findings: {e}")
    else:
        st.write("No run findings yet.")

with tab_audit:
    st.markdown("### 📜 Governance Audit Trail")
    try:
        runs_resp = requests.get(f"{API_BASE}/api/runs?limit=5", timeout=5).json()
        if runs_resp:
            audit_rows = []
            for r in runs_resp:
                audit_rows.append({
                    "Run ID": r["id"],
                    "Timestamp": r["triggered_at"],
                    "Mode": r["mode"].upper(),
                    "Actions Approved": r["actions_approved"],
                    "Actions Rejected": r["actions_rejected"],
                    "Waste Before": f"{r['before_waste_pct']}%",
                    "Waste After": f"{r['after_waste_pct']}%",
                    "Monthly Savings": f"₹{r['savings_inr_month']:,.2f}"
                })
            st.dataframe(pd.DataFrame(audit_rows), use_container_width=True)
    except Exception as e:
        st.warning(f"Error loading audit trail: {e}")
