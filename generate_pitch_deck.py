import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

def create_deck():
    prs = Presentation()
    # 16:9 Widescreen dimensions: 13.333 x 7.5 inches
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_slide_layout = prs.slide_layouts[6] # Blank layout

    # Colors
    C_BG = RGBColor(10, 15, 29)         # Deep Dark Navy #0A0F1D
    C_CARD = RGBColor(19, 27, 46)       # Surface Card #131B2E
    C_CARD_BORDER = RGBColor(37, 99, 235)# Sapphire Blue
    C_ACCENT_BLUE = RGBColor(59, 130, 246) # Bright Blue #3B82F6
    C_ACCENT_CYAN = RGBColor(6, 182, 212) # Cyan #06B6D4
    C_ACCENT_GREEN = RGBColor(16, 185, 129) # Emerald #10B981
    C_ACCENT_AMBER = RGBColor(245, 158, 11) # Amber #F59E0B
    C_ACCENT_RED = RGBColor(239, 68, 68)   # Red #EF4444
    C_WHITE = RGBColor(255, 255, 255)
    C_TEXT_MUTED = RGBColor(148, 163, 184) # Slate #94A3B8
    C_TEXT_LIGHT = RGBColor(226, 232, 240) # Slate #E2E8F0

    def set_slide_background(slide):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
        bg.fill.solid()
        bg.fill.fore_color.rgb = C_BG
        bg.line.fill.background()
        return bg

    def add_header(slide, tag, title, subtitle=None):
        # Category Tag Badge
        tag_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.45), Inches(10), Inches(0.4))
        tf_tag = tag_box.text_frame
        tf_tag.word_wrap = True
        p_tag = tf_tag.paragraphs[0]
        p_tag.text = tag.upper()
        p_tag.font.size = Pt(10)
        p_tag.font.bold = True
        p_tag.font.color.rgb = C_ACCENT_CYAN

        # Title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.75), Inches(11.5), Inches(0.8))
        tf_title = title_box.text_frame
        tf_title.word_wrap = True
        p_title = tf_title.paragraphs[0]
        p_title.text = title
        p_title.font.size = Pt(24)
        p_title.font.bold = True
        p_title.font.color.rgb = C_WHITE

        if subtitle:
            sub_box = slide.shapes.add_textbox(Inches(0.8), Inches(1.4), Inches(11.5), Inches(0.5))
            tf_sub = sub_box.text_frame
            tf_sub.word_wrap = True
            p_sub = tf_sub.paragraphs[0]
            p_sub.text = subtitle
            p_sub.font.size = Pt(12)
            p_sub.font.color.rgb = C_TEXT_MUTED

    def add_card(slide, left, top, width, height, title, content_items, border_color=C_CARD_BORDER, title_color=C_ACCENT_CYAN):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = C_CARD
        card.line.color.rgb = border_color
        card.line.width = Pt(1.5)

        txBox = slide.shapes.add_textbox(left + Inches(0.25), top + Inches(0.2), width - Inches(0.5), height - Inches(0.4))
        tf = txBox.text_frame
        tf.word_wrap = True

        p0 = tf.paragraphs[0]
        p0.text = title
        p0.font.size = Pt(15)
        p0.font.bold = True
        p0.font.color.rgb = title_color
        p0.space_after = Pt(10)

        for item in content_items:
            p = tf.add_paragraph()
            p.text = f"•  {item}"
            p.font.size = Pt(11)
            p.font.color.rgb = C_TEXT_LIGHT
            p.space_after = Pt(6)

    # ----------------------------------------------------
    # SLIDE 1: Title Slide (Cover)
    # ----------------------------------------------------
    s1 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(s1)

    # Accent decorative gradient bar
    bar = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.8), Inches(1.2), Inches(0.08))
    bar.fill.solid()
    bar.fill.fore_color.rgb = C_ACCENT_CYAN
    bar.line.fill.background()

    # Track Tag
    track_box = s1.shapes.add_textbox(Inches(0.8), Inches(2.0), Inches(10), Inches(0.5))
    tf_tr = track_box.text_frame
    p_tr = tf_tr.paragraphs[0]
    p_tr.text = "AGENTIC AI TRACK  |  AUTONOMOUS CLOUD FINOPS & SRE COPILOT"
    p_tr.font.size = Pt(12)
    p_tr.font.bold = True
    p_tr.font.color.rgb = C_ACCENT_CYAN

    # Main Title
    t_box = s1.shapes.add_textbox(Inches(0.8), Inches(2.5), Inches(11.5), Inches(1.8))
    tf_t = t_box.text_frame
    tf_t.word_wrap = True
    p_t = tf_t.paragraphs[0]
    p_t.text = "DevOps Autopilot"
    p_t.font.size = Pt(44)
    p_t.font.bold = True
    p_t.font.color.rgb = C_WHITE

    p_t2 = tf_t.add_paragraph()
    p_t2.text = "Autonomous Infrastructure Waste Resolver"
    p_t2.font.size = Pt(28)
    p_t2.font.bold = True
    p_t2.font.color.rgb = C_ACCENT_BLUE

    # Pitch description
    d_box = s1.shapes.add_textbox(Inches(0.8), Inches(4.5), Inches(11.5), Inches(1.2))
    tf_d = d_box.text_frame
    tf_d.word_wrap = True
    p_d = tf_d.paragraphs[0]
    p_d.text = "A multi-agent AI system that continuously detects cloud waste, simulates capacity risk, enforces strict safety policies, and executes risk-governed remediations across Kubernetes & AWS with Slack ChatOps."
    p_d.font.size = Pt(13)
    p_d.font.color.rgb = C_TEXT_LIGHT

    # Metadata badges
    m_box = s1.shapes.add_textbox(Inches(0.8), Inches(6.0), Inches(11.5), Inches(0.6))
    tf_m = m_box.text_frame
    p_m = tf_m.paragraphs[0]
    p_m.text = "⚡ Stack: Python, Flask, SQLAlchemy, Three.js WebGL, Slack Block Kit, OpenAI Function Calling"
    p_m.font.size = Pt(11)
    p_m.font.bold = True
    p_m.font.color.rgb = C_TEXT_MUTED

    # ----------------------------------------------------
    # SLIDE 2: The Problem
    # ----------------------------------------------------
    s2 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(s2)
    add_header(s2, "The Problem", "The Silent Crisis: $30B+ Lost Annually in Cloud Waste", "Static dashboards dump charts on overworked SREs while idle pods drain engineering budgets.")

    add_card(s2, Inches(0.8), Inches(2.1), Inches(3.6), Inches(4.6), "1. Set-and-Forget Sizing", [
        "Developers over-request CPU and RAM to prevent performance alerts.",
        "Average K8s cluster operates at only 8-15% actual CPU utilization.",
        "Up to 45% of allocated cloud capacity sits completely dormant.",
        "Overprovisioning compounds silently as microservices scale."
    ], border_color=C_ACCENT_RED, title_color=C_ACCENT_RED)

    add_card(s2, Inches(4.8), Inches(2.1), Inches(3.6), Inches(4.6), "2. Staging & Zombie Sprawl", [
        "Ephemeral test and feature-branch namespaces are abandoned after PRs merge.",
        "Zombie EC2 worker instances continue running 24/7 processing zero requests.",
        "Non-prod environments handling 2 req/min run 5 to 10 full replicas.",
        "FinOps bills compound month-over-month without business value."
    ], border_color=C_ACCENT_AMBER, title_color=C_ACCENT_AMBER)

    add_card(s2, Inches(8.8), Inches(2.1), Inches(3.7), Inches(4.6), "3. The Remediation Void", [
        "Datadog & CloudWatch show charts but require manual engineering to fix.",
        "SREs suffer alert fatigue; rightsizing tickets languish in backlogs.",
        "Cron scripts lack context and risk causing catastrophic outages.",
        "Result: Continuous waste with zero automated, safe remediation."
    ], border_color=C_ACCENT_BLUE, title_color=C_ACCENT_CYAN)

    # ----------------------------------------------------
    # SLIDE 3: The Solution (DevOps Autopilot)
    # ----------------------------------------------------
    s3 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(s3)
    add_header(s3, "The Solution", "DevOps Autopilot: Autonomous, Safe, and Explainable", "Transforming cloud FinOps from a manual sprint chore into an indefatigable agentic copilot.")

    # Top KPI Banner
    banner = s3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(2.0), Inches(11.7), Inches(1.1))
    banner.fill.solid()
    banner.fill.fore_color.rgb = C_CARD
    banner.line.color.rgb = C_ACCENT_GREEN
    banner.line.width = Pt(1.5)

    tb_b = s3.shapes.add_textbox(Inches(1.0), Inches(2.15), Inches(11.3), Inches(0.8))
    p_b = tb_b.text_frame.paragraphs[0]
    p_b.text = "DEMONSTRATED RESULTS:   32.8% ➔ 14.2% Cluster Waste Reduction   |   ₹18,450/month Direct Savings   |   0 Incidents"
    p_b.font.size = Pt(14)
    p_b.font.bold = True
    p_b.font.color.rgb = C_ACCENT_GREEN

    # 3 Pillars
    add_card(s3, Inches(0.8), Inches(3.4), Inches(3.6), Inches(3.5), "Autonomous Perception", [
        "Real-time telemetry ingestion from K8s Metrics Server & AWS APIs.",
        "Multi-dimensional waste scoring (CPU, RAM, network packet flow).",
        "Deterministic pre-filtering to eliminate noise."
    ], border_color=C_ACCENT_CYAN, title_color=C_ACCENT_CYAN)

    add_card(s3, Inches(4.8), Inches(3.4), Inches(3.6), Inches(3.5), "Predictive Simulation", [
        "Built-in 'What-If' simulator models post-change utilization.",
        "Predicts SLO breach risks BEFORE any physical mutation.",
        "Generates transparent, auditable natural-language explanations."
    ], border_color=C_ACCENT_BLUE, title_color=C_ACCENT_BLUE)

    add_card(s3, Inches(8.8), Inches(3.4), Inches(3.7), Inches(3.5), "Graduated Governance", [
        "Strict safety policies: namespace filters & change windows.",
        "Auto-executes zero-risk fixes in non-prod (70% autonomous).",
        "Escalates sensitive actions to Slack for one-click human sign-off."
    ], border_color=C_ACCENT_GREEN, title_color=C_ACCENT_GREEN)

    # ----------------------------------------------------
    # SLIDE 4: Multi-Agent Architecture
    # ----------------------------------------------------
    s4 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(s4)
    add_header(s4, "Multi-Agent System", "5 Specialized Cooperating Agents", "Decoupled agents with clear separation of perception, reasoning, safety, execution, and reporting.")

    # 5 Agents horizontal flow
    agents = [
        ("1. Observer", "Perception Engine", ["Polls K8s Metrics & AWS CloudWatch", "Calculates composite Waste Score (0-100)", "Filters healthy services from candidates"], C_ACCENT_CYAN),
        ("2. Optimizer", "Reasoning & What-If", ["Analyzes telemetry with LLM tool calling", "Synthesizes scale/stop proposals", "Runs What-If Simulator for risk (L/M/H)"], C_ACCENT_BLUE),
        ("3. Safety", "Constitutional Gatekeeper", ["Enforces namespace allowlist & windows", "Guarantees min 2 replicas for HA", "Decides: auto_approve | require | reject"], C_ACCENT_AMBER),
        ("4. Executor", "Execution Engine", ["Operates in dry_run or live mode", "Applies K8s AppsV1 / AWS Boto3 patches", "Self-heals with 60s rollback monitoring"], C_ACCENT_GREEN),
        ("5. Reporter", "Slack & UI Sync", ["Compiles interactive Slack Block Kit", "Updates SQLite audit ledger & INR metrics", "Broadcasts topology diffs to Web UI"], C_CARD_BORDER)
    ]

    card_w = Inches(2.22)
    spacing = Inches(0.15)
    start_x = Inches(0.8)

    for i, (name, role, points, col) in enumerate(agents):
        x = start_x + i * (card_w + spacing)
        add_card(s4, x, Inches(2.1), card_w, Inches(4.7), name, [f"{role}"] + points, border_color=col, title_color=col)

    # ----------------------------------------------------
    # SLIDE 5: The What-If Simulator & Risk Scoring
    # ----------------------------------------------------
    s5 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(s5)
    add_header(s5, "Innovation & Reliability", "The What-If Simulator: Predicting Impact Before Execution", "Eliminating downtime risk by mathematically forecasting post-change steady state.")

    add_card(s5, Inches(0.8), Inches(2.1), Inches(5.6), Inches(4.7), "Mathematical Simulation Engine", [
        "Predictive Utilization Equation:",
        "  New Util = Current Util × (Old Replicas / Target Replicas)",
        "Example: cart-service (5 pods @ 2% CPU) scaled to 2 pods:",
        "  Predicted Util = 2.0% × (5 / 2) = 5.0%",
        "  Comfortable Headroom Remaining: 95.0%",
        "Direct Monthly Savings Calculation:",
        "  Savings = (Old - Target) × (Core Cost + RAM Cost)",
        "  Delta 3 pods × ₹2,600/mo = ₹7,800.00/month saved!"
    ], border_color=C_ACCENT_CYAN, title_color=C_ACCENT_CYAN)

    add_card(s5, Inches(6.8), Inches(2.1), Inches(5.7), Inches(4.7), "Risk Matrix & Decision Boundaries", [
        "🟢 LOW RISK (Predicted Util < 65%):",
        "  Massive headroom remaining. Safe for auto-approval in non-prod.",
        "🟡 MEDIUM RISK (Predicted Util 65% - 80%):",
        "  Moderate headroom. Flags require_approval in staging/prod.",
        "🔴 HIGH RISK (Predicted Util > 80%):",
        "  SLO breach hazard! Automatically rejected by Safety Agent.",
        "🛡️ Zero Guesswork:",
        "  Every finding contains explicit mathematical rationale in UI and Slack."
    ], border_color=C_ACCENT_GREEN, title_color=C_ACCENT_GREEN)

    # ----------------------------------------------------
    # SLIDE 6: Safety, Governance & Guardrails
    # ----------------------------------------------------
    s6 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(s6)
    add_header(s6, "Governance & Safety", "Multi-Layered Guardrails: Zero Unintended Outages", "Engineered with defense-in-depth policies so SREs can trust autonomous operations.")

    add_card(s6, Inches(0.8), Inches(2.1), Inches(3.6), Inches(4.7), "1. Policy Guardrails", [
        "Namespace Allowlist:",
        "  Default restricted to staging, dev, demo.",
        "  Prod changes NEVER auto-execute.",
        "Temporal Change Windows:",
        "  Prod operations locked to 02:00-04:00 AM IST.",
        "Minimum Replica Floor:",
        "  Services with ingress traffic maintain >= 2 pods.",
        "Single-Run Blast Radius Ceiling:",
        "  Max 50% replica reduction in single run.",
        "  Max 10 mutating actions per run."
    ], border_color=C_ACCENT_BLUE, title_color=C_ACCENT_BLUE)

    add_card(s6, Inches(4.8), Inches(2.1), Inches(3.6), Inches(4.7), "2. Human-in-the-Loop", [
        "Graduated Autonomy:",
        "  • 70% of actions: auto-approved (low-risk non-prod).",
        "  • 30% of actions: queued for sign-off.",
        "Slack Interactive Approvals:",
        "  SREs click [Approve] directly in Slack.",
        "Cryptographic Verification:",
        "  HMAC signature validation prevents spoofing.",
        "Audited Attribution:",
        "  Database records approver handle and timestamp."
    ], border_color=C_ACCENT_AMBER, title_color=C_ACCENT_AMBER)

    add_card(s6, Inches(8.8), Inches(2.1), Inches(3.7), Inches(4.7), "3. Rollback & Self-Healing", [
        "Idempotency Guarantee:",
        "  Re-verifies cluster state before executing mutation.",
        "60-Second Health Sentinel:",
        "  Monitors pod readiness and crash loops post-patch.",
        "Automated Rollback:",
        "  Immediately reverts to previous replica count if 5xx spikes or pod crashes occur.",
        "Zero Critical Incidents:",
        "  Validated throughout all staging demo runs."
    ], border_color=C_ACCENT_GREEN, title_color=C_ACCENT_GREEN)

    # ----------------------------------------------------
    # SLIDE 7: Visual Experience & 3D Cluster
    # ----------------------------------------------------
    s7 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(s7)
    add_header(s7, "User Experience", "Futuristic Visual Console & 3D Cluster Topography", "A cybernetic, responsive command center designed for rapid SRE situational awareness.")

    add_card(s7, Inches(0.8), Inches(2.1), Inches(5.6), Inches(4.7), "3D Cyber Cluster (WebGL / Three.js)", [
        "🌐 Spatial Infrastructure Visualization:",
        "  Renders Kubernetes namespaces as revolving orbital rings.",
        "🔴 Neon Red Pods: Severe Waste / Zombie candidates (Util < 5%).",
        "🟡 Amber Pods: Overprovisioned workloads (Util 10-30%).",
        "🟢 Emerald Pods: Healthy, optimized services.",
        "Interactive Spatial Topology:",
        "  Full 360° orbit, pan, zoom, and real-time pulse animations.",
        "Real-Time Color Shift:",
        "  Nodes transition to emerald green upon successful optimization."
    ], border_color=C_ACCENT_CYAN, title_color=C_ACCENT_CYAN)

    add_card(s7, Inches(6.8), Inches(2.1), Inches(5.7), Inches(4.7), "Granular FinOps Command Views", [
        "🗺️ Waste Heatmap Tab:",
        "  Hierarchical breakdown by namespace and service.",
        "  Instantly pinpoints top wasting squads and cost drains.",
        "🔮 Run Details & What-If Simulator Tab:",
        "  Exposes predicted utilization, risk reasoning, and safety decisions.",
        "🧠 Agent Cognitive Reasoning Log Panel:",
        "  Live terminal stream displaying deduction steps of all 5 agents.",
        "📜 Comprehensive Audit Trail:",
        "  Permanent ledger of all actions, diffs, approvers, and INR saved."
    ], border_color=C_ACCENT_BLUE, title_color=C_ACCENT_BLUE)

    # ----------------------------------------------------
    # SLIDE 8: Slack ChatOps Integration
    # ----------------------------------------------------
    s8 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(s8)
    add_header(s8, "ChatOps & Collaboration", "Slack ChatOps: SRE Command Center in Shared Channels", "Manage cluster health and approve high-impact optimizations where engineering conversations happen.")

    add_card(s8, Inches(0.8), Inches(2.1), Inches(5.6), Inches(4.7), "Supported Slash Commands", [
        "•  `/autopilot run <scope> <mode>`",
        "   Launches multi-agent cycle (e.g. `/autopilot run staging live`).",
        "•  `/autopilot status`",
        "   Returns real-time cluster waste %, top wasting pods, and pending approvals.",
        "•  `/autopilot explain <run_id>`",
        "   Generates natural-language reasoning summary for specific findings.",
        "",
        "Instant Feedback Loop:",
        "Responds in under 2 seconds directly in Slack channel with rich Block Kit cards."
    ], border_color=C_ACCENT_CYAN, title_color=C_ACCENT_CYAN)

    add_card(s8, Inches(6.8), Inches(2.1), Inches(5.7), Inches(4.7), "Interactive Block Kit Cards", [
        "📊 Visual Waste & Savings Badges:",
        "  Shows exact before/after waste delta and recurring monthly INR savings.",
        "⚡ Inline Action Buttons:",
        "  [ APPROVE & EXECUTE ]   |   [ REJECT ]   |   [ VIEW AUDIT ]",
        "One-Click Remediation:",
        "  Approving in Slack instantly triggers the Executor Agent via webhook.",
        "Immutable Audit Stamp:",
        "  Card dynamically updates to show: 'Approved by @alex.sre at 13:48 UTC'."
    ], border_color=C_ACCENT_AMBER, title_color=C_ACCENT_AMBER)

    # ----------------------------------------------------
    # SLIDE 9: System Architecture & Data Model
    # ----------------------------------------------------
    s9 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(s9)
    add_header(s9, "Technical Blueprint", "End-to-End System Architecture & Data Schema", "Clean modular design built on Python, Flask, SQLAlchemy, and modern cloud APIs.")

    add_card(s9, Inches(0.8), Inches(2.1), Inches(5.6), Inches(4.7), "Core Technology Stack", [
        "•  Backend Engine: Python 3.10+ / Flask API Gateway",
        "•  Agent Orchestration: Cooperative multi-agent handoff pipeline",
        "•  Cognitive LLM: OpenAI Function Calling (GPT-4o / GPT-4o-mini)",
        "•  Persistence: SQLite / PostgreSQL via SQLAlchemy ORM",
        "•  Infrastructure Adapters:",
        "   - Kubernetes: CoreV1Api, AppsV1Api, Metrics API (mock supported)",
        "   - AWS Cloud: Boto3 EC2 & CloudWatch integration",
        "•  Presentation: Three.js WebGL, Vanilla CSS, Slack Webhooks"
    ], border_color=C_CARD_BORDER, title_color=C_ACCENT_CYAN)

    add_card(s9, Inches(6.8), Inches(2.1), Inches(5.7), Inches(4.7), "Relational Data Schema", [
        "1. Resource Table:",
        "   Stores current resource inventory, requests, avg usage, waste_score.",
        "2. OptimizationRun Table:",
        "   Tracks run ID, mode, before/after waste %, total INR savings, summary.",
        "3. Finding Table (Foreign Key -> Run):",
        "   Stores resource_id, issue_type, proposed_action, predicted_util,",
        "   risk_score, risk_reason, safety_decision, executed, approved_by.",
        "Foreign Key Referential Integrity & Fast Indexing on run_id & resource_id."
    ], border_color=C_CARD_BORDER, title_color=C_ACCENT_BLUE)

    # ----------------------------------------------------
    # SLIDE 10: Hackathon Demo Results & Impact
    # ----------------------------------------------------
    s10 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(s10)
    add_header(s10, "Hackathon Demo Results", "Measurable Business & Operational Impact", "Quantified results demonstrated on realistic enterprise staging workloads.")

    # 4 Stat Boxes
    stats = [
        ("WASTE REDUCTION", "32.8% ➔ 14.2%", "56% Relative Drop", C_ACCENT_CYAN),
        ("MONTHLY SAVINGS", "₹18,450 / mo", "₹2,21,400 / year", C_ACCENT_GREEN),
        ("AUTONOMOUS YIELD", "70% Auto-Approved", "30% Human Signoff", C_ACCENT_BLUE),
        ("SLO DOWNTIME", "0 Incidents", "100% Availability", C_ACCENT_AMBER)
    ]
    sw = Inches(2.78)
    for i, (label, val, sub, col) in enumerate(stats):
        x = Inches(0.8) + i * (sw + Inches(0.2))
        box = s10.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, Inches(2.1), sw, Inches(1.8))
        box.fill.solid()
        box.fill.fore_color.rgb = C_CARD
        box.line.color.rgb = col
        box.line.width = Pt(1.5)

        tb = s10.shapes.add_textbox(x + Inches(0.1), Inches(2.25), sw - Inches(0.2), Inches(1.5))
        tf = tb.text_frame
        p1 = tf.paragraphs[0]
        p1.text = label
        p1.font.size = Pt(10)
        p1.font.bold = True
        p1.font.color.rgb = C_TEXT_MUTED

        p2 = tf.add_paragraph()
        p2.text = val
        p2.font.size = Pt(20)
        p2.font.bold = True
        p2.font.color.rgb = col

        p3 = tf.add_paragraph()
        p3.text = sub
        p3.font.size = Pt(11)
        p3.font.color.rgb = C_TEXT_LIGHT

    # Breakdown card
    add_card(s10, Inches(0.8), Inches(4.2), Inches(11.7), Inches(2.6), "Workload Action Breakdown (Demo Topology)", [
        "• cart-service (staging): 5 pods @ 2% CPU ➔ Scaled down to 2 pods (Savings: ₹7,800.00/mo) | Auto-Approved",
        "• payment-mock (staging): 3 pods @ 0.5% CPU ➔ Scaled down to 1 pod (Savings: ₹4,200.00/mo) | Auto-Approved",
        "• i-09f1a2b3c4d5e6f7a (AWS EC2): t3.xlarge Zombie instance ➔ Stopped (Savings: ₹8,640.00/mo) | Auto-Approved",
        "• core-db-replica (prod): Overprovisioned ➔ Flagged for Human Sign-Off due to Prod Namespace Policy | SRE Verified"
    ], border_color=C_CARD_BORDER, title_color=C_WHITE)

    # ----------------------------------------------------
    # SLIDE 11: Future Roadmap
    # ----------------------------------------------------
    s11 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(s11)
    add_header(s11, "Looking Ahead", "Strategic Engineering Roadmap", "Evolving from reactive rightsizing to a continuous, predictive FinOps intelligence plane.")

    roadmap_items = [
        ("Phase 1: GitOps PR Generation", "Q3 2026", [
            "Fork & submit Pull Requests to GitHub/GitLab with updated Helm/Kustomize manifests.",
            "Preserve Git as single source of truth for all cluster configuration changes."
        ], C_ACCENT_CYAN),
        ("Phase 2: OpenTelemetry & Deep SLOs", "Q4 2026", [
            "Ingest distributed trace latency (p95/p99) and Prometheus SLO alert rules.",
            "Dynamic rightsizing based on user-facing request latency thresholds."
        ], C_ACCENT_BLUE),
        ("Phase 3: Carbon-Aware Scheduling", "Q1 2027", [
            "Integrate regional grid carbon intensity APIs (ElectricityMaps).",
            "Automatically shift batch & training compute to clean-energy regions and off-peak hours."
        ], C_ACCENT_GREEN),
        ("Phase 4: Multi-Cloud Optimization", "Q2 2027", [
            "Extend support to Google Cloud (GKE) and Microsoft Azure (AKS).",
            "Autonomous Spot/Preemptible instance bidding and dynamic workload relocation."
        ], C_ACCENT_AMBER)
    ]

    card_w = Inches(2.78)
    for i, (title, timeline, bullets, col) in enumerate(roadmap_items):
        x = Inches(0.8) + i * (card_w + Inches(0.2))
        add_card(s11, x, Inches(2.1), card_w, Inches(4.7), title, [f"Target: {timeline}"] + bullets, border_color=col, title_color=col)

    # ----------------------------------------------------
    # SLIDE 12: Conclusion & Q&A
    # ----------------------------------------------------
    s12 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(s12)

    bar = s12.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.8), Inches(1.2), Inches(0.08))
    bar.fill.solid()
    bar.fill.fore_color.rgb = C_ACCENT_GREEN
    bar.line.fill.background()

    track_box = s12.shapes.add_textbox(Inches(0.8), Inches(2.0), Inches(10), Inches(0.5))
    tf_tr = track_box.text_frame
    p_tr = tf_tr.paragraphs[0]
    p_tr.text = "THANK YOU  |  HACKATHON SUBMISSION 2026"
    p_tr.font.size = Pt(12)
    p_tr.font.bold = True
    p_tr.font.color.rgb = C_ACCENT_GREEN

    t_box = s12.shapes.add_textbox(Inches(0.8), Inches(2.5), Inches(11.5), Inches(1.5))
    tf_t = t_box.text_frame
    p_t = tf_t.paragraphs[0]
    p_t.text = "DevOps Autopilot"
    p_t.font.size = Pt(44)
    p_t.font.bold = True
    p_t.font.color.rgb = C_WHITE

    p_t2 = tf_t.add_paragraph()
    p_t2.text = "Bridging Perception, Reasoning & Safe Autonomous Execution"
    p_t2.font.size = Pt(24)
    p_t2.font.bold = True
    p_t2.font.color.rgb = C_ACCENT_CYAN

    sum_box = s12.shapes.add_textbox(Inches(0.8), Inches(4.4), Inches(11.5), Inches(1.6))
    tf_sum = sum_box.text_frame
    tf_sum.word_wrap = True
    p_s1 = tf_sum.paragraphs[0]
    p_s1.text = "• 5 Specialized Agents: Observer, Optimizer, Safety, Executor, Reporter"
    p_s1.font.size = Pt(14)
    p_s1.font.color.rgb = C_TEXT_LIGHT

    p_s2 = tf_sum.add_paragraph()
    p_s2.text = "• Measurable Impact: 32.8% ➔ 14.2% Waste Reduction | ₹18,450.00/month Recovered"
    p_s2.font.size = Pt(14)
    p_s2.font.color.rgb = C_TEXT_LIGHT

    p_s3 = tf_sum.add_paragraph()
    p_s3.text = "• Trust & Governance: Pre-Execution What-If Simulation + Slack ChatOps + Zero Incidents"
    p_s3.font.size = Pt(14)
    p_s3.font.color.rgb = C_TEXT_LIGHT

    link_box = s12.shapes.add_textbox(Inches(0.8), Inches(6.0), Inches(11.5), Inches(0.6))
    tf_l = link_box.text_frame
    p_l = tf_l.paragraphs[0]
    p_l.text = "🚀 Web Dashboard: http://127.0.0.1:5000  |  Full PDF Report: /report/pdf  |  Deck: /report/ppt"
    p_l.font.size = Pt(12)
    p_l.font.bold = True
    p_l.font.color.rgb = C_ACCENT_CYAN

    # Save presentation
    output_path = os.path.join(os.path.dirname(__file__), "DevOps_Autopilot_Pitch_Deck.pptx")
    prs.save(output_path)
    size_kb = os.path.getsize(output_path) / 1024
    print(f"SUCCESS: PowerPoint Presentation saved to: {output_path} ({size_kb:.1f} KB)")
    return output_path

if __name__ == "__main__":
    create_deck()
