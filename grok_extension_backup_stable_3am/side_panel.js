/**
 * Grok Bulk Premium V6 - Pure Extension Side Panel
 */

const $ = id => document.getElementById(id);
const logArea = $('log');

function log(msg) {
    const time = new Date().toLocaleTimeString();
    logArea.textContent += `[${time}] ${msg}\n`;
    logArea.scrollTop = logArea.scrollHeight;
}

$('btnStart').addEventListener('click', async () => {
    const text = $('prompts').value;
    const prompts = text.split('\n').map(p => p.trim()).filter(p => p.length > 0);

    if (prompts.length === 0) {
        log('❌ 에러: 프롬프트를 입력하세요.');
        return;
    }

    const folderInput = $('image-folder');
    let imageFiles = [];
    if (folderInput && folderInput.files.length > 0) {
        imageFiles = Array.from(folderInput.files)
            .filter(f => f.type.startsWith('image/'))
            .sort((a, b) => a.name.localeCompare(b.name));
    }

    if (imageFiles.length === 0) {
        log('❌ 에러: 이미지 폴더를 선택하세요.');
        return;
    }

    const readAsDataURL = (file) => new Promise(res => {
        const reader = new FileReader();
        reader.onload = e => res({ name: file.name, type: file.type, dataUrl: e.target.result });
        reader.readAsDataURL(file);
    });

    log('⏳ 이미지 읽는 중...');
    const imagesData = await Promise.all(imageFiles.slice(0, prompts.length).map(readAsDataURL));

    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (!tabs || tabs.length === 0) return;
        const activeTab = tabs[0];

        log(`🚀 배치 시작: ${prompts.length}개 프롬프트 (${imagesData.length}개 이미지)`);
        chrome.tabs.sendMessage(activeTab.id, {
            action: 'START_BATCH',
            prompts: prompts,
            images: imagesData
        });
        $('status').textContent = '● 가동 중...';
        $('status').style.color = '#0f0';
    });
});

$('btnStop').addEventListener('click', () => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (!tabs || tabs.length === 0) return;
        chrome.tabs.sendMessage(tabs[0].id, { action: 'STOP_BATCH' });
        log('⏹ 중지 요청됨');
        $('status').textContent = '● 중지됨';
        $('status').style.color = '#f00';
    });
});

chrome.runtime.onMessage.addListener((msg) => {
    if (msg.action === 'UI_LOG') {
        log(msg.text);
    }
});
