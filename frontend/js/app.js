// DealForge AI - Modern Frontend Application Controller
const API_BASE = '/api';

const state = {
    currentView: 'overview',
    activeWorkflowId: null,
    activeRequestId: null,
    pollInterval: null,
    dashboardData: null,
    quotes: [],
    evaluations: [],
    negotiations: [],
    approvals: [],
    orders: []
};

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
    setupNavigation();
    setupQuickPrompts();
    loadDashboardSummary();
    loadVendors();
    loadPendingApprovals();
    loadPurchaseOrders();
});

// View Navigation Router
function setupNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            const target = item.getAttribute('data-view');
            if (target) {
                switchView(target);
            }
        });
    });
}

function switchView(viewName) {
    state.currentView = viewName;
    
    // Update active nav
    document.querySelectorAll('.nav-item').forEach(el => {
        if (el.getAttribute('data-view') === viewName) {
            el.classList.add('active');
        } else {
            el.classList.remove('active');
        }
    });

    // Toggle view containers
    document.querySelectorAll('.view-section').forEach(sec => {
        if (sec.id === `view-${viewName}`) {
            sec.classList.add('active');
        } else {
            sec.classList.remove('active');
        }
    });

    // Update topbar title
    const titles = {
        'overview': 'Overview Dashboard',
        'new-request': 'New Purchase Request',
        'workflow': 'Live Multi-Agent Workflow',
        'vendors': 'Vendor Comparison Matrix',
        'negotiations': 'Negotiation Centre',
        'approvals': 'Human-in-the-Loop Approvals',
        'orders': 'Issued Purchase Orders',
        'audit': 'Enterprise Audit Trail'
    };
    document.getElementById('topbar-title').innerText = titles[viewName] || 'DealForge AI';

    // Refresh view specific data
    if (viewName === 'overview') loadDashboardSummary();
    if (viewName === 'vendors') loadVendors();
    if (viewName === 'approvals') loadPendingApprovals();
    if (viewName === 'orders') loadPurchaseOrders();
    if (viewName === 'negotiations' && state.activeRequestId) loadNegotiations(state.activeRequestId);
}

// Quick Sample Prompts
function setupQuickPrompts() {
    window.fillPrompt = function(type) {
        const textarea = document.getElementById('nl-request-input');
        if (type === 'standard-laptop') {
            textarea.value = "Purchase 50 laptops with at least 16 GB RAM and 512 GB SSD, a maximum budget of ₹35,00,000, delivery within 14 days, and a minimum two-year warranty.";
        } else if (type === 'budget-overrun') {
            textarea.value = "Purchase 60 enterprise laptops with 16 GB RAM and 512 GB SSD, a maximum budget of ₹30,00,000, delivery within 14 days, and a minimum two-year warranty.";
        } else if (type === 'server-cluster') {
            textarea.value = "Procure 4 rackmount PowerEdge servers with 128 GB RAM, a maximum budget of ₹20,00,000, delivery within 14 days, and 3-year warranty.";
        }
    };
}

// 1. Dashboard Summary
async function loadDashboardSummary() {
    try {
        const res = await fetch(`${API_BASE}/dashboard/summary`);
        if (!res.ok) return;
        const data = await res.json();
        state.dashboardData = data;

        document.getElementById('stat-total-requests').innerText = data.total_requests;
        document.getElementById('stat-active-workflows').innerText = data.active_workflows;
        document.getElementById('stat-pending-approvals').innerText = data.pending_approvals;
        document.getElementById('stat-issued-pos').innerText = data.issued_purchase_orders;
        document.getElementById('stat-approved-spend').innerText = `₹${Number(data.total_spend_approved).toLocaleString('en-IN', {minimumFractionDigits: 2})}`;
        document.getElementById('stat-estimated-savings').innerText = `₹${Number(data.estimated_savings).toLocaleString('en-IN', {minimumFractionDigits: 2})}`;
        document.getElementById('stat-vendor-rating').innerText = `${data.average_vendor_rating} / 5.0`;

        // Update badges
        const badge = document.getElementById('nav-pending-badge');
        if (badge) {
            badge.innerText = data.pending_approvals;
            badge.style.display = data.pending_approvals > 0 ? 'inline-block' : 'none';
        }

        renderRecentRequests(data.recent_requests || []);
    } catch (err) {
        console.error('Error fetching dashboard summary:', err);
    }
}

function renderRecentRequests(requests) {
    const container = document.getElementById('recent-requests-table-body');
    if (!container) return;

    if (requests.length === 0) {
        container.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted);">No procurement requests yet. Submit a new request to start.</td></tr>`;
        return;
    }

    container.innerHTML = requests.map(r => `
        <tr>
            <td style="font-family: var(--font-mono); font-size: 11px;">${r.request_id.slice(0, 8)}...</td>
            <td><strong>${r.product_requirements?.category || 'General'}</strong> (${r.quantity} units)</td>
            <td>${r.requester}</td>
            <td>₹${Number(r.budget_limit).toLocaleString('en-IN', {minimumFractionDigits: 2})}</td>
            <td><span class="status-pill ${getStatusPillClass(r.status)}">${r.status}</span></td>
            <td>
                <button class="btn-secondary" style="padding: 4px 10px; font-size: 11px;" onclick="trackWorkflowByRequest('${r.request_id}')">Track Workflow</button>
            </td>
        </tr>
    `).join('');
}

function getStatusPillClass(status) {
    switch (status) {
        case 'COMPLETED':
        case 'PO_CREATED':
        case 'APPROVED':
            return 'success';
        case 'RUNNING':
        case 'ANALYZING':
            return 'running';
        case 'PENDING_APPROVAL':
        case 'PAUSED':
            return 'warning';
        case 'FAILED':
        case 'REJECTED':
            return 'danger';
        default:
            return 'pending';
    }
}

// 2. Submit New Request & Initiate Workflow
async function submitPurchaseRequest(event) {
    event.preventDefault();
    const btn = document.getElementById('btn-submit-request');
    btn.disabled = true;
    btn.innerHTML = `<span class="status-dot"></span> Orchestrating Agents...`;

    const rawText = document.getElementById('nl-request-input').value;
    const qty = document.getElementById('override-qty').value;
    const budget = document.getElementById('override-budget').value;
    const deadline = document.getElementById('override-deadline').value;
    const warranty = document.getElementById('override-warranty').value;

    const payload = {
        requester: "Enterprise Procurement Officer",
        raw_request_text: rawText,
        quantity_override: qty ? parseInt(qty) : null,
        budget_override: budget ? parseFloat(budget) : null,
        deadline_override_days: deadline ? parseInt(deadline) : null,
        warranty_override_months: warranty ? parseInt(warranty) : null
    };

    try {
        // Step 1: Create request
        const createRes = await fetch(`${API_BASE}/requests`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (!createRes.ok) throw new Error('Failed to create purchase request');
        const reqData = await createRes.json();
        state.activeRequestId = reqData.request_id;

        // Step 2: Start workflow in synchronous or background mode
        const wfRes = await fetch(`${API_BASE}/workflows/${reqData.request_id}/start?sync=true`, {
            method: 'POST'
        });
        if (!wfRes.ok) throw new Error('Failed to start multi-agent workflow');
        const wfData = await wfRes.json();
        state.activeWorkflowId = wfData.workflow_id;

        // Switch immediately to Live Workflow Tracker
        switchView('workflow');
        startWorkflowPolling(wfData.workflow_id);

    } catch (err) {
        alert('Workflow Initialization Error: ' + err.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = `🚀 Launch Multi-Agent Workflow`;
    }
}

// 3. Live Workflow Stepper & Polling
function startWorkflowPolling(workflowId) {
    if (state.pollInterval) clearInterval(state.pollInterval);
    pollWorkflowStatus(workflowId);
    state.pollInterval = setInterval(() => pollWorkflowStatus(workflowId), 2000);
}

async function pollWorkflowStatus(workflowId) {
    try {
        const res = await fetch(`${API_BASE}/workflows/${workflowId}/status`);
        if (!res.ok) return;
        const data = await res.json();

        updateWorkflowUI(data);

        // If completed or paused, refresh other views
        if (data.status === 'COMPLETED' || data.status === 'PAUSED' || data.status === 'FAILED') {
            loadDashboardSummary();
            loadPendingApprovals();
            loadPurchaseOrders();
            if (data.request_id) {
                loadVendors(data.request_id);
                loadNegotiations(data.request_id);
            }
        }
    } catch (err) {
        console.error('Error polling workflow status:', err);
    }
}

function updateWorkflowUI(data) {
    document.getElementById('wf-display-id').innerText = data.workflow_id.slice(0, 12);
    document.getElementById('wf-display-status').innerHTML = `<span class="status-pill ${getStatusPillClass(data.status)}">${data.status}</span>`;
    document.getElementById('wf-display-step').innerText = data.current_step;

    // Highlight active agents
    const agents = [
        { id: 'agent-req', name: 'Requirement Analysis Agent' },
        { id: 'agent-vendor', name: 'Vendor Research Agent' },
        { id: 'agent-price', name: 'Price Analysis Agent' },
        { id: 'agent-comp', name: 'Compliance Agent' },
        { id: 'agent-eval', name: 'Deal Evaluation Agent' },
        { id: 'agent-budget', name: 'Budget Validation Agent' },
        { id: 'agent-neg', name: 'Negotiation Agent' },
        { id: 'agent-adk', name: 'Approval and Workflow Coordination Agent' }
    ];

    const logs = data.logs || [];
    agents.forEach(a => {
        const agentCard = document.getElementById(a.id);
        const agentLogs = logs.filter(l => l.agent_name.includes(a.name) || a.name.includes(l.agent_name));
        const pillEl = agentCard ? agentCard.querySelector('.status-pill') : null;
        if (agentCard && agentLogs.length > 0) {
            const latest = agentLogs[agentLogs.length - 1];
            agentCard.classList.remove('running', 'pending', 'paused', 'completed');
            if (latest.event_type.includes('START') || latest.status === 'PENDING') {
                agentCard.classList.add('running');
                if (pillEl) { pillEl.className = 'status-pill running'; pillEl.innerText = 'Running'; }
            } else if (latest.event_type.includes('PAUSED')) {
                agentCard.classList.add('paused');
                if (pillEl) { pillEl.className = 'status-pill warning'; pillEl.innerText = 'Paused'; }
            } else {
                agentCard.classList.add('completed');
                if (pillEl) { pillEl.className = 'status-pill success'; pillEl.innerText = 'Completed'; }
            }
            const outEl = agentCard.querySelector('.agent-output-preview');
            if (outEl) outEl.innerText = latest.output_summary || latest.input_summary || 'Task completed.';
        } else if (agentCard) {
            agentCard.classList.remove('running', 'paused', 'completed');
            agentCard.classList.add('pending');
            if (pillEl) { pillEl.className = 'status-pill pending'; pillEl.innerText = 'Pending'; }
        }
    });

    // Render terminal console logs
    renderAuditLogs(logs);

    // If waiting for approval, show banner
    const approvalBanner = document.getElementById('wf-approval-banner');
    if (approvalBanner) {
        if (data.current_step === 'WAITING_FOR_APPROVAL' || data.status === 'PAUSED') {
            approvalBanner.style.display = 'block';
            document.getElementById('wf-approval-reason').innerText = data.state_data?.approval_reason || 'Requires Manager Sign-off';
        } else {
            approvalBanner.style.display = 'none';
        }
    }
}

function renderAuditLogs(logs) {
    const term = document.getElementById('terminal-audit-stream');
    if (!term) return;

    if (!logs || logs.length === 0) {
        term.innerHTML = `<div class="terminal-line"><span class="terminal-msg">Waiting for agent orchestration events...</span></div>`;
        return;
    }

    term.innerHTML = logs.map(l => {
        const time = new Date(l.started_at).toLocaleTimeString();
        return `
            <div class="terminal-line">
                <span class="terminal-time">[${time}]</span>
                <span class="terminal-agent">[${l.agent_name}]</span>
                <span class="terminal-msg">${l.output_summary || l.input_summary || l.event_type}</span>
            </div>
        `;
    }).join('');
    term.scrollTop = term.scrollHeight;
}

async function trackWorkflowByRequest(requestId) {
    state.activeRequestId = requestId;
    try {
        const wfRes = await fetch(`${API_BASE}/workflows/by-request/${requestId}/status`);
        if (wfRes.ok) {
            const data = await wfRes.json();
            state.activeWorkflowId = data.workflow_id;
            updateWorkflowUI(data);
        }
        // Switch view
        switchView('workflow');
        loadVendors(requestId);
        loadNegotiations(requestId);
    } catch (e) {
        console.error('Error tracking workflow by request:', e);
    }
}

// 4. Vendor Comparison Matrix
async function loadVendors(requestId = null) {
    const reqId = requestId || state.activeRequestId;
    const tbody = document.getElementById('vendors-comparison-table-body');
    if (!tbody) return;

    tbody.innerHTML = `<tr><td colspan="10" style="text-align: center; color: var(--text-muted);">Loading vendor catalog and evaluated deals from MySQL...</td></tr>`;

    try {
        // If we have an active request, fetch evaluated quotes
        if (reqId) {
            const [quotesRes, evalsRes] = await Promise.all([
                fetch(`${API_BASE}/requests/${reqId}/quotes`),
                fetch(`${API_BASE}/requests/${reqId}/evaluations`)
            ]);
            if (quotesRes.ok && evalsRes.ok) {
                const quotes = await quotesRes.json();
                const evals = await evalsRes.json();
                renderEvaluatedQuotesTable(quotes, evals);
                return;
            }
        }

        // Otherwise show catalog
        const catRes = await fetch(`${API_BASE}/vendors/catalog/products`);
        if (catRes.ok) {
            const catalog = await catRes.json();
            renderCatalogTable(catalog);
        }
    } catch (err) {
        console.error('Error loading vendors:', err);
    }
}

function renderEvaluatedQuotesTable(quotes, evals) {
    const tbody = document.getElementById('vendors-comparison-table-body');
    if (!tbody) return;

    if (quotes.length === 0) {
        tbody.innerHTML = `<tr><td colspan="10" style="text-align: center; color: var(--text-muted);">No vendor quotations generated for this request yet.</td></tr>`;
        return;
    }

    // Merge quotes and evals
    const rows = quotes.map(q => {
        const ev = evals.find(e => e.quote_id === q.quote_id) || {};
        return { ...q, ...ev };
    });

    // Sort by rank
    rows.sort((a, b) => (a.rank || 99) - (b.rank || 99));

    tbody.innerHTML = rows.map(r => {
        const isEligible = r.eligibility_status === 'ELIGIBLE';
        const rankHtml = r.rank ? `<span class="rank-badge rank-${r.rank}">${r.rank}</span>` : `<span style="color: var(--text-muted);">-</span>`;
        const complianceHtml = isEligible
            ? `<span class="status-pill success">Compliant</span>`
            : `<span class="status-pill danger" title="${r.exclusion_reason || 'Failed rules'}">Ineligible</span>`;

        return `
            <tr style="${!isEligible ? 'opacity: 0.65; background: rgba(244, 63, 94, 0.05);' : ''}">
                <td>${rankHtml}</td>
                <td><strong>${r.vendor_name || r.vendor_id}</strong></td>
                <td>₹${Number(r.unit_price).toLocaleString('en-IN', {minimumFractionDigits: 2})}</td>
                <td>₹${Number(r.discount).toLocaleString('en-IN', {minimumFractionDigits: 2})}</td>
                <td>₹${Number(r.tax).toLocaleString('en-IN', {minimumFractionDigits: 2})}</td>
                <td><strong>₹${Number(r.total_amount).toLocaleString('en-IN', {minimumFractionDigits: 2})}</strong></td>
                <td>${r.delivery_days} days</td>
                <td>${r.warranty_months} mos</td>
                <td>${complianceHtml}</td>
                <td><strong>${r.final_score ? `${r.final_score}/100` : '-'}</strong></td>
            </tr>
        `;
    }).join('');
}

function renderCatalogTable(catalog) {
    const tbody = document.getElementById('vendors-comparison-table-body');
    if (!tbody) return;

    tbody.innerHTML = catalog.map((c, i) => `
        <tr>
            <td><span style="color: var(--text-muted);">${i+1}</span></td>
            <td><strong>${c.vendor_name}</strong></td>
            <td>₹${Number(c.unit_price).toLocaleString('en-IN', {minimumFractionDigits: 2})}</td>
            <td>-</td>
            <td>18% GST</td>
            <td>₹${Number(c.unit_price).toLocaleString('en-IN', {minimumFractionDigits: 2})} (unit)</td>
            <td>${c.delivery_days} days</td>
            <td>${c.warranty_months} mos</td>
            <td><span class="status-pill success">Active</span></td>
            <td>Catalog</td>
        </tr>
    `).join('');
}

// 5. Negotiation Centre
async function loadNegotiations(requestId = null) {
    const reqId = requestId || state.activeRequestId;
    const container = document.getElementById('negotiations-container');
    if (!container) return;

    if (!reqId) {
        container.innerHTML = `<div class="glass-panel" style="text-align: center; color: var(--text-muted);">Select or submit a procurement request to view AI counter-offer strategies.</div>`;
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/requests/${reqId}/negotiations`);
        if (!res.ok) return;
        const negs = await res.json();
        state.negotiations = negs;

        if (negs.length === 0) {
            container.innerHTML = `<div class="glass-panel" style="text-align: center; color: var(--text-muted);">No negotiations recorded yet for this request.</div>`;
            return;
        }

        container.innerHTML = negs.map(n => `
            <div class="glass-panel">
                <div class="panel-header">
                    <div class="panel-title">
                        <span>💬 Negotiation with <strong>${n.vendor_name || 'Vendor'}</strong></span>
                        <span class="status-pill ${n.negotiation_status === 'ACCEPTED' ? 'success' : (n.negotiation_status === 'REJECTED' ? 'danger' : 'warning')}">${n.negotiation_status}</span>
                    </div>
                </div>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 20px;">
                    <div class="metric-card" style="padding: 14px;">
                        <div class="metric-label">Original Quotation</div>
                        <div style="font-size: 20px; font-weight: 800;">₹${Number(n.original_amount).toLocaleString('en-IN', {minimumFractionDigits: 2})}</div>
                    </div>
                    <div class="metric-card" style="padding: 14px;">
                        <div class="metric-label">Target Ceiling</div>
                        <div style="font-size: 20px; font-weight: 800; color: var(--accent-cyan);">₹${Number(n.target_amount).toLocaleString('en-IN', {minimumFractionDigits: 2})}</div>
                    </div>
                    <div class="metric-card" style="padding: 14px; border-color: rgba(16, 185, 129, 0.4);">
                        <div class="metric-label">Proposed Counter-Offer</div>
                        <div style="font-size: 20px; font-weight: 800; color: var(--accent-emerald);">₹${Number(n.counter_offer_amount).toLocaleString('en-IN', {minimumFractionDigits: 2})}</div>
                    </div>
                </div>

                <div class="form-group">
                    <label class="form-label">Strategic Justification</label>
                    <div style="font-size: 13px; color: var(--text-secondary); background: rgba(255,255,255,0.03); padding: 12px; border-radius: 8px;">
                        ${n.justification}
                    </div>
                </div>

                <div class="form-group">
                    <label class="form-label">Draft Counter-Offer Letter</label>
                    <textarea class="form-textarea" id="neg-draft-${n.negotiation_id}" style="min-height: 100px;">${n.draft_message}</textarea>
                </div>

                ${n.vendor_response ? `
                    <div class="form-group" style="background: rgba(56, 189, 248, 0.05); border: 1px solid rgba(56, 189, 248, 0.2); padding: 14px; border-radius: 8px;">
                        <label class="form-label" style="color: var(--accent-cyan);">Vendor Feedback & Counter-Response</label>
                        <div style="font-size: 13px; color: #e2e8f0;">${n.vendor_response}</div>
                    </div>
                ` : ''}

                <div style="display: flex; gap: 12px; margin-top: 16px;">
                    <button class="btn-primary" onclick="simulateCounterOffer('${n.negotiation_id}')">
                        ⚡ Simulate Vendor Counter-Response
                    </button>
                </div>
            </div>
        `).join('');

    } catch (err) {
        console.error('Error loading negotiations:', err);
    }
}

async function simulateCounterOffer(negId) {
    const draftText = document.getElementById(`neg-draft-${negId}`)?.value;
    const neg = state.negotiations.find(n => n.negotiation_id === negId);
    if (!neg) return;

    try {
        const res = await fetch(`${API_BASE}/negotiations/${negId}/counter-offer`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                revised_counter_offer: neg.counter_offer_amount,
                revised_message: draftText,
                simulate_vendor_reply: true
            })
        });
        if (!res.ok) throw new Error('Simulation failed');
        loadNegotiations();
        loadDashboardSummary();
    } catch (e) {
        alert('Simulation Error: ' + e.message);
    }
}

// 6. Approval Centre
async function loadPendingApprovals() {
    const container = document.getElementById('approvals-container');
    if (!container) return;

    try {
        const res = await fetch(`${API_BASE}/approvals/pending`);
        if (!res.ok) return;
        const approvals = await res.json();
        state.approvals = approvals;

        if (approvals.length === 0) {
            container.innerHTML = `
                <div class="glass-panel" style="text-align: center; color: var(--text-muted); padding: 48px;">
                    <div style="font-size: 36px; margin-bottom: 12px;">✅</div>
                    <div style="font-size: 16px; font-weight: 700; color: #fff;">No Pending Approvals</div>
                    <div style="font-size: 13px; margin-top: 6px;">All workflows are either approved, straight-through processed, or completed.</div>
                </div>
            `;
            return;
        }

        container.innerHTML = approvals.map(a => {
            const risk = a.risk_assessment || {};
            const riskCat = risk.risk_category || 'MEDIUM';
            const riskPill = riskCat === 'HIGH' ? 'danger' : (riskCat === 'MEDIUM' ? 'warning' : 'success');

            return `
                <div class="glass-panel" style="border-color: rgba(245, 158, 11, 0.4);">
                    <div class="panel-header">
                        <div class="panel-title">
                            <span>🛡️ Approval Request for <strong>${a.vendor_name || 'Vendor'}</strong></span>
                            <span class="status-pill ${riskPill}">Google ADK Risk: ${riskCat} (${risk.risk_score || 0}/100)</span>
                        </div>
                    </div>

                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 20px;">
                        <div class="metric-card" style="padding: 14px;">
                            <div class="metric-label">Quoted Total Cost</div>
                            <div style="font-size: 20px; font-weight: 800;">₹${Number(a.total_amount).toLocaleString('en-IN', {minimumFractionDigits: 2})}</div>
                        </div>
                        <div class="metric-card" style="padding: 14px;">
                            <div class="metric-label">Approved Budget Ceiling</div>
                            <div style="font-size: 20px; font-weight: 800; color: var(--accent-cyan);">₹${Number(a.budget_limit).toLocaleString('en-IN', {minimumFractionDigits: 2})}</div>
                        </div>
                        <div class="metric-card" style="padding: 14px;">
                            <div class="metric-label">Governance Trigger</div>
                            <div style="font-size: 13px; font-weight: 600; color: var(--accent-amber);">${a.approval_reason}</div>
                        </div>
                    </div>

                    <div class="form-group" style="background: rgba(255,255,255,0.03); padding: 14px; border-radius: 8px;">
                        <label class="form-label">Google ADK Risk Assessment Summary</label>
                        <div style="font-size: 13px; color: #cbd5e1; line-height: 1.5;">${risk.explanation || 'Independent audit evaluated parameters.'}</div>
                    </div>

                    <div class="form-group">
                        <label class="form-label">Approver Comments</label>
                        <input type="text" class="form-input" id="approval-comment-${a.approval_id}" placeholder="Enter rationale or approval conditions...">
                    </div>

                    <div style="display: flex; gap: 12px; margin-top: 20px;">
                        <button class="btn-success" onclick="submitApproval('${a.approval_id}', 'APPROVED')">
                            ✓ Approve Deal & Issue PO
                        </button>
                        <button class="btn-danger" onclick="submitApproval('${a.approval_id}', 'REJECTED')">
                            ✕ Reject Proposal
                        </button>
                        <button class="btn-secondary" onclick="submitApproval('${a.approval_id}', 'REVISION_REQUESTED')">
                            ↺ Request Revision
                        </button>
                    </div>
                </div>
            `;
        }).join('');

    } catch (err) {
        console.error('Error loading approvals:', err);
    }
}

async function submitApproval(approvalId, decision) {
    const comment = document.getElementById(`approval-comment-${approvalId}`)?.value;

    try {
        const res = await fetch(`${API_BASE}/approvals/${approvalId}/decision`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                decision: decision,
                decided_by: "VP of Enterprise Procurement",
                comments: comment || "Approved following multi-agent evaluation and Google ADK risk review."
            })
        });

        if (!res.ok) throw new Error('Failed to record approval decision');
        const data = await res.json();

        alert(`Decision Recorded: ${decision}. ${data.order_number ? `Purchase Order ${data.order_number} has been issued!` : ''}`);
        loadPendingApprovals();
        loadDashboardSummary();
        loadPurchaseOrders();
        switchView('orders');
    } catch (e) {
        alert('Approval Error: ' + e.message);
    }
}

// 7. Purchase Orders & Document Modal
async function loadPurchaseOrders() {
    const tbody = document.getElementById('pos-table-body');
    if (!tbody) return;

    try {
        const res = await fetch(`${API_BASE}/purchase-orders`);
        if (!res.ok) return;
        const pos = await res.json();
        state.orders = pos;

        if (pos.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-muted);">No Purchase Orders issued yet. Run workflow to generate orders.</td></tr>`;
            return;
        }

        tbody.innerHTML = pos.map(p => `
            <tr>
                <td style="font-family: var(--font-mono); font-weight: 700; color: var(--accent-cyan);">${p.order_number}</td>
                <td><strong>${p.vendor_name || p.vendor_id}</strong></td>
                <td>₹${Number(p.approved_total).toLocaleString('en-IN', {minimumFractionDigits: 2})}</td>
                <td><span class="status-pill success">${p.status}</span></td>
                <td>${p.approved_by}</td>
                <td>${new Date(p.created_at).toLocaleDateString()}</td>
                <td>
                    <button class="btn-secondary" style="padding: 4px 10px; font-size: 11px;" onclick="viewPODocument('${p.purchase_order_id}')">
                        📄 View Formal PO
                    </button>
                </td>
            </tr>
        `).join('');

    } catch (err) {
        console.error('Error loading purchase orders:', err);
    }
}

function viewPODocument(poId) {
    const po = state.orders.find(p => p.purchase_order_id === poId);
    if (!po) return;

    const modal = document.getElementById('po-modal');
    const container = document.getElementById('po-modal-container');
    const details = po.order_details || {};
    const qty = details.quantity || 50;
    const unitPrice = details.unit_price || 68000;
    const discount = details.discount || 0;
    const tax = details.tax || 0;
    const shipping = details.shipping_cost || 0;

    container.innerHTML = `
        <div class="po-document" id="printable-po">
            <div class="po-header">
                <div>
                    <div class="po-title">DEALFORGE ENTERPRISE AI</div>
                    <div style="font-size: 12px; color: #64748b; margin-top: 4px;">Automated Procurement & Supply Chain Division</div>
                    <div style="font-size: 12px; color: #64748b;">CIN: U72200KA2026PTC109988 | GSTIN: 29AABCU9603R1ZM</div>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 11px; text-transform: uppercase; font-weight: 700; color: #64748b;">OFFICIAL PURCHASE ORDER</div>
                    <div class="po-number">${po.order_number}</div>
                    <div style="font-size: 12px; color: #64748b; margin-top: 4px;">Date: ${new Date(po.created_at).toLocaleDateString()}</div>
                </div>
            </div>

            <div class="po-meta-grid">
                <div>
                    <div style="font-weight: 700; color: #0f172a; margin-bottom: 4px;">VENDOR DETAILS</div>
                    <div style="font-weight: 600;">${po.vendor_name || 'Nexus Tech Enterprise Solutions'}</div>
                    <div>Authorized Corporate Hardware Partner</div>
                    <div>Delivery SLA: ${details.delivery_days || 10} Days</div>
                    <div>Mandatory Warranty: ${details.warranty_months || 36} Months</div>
                </div>
                <div>
                    <div style="font-weight: 700; color: #0f172a; margin-bottom: 4px;">BILL TO / SHIP TO</div>
                    <div>DealForge AI Global Operations</div>
                    <div>Tower B, Cyber Park Phase 1</div>
                    <div>Bengaluru, Karnataka - 560100</div>
                    <div>Attn: ${po.approved_by}</div>
                </div>
            </div>

            <table class="po-table">
                <thead>
                    <tr>
                        <th>Item Description</th>
                        <th>Qty</th>
                        <th>Unit Price</th>
                        <th>Discount</th>
                        <th>Tax (18% GST)</th>
                        <th>Net Total</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>
                            <strong>${details.product_requirements?.category || 'Hardware Equipment'}</strong><br>
                            <span style="font-size: 11px; color: #64748b;">Specs: 16 GB RAM | 512 GB SSD | Enterprise Grade</span>
                        </td>
                        <td>${qty}</td>
                        <td>₹${Number(unitPrice).toLocaleString('en-IN', {minimumFractionDigits: 2})}</td>
                        <td>-₹${Number(discount).toLocaleString('en-IN', {minimumFractionDigits: 2})}</td>
                        <td>₹${Number(tax).toLocaleString('en-IN', {minimumFractionDigits: 2})}</td>
                        <td><strong>₹${Number(po.approved_total).toLocaleString('en-IN', {minimumFractionDigits: 2})}</strong></td>
                    </tr>
                </tbody>
            </table>

            <div style="display: flex; justify-content: flex-end; margin-bottom: 24px;">
                <div style="width: 280px; font-size: 13px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                        <span>Freight & Handling:</span>
                        <span>₹${Number(shipping).toLocaleString('en-IN', {minimumFractionDigits: 2})}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; border-top: 2px solid #0f172a; padding-top: 8px; font-weight: 800; font-size: 16px;">
                        <span>GRAND TOTAL:</span>
                        <span style="color: #2563eb;">₹${Number(po.approved_total).toLocaleString('en-IN', {minimumFractionDigits: 2})}</span>
                    </div>
                </div>
            </div>

            <div style="border-top: 1px solid #e2e8f0; padding-top: 16px; display: flex; justify-content: space-between; align-items: flex-end;">
                <div>
                    <div style="font-size: 11px; color: #64748b;">Digital Audit Footprint:</div>
                    <div style="font-family: var(--font-mono); font-size: 10px; color: #94a3b8;">AUTH-HASH: SHA256-DF-${po.order_number}-${po.purchase_order_id.slice(0,8)}</div>
                </div>
                <div style="text-align: right;">
                    <div style="font-weight: 700; color: #0f172a;">${po.approved_by}</div>
                    <div style="font-size: 11px; color: #64748b;">Authorized Signatory</div>
                </div>
            </div>

            <div class="po-watermark">
                System-Generated Enterprise Procurement Document — DealForge AI Multi-Agent Platform
            </div>
        </div>
    `;

    modal.classList.add('active');
}

function closePOModal() {
    document.getElementById('po-modal')?.classList.remove('active');
}
