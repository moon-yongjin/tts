/**
 * Grok Bulk Premium V6 - Bridge Mode Popup
 */

const $ = id => document.getElementById(id);

$('btnStart').addEventListener('click', () => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (tabs[0]) {
            chrome.tabs.sendMessage(tabs[0].id, { action: 'START_FULL_AUTO' });
            $('status').textContent = '가동 중 (브릿지 연결)';
            $('status').style.color = '#0f0';
        }
    });
});

$('btnStop').addEventListener('click', () => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (tabs[0]) {
            chrome.tabs.sendMessage(tabs[0].id, { action: 'STOP_AUTO' });
            $('status').textContent = '대기 중';
            $('status').style.color = '#ff0';
        }
    });
});
