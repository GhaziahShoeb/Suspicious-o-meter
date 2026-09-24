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

function renderResults(data) {
  document.getElementById("loading").style.display = "none";
  document.getElementById("results").style.display = "block";
  document.getElementById("status").textContent = "Scan complete";

  document.getElementById("score-number").textContent = data.suspicion_score;
  document.getElementById("verdict-label").textContent = data.verdict;
  setScoreColor(data.suspicion_score);
  document.getElementById("status").textContent = "Company: " + (data.company_name || "Unknown");

  const b = data.breakdown;
  document.getElementById("llm-tab").innerHTML =
    `<b>Verdict:</b> ${b.llm_verdict}<br><b>Score contribution:</b> ${b.llm_score}`;

  document.getElementById("reddit-tab").innerHTML =
    `<b>Results found:</b> ${b.reddit_results_found}<br><b>Score contribution:</b> ${b.reddit_score}`;

  document.getElementById("legitimacy-tab").innerHTML =
    `<b>Domain age (days):</b> ${b.domain_age_days ?? "Unknown"}<br>` +
    `<b>Found online:</b> ${b.company_found_online ? "Yes" : "No"}<br>` +
    `<b>Score contribution:</b> ${b.legitimacy_score}`;
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

    // Call your backend's /scan endpoint (must be running locally for now)
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