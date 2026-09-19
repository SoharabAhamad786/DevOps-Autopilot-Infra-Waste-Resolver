document.addEventListener("DOMContentLoaded", () => {
    // Top Nav Tabs
    const navTabs = document.querySelectorAll(".nav-tab");
    const tabContents = document.querySelectorAll(".tab-content");

    // Overview Elements
    const totalSavingsEl = document.getElementById("total-savings-val");
    const wasteBeforeEl = document.getElementById("waste-before-text");
    const wasteAfterEl = document.getElementById("waste-after-text");
    const statApprovedEl = document.getElementById("stat-approved");
    const statPendingEl = document.getElementById("stat-pending");
    const statRejectedEl = document.getElementById("stat-rejected");
    const totalActionsEl = document.getElementById("total-actions-val");

    const scopeSelect = document.getElementById("scope-select");
    const btnDryRun = document.getElementById("btn-dry-run");
    const btnLiveRun = document.getElementById("btn-live-run");
    const btnClearLogs = document.getElementById("btn-clear-logs");

    const agentStateLabel = document.getElementById("agent-state-label");
    const agentStateSub = document.getElementById("agent-state-sub");
    const terminalBody = document.getElementById("terminal-body");

    const latestRunCard = document.getElementById("latest-run-card");
    const runModeBadge = document.getElementById("run-mode-badge");
    const runTitleText = document.getElementById("run-title-text");
    const runTimeText = document.getElementById("run-time-text");
    const latestRunSummaryText = document.getElementById("latest-run-summary-text");

    // Waste Map Elements
    const wasteMapCards = document.getElementById("waste-map-cards");
    const wasteMapTbody = document.getElementById("waste-map-tbody");
    const btnRefreshMap = document.getElementById("btn-refresh-map");

    // Findings & What-If Elements
    const findingsTbody = document.getElementById("findings-tbody");
    const btnRefreshFindings = document.getElementById("btn-refresh-findings");
    const accordionToggle = document.getElementById("accordion-toggle");
    const accordionBody = document.getElementById("accordion-body");
    const detailedReasoningList = document.getElementById("detailed-reasoning-list");

    // Audit Trail Elements
    const auditTbody = document.getElementById("audit-tbody");

    let currentRunId = null;

    // Currency Formatter
    const formatINR = (val) => {
        return new Intl.NumberFormat("en-IN", {
            style: "currency",
            currency: "INR",
            maximumFractionDigits: 2
        }).format(val || 0);
    };

    // Tab Switching Logic
    navTabs.forEach(tab => {
        tab.addEventListener("click", () => {
            const target = tab.getAttribute("data-tab");
            navTabs.forEach(t => t.classList.remove("active"));
            tabContents.forEach(c => {
                c.classList.remove("active");
                c.style.display = "none";
            });
            tab.classList.add("active");
            const targetEl = document.getElementById(target);
            if (targetEl) {
                targetEl.classList.add("active");
                targetEl.style.display = "block";
            }
            if (target === "tab-waste-map") fetchWasteMap();
            if (target === "tab-audit") fetchAuditTrail();
            if (target === "tab-3d-cluster" && window.cluster3D) {
                window.cluster3D.onTabOpen();
            }
        });
    });

    // Append Log to Terminal
    const addLog = (text, type = "normal") => {
        const line = document.createElement("div");
        line.className = `log-line ${type}`;
        const timestamp = new Date().toLocaleTimeString();
        line.textContent = `[${timestamp}] ${text}`;
        terminalBody.appendChild(line);
        terminalBody.scrollTop = terminalBody.scrollHeight;
    };

    // Fetch Overview & Savings
    const fetchSavings = async () => {
        try {
            const res = await fetch("/api/savings");
            if (!res.ok) return;
            const data = await res.json();
            totalSavingsEl.textContent = formatINR(data.total_estimated_savings_inr_month);
            totalActionsEl.textContent = data.total_actions_count || 0;

            if (data.latest_run) {
                currentRunId = data.latest_run.id;
                renderLatestRun(data.latest_run);
                fetchRunFindings(data.latest_run.id);
            }
        } catch (err) {
            console.error("Error fetching savings:", err);
        }
    };

    // Render Latest Run Banner
    const renderLatestRun = (run) => {
        latestRunCard.style.display = "block";
        runModeBadge.textContent = run.mode.toUpperCase();
        runModeBadge.className = `run-badge ${run.mode === 'live' ? 'live' : ''}`;
        runTitleText.textContent = `Run #${run.id} Multi-Agent Optimization Summary`;
        runTimeText.textContent = run.triggered_at ? new Date(run.triggered_at).toLocaleString() : "Recently";
        latestRunSummaryText.textContent = run.summary_text || `Evaluated ${run.findings_count} workloads. Saved ${formatINR(run.savings_inr_month)}/mo.`;

        wasteBeforeEl.textContent = `${run.before_waste_pct || 0.0}%`;
        wasteAfterEl.textContent = `${run.after_waste_pct || 0.0}%`;

        statApprovedEl.textContent = `${run.actions_approved || 0} Approved`;
        statPendingEl.textContent = `${(run.findings_count - run.actions_approved - run.actions_rejected) || 0} Pending`;
        statRejectedEl.textContent = `${run.actions_rejected || 0} Rejected`;
    };

    // Fetch Findings & What-If Details
    const fetchRunFindings = async (runId) => {
        try {
            const res = await fetch(`/api/runs/${runId}`);
            if (!res.ok) return;
            const data = await res.json();
            renderFindingsTable(data.findings || []);
            renderDetailedReasoning(data.findings || []);
        } catch (err) {
            console.error("Error fetching run details:", err);
        }
    };

    // Render Findings Table
    const renderFindingsTable = (findings) => {
        if (!findings || findings.length === 0) {
            findingsTbody.innerHTML = `<tr><td colspan="9" class="text-center py-4 text-muted">No findings recorded in this run.</td></tr>`;
            return;
        }

        findingsTbody.innerHTML = findings.map(f => {
            const issueClass = f.issue_type === "idle" ? "badge-idle" : "badge-overprov";
            const typeClass = f.resource_type === "pod" ? "badge-pod" : "badge-instance";
            const action = f.proposed_action || {};

            let actionDesc = "Analyze";
            if (f.resource_type === "pod") {
                actionDesc = `Scale: ${action.current_replicas || '?'} ➔ ${action.target_replicas || '1'} reps`;
            } else if (f.resource_type === "instance") {
                actionDesc = `Stop Instance (${action.instance_type || 'EC2'})`;
            }

            // Risk badge
            const riskClass = f.risk_score === "high" ? "badge-risk-high" : (f.risk_score === "medium" ? "badge-risk-med" : "badge-risk-low");

            // Safety Decision Badge
            let safetyBadge = `<span class="badge badge-success">✓ Auto-Approved</span>`;
            if (f.safety_decision === "reject") {
                safetyBadge = `<span class="badge badge-idle" title="${escapeHtml(f.safety_reason)}">🛡️ Rejected</span>`;
            } else if (f.safety_decision === "require_approval") {
                safetyBadge = `<span class="badge badge-amber" title="${escapeHtml(f.safety_reason)}">⏳ Needs Approval</span>`;
            }

            // Status & Approval Action
            let statusCol = `<span class="badge badge-success">✓ Applied</span>`;
            if (!f.executed) {
                if (f.safety_decision === "require_approval") {
                    statusCol = `<button class="btn-approve" onclick="window.approveFinding(${f.run_id}, ${f.id})">Approve & Run</button>`;
                } else {
                    statusCol = `<span class="badge badge-simulated">Simulated</span>`;
                }
            }

            return `
                <tr>
                    <td><code>${escapeHtml(f.resource_id)}</code></td>
                    <td><span class="badge ${typeClass}">${escapeHtml(f.resource_type.toUpperCase())}</span> <span class="text-muted">(${escapeHtml(action.namespace || 'dev')})</span></td>
                    <td><strong>${f.utilization_pct}%</strong></td>
                    <td>${escapeHtml(actionDesc)}</td>
                    <td><strong class="text-accent">${f.predicted_util_pct}%</strong></td>
                    <td><span class="badge ${riskClass}" title="${escapeHtml(f.risk_reason || '')}">${(f.risk_score || 'low').toUpperCase()}</span></td>
                    <td>${safetyBadge}</td>
                    <td><strong class="text-success">${formatINR(f.estimated_savings_inr_month)}</strong></td>
                    <td>${statusCol}</td>
                </tr>
            `;
        }).join("");
    };

    // Render Natural-Language Agent Reasoning Steps
    const renderDetailedReasoning = (findings) => {
        detailedReasoningList.innerHTML = findings.map(f => {
            const action = f.proposed_action || {};
            return `
                <div style="margin-bottom: 12px; padding: 10px; background: rgba(255,255,255,0.03); border-radius: 8px;">
                    <div><strong>Workload:</strong> <code>${escapeHtml(f.resource_id)}</code> (${escapeHtml(f.resource_type)})</div>
                    <div><strong>Optimizer Reasoning:</strong> CPU util is ${f.utilization_pct}%. Propose ${escapeHtml(action.action || 'scale')}. What-If predicted utilization is ${f.predicted_util_pct}% (${escapeHtml(f.risk_reason || 'Low risk')}).</div>
                    <div><strong>Safety Agent Governance:</strong> Decision: <code>${f.safety_decision}</code>. Reason: ${escapeHtml(f.safety_reason || 'Approved')}</div>
                </div>
            `;
        }).join("");
    };

    // Waste Map Fetcher
    const fetchWasteMap = async () => {
        try {
            const res = await fetch("/api/waste-map");
            if (!res.ok) return;
            const data = await res.json();
            renderWasteMap(data);
        } catch (err) {
            console.error("Error fetching waste map:", err);
        }
    };

    // Render Waste Map
    const renderWasteMap = (mapData) => {
        if (!mapData || mapData.length === 0) {
            wasteMapCards.innerHTML = `<div class="text-muted py-4">No waste map data available. Run optimization first.</div>`;
            wasteMapTbody.innerHTML = `<tr><td colspan="5" class="text-center py-4 text-muted">No data.</td></tr>`;
            return;
        }

        // Cards
        wasteMapCards.innerHTML = mapData.map(ns => {
            const meterLevel = ns.waste_score > 70 ? "high" : (ns.waste_score > 35 ? "med" : "low");
            return `
                <div class="waste-card">
                    <div class="waste-card-title">
                        <span>Namespace: <strong>${escapeHtml(ns.namespace)}</strong></span>
                        <span class="badge ${meterLevel === 'high' ? 'badge-idle' : 'badge-amber'}">${ns.waste_score}% Waste</span>
                    </div>
                    <div class="meter-bg">
                        <div class="meter-fill ${meterLevel}" style="width: ${ns.waste_score}%;"></div>
                    </div>
                    <div style="font-size: 12px; color: var(--text-secondary); margin-top: 8px;">
                        <div>Workloads: <strong>${ns.resource_count}</strong></div>
                        <div>Est. Monthly Waste Leakage: <strong class="text-accent">${formatINR(ns.estimated_waste_inr_month)}</strong></div>
                    </div>
                </div>
            `;
        }).join("");

        // Table
        wasteMapTbody.innerHTML = mapData.map(ns => {
            const meterLevel = ns.waste_score > 70 ? "high" : (ns.waste_score > 35 ? "med" : "low");
            return `
                <tr>
                    <td><code>${escapeHtml(ns.namespace)}</code></td>
                    <td>${ns.resource_count} services</td>
                    <td><strong>${ns.waste_score}%</strong></td>
                    <td><strong class="text-success">${formatINR(ns.estimated_waste_inr_month)}</strong></td>
                    <td><span class="badge ${meterLevel === 'high' ? 'badge-idle' : (meterLevel === 'med' ? 'badge-amber' : 'badge-success')}">${meterLevel.toUpperCase()}</span></td>
                </tr>
            `;
        }).join("");
    };

    // Fetch Audit Trail
    const fetchAuditTrail = async () => {
        try {
            const res = await fetch("/api/runs?limit=10");
            if (!res.ok) return;
            const runs = await res.json();
            renderAuditTrail(runs);
        } catch (err) {
            console.error("Error fetching audit runs:", err);
        }
    };

    // Render Audit Trail
    const renderAuditTrail = async (runs) => {
        let allAuditRows = [];
        for (let r of runs.slice(0, 5)) {
            try {
                const detailRes = await fetch(`/api/runs/${r.id}`);
                const detail = await detailRes.json();
                for (let f of (detail.findings || [])) {
                    allAuditRows.push({
                        timestamp: f.executed_at || r.triggered_at,
                        run_id: r.id,
                        resource_id: f.resource_id,
                        approved_by: f.approved_by || (f.safety_decision === 'auto_approve' ? 'System Policy' : 'Operator'),
                        safety_reason: f.safety_reason || 'Auto-verified',
                        action: f.proposed_action || {},
                        mode: r.mode,
                        executed: f.executed
                    });
                }
            } catch (e) {
                console.error(e);
            }
        }

        if (allAuditRows.length === 0) {
            auditTbody.innerHTML = `<tr><td colspan="8" class="text-center py-4 text-muted">No audit entries found.</td></tr>`;
            return;
        }

        auditTbody.innerHTML = allAuditRows.map(row => {
            let beforeAfter = row.action.action === 'scale_down' ? 
                `${row.action.current_replicas || '?'} ➔ ${row.action.target_replicas || '1'} reps` : 
                (row.action.action === 'stop' ? 'Running ➔ Stopped' : 'Configured');

            return `
                <tr>
                    <td style="font-size: 11px;">${new Date(row.timestamp).toLocaleTimeString()}</td>
                    <td>#${row.run_id}</td>
                    <td><code>${escapeHtml(row.resource_id)}</code></td>
                    <td><span class="badge ${row.approved_by === 'operator' ? 'badge-amber' : 'badge-pod'}">${escapeHtml(row.approved_by)}</span></td>
                    <td style="font-size: 12px; color: var(--text-secondary);">${escapeHtml(row.safety_reason)}</td>
                    <td><strong>${escapeHtml(beforeAfter)}</strong></td>
                    <td><code>${row.mode.toUpperCase()}</code></td>
                    <td>${row.executed ? '<span class="badge badge-success">✓ Executed</span>' : '<span class="badge badge-simulated">Simulated</span>'}</td>
                </tr>
            `;
        }).join("");
    };

    // Global Approval Handler
    window.approveFinding = async (runId, findingId) => {
        try {
            addLog(`Operator approved finding #${findingId} for run #${runId}. Dispatching live execution...`, "agent");
            const res = await fetch("/api/approve", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ run_id: runId, finding_ids: [findingId] })
            });
            const data = await res.json();
            if (res.ok) {
                addLog(`✓ Successfully executed approved action on ${data.executed_resources.join(", ")}.`, "success");
                fetchSavings();
                fetchRunFindings(runId);
            } else {
                addLog(`Failed to approve: ${data.error}`, "warn");
            }
        } catch (e) {
            addLog(`Approval error: ${e.message}`, "warn");
        }
    };

    // Trigger Multi-Agent Optimization
    const runOptimization = async (mode) => {
        const scope = scopeSelect.value;
        setAgentRunning(true, mode);
        addLog(`=== Launching Multi-Agent Swarm [Mode: ${mode.toUpperCase()}, Scope: ${scope}] ===`, "agent");

        try {
            const res = await fetch("/api/optimize", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ mode, scope })
            });

            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.error || "Optimization run failed");
            }

            const data = await res.json();
            addLog(`Multi-Agent Run #${data.run_id} concluded in ${data.elapsed_seconds}s.`, "success");

            // Stream Agent Reasoning Trail
            if (data.reasoning_trail && data.reasoning_trail.length > 0) {
                data.reasoning_trail.forEach(step => {
                    let type = "tool";
                    if (step.agent.includes("Observer")) type = "agent";
                    if (step.agent.includes("Safety")) type = "guard";
                    if (step.agent.includes("Executor")) type = "success";
                    addLog(`[${step.agent}] ${step.message}`, type);
                });
            }

            addLog(`Cluster waste reduced from ${data.before_waste_pct}% ➔ ${data.after_waste_pct}%.`, "agent");
            addLog(`Total recurring monthly savings: ${formatINR(data.savings_inr_month)} / month.`, "success");

            await fetchSavings();
            if (data.run_id) {
                await fetchRunFindings(data.run_id);
            }
            fetchWasteMap();

            // Trigger 3D Cluster Optimization Animation simultaneously!
            if (window.cluster3D) {
                window.cluster3D.animateOptimization();
            }
        } catch (err) {
            addLog(`Execution error: ${err.message}`, "warn");
            console.error(err);
        } finally {
            setAgentRunning(false);
        }
    };

    const setAgentRunning = (isRunning, mode = "dry_run") => {
        btnDryRun.disabled = isRunning;
        btnLiveRun.disabled = isRunning;
        scopeSelect.disabled = isRunning;

        if (isRunning) {
            agentStateLabel.textContent = `SWARM ACTIVE (${mode.toUpperCase()})`;
            agentStateLabel.style.color = mode === "live" ? "var(--accent-rose)" : "var(--accent-blue)";
            agentStateSub.textContent = "Observer ➔ Optimizer ➔ Safety ➔ Executor handoff...";
        } else {
            agentStateLabel.textContent = "AGENTS IDLE & READY";
            agentStateLabel.style.color = "var(--accent-green)";
            agentStateSub.textContent = "Observer standing by for cluster trigger...";
        }
    };

    // Event Listeners
    btnDryRun.addEventListener("click", () => runOptimization("dry_run"));
    btnLiveRun.addEventListener("click", () => {
        if (confirm("Execute LIVE modifications? Safety Agent policies will protect production workloads.")) {
            runOptimization("live");
        }
    });

    btnClearLogs.addEventListener("click", () => {
        terminalBody.innerHTML = `<div class="log-line text-muted">[SYSTEM] Console feed cleared.</div>`;
    });

    if (btnRefreshMap) btnRefreshMap.addEventListener("click", fetchWasteMap);
    if (btnRefreshFindings) btnRefreshFindings.addEventListener("click", () => {
        if (currentRunId) fetchRunFindings(currentRunId);
    });

    if (accordionToggle) {
        accordionToggle.addEventListener("click", () => {
            const isHidden = accordionBody.style.display === "none";
            accordionBody.style.display = isHidden ? "block" : "none";
            accordionToggle.querySelector(".chevron").textContent = isHidden ? "▲" : "▼";
        });
    }

    const escapeHtml = (unsafe) => {
        return (unsafe || "")
            .toString()
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    };

    // =========================================================================
    // 🌐 3D CYBER CLUSTER VISUALIZER ENGINE (Three.js + OrbitControls + Tween)
    // =========================================================================
    class Cluster3DVisualizer {
        constructor() {
            this.container = document.getElementById("three-viewport");
            this.hud = document.getElementById("node-inspector-hud");
            this.initialized = false;
            this.workloadMeshes = [];
            this.platforms = [];
            this.currentLayout = "namespaces"; // "namespaces" or "grid"
            this.hoveredMesh = null;
            this.selectedMesh = null;

            // Platform coordinates for namespaces
            this.platformCoords = {
                dev: { x: -22, z: -16, color: 0x10b981, label: "NAMESPACE: DEV" },
                staging: { x: 22, z: -16, color: 0xf59e0b, label: "NAMESPACE: STAGING" },
                demo: { x: -22, z: 20, color: 0x8b5cf6, label: "NAMESPACE: DEMO" },
                prod: { x: 22, z: 20, color: 0x06b6d4, label: "NAMESPACE: PROD (GUARDED)" },
                "ap-south-1a": { x: -38, z: 0, color: 0x38bdf8, label: "AWS EC2 (SOUTH-1A)" },
                "ap-south-1b": { x: 38, z: 0, color: 0x38bdf8, label: "AWS EC2 (SOUTH-1B)" }
            };
        }

        init() {
            if (this.initialized || !this.container || typeof THREE === "undefined") return;

            const width = this.container.clientWidth || 1000;
            const height = this.container.clientHeight || 620;

            // 1. Scene & Camera
            this.scene = new THREE.Scene();
            this.scene.fog = new THREE.FogExp2(0x05070e, 0.007);

            this.camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
            this.camera.position.set(0, 42, 68);

            // 2. WebGL Renderer
            this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: "high-performance" });
            this.renderer.setSize(width, height);
            this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
            this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
            this.renderer.toneMappingExposure = 1.2;
            this.container.appendChild(this.renderer.domElement);

            // 3. OrbitControls
            if (typeof THREE.OrbitControls !== "undefined") {
                this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
                this.controls.enableDamping = true;
                this.controls.dampingFactor = 0.05;
                this.controls.maxPolarAngle = Math.PI / 2 - 0.03;
                this.controls.minDistance = 15;
                this.controls.maxDistance = 160;
                this.controls.autoRotate = true;
                this.controls.autoRotateSpeed = 0.6;
            }

            // 4. Lights
            const ambient = new THREE.AmbientLight(0x1e293b, 1.8);
            this.scene.add(ambient);

            const dirLight1 = new THREE.DirectionalLight(0x38bdf8, 1.4);
            dirLight1.position.set(30, 50, 40);
            this.scene.add(dirLight1);

            const dirLight2 = new THREE.DirectionalLight(0x818cf8, 0.8);
            dirLight2.position.set(-30, 40, -40);
            this.scene.add(dirLight2);

            // 5. Ambient Cyber Elements
            this.createCyberStarfield();
            this.createGridFloor();
            this.createNamespacePlatforms();

            // 6. Raycaster for Interactions
            this.raycaster = new THREE.Raycaster();
            this.mouse = new THREE.Vector2();

            this.bindEvents();
            this.loadWorkloadNodes();

            // 7. Render Loop
            this.initialized = true;
            this.animate = this.animate.bind(this);
            requestAnimationFrame(this.animate);
        }

        createCyberStarfield() {
            const particleCount = 1000;
            const geometry = new THREE.BufferGeometry();
            const positions = new Float32Array(particleCount * 3);

            for (let i = 0; i < particleCount * 3; i += 3) {
                positions[i] = (Math.random() - 0.5) * 300;
                positions[i + 1] = Math.random() * 80;
                positions[i + 2] = (Math.random() - 0.5) * 300;
            }

            geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
            const material = new THREE.PointsMaterial({
                color: 0x38bdf8,
                size: 0.9,
                transparent: true,
                opacity: 0.65,
                blending: THREE.AdditiveBlending
            });

            this.starfield = new THREE.Points(geometry, material);
            this.scene.add(this.starfield);
        }

        createGridFloor() {
            const grid = new THREE.GridHelper(110, 55, 0x0ea5e9, 0x1e293b);
            grid.position.y = -0.05;
            grid.material.opacity = 0.35;
            grid.material.transparent = true;
            this.scene.add(grid);
        }

        createNamespacePlatforms() {
            Object.entries(this.platformCoords).forEach(([ns, cfg]) => {
                const group = new THREE.Group();
                group.position.set(cfg.x, 0, cfg.z);

                // Platform Disc
                const discGeo = new THREE.CylinderGeometry(9.5, 9.5, 0.4, 32);
                const discMat = new THREE.MeshStandardMaterial({
                    color: 0x0a101d,
                    roughness: 0.4,
                    metalness: 0.8
                });
                const disc = new THREE.Mesh(discGeo, discMat);
                disc.position.y = 0.2;
                group.add(disc);

                // Glowing Wireframe Rim
                const ringGeo = new THREE.RingGeometry(8.8, 9.5, 32);
                const ringMat = new THREE.MeshBasicMaterial({
                    color: cfg.color,
                    side: THREE.DoubleSide,
                    transparent: true,
                    opacity: 0.85
                });
                const ring = new THREE.Mesh(ringGeo, ringMat);
                ring.rotation.x = -Math.PI / 2;
                ring.position.y = 0.42;
                group.add(ring);

                // 3D Canvas Text Label Marker
                const labelSprite = this.createTextSprite(cfg.label, cfg.color);
                labelSprite.position.set(0, 2.8, -10.5);
                group.add(labelSprite);

                this.scene.add(group);
                this.platforms.push({ group, ns, cfg });
            });
        }

        createTextSprite(message, colorHex) {
            const canvas = document.createElement("canvas");
            canvas.width = 512;
            canvas.height = 128;
            const ctx = canvas.getContext("2d");
            ctx.fillStyle = "rgba(10, 15, 28, 0.85)";
            ctx.roundRect(10, 10, 492, 108, 18);
            ctx.fill();
            ctx.strokeStyle = `#${colorHex.toString(16).padStart(6, "0")}`;
            ctx.lineWidth = 4;
            ctx.stroke();

            ctx.fillStyle = "#ffffff";
            ctx.font = "bold 32px 'JetBrains Mono', monospace";
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            ctx.fillText(message, 256, 64);

            const texture = new THREE.CanvasTexture(canvas);
            const spriteMat = new THREE.SpriteMaterial({ map: texture, transparent: true });
            const sprite = new THREE.Sprite(spriteMat);
            sprite.scale.set(11, 2.8, 1);
            return sprite;
        }

        async loadWorkloadNodes() {
            let data = [];
            try {
                const res = await fetch("/api/metrics");
                if (res.ok) data = await res.json();
            } catch (e) {
                console.error("3D loader error:", e);
            }

            if (!data || data.length === 0) return;

            // Clear previous meshes
            this.workloadMeshes.forEach(m => this.scene.remove(m));
            this.workloadMeshes = [];

            // Group by namespace
            const nsGroups = {};
            data.forEach(item => {
                const ns = item.namespace || "dev";
                if (!nsGroups[ns]) nsGroups[ns] = [];
                nsGroups[ns].push(item);
            });

            let globalIdx = 0;
            Object.entries(nsGroups).forEach(([ns, items]) => {
                const pCfg = this.platformCoords[ns] || { x: 0, z: 0, color: 0x38bdf8 };
                const count = items.length;

                items.forEach((item, idx) => {
                    const angle = (idx / count) * Math.PI * 2;
                    const radius = count > 1 ? 5.2 : 0;
                    const posX = pCfg.x + Math.cos(angle) * radius;
                    const posZ = pCfg.z + Math.sin(angle) * radius;

                    // Grid layout alternate position
                    const gridCol = (globalIdx % 5) - 2;
                    const gridRow = Math.floor(globalIdx / 5) - 1;
                    const gridX = gridCol * 15;
                    const gridZ = gridRow * 15;
                    globalIdx++;

                    const mesh = this.createWorkloadMesh(item, { x: posX, z: posZ }, { x: gridX, z: gridZ });
                    this.scene.add(mesh);
                    this.workloadMeshes.push(mesh);
                });
            });
        }

        createWorkloadMesh(item, nsPos, gridPos) {
            const group = new THREE.Group();
            const cpuReq = item.current_cpu_request || 1.0;
            const isInstance = item.resource_type === "instance";
            const height = Math.min(14, Math.max(3.2, cpuReq * 2.2));
            const width = isInstance ? 3.4 : 2.4;

            // Color coding by status/waste
            let color = 0x10b981; // green
            let isProd = (item.namespace || "").toLowerCase() === "prod";
            let isIdle = (item.avg_cpu_usage / cpuReq) < 0.05;

            if (isProd) color = 0x06b6d4; // cyan
            else if (isIdle) color = 0xef4444; // crimson red
            else if ((item.avg_cpu_usage / cpuReq) < 0.3) color = 0xf59e0b; // amber

            // Main Server Blade Geometry
            const geo = new THREE.BoxGeometry(width, height, width);
            const mat = new THREE.MeshStandardMaterial({
                color: color,
                emissive: color,
                emissiveIntensity: 0.35,
                roughness: 0.25,
                metalness: 0.85,
                transparent: true,
                opacity: 0.92
            });

            const mainMesh = new THREE.Mesh(geo, mat);
            mainMesh.position.y = height / 2 + 0.4;
            group.add(mainMesh);

            // Glowing Wireframe Edges
            const edgeGeo = new THREE.EdgesGeometry(geo);
            const edgeMat = new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.65 });
            const edges = new THREE.LineSegments(edgeGeo, edgeMat);
            mainMesh.add(edges);

            // Top Status LED Sphere
            const ledGeo = new THREE.SphereGeometry(0.35, 16, 16);
            const ledMat = new THREE.MeshBasicMaterial({ color: color });
            const led = new THREE.Mesh(ledGeo, ledMat);
            led.position.y = height + 0.6;
            group.add(led);

            // Forcefield Shield for Production Workloads
            if (isProd) {
                const shieldGeo = new THREE.SphereGeometry(width * 1.5, 16, 16);
                const shieldMat = new THREE.MeshBasicMaterial({ color: 0x06b6d4, wireframe: true, transparent: true, opacity: 0.3 });
                const shield = new THREE.Mesh(shieldGeo, shieldMat);
                shield.position.y = height / 2 + 0.4;
                group.add(shield);
            }

            // Set initial namespace layout position
            group.position.set(nsPos.x, 0, nsPos.z);

            // Metadata for raycasting and animation
            group.userData = {
                id: item.resource_id,
                name: item.parent_workload || item.resource_id,
                type: item.resource_type.toUpperCase(),
                namespace: item.namespace,
                cpu_util: `${((item.avg_cpu_usage / cpuReq) * 100).toFixed(1)}%`,
                waste_score: `${(100 - (item.avg_cpu_usage / cpuReq) * 100).toFixed(1)}%`,
                cost: `₹${(item.cost_per_hour * 720).toFixed(0)}/mo`,
                isIdle: isIdle,
                color: color,
                initialHeight: height,
                targetHeight: Math.max(2.2, height * 0.55),
                nsPos: nsPos,
                gridPos: gridPos,
                mainMesh: mainMesh,
                led: led,
                mat: mat
            };

            return group;
        }

        bindEvents() {
            const el = this.renderer.domElement;

            el.addEventListener("pointermove", (e) => {
                const rect = el.getBoundingClientRect();
                this.mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
                this.mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
                this.checkIntersection();
            });

            el.addEventListener("click", () => {
                if (this.hoveredMesh) {
                    this.focusNode(this.hoveredMesh);
                }
            });

            // UI Control Buttons
            const btnLayout = document.getElementById("btn-3d-layout");
            if (btnLayout) {
                btnLayout.addEventListener("click", () => this.toggleLayout());
            }

            const btnRotate = document.getElementById("btn-3d-rotate");
            if (btnRotate) {
                btnRotate.addEventListener("click", () => {
                    if (this.controls) {
                        this.controls.autoRotate = !this.controls.autoRotate;
                        btnRotate.textContent = `🔄 Auto-Rotate: ${this.controls.autoRotate ? 'ON' : 'OFF'}`;
                    }
                });
            }

            const btnReset = document.getElementById("btn-3d-reset");
            if (btnReset) {
                btnReset.addEventListener("click", () => {
                    if (typeof TWEEN !== "undefined") {
                        new TWEEN.Tween(this.camera.position)
                            .to({ x: 0, y: 42, z: 68 }, 1000)
                            .easing(TWEEN.Easing.Cubic.Out)
                            .start();
                    } else {
                        this.camera.position.set(0, 42, 68);
                    }
                });
            }

            const btnAnimate = document.getElementById("btn-3d-animate");
            if (btnAnimate) {
                btnAnimate.addEventListener("click", () => this.animateOptimization());
            }

            const btnCloseHud = document.getElementById("btn-hud-close");
            if (btnCloseHud) {
                btnCloseHud.addEventListener("click", () => {
                    if (this.hud) this.hud.style.display = "none";
                });
            }

            window.addEventListener("resize", () => this.onResize());
        }

        checkIntersection() {
            if (!this.raycaster || !this.camera) return;
            this.raycaster.setFromCamera(this.mouse, this.camera);

            const collidables = this.workloadMeshes.map(g => g.userData.mainMesh);
            const intersects = this.raycaster.intersectObjects(collidables);

            if (intersects.length > 0) {
                const hitMesh = intersects[0].object.parent; // parent group
                if (this.hoveredMesh !== hitMesh) {
                    this.unhover();
                    this.hoveredMesh = hitMesh;
                    this.onHover(hitMesh);
                }
            } else {
                if (this.hoveredMesh && !this.selectedMesh) {
                    this.unhover();
                }
            }
        }

        onHover(group) {
            const data = group.userData;
            // Levitate and glow
            if (typeof TWEEN !== "undefined") {
                new TWEEN.Tween(group.position).to({ y: 1.2 }, 200).start();
            } else {
                group.position.y = 1.2;
            }
            data.mat.emissiveIntensity = 0.9;

            // Populate HUD Tooltip
            if (this.hud) {
                this.hud.style.display = "block";
                document.getElementById("hud-node-type").textContent = data.type;
                document.getElementById("hud-node-name").textContent = data.name;
                document.getElementById("hud-node-ns").textContent = data.namespace;
                document.getElementById("hud-node-cpu").textContent = data.cpu_util;
                document.getElementById("hud-node-waste").textContent = data.waste_score;
                document.getElementById("hud-node-cost").textContent = data.cost;
                document.getElementById("hud-node-whatif").textContent = data.isIdle ? "4.0% (LOW RISK)" : "Safe Headroom (LOW)";
                document.getElementById("hud-action-text").textContent = data.isIdle ? "Action: Scale 50% Replicas" : "Status: Monitored";
                document.getElementById("hud-savings-text").textContent = data.isIdle ? "Unlocks ~₹1,300/mo" : "No Action Needed";
            }
        }

        unhover() {
            if (!this.hoveredMesh) return;
            const group = this.hoveredMesh;
            const data = group.userData;
            if (typeof TWEEN !== "undefined") {
                new TWEEN.Tween(group.position).to({ y: 0 }, 200).start();
            } else {
                group.position.y = 0;
            }
            data.mat.emissiveIntensity = 0.35;
            this.hoveredMesh = null;
        }

        focusNode(group) {
            this.selectedMesh = group;
            if (typeof TWEEN !== "undefined") {
                const targetPos = {
                    x: group.position.x + 12,
                    y: group.position.y + 10,
                    z: group.position.z + 16
                };
                new TWEEN.Tween(this.camera.position)
                    .to(targetPos, 900)
                    .easing(TWEEN.Easing.Cubic.Out)
                    .start();
                if (this.controls) {
                    new TWEEN.Tween(this.controls.target)
                        .to({ x: group.position.x, y: group.position.y + 2, z: group.position.z }, 900)
                        .start();
                }
            }
        }

        toggleLayout() {
            this.currentLayout = this.currentLayout === "namespaces" ? "grid" : "namespaces";
            const btn = document.getElementById("btn-3d-layout");
            if (btn) btn.textContent = `🔀 Layout: ${this.currentLayout === 'namespaces' ? 'Namespaces' : 'Matrix Grid'}`;

            this.workloadMeshes.forEach(mesh => {
                const target = this.currentLayout === "namespaces" ? mesh.userData.nsPos : mesh.userData.gridPos;
                if (typeof TWEEN !== "undefined") {
                    new TWEEN.Tween(mesh.position)
                        .to({ x: target.x, z: target.z }, 900)
                        .easing(TWEEN.Easing.Quadratic.Out)
                        .start();
                } else {
                    mesh.position.set(target.x, 0, target.z);
                }
            });
        }

        animateOptimization() {
            // Animate each idle or oversized node: shrink height & turn neon emerald green
            this.workloadMeshes.forEach(mesh => {
                const data = mesh.userData;
                if (data.isIdle && (data.namespace || "").toLowerCase() !== "prod") {
                    const targetScaleY = data.targetHeight / data.initialHeight;

                    if (typeof TWEEN !== "undefined") {
                        // Shrink height
                        new TWEEN.Tween(data.mainMesh.scale)
                            .to({ y: targetScaleY }, 1200)
                            .easing(TWEEN.Easing.Back.Out)
                            .start();

                        // Color transform to emerald green
                        const startColor = new THREE.Color(data.color);
                        const endColor = new THREE.Color(0x10b981);
                        new TWEEN.Tween({ t: 0 })
                            .to({ t: 1 }, 1200)
                            .onUpdate((obj) => {
                                data.mat.color.lerpColors(startColor, endColor, obj.t);
                                data.mat.emissive.lerpColors(startColor, endColor, obj.t);
                                data.led.material.color.lerpColors(startColor, endColor, obj.t);
                            })
                            .start();
                    } else {
                        data.mainMesh.scale.y = targetScaleY;
                        data.mat.color.setHex(0x10b981);
                        data.mat.emissive.setHex(0x10b981);
                    }
                }
            });

            // Expand glowing shockwave on platforms
            this.platforms.forEach(p => {
                const waveGeo = new THREE.RingGeometry(0.5, 1.2, 32);
                const waveMat = new THREE.MeshBasicMaterial({ color: 0x38bdf8, side: THREE.DoubleSide, transparent: true, opacity: 0.9 });
                const wave = new THREE.Mesh(waveGeo, waveMat);
                wave.rotation.x = -Math.PI / 2;
                wave.position.y = 0.5;
                p.group.add(wave);

                if (typeof TWEEN !== "undefined") {
                    new TWEEN.Tween(wave.scale).to({ x: 9.5, y: 9.5 }, 1400).start();
                    new TWEEN.Tween(waveMat).to({ opacity: 0 }, 1400).onComplete(() => p.group.remove(wave)).start();
                }
            });
        }

        onTabOpen() {
            if (!this.initialized) {
                this.init();
            } else {
                setTimeout(() => this.onResize(), 60);
            }
        }

        onResize() {
            if (!this.container || !this.renderer || !this.camera) return;
            const width = this.container.clientWidth;
            const height = this.container.clientHeight;
            this.camera.aspect = width / height;
            this.camera.updateProjectionMatrix();
            this.renderer.setSize(width, height);
        }

        animate(time) {
            requestAnimationFrame(this.animate);
            if (typeof TWEEN !== "undefined") TWEEN.update();
            if (this.controls) this.controls.update();

            // Rotate cyber starfield slowly
            if (this.starfield) {
                this.starfield.rotation.y += 0.0003;
            }

            if (this.renderer && this.scene && this.camera) {
                this.renderer.render(this.scene, this.camera);
            }
        }
    }

    // Initialize 3D Engine instance
    window.cluster3D = new Cluster3DVisualizer();

    // Initial Load
    fetchSavings();
    fetchWasteMap();
    addLog("System connected to Flask Multi-Agent API. 3D Cyber Cluster ready.", "success");
});

