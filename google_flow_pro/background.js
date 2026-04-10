chrome.action.onClicked.addListener((tab) => {
  chrome.sidePanel.open({ tabId: tab.id });
});

chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true });

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.action === 'download' || msg.type === 'download') {
    chrome.downloads.download({
      url: msg.url,
      filename: msg.filename,
      conflictAction: 'uniquify'
    }, (downloadId) => {
      sendResponse({ ok: true, downloadId });
    });
    return true;
  }

});

chrome.runtime.onInstalled.addListener(() => {
  console.log('[NB2 Auto] Extension installed');
  chrome.storage.local.set({ state: 'idle' });
});
