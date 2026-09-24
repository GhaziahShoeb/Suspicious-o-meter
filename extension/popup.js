// Tab switching
document.querySelectorAll(".tab-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(btn.dataset.tab + "-tab").classList.add("active");
  });
});

function setScoreColor(score) {
  const box = document.getElementById("score-box");
  if (score >= 50) box.style.background = "#fde2e2";
  else if (score >= 20) box.style.background = "#fff4cc";
  else box.style.background = "#e2f7e2";
}

// Fills a tab with "label value" lines using textContent only, so any value
// (even one containing HTML) is displayed as plain text and never executed.
function renderRows(elementId, rows) {
  const container = document.getElementById(elementId);
  container.textContent = "";
  rows.forEach(([label, value]) => {
    const line = document.createElement("div");
    const bold = document.createElement("b");
    bold.textContent = label + " ";
    line.appendChild(bold);
    line.appendChild(document.createTextNode(String(value)));
    container.appendChild(line);
  });
}

function renderResults(data) {
  // Error responses (rate limit, internal error) have no breakdown to show
  if (!data || !data.breakdown) {
    showError((data && data.error) || "Scan failed. Please try again.");
    return;
  }

  document.getElementById("loading").style.display = "none";
  document.getElementById("results").style.display = "block";

  document.getElementById("score-number").textContent = data.suspicion_score;
  document.getElementById("verdict-label").textContent = data.verdict;
  setScoreColor(data.suspicion_score);
  document.getElementById("status").textContent = "Company: " + (data.company_name || "Unknown");

  const b = data.breakdown;

  renderRows("llm-tab", [
    ["Verdict:", b.llm_verdict],
    ["Score contribution:", b.llm_score],
  ]);

  renderRows("reddit-tab", [
    ["Results found:", b.reddit_results_found],
    ["Score contribution:", b.reddit_score],
  ]);

  renderRows("legitimacy-tab", [
    ["Domain age (days):", b.domain_age_days ?? "Unknown"],
    ["Found online:", b.company_found_online ? "Yes" : "No"],
    ["Score contribution:", b.legitimacy_score],
  ]);
}

function showError(message) {
  document.getElementById("loading").style.display = "none";
  document.getElementById("status").textContent = message;
}

// Ask the content script (running on the current tab) for the extracted posting text
chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
  chrome.tabs.sendMessage(tabs[0].id, { action: "getPostingText" }, (response) => {
    if (chrome.runtime.lastError || !response || !response.text) {
      showError("No job posting detected on this page.");
      return;
    }

    // Call your backend's /scan endpoint
    fetch("https://suspicious-o-meter.onrender.com/scan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: tabs[0].url, text: response.text })
    })
      .then(res => res.json())
      .then(renderResults)
      .catch(() => showError("Could not reach backend. Is it running?"));
  });
});