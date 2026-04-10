// background.js - 사이드패널 자동 열기
chrome.action.onClicked.addListener((tab) => {
  if (tab.url && (tab.url.includes('grok.com') || tab.url.includes('grok.x.ai'))) {
    chrome.sidePanel.open({ tabId: tab.id });
  } else {
    chrome.tabs.create({ url: "https://grok.com/imagine" });
  }
});

chrome.sidePanel.setPanelBehavior({ 
  openPanelOnActionClick: true 
});

console.log("Grok Bulk Background Service loaded - Side Panel Auto Open");
