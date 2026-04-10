/**
 * Grok Bulk Premium V6 - Pure Extension Content Script
 */

let isBatchRunning = false;
let batchQueue = [];
let currentIndex = 0;

const sendLog = (text) => chrome.runtime.sendMessage({ action: 'UI_LOG', text });

async function processNextTask() {
    if (!isBatchRunning || currentIndex >= batchQueue.length) {
        if (isBatchRunning) sendLog('✅ 모든 배치가 완료되었습니다.');
        isBatchRunning = false;
        return;
    }

    const task = batchQueue[currentIndex];
    sendLog(`🎬 파트 [${currentIndex + 1}/${batchQueue.length}] 처리 시작...`);

    try {
        // 1. 이미지 로드 및 주입 (DataURL -> Blob -> File)
        const res = await fetch(task.image.dataUrl);
        const blob = await res.blob();
        const file = new File([blob], task.image.name, { type: task.image.type });

        const fileInput = document.querySelector('input[type="file"]') || document.querySelector('input[accept*="image"]');
        if (fileInput) {
            const dt = new DataTransfer();
            dt.items.add(file);
            fileInput.files = dt.files;
            fileInput.dispatchEvent(new Event('change', { bubbles: true }));
            await new Promise(r => setTimeout(r, 4500)); // 업로드 대기
        }

        // 2. 비디오 모드 자동 클릭 (있을 때만)
        const videoBtns = Array.from(document.querySelectorAll('button')).filter(b => b.textContent.includes('Video') || b.textContent.includes('비디오'));
        if (videoBtns.length > 0) {
            videoBtns[0].click();
            await new Promise(r => setTimeout(r, 1000));
        }

        // 3. 프롬프트 타이핑 & 전송
        const editor = document.querySelector('div.ProseMirror') || 
                       document.querySelector('div[role="textbox"]') ||
                       document.querySelector('textarea[aria-label*="Grok"]');
        
        if (editor) {
            editor.focus();
            document.execCommand('selectAll', false, null);
            document.execCommand('delete', false, null);
            document.execCommand('insertText', false, task.prompt);
            editor.dispatchEvent(new Event('input', { bubbles: true }));
            await new Promise(r => setTimeout(r, 1500));

            const submitBtn = document.querySelector('button[aria-label="제출"]') || 
                            document.querySelector('button[aria-label="Submit"]') ||
                            Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes("Submit") || b.textContent.includes("제출"));

            if (submitBtn) {
                submitBtn.click();
                sendLog(`🚀 전송됨: ${task.image.name}`);
                
                // 4. 생성 대기 루프 (비디오가 나타날 때까지 또는 타임아웃 2분)
                sendLog('⏳ 생성 중... (최대 120초 대기)');
                const startTime = Date.now();
                let generated = false;
                
                while (Date.now() - startTime < 120000) {
                    const video = document.querySelector('video');
                    // 만약 새로운 비디오가 나타나면 (Grok은 SPA이므로 기존 비디오가 있을 수 있음, 주의 필요)
                    // 여기서는 간단하게 80초 고정 대기 후 다음으로 넘어가는 방식이 3시 버전의 특징일 수 있음
                    await new Promise(r => setTimeout(r, 10000));
                    sendLog(`... 대기 중 (${Math.floor((Date.now() - startTime)/1000)}초)`);
                    
                    // Grok은 전송 후 입력창이 비워짐 -> 다음 작업을 위해 리셋
                    if (Date.now() - startTime > 90000) { break; } // 90초면 보통 완료됨
                }
            }
        }

        // 5. 다음 파트로 이동
        currentIndex++;
        
        // 6. SPA 라우팅 초기화 (Grok Imagine 초기화)
        const resetBtn = Array.from(document.querySelectorAll('a[href*="/imagine"]')).find(el => el.textContent.includes("이미지") || el.textContent.includes("Imagine")) ||
                         document.querySelector('nav a[href="/imagine"]');
        if (resetBtn) {
            resetBtn.click();
            await new Promise(r => setTimeout(r, 3000));
        }
        
        processNextTask();

    } catch (err) {
        sendLog(`❌ 처리 오류: ${err.message}`);
        isBatchRunning = false;
    }
}

chrome.runtime.onMessage.addListener((msg) => {
    if (msg.action === 'START_BATCH') {
        isBatchRunning = true;
        currentIndex = 0;
        batchQueue = msg.prompts.map((p, i) => ({
            prompt: p,
            image: msg.images[i % msg.images.length]
        }));
        sendLog('🔥 배치 가동 시작!');
        processNextTask();
    }
    if (msg.action === 'STOP_BATCH') {
        isBatchRunning = false;
        sendLog('⏹ 배치 중단 요청됨');
    }
});
