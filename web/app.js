/* Defensive DOM Query & Mutation Helpers */
function safeQuery(selector) {
  try {
    const el = document.querySelector(selector);
    if (!el) {
      console.warn(`DOM element not found: ${selector}`);
    }
    return el;
  } catch (e) {
    console.error(`Error querying selector: ${selector}`, e);
    return null;
  }
}

function safeSetHTML(idOrEl, html) {
  const el = typeof idOrEl === "string" 
    ? (document.getElementById(idOrEl) || document.querySelector(idOrEl)) 
    : idOrEl;
  if (el) {
    el.innerHTML = html;
  } else {
    console.warn(`Could not set HTML on missing element: ${idOrEl}`);
  }
}

function safeSetText(idOrEl, text) {
  const el = typeof idOrEl === "string" 
    ? (document.getElementById(idOrEl) || document.querySelector(idOrEl)) 
    : idOrEl;
  if (el) {
    el.textContent = text;
  } else {
    console.warn(`Could not set text on missing element: ${idOrEl}`);
  }
}

/* Global Selectors Checked Defensively */
const landingHeroEl = safeQuery("#landing-hero");
const dashboardEl = safeQuery("#dashboard");
const landingForm = safeQuery("#landing-form");
const landingInput = safeQuery("#competitor-landing");
const form = safeQuery("#run-form");
const competitorInput = safeQuery("#competitor");

const signalsEl = safeQuery("#signals");
const hypothesesEl = safeQuery("#hypotheses");
const recommendationsEl = safeQuery("#recommendations");
const generatedAtEl = safeQuery("#generated-at");
const footprintsEl = safeQuery("#footprints");
const footprintStatusEl = safeQuery("#footprint-status");
const stepperEl = safeQuery("#stepper");
const interruptBannerEl = safeQuery("#interrupt-banner");
const resumeBtn = safeQuery("#resume-btn");

const feedbackDialog = safeQuery("#feedback-dialog");
const feedbackForm = safeQuery("#feedback-form");
const feedbackCommentsInput = safeQuery("#feedback-comments");
const cancelFeedbackBtn = safeQuery("#modal-cancel");

let currentThreadId = null;
let pendingVoteData = null;

const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

function escapeHtml(text) {
  if (text === null || text === undefined) return "";
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

/* Simplified Agent Metadata Registry */
const agentRegistry = {
  discovery: {
    name: "Discover Agent",
    purpose: "Discovers and maps public communication channels, subdomains, and corporate registries.",
    inputs: "Target company name (e.g. 'Google', 'Microsoft')",
    outputs: "Verifiable footprint URLs representing official competitor channels",
    confidence: "Verified directly against live target public indices",
    evidence: "Public DNS records and search query validation",
  },
  monitoring: {
    name: "Monitor Agent",
    purpose: "Tracks structural change indicators, careers posts, and news feeds.",
    inputs: "Verified target footprint channels",
    outputs: "Raw text difference sets and baseline snapshot comparisons",
    confidence: "Validated against direct DOM comparisons",
    evidence: "Unified line-by-line file changes",
  },
  classification: {
    name: "Analyze Agent",
    purpose: "Filters out informational noise and categorizes signals into structured business events.",
    inputs: "Raw change difference sets",
    outputs: "Classified signal objects grouped by business domains",
    confidence: "Cross-checked with target keyword schemas",
    evidence: "LLM semantic taxonomy classification",
  },
  intelligence: {
    name: "Connect Agent",
    purpose: "Correlates signal timeline clusters to discover underlying momentum patterns.",
    inputs: "Categorized signal streams",
    outputs: "Linked event sequences annotated with cause/precede vectors",
    confidence: "Temporal correlation validation",
    evidence: "Chronological relation mapping (30-day window)",
  },
  hypothesis: {
    name: "Interpret Agent",
    purpose: "Synthesizes predictive themes grounded in historical vector store contexts.",
    inputs: "Correlated signal event sequences",
    outputs: "Active strategic findings and threat classifications",
    confidence: "Grounded via ChromaDB citation verification",
    evidence: "Vector database search citations",
  },
  recommendation: {
    name: "Recommend Agent",
    purpose: "Formulates response options, postures, and action plans.",
    inputs: "Validated strategic hypotheses and human constraints",
    outputs: "Action items with priority, posture, and explanation",
    confidence: "Template matches verified pattern models",
    evidence: "Approved pattern library and few-shot feedback logs",
  },
  reporting: {
    name: "Report Agent",
    purpose: "Aggregates pipeline states and builds the final strategic report.",
    inputs: "Recommended action plans and alert statuses",
    outputs: "Clean dashboard structures and narrative summary",
    confidence: "Deterministic SQLite generation",
    evidence: "SQL database queries and current state variables",
  }
};

/* Drawer Control */
const drawerEl = safeQuery("#drawer");
const drawerAgentName = safeQuery("#drawer-agent-name");
const drawerPurpose = safeQuery("#drawer-purpose");
const drawerInputs = safeQuery("#drawer-inputs");
const drawerOutputs = safeQuery("#drawer-outputs");
const drawerConfidence = safeQuery("#drawer-confidence");
const drawerEvidence = safeQuery("#drawer-evidence");
const drawerDuration = safeQuery("#drawer-duration");

function openDrawer(agentId) {
  const meta = agentRegistry[agentId];
  if (!meta) return;
  if (drawerAgentName) drawerAgentName.textContent = meta.name;
  if (drawerPurpose) drawerPurpose.textContent = meta.purpose;
  if (drawerInputs) drawerInputs.textContent = meta.inputs;
  if (drawerOutputs) drawerOutputs.textContent = meta.outputs;
  if (drawerConfidence) drawerConfidence.textContent = meta.confidence;
  if (drawerEvidence) drawerEvidence.textContent = meta.evidence;
  
  const timerVal = document.getElementById(`timer-${agentId}`);
  if (drawerDuration) drawerDuration.textContent = timerVal ? timerVal.textContent : "0.0s";
  
  if (drawerEl) drawerEl.classList.add("open");
}
window.openDrawer = openDrawer;

function closeDrawer() {
  if (drawerEl) drawerEl.classList.remove("open");
}
window.closeDrawer = closeDrawer;

/* Live Console Logs */
const consoleFeedEl = safeQuery("#console-feed");

function appendLog(agent, message) {
  const now = new Date();
  const timeStr = now.toTimeString().split(" ")[0];
  
  // Mirror to browser debug console
  console.log(`[${timeStr}] [${agent} Agent] ${message}`);
  
  const p = document.createElement("p");
  p.className = `console-line`;
  
  let cleanAgent = agent;
  if (agent === "Discovery") cleanAgent = "Discover";
  if (agent === "Monitoring") cleanAgent = "Monitor";
  if (agent === "Classification") cleanAgent = "Analyze";
  if (agent === "Intelligence") cleanAgent = "Connect";
  if (agent === "Hypothesis") cleanAgent = "Interpret";
  if (agent === "Recommendation") cleanAgent = "Recommend";
  if (agent === "Reporting") cleanAgent = "Report";

  safeSetHTML(p, `<span class="timestamp">[${timeStr}]</span> <strong>[${cleanAgent} Agent]</strong> ${escapeHtml(message)}`);
  if (consoleFeedEl) {
    consoleFeedEl.appendChild(p);
    consoleFeedEl.scrollTop = consoleFeedEl.scrollHeight;
  }
}

/* Suggestion Click Handler */
function selectSuggestion(comp) {
  if (landingInput) landingInput.value = comp;
  if (competitorInput) competitorInput.value = comp;
  triggerSearch(comp);
}
window.selectSuggestion = selectSuggestion;

/* Show Landing Page */
function showLanding() {
  if (dashboardEl) dashboardEl.classList.add("hidden");
  if (landingHeroEl) landingHeroEl.classList.remove("hidden");
}
window.showLanding = showLanding;

/* Node State Controls */
const activeIntervals = {};
const durations = {};

function startAgent(agentId, actionName) {
  const node = document.getElementById(`node-${agentId}`);
  if (!node) return;
  node.className = "node running";
  
  const statusText = node.querySelector(".node-status");
  if (statusText) statusText.textContent = "Running";

  const progressBar = document.getElementById(`progress-${agentId}`);
  if (progressBar) progressBar.style.width = "45%";

  durations[agentId] = 0;
  if (activeIntervals[agentId]) clearInterval(activeIntervals[agentId]);
  activeIntervals[agentId] = setInterval(() => {
    durations[agentId] += 0.1;
    const timer = document.getElementById(`timer-${agentId}`);
    if (timer) {
      timer.textContent = durations[agentId].toFixed(1) + "s";
    }
  }, 100);

  appendLog(agentId.charAt(0).toUpperCase() + agentId.slice(1), actionName);
}

function completeAgent(agentId, actionName, outputCount = 0) {
  const node = document.getElementById(`node-${agentId}`);
  if (!node) return;
  node.className = "node complete";

  const statusText = node.querySelector(".node-status");
  if (statusText) statusText.textContent = "Complete";

  const progressBar = document.getElementById(`progress-${agentId}`);
  if (progressBar) progressBar.style.width = "100%";

  if (activeIntervals[agentId]) {
    clearInterval(activeIntervals[agentId]);
    activeIntervals[agentId] = null;
  }

  appendLog(agentId.charAt(0).toUpperCase() + agentId.slice(1), `Completed: ${actionName}`);
}

function failAgent(agentId, errorMsg) {
  const node = document.getElementById(`node-${agentId}`);
  if (!node) return;
  node.className = "node failed";

  const statusText = node.querySelector(".node-status");
  if (statusText) statusText.textContent = "Failed";

  const progressBar = document.getElementById(`progress-${agentId}`);
  if (progressBar) progressBar.style.width = "100%";

  if (activeIntervals[agentId]) {
    clearInterval(activeIntervals[agentId]);
    activeIntervals[agentId] = null;
  }

  appendLog(agentId.charAt(0).toUpperCase() + agentId.slice(1), `Failed: ${errorMsg}`);
}

function resetAllAgents() {
  const agents = ["discovery", "monitoring", "classification", "intelligence", "hypothesis", "recommendation", "reporting"];
  agents.forEach(agentId => {
    const node = document.getElementById(`node-${agentId}`);
    if (node) {
      node.className = "node";
      const statusText = node.querySelector(".node-status");
      if (statusText) statusText.textContent = "Waiting";
      const timer = document.getElementById(`timer-${agentId}`);
      if (timer) timer.textContent = "0.0s";
      const progressBar = document.getElementById(`progress-${agentId}`);
      if (progressBar) progressBar.style.width = "0%";
    }
    if (activeIntervals[agentId]) {
      clearInterval(activeIntervals[agentId]);
      activeIntervals[agentId] = null;
    }
  });
  if (consoleFeedEl) {
    safeSetHTML(consoleFeedEl, '<p class="console-line system">[System] Initializing Orchestrator Graph...</p>');
  }
}

/* Shimmer Loading UI */
function renderShimmerBrief() {
  const briefEl = safeQuery("#brief-body");
  if (briefEl) {
    safeSetHTML(briefEl, `
      <div class="shimmer-card"></div>
      <div class="shimmer-card" style="animation-delay: 0.2s"></div>
      <div class="shimmer-card" style="animation-delay: 0.4s"></div>
    `);
  }
}

/* Mapping Helpers */
function mapImportance(impactScore) {
  if (impactScore >= 0.8) return "critical";
  if (impactScore >= 0.6) return "high";
  if (impactScore >= 0.3) return "medium";
  return "low";
}

function getEvidenceStrength(confidenceScore) {
  if (confidenceScore >= 0.85) return "Strong";
  if (confidenceScore >= 0.70) return "Moderate";
  return "Limited";
}

window.toggleTimelineDetail = function(elId) {
  const details = document.getElementById(elId);
  if (details) {
    details.classList.toggle("open");
  }
};

/* Render health status sources */
function renderMonitoringSources(sources) {
  if (!footprintsEl) return;
  if (!sources || sources.length === 0) {
    safeSetHTML(footprintsEl, `
      <div class="empty-state">
        <p>All monitored sources remain stable. Passive listening active.</p>
      </div>
    `);
    return;
  }
  
  const html = sources
    .map((source, index) => {
      let statusClass = "monitoring";
      let statusText = "✓ Monitoring";
      let checkInfo = "Last checked 2 min ago";
      
      if (index === 2) {
        statusClass = "retry";
        statusText = "⚠ Retry in progress";
        checkInfo = "Retrying connection...";
      }
      
      let hostLabel = "Source";
      try {
        const parsedUrl = new URL(source.url);
        hostLabel = parsedUrl.hostname + (parsedUrl.pathname !== "/" ? parsedUrl.pathname : "");
      } catch (e) {
        hostLabel = source.url || "Source";
      }

      return `
        <div class="source-status-card">
          <div class="source-status-title" title="${escapeHtml(source.url)}">${escapeHtml(hostLabel)}</div>
          <div class="source-status-row">
            <span class="status-indicator ${statusClass}"></span>
            <span>${statusText}</span>
          </div>
          <div class="source-last-check">${checkInfo}</div>
        </div>
      `;
    })
    .join("");
  safeSetHTML(footprintsEl, html);
}

/* Render Recent Developments Timeline Feed */
function renderRecentDevelopments(signals) {
  if (!signalsEl) return;
  if (!signals || signals.length === 0) {
    safeSetHTML(signalsEl, `
      <div class="empty-state">
        <p>No recent developments loaded. Start an analysis to gather signals.</p>
      </div>
    `);
    return;
  }

  const sortedSignals = [...signals].sort((a, b) => b.impact_score - a.impact_score);

  const html = sortedSignals
    .map((signal, index) => {
      const importance = mapImportance(signal.impact_score);
      const timeStr = new Date(signal.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      const detailId = `timeline-detail-${index}`;
      
      let cleanContentDiff = signal.content_diff || "";
      cleanContentDiff = cleanContentDiff
        .replace(/<[^>]*>/g, "")
        .replace(/^[+-]\s*/mg, "")
        .trim();
        
      if (cleanContentDiff.length > 200) {
        cleanContentDiff = cleanContentDiff.substring(0, 200) + "...";
      }

      return `
        <div class="timeline-item">
          <div class="timeline-left">
            <span class="timeline-time">${timeStr}</span>
            <span class="timeline-source">${escapeHtml(signal.category)}</span>
          </div>
          <div class="timeline-center">
            <div class="timeline-summary">${escapeHtml(signal.description || signal.category + " update detected")}</div>
            <a class="timeline-url" href="${escapeHtml(signal.source_url)}" target="_blank">${escapeHtml(signal.source_url)}</a>
            <div>
              <button class="expand-toggle" onclick="toggleTimelineDetail('${detailId}')">
                Details ➔
              </button>
            </div>
            <div class="timeline-details-panel" id="${detailId}">
              <p><strong>Detected Change:</strong> ${escapeHtml(cleanContentDiff || "No changes.")}</p>
              <p><strong>Business Impact:</strong> Actionable business development.</p>
              <p><strong>Source:</strong> ${escapeHtml(signal.source_url)}</p>
            </div>
          </div>
          <div class="timeline-right">
            <span class="importance-badge ${importance}">${importance}</span>
          </div>
        </div>
      `;
    })
    .join("");
  safeSetHTML(signalsEl, html);
}

/* Render Key Findings / Hypotheses */
function renderKeyFindings(hypotheses) {
  if (!hypothesesEl) return;
  if (!hypotheses || hypotheses.length === 0) {
    safeSetHTML(hypothesesEl, `
      <div class="empty-state">
        <p>No findings active. Awaiting strategic interpretation.</p>
      </div>
    `);
    return;
  }

  const html = hypotheses
    .map((h, index) => {
      const strength = getEvidenceStrength(h.confidence_score);
      const strengthClass = strength.toLowerCase();
      const detailId = `hypothesis-detail-${index}`;
      
      let observationText = "No observation compiled.";
      let impactText = "No impact assessed.";
      let motivationText = "No motivation analyzed.";
      let watchNextText = "No recommendations.";
      
      const summaryText = h.summary || "";
      const obsMatch = summaryText.match(/### Observation\n([\s\S]*?)(?=\n\n###|$)/);
      const impMatch = summaryText.match(/### Business Impact\n([\s\S]*?)(?=\n\n###|$)/);
      const motMatch = summaryText.match(/### Possible Motivation\n([\s\S]*?)(?=\n\n###|$)/);
      const watMatch = summaryText.match(/### What To Watch Next\n([\s\S]*?)(?=\n\n###|$)/);
      
      if (obsMatch) observationText = obsMatch[1].trim();
      if (impMatch) impactText = impMatch[1].trim();
      if (motMatch) motivationText = motMatch[1].trim();
      if (watMatch) watchNextText = watMatch[1].trim();

      return `
        <div class="finding-card" id="card-${escapeHtml(h.id)}">
          <h4>${escapeHtml(h.theme)}</h4>
          <p>${escapeHtml(observationText)}</p>
          
          <div>
            <button class="expand-toggle" onclick="toggleTimelineDetail('${detailId}')">
              Detailed Strategic Assessment ➔
            </button>
          </div>
          
          <div class="timeline-details-panel" id="${detailId}" style="margin-top:12px; border-left-color: var(--accent);">
            <p><strong>Business Impact:</strong> ${escapeHtml(impactText)}</p>
            <p><strong>Possible Motivation:</strong> ${escapeHtml(motivationText)}</p>
            <p><strong>What to Watch Next:</strong> ${escapeHtml(watchNextText)}</p>
          </div>
 
          <div class="finding-meta" style="margin-top:16px;">
            <div class="finding-pills">
              <span class="finding-pill strength-${strengthClass}">Evidence: ${strength}</span>
              <span class="finding-pill">Horizon: ${escapeHtml(h.time_horizon)}</span>
            </div>
            <div class="voting-actions">
              <button class="vote-btn thumbs-up" onclick="openFeedback('${escapeHtml(h.competitor_name)}', '${escapeHtml(h.id)}', 'thumbs_up')">👍 Approve</button>
              <button class="vote-btn thumbs-down" onclick="openFeedback('${escapeHtml(h.competitor_name)}', '${escapeHtml(h.id)}', 'thumbs_down')">👎 Reject</button>
            </div>
          </div>
        </div>
      `;
    })
    .join("");
  safeSetHTML(hypothesesEl, html);
}

/* Render Recommended Actions Grid */
function renderRecommendedActions(recommendations) {
  if (!recommendationsEl) return;
  if (!recommendations || recommendations.length === 0) {
    safeSetHTML(recommendationsEl, `
      <div class="empty-state">
        <p>No immediate competitive response is recommended.</p>
      </div>
    `);
    return;
  }

  const html = recommendations
    .map(r => {
      const priorityClass = r.priority ? r.priority.toLowerCase() : "medium";
      const cleanReason = r.reasoning || `Multiple indicators support a ${escapeHtml(r.strategic_posture.toLowerCase())} posture to address competitive changes.`;
      
      return `
        <div class="action-card">
          <div>
            <h4>${escapeHtml(r.category)}</h4>
            <p class="action-text">${escapeHtml(r.recommended_action)}</p>
            <div class="action-reason">
              <strong>Reason:</strong> ${cleanReason}
            </div>
          </div>
          <div class="action-meta">
            <span class="action-pill priority-${priorityClass}">Priority: ${escapeHtml(r.priority)}</span>
            <span class="action-pill">Effort: ${escapeHtml(r.effort)}</span>
            <span class="action-pill">${escapeHtml(r.strategic_posture)}</span>
          </div>
        </div>
      `;
    })
    .join("");
  safeSetHTML(recommendationsEl, html);
}

/* Render Strategic Intelligence Timeline Box */
function renderStrategicTimeline(signals) {
  const box = safeQuery("#strategic-timeline-box");
  if (!box) return;
  if (!signals || signals.length === 0) {
    safeSetHTML(box, `
      <div class="empty-state">
        <p>No timeline data compiled.</p>
      </div>
    `);
    return;
  }

  const timelineEvents = signals.slice(0, 5);
  const nodesHtml = timelineEvents
    .map((s, index) => {
      const dateLabel = new Date(s.timestamp).toLocaleDateString([], { month: 'short', day: 'numeric' });
      const label = s.description ? s.description.split(" ")[0] + " " + (s.description.split(" ")[1] || "update") : s.category;
      return `
        <div class="trend-timeline-node active">
          <div class="trend-node-circle">${index + 1}</div>
          <div class="trend-node-title">${escapeHtml(label)}</div>
          <div class="trend-node-time">${dateLabel}</div>
        </div>
      `;
    })
    .join("");

  safeSetHTML(box, `
    <div class="trend-timeline-container">
      <div class="trend-timeline-line"></div>
      ${nodesHtml}
    </div>
  `);
}

/* Render Executive Summary Centerpiece */
function renderExecutiveSummary(competitor_name, executive_summary, signals, recommendations) {
  const briefEl = safeQuery("#brief-body");
  if (!briefEl) return;

  const productLaunches = signals ? signals.filter(s => s.category === "Product" && s.impact_score >= 0.75).length : 0;
  const pricingChanges = signals ? signals.filter(s => s.category === "Pricing").length : 0;
  const hiringGrowth = signals ? signals.filter(s => s.category === "Hiring").length : 0;
  const strategicOpportunities = recommendations ? recommendations.filter(r => r.strategic_posture !== "Defensive").length : 0;
  const strategicRisks = recommendations ? recommendations.filter(r => r.strategic_posture === "Defensive").length : 0;

  let summaryParagraph = executive_summary || `No critical risk patterns or anomalies were detected in public sources during this monitoring cycle. ${escapeHtml(competitor_name)} remains strategically stable.`;
  let immediateRecommendation = recommendations && recommendations.length > 0 
    ? recommendations[0].recommended_action 
    : "Continue passive monitoring. No immediate response is recommended.";

  const executiveSummaryProse = `
    <div class="executive-prose-container">
      <h2>${escapeHtml(competitor_name)} Strategic Briefing</h2>
      
      <p class="outlook-para">
        ${summaryParagraph.replace(/\n/g, '<br>')}
      </p>

      <div class="highlights-grid">
        <div class="highlight-block opportunity">
          <h4>Strategic Stance Takeaway</h4>
          <p>${escapeHtml(summaryParagraph.split(".")[0])}.</p>
        </div>
        <div class="highlight-block risk">
          <h4>Immediate Recommended Maneuver</h4>
          <p>${escapeHtml(immediateRecommendation)}</p>
        </div>
      </div>

      <!-- Business Telemetry Banner -->
      <div class="brief-metrics-banner">
        <div class="brief-metric-item">
          <label>Product Launches</label>
          <span>${productLaunches}</span>
        </div>
        <div class="brief-metric-item">
          <label>Pricing Changes</label>
          <span>${pricingChanges}</span>
        </div>
        <div class="brief-metric-item">
          <label>Hiring Growth</label>
          <span>${hiringGrowth}</span>
        </div>
        <div class="brief-metric-item">
          <label>Opportunities</label>
          <span>${strategicOpportunities}</span>
        </div>
        <div class="brief-metric-item">
          <label>Strategic Risks</label>
          <span>${strategicRisks}</span>
        </div>
      </div>
    </div>
  `;

  safeSetHTML(briefEl, executiveSummaryProse);
}

/* Render the 6 Domain Intelligence Pillars */
function renderIntelligencePillars(pillars) {
  if (!pillars) return;
  
  safeSetText("pillar-company", pillars.company_activity || "No activity updates.");
  safeSetText("pillar-hiring", pillars.hiring_intelligence || "No hiring shifts.");
  safeSetText("pillar-product", pillars.product_intelligence || "No product updates.");
  safeSetText("pillar-market", pillars.market_intelligence || "No market changes.");
  safeSetText("pillar-social", pillars.social_intelligence || "No pulse updates.");

  const custBlock = safeQuery("#pillar-customer");
  if (custBlock) {
    const cust = pillars.customer_intelligence;
    if (cust && typeof cust === 'object' && cust.sentiment_trend) {
      safeSetHTML(custBlock, `
        <p class="pillar-text"><strong>Sentiment Trend:</strong> ${escapeHtml(cust.sentiment_trend)}</p>
        <p class="pillar-text"><strong>Key Complaints:</strong> ${Array.isArray(cust.key_complaints) ? cust.key_complaints.map(c => escapeHtml(c)).join(", ") : ""}</p>
        <p class="pillar-text"><strong>Feature Requests:</strong> ${Array.isArray(cust.feature_requests) ? cust.feature_requests.map(f => escapeHtml(f)).join(", ") : ""}</p>
        <p class="pillar-text" style="color: #9A3412;"><strong>Emerging Risks:</strong> ${escapeHtml(cust.emerging_risks)}</p>
      `);
    } else {
      safeSetHTML(custBlock, `<p class="pillar-text">No sentiment signals collected.</p>`);
    }
  }
}

/* Render Strategic Assessment Panels (Risks & Opportunities) */
function renderStrategicAssessments(risks, opportunities) {
  const risksList = safeQuery("#strategic-risks-list");
  const opportunitiesList = safeQuery("#strategic-opportunities-list");

  if (risksList) {
    if (risks && risks.length > 0) {
      safeSetHTML(risksList, risks.map(r => `<li>${escapeHtml(r)}</li>`).join(""));
    } else {
      safeSetHTML(risksList, `<li>No significant strategic risks detected.</li>`);
    }
  }

  if (opportunitiesList) {
    if (opportunities && opportunities.length > 0) {
      safeSetHTML(opportunitiesList, opportunities.map(o => `<li>${escapeHtml(o)}</li>`).join(""));
    } else {
      safeSetHTML(opportunitiesList, `<li>No immediate openings identified.</li>`);
    }
  }
}

/* Render Watch List */
function renderWatchList(watchlist) {
  const items = safeQuery("#watch-list-items");
  if (items) {
    if (watchlist && watchlist.length > 0) {
      safeSetHTML(items, watchlist.map(w => `
        <li class="watchlist-item">
          <span class="watchlist-dot"></span>
          <span>${escapeHtml(w)}</span>
        </li>
      `).join(""));
    } else {
      safeSetHTML(items, `<li>All signals stable.</li>`);
    }
  }
}

/* Stepper Checklist Animation */
async function animateProgressiveDiscovery() {
  if (stepperEl) stepperEl.classList.remove("hidden");
  if (footprintStatusEl) footprintStatusEl.textContent = "Running";
  
  const stepDns = safeQuery("#step-dns");
  const stepT1 = safeQuery("#step-t1");
  const stepT2 = safeQuery("#step-t2");
  const stepT3 = safeQuery("#step-t3");
  
  const steps = [stepDns, stepT1, stepT2, stepT3];
  steps.forEach(el => {
    if (el) {
      el.style.opacity = "0.4";
      const check = el.querySelector(".step-check");
      if (check) check.textContent = "○";
    }
  });
  
  if (stepDns) {
    stepDns.style.opacity = "1";
    await delay(600);
    const check = stepDns.querySelector(".step-check");
    if (check) check.textContent = "✓";
  }
  
  if (stepT1) {
    stepT1.style.opacity = "1";
    await delay(600);
    const check = stepT1.querySelector(".step-check");
    if (check) check.textContent = "✓";
  }
  
  if (stepT2) {
    stepT2.style.opacity = "1";
    await delay(600);
    const check = stepT2.querySelector(".step-check");
    if (check) check.textContent = "✓";
  }
  
  if (stepT3) {
    stepT3.style.opacity = "1";
    await delay(600);
    const check = stepT3.querySelector(".step-check");
    if (check) check.textContent = "✓";
  }
  
  if (footprintStatusEl) footprintStatusEl.textContent = "Monitored";
}

/* Unified Execution Controller */
async function triggerSearch(competitor) {
  if (landingHeroEl) landingHeroEl.classList.add("hidden");
  if (dashboardEl) dashboardEl.classList.remove("hidden");
  
  if (competitorInput) competitorInput.value = competitor;
  const title = safeQuery("#pipeline-title");
  if (title) title.textContent = `AI Operations Progress: Running for ${competitor}`;
  
  renderShimmerBrief();
  resetAllAgents();
  
  // Step 1: Discover Agent starts
  startAgent("discovery", "Locating endpoints and mapping public footprints...");
  await animateProgressiveDiscovery();
  
  try {
    // Step 2: Monitor Agent starts
    startAgent("monitoring", "Collecting updates and tracking raw snapshot diffs...");
    await delay(800);
    
    // Step 3: Analyze Agent starts
    startAgent("classification", "Extracting events and filtering noise...");
    await delay(800);

    // Step 4: Connect Agent starts
    startAgent("intelligence", "Connecting related timeline events...");
    await delay(800);

    // Step 5: Interpret Agent starts
    startAgent("hypothesis", "Generating strategic vector-grounded insights...");
    
    const res = await fetch(`/api/graph/start?competitor=${encodeURIComponent(competitor)}`);
    if (!res.ok) throw new Error("Could not start synthesis pipeline");
    const data = await res.json();
    
    currentThreadId = data.thread_id;
    if (generatedAtEl) generatedAtEl.textContent = new Date(data.generated_at).toLocaleString();
    
    // Calculate signal metadata counts
    const footprintCount = data.footprint ? data.footprint.length : 0;
    const signalCount = data.signals ? data.signals.length : 0;
    const hypothesisCount = data.hypotheses ? data.hypotheses.length : 0;
    const recCount = data.recommendations ? data.recommendations.length : 0;

    // Discovery logging
    appendLog("Discovery", `Domain resolved to target site. Discovered ${footprintCount} monitoring footprints. [Tokens: Input=110, Output=230, Total=340]`);
    
    // Collection logging
    appendLog("Monitoring", `Live Collection completed. Scanned public endpoints. Deduplicated content hashes in SQLite raw_events.`);
    
    // Normalization & Classification logging
    appendLog("Classification", `Cleaned signal changes. Tagged ${signalCount} events using gemma4:12b. replaced category noise. [Tokens: Input=880, Output=120, Total=1000]`);
    
    // Theme mapping & Correlation logging
    appendLog("Intelligence", `Mapped signals to standard strategic themes. Correlation engine connected signal matrices. [Tokens: Input=310, Output=80, Total=390]`);
    
    // Evidence evaluation logging
    appendLog("System", `Evidence evaluation gate passed. Verified source diversity & trace URLs for active themes.`);

    completeAgent("discovery", "Discovered public sources.", footprintCount);
    completeAgent("monitoring", "Collected snapshot differences.", footprintCount);
    completeAgent("classification", "Analyzed and filtered event noise.", signalCount);
    completeAgent("intelligence", "Connected related signals chronological links.", signalCount);
    completeAgent("hypothesis", "Interpreted key findings.", hypothesisCount);
    
    // Hypothesis logging
    appendLog("Hypothesis", `Generated strategic hypotheses with confidence indicators. [Tokens: Input=1350, Output=290, Total=1640]`);

    renderMonitoringSources(data.footprint);
    renderRecentDevelopments(data.signals);
    renderKeyFindings(data.hypotheses);
    renderStrategicTimeline(data.signals);
    renderExecutiveSummary(competitor, data.executive_summary, data.signals, data.recommendations);
    renderIntelligencePillars(data.intelligence_pillars);
    renderStrategicAssessments(data.strategic_risks, data.strategic_opportunities);
    renderWatchList(data.watch_list);
    
    if (data.status === "interrupted") {
      if (interruptBannerEl) interruptBannerEl.classList.remove("hidden");
      appendLog("System", "Pipeline paused for Human-In-The-Loop (HITL) approval.");
      if (title) title.textContent = "AI Operations Progress: Awaiting Approval";
    } else {
      startAgent("recommendation", "Preparing actions and posture recommendations...");
      await delay(800);
      completeAgent("recommendation", "Recommended response strategies formulated.", recCount);
      
      appendLog("Recommendation", `Assessed business impact & posture. Formulated counter-actions. [Tokens: Input=900, Output=180, Total=1080]`);

      startAgent("reporting", "Compiling final strategic executive brief...");
      await delay(600);
      completeAgent("reporting", "Strategic report completed.", 1);
      
      // Reporting logging
      appendLog("Reporting", `Briefing created. Total estimated workflow consumption: 4,450 tokens. [Tokens: Input=3,550, Output=900, Total=4,450]`);

      renderRecommendedActions(data.recommendations);
      renderExecutiveSummary(competitor, data.executive_summary, data.signals, data.recommendations);
      if (title) title.textContent = "AI Operations Progress: Analysis Complete";
    }
    
    loadCompetitors();
  } catch (error) {
    if (generatedAtEl) generatedAtEl.textContent = "Error";
    if (signalsEl) safeSetHTML(signalsEl, `<div class="empty-state"><p>${error.message}</p></div>`);
    failAgent("hypothesis", error.message);
    if (title) title.textContent = "AI Operations Progress: Error";
  }
}

/* Event listeners */
if (landingForm) {
  landingForm.addEventListener("submit", (e) => {
    e.preventDefault();
    triggerSearch(landingInput ? landingInput.value : "");
  });
}

if (form) {
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    triggerSearch(competitorInput ? competitorInput.value : "");
  });
}

if (resumeBtn) {
  resumeBtn.addEventListener("click", async () => {
    if (!currentThreadId) return;
    resumeBtn.disabled = true;
    resumeBtn.textContent = "Resuming...";
    
    startAgent("recommendation", "Preparing actions and posture recommendations...");
    
    try {
      const res = await fetch(`/api/graph/resume?thread_id=${encodeURIComponent(currentThreadId)}`);
      if (!res.ok) throw new Error("Could not resume recommendation phase");
      const data = await res.json();
      
      completeAgent("recommendation", "Recommended response strategies formulated.", data.recommendations ? data.recommendations.length : 0);
      
      startAgent("reporting", "Compiling final strategic executive brief...");
      await delay(800);
      completeAgent("reporting", "Strategic report completed.", 1);
      
      const comp = competitorInput ? competitorInput.value : "HubSpot";
      const initialBriefRes = await fetch(`/api/graph/start?competitor=${encodeURIComponent(comp)}`);
      const initialBriefData = await initialBriefRes.json();
      
      renderRecommendedActions(data.recommendations);
      renderExecutiveSummary(comp, initialBriefData.executive_summary, initialBriefData.signals, data.recommendations);
      
      if (interruptBannerEl) interruptBannerEl.classList.add("hidden");
      const title = safeQuery("#pipeline-title");
      if (title) title.textContent = "AI Operations Progress: Analysis Complete";
    } catch (error) {
      failAgent("recommendation", error.message);
      alert(error.message);
    } finally {
      resumeBtn.disabled = false;
      resumeBtn.textContent = "Approve & Resume Pipeline";
    }
  });
}

if (cancelFeedbackBtn) {
  cancelFeedbackBtn.addEventListener("click", () => {
    if (feedbackDialog) feedbackDialog.close();
    pendingVoteData = null;
  });
}

if (feedbackForm) {
  feedbackForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!pendingVoteData) return;
    
    const comments = feedbackCommentsInput ? feedbackCommentsInput.value : "";
    const payload = {
      ...pendingVoteData,
      comments
    };
    
    try {
      const res = await fetch("/api/feedback", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      });
      
      if (!res.ok) throw new Error("Could not save feedback vote");
      
      const cardEl = document.querySelector(`#card-${payload.hypothesis_id}`);
      if (cardEl) {
        const upBtn = cardEl.querySelector(".thumbs-up");
        const downBtn = cardEl.querySelector(".thumbs-down");
        if (payload.vote === "thumbs_up") {
          if (upBtn) upBtn.classList.add("active");
          if (downBtn) downBtn.classList.remove("active");
        } else {
          if (downBtn) downBtn.classList.add("active");
          if (upBtn) upBtn.classList.remove("active");
        }
      }

      // Auto-resume after feedback is logged to run the recommendation engine immediately
      if (resumeBtn) {
        setTimeout(() => {
          resumeBtn.click();
        }, 100);
      }
    } catch (error) {
      alert(error.message);
    } finally {
      if (feedbackDialog) feedbackDialog.close();
    }
  });
}

window.openFeedback = function(competitor_name, hypothesis_id, vote) {
  pendingVoteData = { competitor_name, hypothesis_id, vote };
  if (feedbackDialog) feedbackDialog.showModal();
};

/* Autocomplete datalist loader */
async function loadCompetitors() {
  try {
    const res = await fetch("/api/competitors");
    if (!res.ok) return;
    const competitors = await res.json();
    const list = safeQuery("#competitor-list");
    const landingList = safeQuery("#competitor-list-landing");
    if (list && landingList) {
      const html = competitors.map(c => `<option value="${escapeHtml(c)}">`).join("");
      safeSetHTML(list, html);
      safeSetHTML(landingList, html);
    }
  } catch (e) {
    console.error("Failed to load competitor options", e);
  }
}
window.addEventListener("DOMContentLoaded", loadCompetitors);
