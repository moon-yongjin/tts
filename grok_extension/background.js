// background.js - Grok Bulk 안정화 버전
console.log("✅ Grok Bulk Background Service Worker Loaded", new Date().toISOString());

chrome.runtime.onInstalled.addListener(() => {
    console.log("✅ Grok Bulk 확장 설치/업데이트 완료");
});

chrome.runtime.onStartup.addListener(() => {
    console.log("✅ Chrome 시작 - Background 재로드");
});

// Grok 페이지 로드될 때 content.js 강제 주입은 manifest.json에서 처리하므로 삭제 (중복 방지)


chrome.action.onClicked.addListener((tab) => {
    if (tab.url && (tab.url.includes('grok.com') || tab.url.includes('grok.x.ai'))) {
        chrome.sidePanel.open({ tabId: tab.id });
    } else {
        chrome.tabs.create({ url: "https://grok.com/imagine" });
    }
});

chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true });

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
    if (msg.action === 'DOWNLOAD_VIDEOS') {
        // 병렬 다운로드: 각 파일을 동시에 시작 (순차 await 제거)
        Promise.all(
            msg.videos.map(({ url, filename }) =>
                new Promise(resolve =>
                    chrome.downloads.download({ url, filename, conflictAction: 'uniquify' }, resolve)
                )
            )
        );
        return true;
    }
});
