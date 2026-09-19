# ⚡ DevOps Autopilot – Multi-Agent Infra Waste Resolver

> **Production-Grade Autonomous Multi-Agent AI System for Kubernetes & Cloud Infrastructure Cost Optimization with What-If Predictive Simulation, Safety Governance, and Real-Time INR Savings Tracking.**  
> *Built for the Agentic AI Hackathon Track.*

---

## 💡 Problem Statement & Value Proposition

Cloud infrastructure waste accounts for **30–45% of enterprise cloud spend**. Development and staging environments operate at peak scale over weekends, background workers run idle at 2% CPU, and oversized EC2 instances are forgotten.

Traditional automation tools fail because:
1. **Blind scripts break applications** by reducing capacity without considering traffic surges or SLO ceilings.
2. **Spreadsheet FinOps is too slow** to keep pace with dynamic containerized deployments.

**DevOps Autopilot** solves this with a **collaborative 5-agent architecture**:
- **Observer Agent**: Ingests multi-dimensional telemetry (CPU, memory, network I/O) and computes normalized waste scores.
- **Optimizer Agent**: Identifies idle/oversized capacity, proposes right-sizing actions, and runs a **What-If predictive simulation** to estimate post-change utilization and SLO breach risk.
- **Safety Agent**: Enforces organizational governance (namespace allowlists, maintenance change windows, minimum replicas, max 50% scale-down caps) and categorizes actions as `auto_approve`, `require_approval`, or `reject`.
- **Executor Agent**: Applies approved actions in dry-run or live mode via Kubernetes `apps/v1` and AWS EC2 APIs.
- **Reporter Agent**: Quantifies before/after cluster waste percentages, calculates recurring monthly INR savings, and broadcasts executive ChatOps alerts.

---

## 🏛️ Multi-Agent Swarm Architecture

```
                    ┌────────────────────────┐
                    │   Operator / Web UI    │
                    │   (SPA / ChatOps)      │
                    └───────────┬────────────┘
                                │ Trigger / Approval
                                ▼
         ┌─────────────────────────────────────────────────┐
         │            Multi-Agent Orchestrator             │
         └──────┬────────────┬────────────┬────────────┬───┘
                │            │            │            │
         Step 1 │     Step 2 │     Step 3 │     Step 4 │  Step 5
                ▼            ▼            ▼            ▼       ▼
          ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────┐ ┌─────────┐
          │ Observer │ │Optimizer │ │  Safety  │ │Executor │ │Reporter │
          │  Agent   │ │  Agent   │ │  Agent   │ │  Agent  │ │  Agent  │
          └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬────┘ └────┬────┘
               │            │            │            │           │
          Metrics       What-If      Policy &       Execute     Slack &
          Ingestion    Simulations  Governance    or Simulate   Audit Trail
               │            │            │            │           │
               ▼            ▼            ▼            ▼           ▼
        ┌──────────────────────────────────────────────────────────────┐
        │                 SQLite Storage & Audit Trail                 │
        │           (Resources, OptimizationRuns, Findings)            │
        └──────────────────────────────────────────────────────────────┘
```

---

## 🔮 What-If Simulation Engine

Before any capacity change is executed, the **Optimizer Agent** runs a predictive What-If simulation:
- **Predicted Utilization**: Calculates estimated post-scaling utilization ($\text{New Util} = \text{Old Util} \times \frac{\text{Old Replicas}}{\text{New Replicas}}$).
- **SLO Breach Risk**: Flags actions where predicted CPU exceeds safety limits (default 80%) as **HIGH RISK**.
- **Traffic Awareness**: Inspects network I/O; workloads handling active traffic are classified as **MEDIUM RISK** requiring human verification.
- **Safe Headroom**: Workloads maintaining $<60\%$ predicted utilization with low network activity are verified as **LOW RISK**.

---

## 🌐 Interactive 3D Cyber Cluster Visualizer

DevOps Autopilot includes a real-time **Three.js WebGL 3D holographic digital twin** of your infrastructure:
- **Spatial Topology**: Kubernetes namespaces (`dev`, `staging`, `demo`, `prod`) and AWS EC2 regions are rendered as elevated holographic platforms on a glowing cyber grid floor.
- **Node Volumetrics**: Server tower height scales proportionally with CPU core allocation ($0.5 \to 16.0\text{ cores}$), with neon status LED beacons.
- **Dynamic Color State**:
  - 🔴 **Crimson Red**: Idle waste (<5% CPU) with pulsing emissive glow.
  - 🟡 **Neon Amber**: Overprovisioned allocation (<30% CPU).
  - 🟢 **Neon Emerald**: Optimized & healthy capacity.
  - 🛡️ **Cyan Blue**: Protected production nodes wrapped in a wireframe forcefield.
- **Interactive OrbitControls & Raycasting**:
  - Left-click + drag to orbit, right-click to pan, scroll to zoom.
  - Hover or click any 3D node to summon the **Hologram Inspector HUD** displaying real-time telemetry, What-If predictions, and immediate approval actions.
- **Live 3D Optimization Animation**:
  - Clicking "Run Optimization" or "Animate Optimization" triggers a real-time `Tween.js` animation: oversized server towers physically shrink down to right-sized scale, idle nodes shift from red to green, and shockwave energy rings expand across cluster zones!
- **Layout Toggles**: Seamlessly switch between **Namespace Cluster Layout** and **Matrix Grid Layout**.

---

## 🛡️ Safety Agent & Governance Policies

1. **Namespace Isolation**: Automated changes **never** touch production (`prod`, `production`) by default.
2. **Change Windows**: High-risk modifications are held for operator approval outside configured maintenance windows (e.g., 02:00–04:00 IST).
3. **Minimum Traffic Replicas**: Workloads with active traffic are guarded against scaling below `MIN_REPLICAS_TRAFFIC` (default 2).
4. **Gradual Scale-Down Cap**: Replicas can only be reduced by a maximum of **50%** per run.
5. **Action Rate Limiting**: Capped at **10 actions per run** by default.
6. **Human-in-the-Loop Approvals**: Items marked `require_approval` can be reviewed and authorized directly via the UI or Slack ChatOps.

---

## 🚀 Quickstart & One-Click Launch

### 1. Install Dependencies
```bash
cd agentic
pip install -r requirements.txt
```

### 2. Launch Unified Server & Web Browser
```bash
python run_server.py
```
This starts the backend API and **automatically opens your web browser** to `http://localhost:5000`.

*(Alternatively, run `streamlit run streamlit_app.py` for the Streamlit dashboard.)*

---

## 📡 REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/optimize` | Triggers a multi-agent optimization cycle (`mode: dry_run \| live`, `scope: all \| staging \| dev`). |
| `GET` | `/api/savings` | Aggregate monthly INR savings and cluster waste % trend. |
| `GET` | `/api/waste-map` | Aggregated waste score and cost leakage by namespace and service. |
| `POST` | `/api/approve` | Human-in-the-loop: approves specific finding IDs for live execution. |
| `GET` | `/api/runs` | List recent optimization runs. |
| `GET` | `/api/runs/<id>` | Full run details with What-If simulations and safety decisions. |
| `POST` | `/slack/commands` | Slack ChatOps slash command handler (`/autopilot run`, `status`, `explain`). |
| `GET` | `/health` | Service and multi-agent health status. |

---

## 💬 Slack ChatOps Commands

- `/autopilot run <scope> <mode>`: Trigger an autonomous multi-agent optimization.
- `/autopilot status`: View summary of the latest cluster run.
- `/autopilot explain <run_id>`: Natural-language explanation of top findings and safety decisions.

---

## 🧪 Hackathon Demo Walkthrough (90 Seconds)

1. Run `python run_server.py`. Browser opens to `http://localhost:5000`.
2. Click **"Run Optimization (Dry-Run)"**.
3. Watch the **Agent Reasoning Feed** stream Observer ➔ Optimizer ➔ Safety ➔ Executor ➔ Reporter handoffs.
4. Review the **What-If Simulator** table: see predicted CPU utilizations and risk ratings.
5. Click **"Waste Map"** to view capacity leakage across namespaces.
6. Click **"Audit Trail"** to inspect system and operator approval histories.
7. Verify recurring monthly savings in **₹ INR** and before/after waste reduction.

---

## 📄 License
MIT License. Built for the Agentic AI Hackathon 2026.
