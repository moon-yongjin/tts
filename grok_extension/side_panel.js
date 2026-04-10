const $ = id => document.getElementById(id);

function log(msg) {
    const logEl = $('log');
    if (!logEl) return;
    const time = new Date().toLocaleTimeString('ko-KR', { hour12: false });
    logEl.textContent += `[${time}] ${msg}\n`;
    logEl.scrollTop = logEl.scrollHeight;
}

function setStatus(text, color = '#0f0') {
    const st = $('status');
    if (st) {
        st.textContent = text;
        st.style.color = color;
    }
}

// 시작 버튼
$('btnStart').addEventListener('click', () => {
    const input = $('imageFiles');
    if (!input.files || input.files.length === 0) {
        log('❌ 파일을 선택하세요');
        return;
    }

    log(`${input.files.length}개 파일 선택됨`);

    // 실제 content.js로 전송
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (!tabs || !tabs[0]) {
            log('❌ Grok 탭을 찾을 수 없습니다.');
            return;
        }

        // 파일을 DataURL로 변환해서 보내기
        const files = Array.from(input.files);
        const promises = files.map(file => {
            return new Promise(resolve => {
                const reader = new FileReader();
                reader.onload = () => resolve({
                    name: file.name,
                    type: file.type,
                    dataUrl: reader.result
                });
                reader.readAsDataURL(file);
            });
        });

        Promise.all(promises).then(allImages => {
            log(`📸 ${allImages.length}장 로드 완료 → 배치 처리 시작`);
            const BATCH_SIZE = 15;  // 기존 세팅(15장)으로 복구
            const promptValue = $('promptText').value.trim() || "Animate this image with smooth natural motion";

            (async () => {
                for (let i = 0; i < allImages.length; i += BATCH_SIZE) {
                    const batch = allImages.slice(i, i + BATCH_SIZE);
                    const batchNumber = Math.floor(i / BATCH_SIZE) + 1;
                    const isLastBatch = (i + BATCH_SIZE >= allImages.length);

                    try {
                        const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
                        if (!tabs || !tabs[0]) {
                            log('❌ Grok 탭을 찾을 수 없습니다.');
                            return;
                        }

                        // content script 살아있는지 확인 (PING)
                        await chrome.tabs.sendMessage(tabs[0].id, { action: 'PING' }).catch(() => {});

                        await chrome.tabs.sendMessage(tabs[0].id, {
                            action: 'ADD_IMAGES_BATCH',
                            images: batch,
                            prompt: promptValue,
                            batchNumber: batchNumber,
                            totalBatches: Math.ceil(allImages.length / BATCH_SIZE),
                            isLastBatch: isLastBatch
                        });

                        log(`✅ 배치 [${batchNumber}/${Math.ceil(allImages.length / BATCH_SIZE)}] 전송 성공 (${batch.length}장)`);

                    } catch (err) {
                        log(`❌ 배치 [${batchNumber}] 전송 실패: ${err.message}`);
                        log('💡 Grok 탭을 Ctrl + Shift + R (강력 새로고침) 후 다시 시작하세요.');
                    }

                    await new Promise(r => setTimeout(r, 1200)); // 배치 간 여유
                }
                setStatus('● 가동 중...', '#0f0');
            })();
        });
    });
});

// 중지 버튼
$('btnStop').addEventListener('click', () => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (tabs[0]) chrome.tabs.sendMessage(tabs[0].id, { action: 'STOP_BATCH' });
    });
    log('⏹ 중지 요청');
    setStatus('● 중지됨', '#f00');
});

log('✅ Grok Bulk Premium v11 로드 완료');

// content.js로부터 로그를 수신하여 표시
chrome.runtime.onMessage.addListener((msg) => {
    if (msg.action === 'UI_LOG') {
        log(msg.text);
        // 낚아채기 수량 업데이트
        const match = msg.text.match(/낚아채기 성공.*\((\d+)개 확보\)/);
        if (match) {
            const el = $('captureStatus');
            if (el) el.textContent = `📡 낚아챈 영상: ${match[1]}개`;
        }
    }
});

// 다운로드 버튼
$('btnDownload').addEventListener('click', () => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (!tabs || !tabs[0]) {
            log('❌ Grok 탭을 찾을 수 없습니다.');
            return;
        }
        chrome.tabs.sendMessage(tabs[0].id, { action: 'DOWNLOAD_ALL' });
        log('⬇️ 다운로드 요청 전송...');
    });
});

