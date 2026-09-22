chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "scanSelectionWithMeter",
    title: "Scan selection with Suspicious-o-meter",
    contexts: ["selection"]
  });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === "scanSelectionWithMeter" && info.selectionText) {
    chrome.storage.local.set({ pendingScanText: info.selectionText }, () => {
      if (chrome.action.openPopup) {
        chrome.action.openPopup();
      }
    });
  }
});

chrome.runtime.onMessage.addListener((message, sender) => {
  if (message.action === "updateBadge" && sender.tab) {
    const score = message.score;
    const color = score >= 50 ? "#dc2626" : score >= 20 ? "#eab308" : "#16a34a";

    chrome.action.setBadgeText({ text: String(score), tabId: sender.tab.id });
    chrome.action.setBadgeBackgroundColor({ color, tabId: sender.tab.id });
  }
});