chrome.runtime.onMessage.addListener((message, sender) => {
  if (message.action === "updateBadge" && sender.tab) {
    const score = message.score;
    const color = score >= 50 ? "#dc2626" : score >= 20 ? "#eab308" : "#16a34a";

    chrome.action.setBadgeText({ text: String(score), tabId: sender.tab.id });
    chrome.action.setBadgeBackgroundColor({ color, tabId: sender.tab.id });
  }
});