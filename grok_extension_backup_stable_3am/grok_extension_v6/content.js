/**
 * Grok Bulk Premium V6 - Asset Name Support (Final Version)
 */

let isBatchRunning = false;
let batchQueue = [];
let currentIndex = 0;

const sendLog = (text) => chrome.runtime.sendMessage({ action: 'UI_LOG', text });

async function loadAsset(name) {
    if (!window.GrokAssets) return null;
    const dataUrl = await window.GrokAssets.getAsset(name);
    if (!dataUrl) {
        sendLog(`❌ 에셋 없음: ${name}`);
        return null;
    }
    const res = await fetch(dataUrl);
    const blob = await res.blob();
    return new File([blob], `${name}.png`, { type: 'image/png' });
}

async function processNextTask() {
    if (!isBatchRunning || currentIndex >= batchQueue.length) {
        if (isBatchRunning) sendLog('✅ 모든 배치 완료');
        isBatchRunning = false;
        return;
    }

    const task = batchQueue[currentIndex];
    sendLog(`🎬 [${currentIndex + 1}/${batchQueue.length}] 처리 중...`);

    try {
        const assetRegex = /@\[(.*?)\]/g;
        const assetMatches = [...task.prompt.matchAll(assetRegex)];
        const assetNames = assetMatches.map(m => m[1].trim());

        const filesToUpload = [];
        for (const name of assetNames) {
            const file = await loadAsset(name);
            if (file) filesToUpload.push(file);
        }

        const fileInput = document.querySelector('input[type="file"]') || 
                         document.querySelector('input[accept*="image"]');
        
        if (fileInput && filesToUpload.length > 0) {
            const dt = new DataTransfer();
            filesToUpload.forEach(file => dt.items.add(file));
            fileInput.files = dt.files;
            fileInput.dispatchEvent(new Event('change', { bubbles: true }));
            sendLog(`📦 ${filesToUpload.length}개 에셋 자동 업로드`);
            await new Promise(r => setTimeout(r, 4500));
        }

        const editor = document.querySelector('div.ProseMirror') || 
                       document.querySelector('div[role="textbox"]') ||
                       document.querySelector('textarea');
        
        if (editor) {
            editor.focus();
            document.execCommand('selectAll', false, null);
            document.execCommand('delete', false, null);
            document.execCommand('insertText', false, task.prompt);
            editor.dispatchEvent(new Event('input', { bubbles: true }));
            await new Promise(r => setTimeout(r, 1500));

            const submitBtn = document.querySelector('button[aria-label="제출"]') || 
                            document.querySelector('button[aria-label="Submit"]') ||
                            Array.from(document.querySelectorAll('button')).find(b => 
                                b.textContent.includes("Submit") || b.textContent.includes("제출")
                            );

            if (submitBtn) {
                submitBtn.click();
                sendLog(`🚀 Video 생성 요청 완료`);
                await new Promise(r => setTimeout(r, 90000)); // 90초 대기
            }
        }

        currentIndex++;
        processNextTask();

    } catch (err) {
        sendLog(`❌ 오류: ${err.message}`);
        isBatchRunning = false;
    }
}

chrome.runtime.onMessage.addListener((msg) => {
    if (msg.action === 'START_BATCH') {
        isBatchRunning = true;
        currentIndex = 0;
        batchQueue = msg.prompts.map(p => ({ prompt: p }));
        sendLog('🔥 배치 가동 시작 (에셋 지원 버전)');
        processNextTask();
    }
    if (msg.action === 'STOP_BATCH') {
        isBatchRunning = false;
        sendLog('⏹ 중지됨');
    }
});
