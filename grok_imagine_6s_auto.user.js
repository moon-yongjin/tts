// ==UserScript==
// @name         Grok Imagine Private 6s Video Auto (너만 써)
// @namespace    https://grok.com
// @version      1.0
// @description  이미지→6초 비디오 자동 + 세로/가로 자동 + 즉시 다운로드 (개인용)
// @author       Grok (너만)
// @match        https://grok.x.ai/*
// @match        https://grok.com/*
// @grant        GM_download
// @grant        GM_notification
// @run-at       document-start
// ==/UserScript==

(function() {
    'use strict';
    
    let autoEnabled = true;
    
    // 컨트롤 패널 추가
    function addPanel() {
        if (document.getElementById('grok-private-panel')) return;
        const panel = document.createElement('div');
        panel.id = 'grok-private-panel';
        panel.style.cssText = 'position:fixed;bottom:20px;right:20px;background:#111;color:#0f0;padding:15px;border-radius:12px;z-index:99999;box-shadow:0 0 30px #0f0;font-family:sans-serif;min-width:220px;';
        panel.innerHTML = `
            <div style="margin-bottom:10px;font-weight:bold;">🚀 Grok 6s Video Auto (개인용)</div>
            <button id="toggle-btn" style="background:#0f0;color:#000;padding:8px 15px;border:none;border-radius:8px;cursor:pointer;margin-right:8px;">ON</button>
            <button id="force-6s" style="background:#333;color:#fff;padding:8px 12px;border:none;border-radius:8px;cursor:pointer;">6초 강제 + 자동 비율</button>
        `;
        document.body.appendChild(panel);
        
        document.getElementById('toggle-btn').addEventListener('click', function() {
            autoEnabled = !autoEnabled;
            this.textContent = autoEnabled ? 'ON' : 'OFF';
            this.style.background = autoEnabled ? '#0f0' : '#f00';
        });
        
        document.getElementById('force-6s').addEventListener('click', forceSettings);
    }
    
    // 6초 + 자동 세로/가로 설정
    function forceSettings() {
        // 프롬프트에 6초 자동 추가
        const promptArea = document.querySelector('textarea, [contenteditable="true"], input[type="text"]');
        if (promptArea && !promptArea.value.includes('6 seconds')) {
            promptArea.value += (promptArea.value ? ' ' : '') + 'exactly 6 seconds long, smooth motion';
            promptArea.dispatchEvent(new Event('input', {bubbles:true}));
        }
        
        // 업로드된 이미지 비율 보고 자동 aspect 클릭
        const previewImg = document.querySelector('img[src*="imagine"], img[alt*="preview"], .media-preview img');
        if (previewImg && previewImg.complete) {
            const ratio = previewImg.naturalWidth / previewImg.naturalHeight;
            const buttons = document.querySelectorAll('button');
            buttons.forEach(btn => {
                const text = (btn.textContent || '').toLowerCase();
                if (ratio > 1.1 && (text.includes('landscape') || text.includes('16:9') || text.includes('가로'))) {
                    btn.click();
                } else if (ratio <= 1.1 && (text.includes('portrait') || text.includes('9:16') || text.includes('세로'))) {
                    btn.click();
                }
            });
        }
        
        GM_notification('6초 + 자동 세로/가로 설정 완료!');
    }
    
    // 비디오 생성되면 즉시 자동 다운로드
    const observer = new MutationObserver(() => {
        if (!autoEnabled) return;
        
        document.querySelectorAll('video').forEach(video => {
            if (video.src && video.src.includes('.mp4') && !video.dataset.downloaded) {
                video.dataset.downloaded = 'true';
                
                const filename = `grok_6s_${new Date().toISOString().slice(0,19).replace(/:/g,'-')}.mp4`;
                
                GM_download({
                    url: video.src,
                    name: filename,
                    saveAs: false
                });
                
                GM_notification({
                    title: '✅ 자동 다운로드 완료',
                    text: filename,
                    timeout: 3000
                });
            }
        });
    });
    
    observer.observe(document.body, { childList: true, subtree: true });
    
    // 페이지 로드되면 패널 띄우기
    window.addEventListener('load', () => {
        addPanel();
        setTimeout(addPanel, 2000); // Imagine 페이지 늦게 로드될 때 대비
    });
    
    console.log('%c✅ Grok Private 6s Video Auto 로드 완료 (너만 써)', 'color:#0f0;font-size:14px');
})();
