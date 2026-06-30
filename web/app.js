const form = document.querySelector("#run-form");
const competitorInput = document.querySelector("#competitor");
const signalsEl = document.querySelector("#signals");
const hypothesesEl = document.querySelector("#hypotheses");
const recommendationsEl = document.querySelector("#recommendations");
const signalCountEl = document.querySelector("#signal-count");
const generatedAtEl = document.querySelector("#generated-at");
const footprintsEl = document.querySelector("#footprints");
const footprintStatusEl = document.querySelector("#footprint-status");
const stepperEl = document.querySelector("#stepper");
const interruptBannerEl = document.querySelector("#interrupt-banner");
const resumeBtn = document.querySelector("#resume-btn");

const feedbackDialog = document.querySelector("#feedback-dialog");
const feedbackForm = document.querySelector("#feedback-form");
const feedbackCommentsInput = document.querySelector("#feedback-comments");
const cancelFeedbackBtn = document.querySelector("#modal-cancel");

let currentThreadId = null;
let pendingVoteData = null;

// Simulated delay helper for progressive discovery
const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

function renderFootprint(sources) {
  footprintsEl.innerHTML = sources
    .map((source) => `
      <article class="item">
        <a class="item-source-link" href="${source.url}" target="_blank">${source.url}</a>
        <div class="meta">
          <span class="pill">${source.source_type}</span>
          <span class="pill success">Confidence ${Math.round(source.confidence * 100)}%</span>
          <span class="pill">${source.status}</span>
          <span class="pill">${source.monitoring_priority} priority</span>
        </div>
      </article>
    `)
    .join("");
}

function renderSignals(signals) {
  signalCountEl.textContent = String(signals.length);
  signalsEl.innerHTML = signals
    .map((signal) => `
      <article class="item">
        <h3>${signal.category}</h3>
        <p>${signal.content_diff}</p>
        <a class="item-source-link" href="${signal.source_url}" target="_blank">${signal.source_url}</a>
        <div class="meta">
          <span class="pill">${signal.source_reliability} reliability</span>
          <span class="pill">impact ${Math.round(signal.impact_score * 100)}%</span>
          <span class="pill">${new Date(signal.timestamp).toLocaleDateString()}</span>
        </div>
      </article>
    `)
    .join("");
}

function renderHypotheses(hypotheses) {
  hypothesesEl.innerHTML = hypotheses
    .map((hypothesis) => {
      const isHighRisk = hypothesis.confidence_score >= 0.85;
      const warningPill = isHighRisk ? '<span class="pill high-threat">High Warning Score</span>' : '';
      return `
        <article class="item" id="card-${hypothesis.id}">
          <h3>${hypothesis.theme}</h3>
          <p>${hypothesis.summary}</p>
          <div class="meta">
            <span class="pill">Confidence <strong class="confidence">${Math.round(hypothesis.confidence_score * 100)}%</strong></span>
            <span class="pill">${hypothesis.time_horizon}</span>
            ${warningPill}
          </div>
          <div class="voting-actions">
            <button class="vote-btn thumbs-up" onclick="openFeedback('${hypothesis.competitor_name}', '${hypothesis.id}', 'thumbs_up')">
              👍 Approve
            </button>
            <button class="vote-btn thumbs-down" onclick="openFeedback('${hypothesis.competitor_name}', '${hypothesis.id}', 'thumbs_down')">
              👎 Reject
            </button>
          </div>
        </article>
      `;
    })
    .join("");
}

function renderRecommendations(recommendations) {
  const countEl = document.querySelector("#recommendation-count");
  if (countEl) countEl.textContent = String(recommendations.length);
  
  recommendationsEl.innerHTML = recommendations
    .map((recommendation) => `
      <article class="item">
        <h3>${recommendation.category}</h3>
        <p><strong>Action:</strong> ${recommendation.recommended_action}</p>
        <p><strong>Reasoning:</strong> ${recommendation.reasoning}</p>
        <div class="meta">
          <span class="pill">Priority <strong class="priority">${recommendation.priority}</strong></span>
          <span class="pill">Effort: ${recommendation.effort}</span>
          <span class="pill">${recommendation.strategic_posture}</span>
        </div>
      </article>
    `)
    .join("");
}

async function animateProgressiveDiscovery() {
  stepperEl.classList.remove("hidden");
  footprintStatusEl.textContent = "Running";
  
  const stepDns = document.querySelector("#step-dns");
  const stepT1 = document.querySelector("#step-t1");
  const stepT2 = document.querySelector("#step-t2");
  const stepT3 = document.querySelector("#step-t3");
  
  // Reset steps
  [stepDns, stepT1, stepT2, stepT3].forEach(el => {
    el.style.opacity = "0.4";
    el.querySelector(".step-check").textContent = "○";
  });
  
  stepDns.style.opacity = "1";
  await delay(600);
  stepDns.querySelector(".step-check").textContent = "✓";
  
  stepT1.style.opacity = "1";
  await delay(600);
  stepT1.querySelector(".step-check").textContent = "✓";
  
  stepT2.style.opacity = "1";
  await delay(600);
  stepT2.querySelector(".step-check").textContent = "✓";
  
  stepT3.style.opacity = "1";
  await delay(600);
  stepT3.querySelector(".step-check").textContent = "✓";
  
  footprintStatusEl.textContent = "Monitored";
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const competitor = competitorInput.value;
  generatedAtEl.textContent = "Running";
  interruptBannerEl.classList.add("hidden");
  recommendationsEl.innerHTML = "";
  
  await animateProgressiveDiscovery();
  
  try {
    const res = await fetch(`/api/graph/start?competitor=${encodeURIComponent(competitor)}`);
    if (!res.ok) throw new Error("Could not start synthesis pipeline");
    const data = await res.json();
    
    currentThreadId = data.thread_id;
    generatedAtEl.textContent = new Date(data.generated_at).toLocaleString();
    
    renderFootprint(data.footprint);
    renderSignals(data.signals);
    renderHypotheses(data.hypotheses);
    
    if (data.status === "interrupted") {
      interruptBannerEl.classList.remove("hidden");
    }
  } catch (error) {
    generatedAtEl.textContent = "Error";
    signalsEl.innerHTML = `<article class="item"><p>${error.message}</p></article>`;
  }
});

resumeBtn.addEventListener("click", async () => {
  if (!currentThreadId) return;
  resumeBtn.disabled = true;
  resumeBtn.textContent = "Resuming...";
  
  try {
    const res = await fetch(`/api/graph/resume?thread_id=${encodeURIComponent(currentThreadId)}`);
    if (!res.ok) throw new Error("Could not resume recommendation phase");
    const data = await res.json();
    
    renderRecommendations(data.recommendations);
    interruptBannerEl.classList.add("hidden");
  } catch (error) {
    alert(error.message);
  } finally {
    resumeBtn.disabled = false;
    resumeBtn.textContent = "Approve & Resume";
  }
});

// Feedback dialog triggers
window.openFeedback = function(competitor_name, hypothesis_id, vote) {
  pendingVoteData = { competitor_name, hypothesis_id, vote };
  feedbackCommentsInput.value = "";
  feedbackDialog.showModal();
};

cancelFeedbackBtn.addEventListener("click", () => {
  feedbackDialog.close();
  pendingVoteData = null;
});

feedbackForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!pendingVoteData) return;
  
  const comments = feedbackCommentsInput.value;
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
    
    // Update visual active state on card
    const cardEl = document.querySelector(`#card-${payload.hypothesis_id}`);
    if (cardEl) {
      const upBtn = cardEl.querySelector(".thumbs-up");
      const downBtn = cardEl.querySelector(".thumbs-down");
      if (payload.vote === "thumbs_up") {
        upBtn.classList.add("active");
        downBtn.classList.remove("active");
      } else {
        downBtn.classList.add("active");
        upBtn.classList.remove("active");
      }
    }
  } catch (error) {
    alert(error.message);
  } finally {
    feedbackDialog.close();
    pendingVoteData = null;
  }
});

// Run default onload
form.dispatchEvent(new Event("submit"));
