// Tab switching
document.querySelectorAll(".tab-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
    btn.classList.add("active");
    const target = document.getElementById(btn.dataset.tab + "-tab");
    if (target) target.classList.add("active");
  });
});

function setScoreColor(score) {
  const box = document.getElementById("score-box");
  if (score >= 50) {
    box.style.background = "#fef2f2";
    box.style.borderColor = "#f87171";
    box.style.color = "#991b1b";
  } else if (score >= 20) {
    box.style.background = "#fffbeb";
    box.style.borderColor = "#fcd34d";
    box.style.color = "#92400e";
  } else {
    box.style.background = "#f0fdf4";
    box.style.borderColor = "#86efac";
    box.style.color = "#166534";
  }
}

function createMetricRow(label, value) {
  const row = document.createElement("div");
  row.className = "metric-row";

  const lbl = document.createElement("span");
  lbl.className = "metric-label";
  lbl.textContent = label;

  const val = document.createElement("span");
  val.textContent = String(value);

  row.appendChild(lbl);
  row.appendChild(val);
  return row;
}

function clearElement(element) {
  while (element.firstChild) {
    element.removeChild(element.firstChild);
  }
}

function renderResults(data) {
  document.getElementById("loading").style.display = "none";
  document.getElementById("results").style.display = "block";
  document.getElementById("status").textContent = "Company: " + (data.company_name || "Unknown");

  document.getElementById("score-number").textContent = data.suspicion_score ?? "--";
  document.getElementById("verdict-label").textContent = data.verdict ?? "--";
  setScoreColor(data.suspicion_score || 0);

  const b = data.breakdown || {};

  // Reasoning card
  const reasonElem = document.getElementById("reasoning-text");
  if (b.reasoning) {
    reasonElem.textContent = "💡 " + b.reasoning;
    reasonElem.style.display = "block";
  } else {
    reasonElem.style.display = "none";
  }

  // Red Flags Tab
  const flagsTab = document.getElementById("flags-tab");
  clearElement(flagsTab);
  const flags = b.red_flags || [];
  if (flags.length === 0) {
    const emptyNotice = document.createElement("div");
    emptyNotice.textContent = "✓ No structural deception red flags detected in text.";
    emptyNotice.style.color = "#16a34a";
    flagsTab.appendChild(emptyNotice);
  } else {
    flags.forEach(flag => {
      const item = document.createElement("div");
      item.className = "flag-item";
      item.textContent = "⚠️ " + flag;
      flagsTab.appendChild(item);
    });
  }

  // LLM Tab
  const llmTab = document.getElementById("llm-tab");
  clearElement(llmTab);
  llmTab.appendChild(createMetricRow("LLM Verdict", b.llm_verdict || "UNKNOWN"));
  llmTab.appendChild(createMetricRow("Score Contribution", b.llm_score ?? 0));
  llmTab.appendChild(createMetricRow("Recruiter Email Mismatch", b.email_mismatch_detected ? "Yes (+15)" : "No"));
  if (b.keyword_matches && b.keyword_matches.length > 0) {
    llmTab.appendChild(createMetricRow("Flagged Keywords", b.keyword_matches.join(", ")));
  }

  // Reddit Tab
  const redditTab = document.getElementById("reddit-tab");
  clearElement(redditTab);
  redditTab.appendChild(createMetricRow("Evidence Posts Found", b.reddit_results_found ?? 0));
  redditTab.appendChild(createMetricRow("Score Contribution", b.reddit_score ?? 0));

  // Legitimacy Tab
  const legTab = document.getElementById("legitimacy-tab");
  clearElement(legTab);
  legTab.appendChild(createMetricRow("Domain Age (Days)", b.domain_age_days ?? "Unknown"));
  legTab.appendChild(createMetricRow("Found in Business Registry", b.company_found_online ? "Yes" : "No"));
  legTab.appendChild(createMetricRow("Suspicious TLD (.xyz/.top)", b.suspicious_tld_detected ? "Yes (+10)" : "No"));
  legTab.appendChild(createMetricRow("Score Contribution", b.legitimacy_score ?? 0));
}

function showError(message) {
  document.getElementById("loading").style.display = "none";
  document.getElementById("results").style.display = "none";
  document.getElementById("status").textContent = message;
}

function performScanWithText(text, url = "") {
  document.getElementById("status").textContent = "Analyzing with backend...";
  document.getElementById("loading").style.display = "block";
  document.getElementById("results").style.display = "none";

  fetch("http://127.0.0.1:8000/scan", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url: url, text: text })
  })
    .then(res => {
      if (res.status === 429) {
        throw new Error("Rate limit exceeded (10 scans/min). Please wait a moment.");
      }
      if (!res.ok) {
        throw new Error(`Server returned status ${res.status}`);
      }
      return res.json();
    })
    .then(data => {
      if (data.verdict === "ERROR") {
        throw new Error(data.error || "Analysis failed.");
      }
      renderResults(data);
    })
    .catch(err => {
      showError(err.message || "Could not reach backend. Is it running on port 8000?");
    });
}

function triggerScan() {
  // Check if context menu saved a pending selection scan first
  chrome.storage.local.get("pendingScanText", (res) => {
    if (res && res.pendingScanText) {
      const text = res.pendingScanText;
      chrome.storage.local.remove("pendingScanText");
      performScanWithText(text, "Selection context menu scan");
      return;
    }

    document.getElementById("status").textContent = "Extracting posting...";
    document.getElementById("loading").style.display = "block";
    document.getElementById("results").style.display = "none";

    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (!tabs || !tabs[0]) {
        showError("No active tab found.");
        return;
      }

      chrome.tabs.sendMessage(tabs[0].id, { action: "getPostingText" }, (response) => {
        if (chrome.runtime.lastError || !response || !response.text) {
          showError("No job posting or email detected on this page.");
          return;
        }
        performScanWithText(response.text, tabs[0].url || "");
      });
    });
  });
}

const scanBtn = document.getElementById("scan-btn");
if (scanBtn) {
  scanBtn.addEventListener("click", triggerScan);
}

const feedbackBtn = document.getElementById("feedback-btn");
if (feedbackBtn) {
  feedbackBtn.addEventListener("click", () => {
    const toast = document.getElementById("toast");
    if (toast) {
      toast.style.display = "inline";
      setTimeout(() => { toast.style.display = "none"; }, 2500);
    }
  });
}

triggerScan();