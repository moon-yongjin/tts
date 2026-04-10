chrome.action.onClicked.addListener((tab) => {
  chrome.sidePanel.open({ tabId: tab.id });
});

chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true });

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.action === 'download' || msg.type === 'download') {
    const url = msg.url;
    const filename = msg.filename;
    if (!url || !filename) {
      sendResponse({ ok: false, error: 'URL 또는 파일명 누락' });
      return true;
    }
    chrome.downloads.download({
      url: url,
      filename: filename,
      saveAs: false,
      conflictAction: 'uniquify'
    }, (downloadId) => {
      if (chrome.runtime.lastError) {
        sendResponse({ ok: false, error: chrome.runtime.lastError.message });
      } else {
        sendResponse({ ok: true, downloadId });
      }
    });
    return true;
  }
});

chrome.runtime.onInstalled.addListener(() => {
  console.log('[NB2 Auto] Extension installed');
  chrome.storage.local.set({ state: 'idle' });
});
