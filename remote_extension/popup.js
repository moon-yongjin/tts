document.getElementById('connectBtn').addEventListener('click', async () => {
    const url = document.getElementById('serverUrl').value;
    if (!url) return alert('Server URL을 입력해주세요!');

    // 설정을 저장하고 Content Script에 전달
    await chrome.storage.local.set({ serverUrl: url });

    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    chrome.tabs.sendMessage(tab.id, { action: 'CONNECT_SERVER', url: url });

    document.getElementById('status').innerText = 'Connection Requested...';
});

// 초기 설정 로드
chrome.storage.local.get(['serverUrl'], (res) => {
    if (res.serverUrl) document.getElementById('serverUrl').value = res.serverUrl;
});
