const $ = id => document.getElementById(id);
const logArea = $('log');

function log(msg) {
    const time = new Date().toLocaleTimeString();
    logArea.textContent += `[${time}] ${msg}\n`;
    logArea.scrollTop = logArea.scrollHeight;
}

// ========== 에셋 등록 ==========
$('btnRegister').addEventListener('click', async () => {
    const fileInput = $('assetFile');
    const nameInput = $('assetName').value.trim();
    
    if (!fileInput.files.length) {
        log('❌ 에셋 파일을 선택하세요');
        return;
    }
    if (!nameInput) {
        log('❌ 에셋 이름을 입력하세요 (예: Mother_Face)');
        return;
    }

    const file = fileInput.files[0];
    const reader = new FileReader();
    reader.onload = async (e) => {
        await window.GrokAssets.saveAsset(nameInput, e.target.result);
        log(`✅ 에셋 등록 완료: ${nameInput}`);
        fileInput.value = '';
        $('assetName').value = '';
    };
    reader.readAsDataURL(file);
});

// ========== 배치 실행 ==========
$('btnStart').addEventListener('click', async () => {
    const text = $('prompts').value;
    const prompts = text.split('\n').map(p => p.trim()).filter(p => p.length > 0);

    if (prompts.length === 0) {
        log('❌ 프롬프트를 입력하세요.');
        return;
    }

    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (!tabs || tabs.length === 0) return;
        chrome.tabs.sendMessage(tabs[0].id, {
            action: 'START_BATCH',
            prompts: prompts
        });
        $('status').textContent = '● 가동 중...';
        $('status').style.color = '#0f0';
        log(`🚀 배치 시작: ${prompts.length}개`);
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
    if (msg.action === 'UI_LOG') log(msg.text);
});
