(function() {
  if (window.__NB2_AUTO_LOADED__) {
    if (window.__NB2_MESSAGE_HANDLER__) {
      chrome.runtime.onMessage.removeListener(window.__NB2_MESSAGE_HANDLER__);
    }
  }
  window.__NB2_AUTO_LOADED__ = true;

  let prompts = [];
  let settings = {};
  let currentIndex = 0;
  let state = 'idle';
  let automationRunning = false;

  let knownTileIds = new Set();
  let failedPrompts = [];
  let submittedOrder = [];

  let activeGenerations = [];
  const MAX_SLOTS = 5;

  let slotResolvers = [];
  function notifySlotFree() {
    const resolvers = slotResolvers.splice(0);
    resolvers.forEach(r => r());
  }
  function waitForSlotFree() {
    if (activeGenerations.length < MAX_SLOTS) return Promise.resolve();
    return new Promise(resolve => { slotResolvers.push(resolve); });
  }

  let watcherRunning = false;

  function fullReset() {
    state = 'stopped';
    automationRunning = false;
    prompts = [];
    settings = {};
    currentIndex = 0;
    knownTileIds = new Set();
    failedPrompts = [];
    submittedOrder = [];
    activeGenerations = [];
    slotResolvers.forEach(r => r());
    slotResolvers = [];
    watcherRunning = false;
    setTimeout(() => { state = 'idle'; }, 100);
  }

  // ========== 유틸리티 ==========
  function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }
  function humanDelay(minMs, maxMs) { return sleep(minMs + Math.random() * (maxMs - minMs)); }
  function typingDelay() {
    if (Math.random() < 0.2) return sleep(150 + Math.random() * 150);
    return sleep(30 + Math.random() * 90);
  }

  function sendLog(text) {
    const now = new Date();
    const timeStr = now.getHours().toString().padStart(2, '0') + ':' + 
                    now.getMinutes().toString().padStart(2, '0') + ':' + 
                    now.getSeconds().toString().padStart(2, '0');
    const stampedText = `[${timeStr}] ${text}`;
    console.log('[NB2]', stampedText);
    try { chrome.runtime.sendMessage({ type: 'log', text: stampedText }); } catch(e) {}
  }
  function sendProgress(current, total) {
    try { chrome.runtime.sendMessage({ type: 'progress', current, total }); } catch(e) {}
  }
  function sendDone() {
    try { 
      chrome.runtime.sendMessage({ 
        type: 'done',
        submittedOrder: submittedOrder.map(s => ({
          index: s.index,
          id: s.item.id,
          tileIds: s.tileIds
        }))
      }); 
    } catch(e) {}
  }
  function isVisible(el) {
    const rect = el.getBoundingClientRect();
    return rect.width > 0 && rect.height > 0 && !el.disabled;
  }

  // ========== 에디터 ==========
  function getEditor() {
    return document.querySelector('div[data-slate-editor="true"]')
        || document.querySelector('div[contenteditable="true"]');
  }
  function getEditorType() {
    if (document.querySelector('div[data-slate-editor="true"]')) return 'slate';
    return 'unknown';
  }

  // ========== Generate 버튼 ==========
  function getGenerateButton() {
    const allBtns = [...document.querySelectorAll('button')];
    for (const btn of allBtns) {
      const icon = btn.querySelector('i');
      if (icon && icon.textContent.trim() === 'arrow_forward' && isVisible(btn)) return btn;
    }
    for (const btn of allBtns) {
      const label = (btn.getAttribute('aria-label') || '').toLowerCase();
      if (['send', 'submit', 'generate', '전송', '보내기'].some(k => label.includes(k))) {
        if (isVisible(btn)) return btn;
      }
    }
    for (let i = allBtns.length - 1; i >= 0; i--) {
      const btn = allBtns[i];
      const rect = btn.getBoundingClientRect();
      if (rect.top > window.innerHeight * 0.75 && rect.width < 50 && rect.height < 50) {
        if (btn.querySelector('i') && isVisible(btn)) return btn;
      }
    }
    return null;
  }

  // ========== 에디터 초기화 ==========
  async function clearEditor() {
    const editor = getEditor();
    if (!editor) return;
    editor.focus();
    editor.click();
    await humanDelay(50, 150);
    editor.dispatchEvent(new KeyboardEvent('keydown', {
      key: 'a', code: 'KeyA', keyCode: 65, which: 65,
      ctrlKey: true, bubbles: true, cancelable: true
    }));
    await sleep(150);
    editor.dispatchEvent(new KeyboardEvent('keyup', {
      key: 'a', code: 'KeyA', keyCode: 65, which: 65,
      ctrlKey: true, bubbles: true
    }));
    await humanDelay(100, 250);
    editor.dispatchEvent(new KeyboardEvent('keydown', {
      key: 'Backspace', code: 'Backspace', keyCode: 8, which: 8,
      bubbles: true, cancelable: true
    }));
    await sleep(150);
    editor.dispatchEvent(new KeyboardEvent('keyup', {
      key: 'Backspace', code: 'Backspace', keyCode: 8, which: 8,
      bubbles: true
    }));
    await humanDelay(50, 150);
    sendLog('🧹 에디터 초기화 완료');
  }

  // ========== 텍스트 입력 (Slate) ==========
  async function insertTextSlate(text) {
    const editor = getEditor();
    if (!editor) return false;
    editor.focus();
    editor.click();
    await humanDelay(150, 300);
    for (let i = 0; i < text.length; i++) {
      if (state === 'stopped') return false;
      const char = text[i];
      editor.dispatchEvent(new KeyboardEvent('keydown', {
        key: char, code: `Key${char.toUpperCase()}`,
        keyCode: char.charCodeAt(0), which: char.charCodeAt(0),
        bubbles: true, cancelable: true
      }));
      editor.dispatchEvent(new InputEvent('beforeinput', {
        inputType: 'insertText', data: char,
        bubbles: true, cancelable: true, composed: true
      }));
      editor.dispatchEvent(new InputEvent('input', {
        inputType: 'insertText', data: char,
        bubbles: true, composed: true
      }));
      editor.dispatchEvent(new KeyboardEvent('keyup', {
        key: char, code: `Key${char.toUpperCase()}`,
        keyCode: char.charCodeAt(0), which: char.charCodeAt(0),
        bubbles: true
      }));
      await sleep(10 + Math.random() * 15);
    }
    await humanDelay(200, 500);
    return true;
  }

  // ========== TileId 감지 ==========
  function getCurrentTileIds() {
    const ids = new Set();
    document.querySelectorAll('div[data-tile-id]').forEach(div => {
      ids.add(div.dataset.tileId);
    });
    return ids;
  }

  function getTileInfo(targetTileId) {
    const divs = document.querySelectorAll(`div[data-tile-id="${targetTileId}"]`);
    for (const div of divs) {
      if (div.children.length <= 1) {
        const img = div.querySelector('img');
        const pct = div.textContent.match(/(\d{1,3})%/);
        return {
          found: true,
          hasImg: !!(img && img.src.includes('labs.google')),
          imgSrc: img && img.src.includes('labs.google') ? img.src : null,
          pct: pct ? parseInt(pct[1]) : -1
        };
      }
    }
    if (divs.length > 0) {
      const div = divs[0];
      const img = div.querySelector('img');
      const pct = div.textContent.match(/(\d{1,3})%/);
      return {
        found: true,
        hasImg: !!(img && img.src.includes('labs.google')),
        imgSrc: img && img.src.includes('labs.google') ? img.src : null,
        pct: pct ? parseInt(pct[1]) : -1
      };
    }
    return { found: false };
  }

  function findNewTileIds() {
    const current = getCurrentTileIds();
    const assignedIds = new Set();
    for (const gen of activeGenerations) {
      for (const tid of gen.tileIds) {
        assignedIds.add(tid);
      }
    }
    const newIds = [];
    for (const id of current) {
      if (!knownTileIds.has(id) && !assignedIds.has(id)) {
        newIds.push(id);
      }
    }
    return newIds;
  }

  // ========== 다운로드 ==========
  async function downloadImages(imageSrcs, promptItem, index) {
    const folderName = settings.folderName || 'NB2_output';
    const ts = settings.sessionTimestamp || new Date().toISOString().replace(/[-:T]/g,'').slice(0,14);
    const subFolder = `${folderName}_${ts}`; // 1단계 폴더 (Chrome 호환성)
    for (let i = 0; i < imageSrcs.length; i++) {
      const src = imageSrcs[i];
      const paddedIndex = String(index + 1).padStart(3, '0');
      const paddedImg = imageSrcs.length > 1 ? `_${i + 1}` : '';
      const safeMemo = (promptItem.memo || promptItem.id).replace(/[^a-zA-Z0-9_가-힣]/g, '_');
      const filename = `${subFolder}/${paddedIndex}_${safeMemo}${paddedImg}.jpg`;
      
      try {
        chrome.runtime.sendMessage({
          type: 'download',
          url: src,
          filename: filename
        });
      } catch(e) {}
      await sleep(500); // 다운로드 사이 간격
    }
  }

  // ========== 에셋 관련 (v17 범용 DOM 감지) ==========
  function findAssetSearchInput() {
    const inputs = document.querySelectorAll('input');
    for (const inp of inputs) {
      if (inp.placeholder && inp.placeholder.includes('애셋') && isVisible(inp)) return inp;
      if (inp.placeholder && inp.placeholder.includes('검색') && isVisible(inp)) return inp;
      if (inp.placeholder && inp.placeholder.toLowerCase().includes('search') && isVisible(inp)) return inp;
    }
    return null;
  }

  async function waitForAssetPopup() {
    for (let i = 0; i < 20; i++) {
      if (findAssetSearchInput()) return true;
      const dialog = document.querySelector('[role="dialog"]');
      if (dialog) {
        const imgs = dialog.querySelectorAll('img');
        if (imgs.length > 0) return true;
      }
      await sleep(300);
    }
    return false;
  }

  async function searchAndSelectAsset(assetName) {
    const searchInput = findAssetSearchInput();
    if (!searchInput) { sendLog('⚠️ 에셋 검색창 못 찾음'); return false; }

    searchInput.focus();
    searchInput.click();
    await humanDelay(50, 150);

    searchInput.value = '';
    searchInput.dispatchEvent(new Event('input', { bubbles: true }));
    await humanDelay(50, 150);

    for (const char of assetName) {
      searchInput.value += char;
      searchInput.dispatchEvent(new Event('input', { bubbles: true }));
      await typingDelay();
    }

    sendLog(`🔍 "${assetName}" 검색 중...`);
    await humanDelay(50, 150);

    for (let retry = 0; retry < 10; retry++) {
      const dialog = document.querySelector('[role="dialog"]');
      const scope = dialog || document;
      const candidates = [];
      scope.querySelectorAll('div').forEach(div => {
        const style = getComputedStyle(div);
        if (style.cursor !== 'pointer') return;
        const img = div.querySelector('img');
        if (!img) return;
        const rect = div.getBoundingClientRect();
        if (rect.width < 50 || rect.height < 50 || rect.width > 400) return;

        let name = '';
        div.querySelectorAll('div').forEach(child => {
          if (child.children.length === 0 && child.textContent.trim().length > 0) {
            if (!name) name = child.textContent.trim();
          }
        });
        if (!name) name = div.textContent.replace(/\s+/g, ' ').trim().substring(0, 50);
        candidates.push({ el: div, name });
      });

      if (candidates.length > 0) {
        for (const c of candidates) {
          if (c.name === assetName) {
            sendLog(`📌 에셋 정확 매칭: "${c.name}"`);
            await humanDelay(200, 500);
            c.el.click();
            await humanDelay(500, 800);
            return true;
          }
        }
        for (const c of candidates) {
          if (c.name.includes(assetName) || assetName.includes(c.name)) {
            sendLog(`📌 에셋 부분 매칭: "${c.name}"`);
            await humanDelay(200, 500);
            c.el.click();
            await humanDelay(500, 800);
            return true;
          }
        }
        if (candidates.length <= 3) {
          sendLog(`📌 첫 검색 결과 선택: "${candidates[0].name}"`);
          await humanDelay(200, 500);
          candidates[0].el.click();
          await humanDelay(500, 800);
          return true;
        }
      }
      await sleep(500);
    }
    sendLog(`⚠️ "${assetName}" 선택 실패`);
    return false;
  }

  async function waitForPopupClose() {
    for (let i = 0; i < 15; i++) {
      if (!findAssetSearchInput()) return;
      const dialog = document.querySelector('[role="dialog"]');
      if (!dialog || dialog.getBoundingClientRect().width === 0) return;
      await sleep(300);
    }
  }

  // ========== 프롬프트 파싱 & 입력 ==========
  function parsePromptTokens(promptText) {
    const tokens = [];
    const regex = /@\[([^\]]+)\]/g;
    let last = 0, m;
    while ((m = regex.exec(promptText)) !== null) {
      if (m.index > last) tokens.push({ type: 'text', value: promptText.slice(last, m.index) });
      tokens.push({ type: 'ref', value: m[1] });
      last = regex.lastIndex;
    }
    if (last < promptText.length) tokens.push({ type: 'text', value: promptText.slice(last) });
    return tokens;
  }

  async function inputPrompt(promptText) {
    const editor = getEditor();
    if (!editor) { sendLog('❌ 에디터 없음'); return false; }
    if (!promptText.includes('@[')) {
      return await insertTextSlate(promptText);
    }
    const tokens = parsePromptTokens(promptText);
    sendLog(`📝 토큰 ${tokens.length}개`);
    for (let t = 0; t < tokens.length; t++) {
      const token = tokens[t];
      if (state === 'stopped') return false;
      while (state === 'paused') await sleep(500);
      if (token.type === 'ref') {
        await humanDelay(50, 150);
        await insertTextSlate('@');
        sendLog(`🔗 @ 입력 → "${token.value}" 검색`);
        await humanDelay(300, 600);
        const opened = await waitForAssetPopup();
        if (!opened) { sendLog('⚠️ 에셋 팝업 안 열림'); continue; }
        const selected = await searchAndSelectAsset(token.value);
        if (selected) sendLog(`✅ "${token.value}" 선택 완료`);
        await waitForPopupClose();
        await humanDelay(200, 500);
        editor.focus();
        editor.click();
        await humanDelay(50, 150);
      } else {
        await insertTextSlate(token.value);
        await humanDelay(50, 150);
      }
    }
    return true;
  }

  // [Update] 캐릭터 에셋 '실사 초상화' 및 '얼굴 전용' 최적화 (v4.4.0)
  function applyFaceOnlyConstraint(prompt) {
    const p = prompt.toLowerCase();
    // 캐릭터/레퍼런스/초상화 관련 키워드가 포함될 때 트리거
    if (p.includes('reference sheet') || p.includes('character') || p.includes('portrait')) {
      sendLog('🎭 캐릭터/초상화 감지: 실사 최적화 및 얼굴 전용(Realism & Face Only) 모드 적용');
      
      let newPrompt = prompt;
      
      // 1. 만화/그림/레퍼런스 문구 제거 및 실사 문구로 교체
      newPrompt = newPrompt.replace(/Create a character reference sheet of/gi, 'Cinematic photorealistic portrait of');
      newPrompt = newPrompt.replace(/Create a character reference sheet/gi, 'Cinematic photorealistic portrait');
      newPrompt = newPrompt.replace(/character reference sheet/gi, 'photorealistic portrait');
      newPrompt = newPrompt.replace(/character reference/gi, 'portrait');
      
      // 2. 뷰 관련 표현들을 '얼굴 클로즈업'으로 교체
      newPrompt = newPrompt.replace(/\b8\s*views\s*\(Full\s*body\s*and\s*Head\)/gi, 'Closeup face only, frontal view');
      newPrompt = newPrompt.replace(/\b8\s*views\b/gi, 'Closeup face only, frontal view');
      newPrompt = newPrompt.replace(/\bFull\s*body\s*and\s*Head\b/gi, 'Closeup face only, frontal view');
      newPrompt = newPrompt.replace(/\b4\s*views\b/gi, 'Full photorealistic scene');
      
      // 3. 실사 품질 및 제외 키워드 강화
      const styleSuffix = ', highly detailed skin texture, cinematic lighting, 8k resolution, masterpiece, professional photography --no drawing, illustration, sketch, cartoon, composite, multiple views';
      
      if (!newPrompt.toLowerCase().includes('portrait')) {
        newPrompt = 'Cinematic photorealistic portrait of ' + newPrompt;
      }
      
      if (!newPrompt.toLowerCase().includes('face only')) {
        newPrompt += ', closeup face only, frontal view';
      }
      
      newPrompt += styleSuffix;
      
      return newPrompt;
    }
    return prompt;
  }

  async function prepareAndVerifyPrompt(item) {
    const editor = getEditor();
    if (!editor) { sendLog('❌ 에디터 없음'); return false; }
    editor.focus();
    editor.click();
    await humanDelay(300, 600);
    try {
      await clearEditor();
      await humanDelay(300, 600);
    } catch(e) {
      sendLog(`⚠️ 클리어 에러: ${e.message}`);
    }

    // 캐릭터 에셋에 "얼굴만" 제약 적용
    const finalPrompt = applyFaceOnlyConstraint(item.prompt);

    sendLog(`📝 [${item.id}] ${finalPrompt.substring(0, 50)}...`);
    try {
      const inputOk = await inputPrompt(finalPrompt);
      if (!inputOk) { sendLog(`❌ [${item.id}] 입력 실패`); return false; }
    } catch(e) {
      sendLog(`❌ [${item.id}] 입력 에러: ${e.message}`);
      return false;
    }
    await humanDelay(50, 150);
    const currentText = (editor.textContent || '').replace('무엇을 만들고 싶으신가요?', '').trim();
    return currentText.length > 0;
  }

  // ========== 메인 루프 (3초 간격 Push 모드) ==========
  async function runAutomation() {
    if (automationRunning) {
      sendLog('⚠️ 이미 자동화가 실행 중입니다');
      return;
    }
    automationRunning = true;
    state = 'running';
    const total = prompts.length;
    failedPrompts = [];
    submittedOrder = [];

    if (!settings.sessionTimestamp) {
      settings.sessionTimestamp = new Date().toISOString().replace(/[-:T]/g,'').slice(0,14);
    }

    sendLog(`🚀 3초 간격 Push 모드 시작: 총 ${total}개 프롬프트`);

    const editor = getEditor();
    if (!editor) {
      sendLog('❌ 에디터를 찾을 수 없습니다!');
      automationRunning = false;
      state = 'idle';
      sendDone();
      return;
    }

    // [Mod] 타일 감시 워커 불필요하므로 시작하지 않음
    // startCompletionWatcher();

    for (let i = 0; i < total; i++) {
      if (state === 'stopped') break;
      while (state === 'paused') await sleep(500);

      const item = prompts[i];
      currentIndex = i;
      sendProgress(i + 1, total);
      sendLog(`\n━━━ [${item.id}] Push 준비 (${i+1}/${total}) ━━━`);

      // 1. 프롬프트 입력 및 확인
      const inputOk = await prepareAndVerifyPrompt(item);
      if (!inputOk) {
        sendLog(`❌ [${item.id}] 입력 실패 - 다음으로 건너뜁니다`);
        failedPrompts.push(item.id);
        continue;
      }

      await humanDelay(50, 150);

      // 2. Generate 버튼 클릭
      const btn = getGenerateButton();
      if (!btn) {
        sendLog(`❌ [${item.id}] Generate 버튼 없음`);
        failedPrompts.push(item.id);
        continue;
      }

      btn.click();
      sendLog(`🎨 [${item.id}] Push 완료!`);

      let newIds = [];
      for (let t = 0; t < 6; t++) {
        await sleep(500);
        newIds = findNewTileIds();
        if (newIds.length > 0) break;
      }
      newIds.forEach(id => knownTileIds.add(id));
      submittedOrder.push({ index: i, item, tileIds: newIds });

      // 3. 3초 대기 (사용자 요청 사항)
      if (i < total - 1) {
        sendLog(`🕒 3초 대기 중...`);
        await sleep(3000);
      }
    }

    sendLog(`\n✅ 모든 프롬프트 Push가 완료되었습니다.`);
    automationRunning = false;
    state = 'idle';
    sendDone();
  }
  function stopCompletionWatcher() {
    watcherRunning = false;
    activeGenerations = [];
    notifySlotFree();
  }

  // ========== 메시지 수신 ==========

  function messageHandler(msg, sender, sendResponse) {
    if (msg.action === 'ping') {
      sendResponse({ ok: true }); return true;
    }
    if (msg.action === 'downloadAll') {
      const order = msg.order || [];
      sendLog('📥 자동 다운로드 시작...');
      (async () => {
        for (const entry of order) {
          const srcs = [];
          for (const tileId of entry.tileIds) {
            const info = getTileInfo(tileId);
            if (info.hasImg && info.imgSrc) srcs.push(info.imgSrc);
          }
          if (srcs.length > 0) {
            sendLog(`💾 [${entry.id}] ${srcs.length}개 이미지 다운로드 시작`);
            await downloadImages(srcs, { id: entry.id }, entry.index);
          } else {
            let found = false;
            for (let retry = 0; retry < 3; retry++) {
              sendLog(`⏳ [${entry.id}] 이미지 없음 — 5초 후 재시도 (${retry+1}/3)...`);
              await sleep(5000);
              const retrySrcs = [];
              for (const tileId of entry.tileIds) {
                const info = getTileInfo(tileId);
                if (info.hasImg && info.imgSrc) retrySrcs.push(info.imgSrc);
              }
              if (retrySrcs.length > 0) {
                sendLog(`✅ [${entry.id}] 재시도 성공 — ${retrySrcs.length}개 다운로드`);
                await downloadImages(retrySrcs, { id: entry.id }, entry.index);
                found = true;
                break;
              }
            }
            if (!found) sendLog(`❌ [${entry.id}] 3회 재시도 실패 — 건너뜀`);
          }
        }
        sendLog('✅ 전체 다운로드 완료!');
        try { chrome.runtime.sendMessage({ type: 'downloadDone' }); } catch(e) {}
      })();
      sendResponse({ ok: true }); return true;
    }
    if (msg.action === 'start') {
      if (automationRunning) {
        sendResponse({ ok: false, error: '이미 실행 중입니다.' }); return true;
      }
      prompts = msg.prompts || [];
      settings = msg.settings || {};
      currentIndex = 0;
      state = 'idle';
      runAutomation();
      sendResponse({ ok: true }); return true;
    }
    if (msg.action === 'pause') {
      state = 'paused'; sendLog('⏸️ 일시정지');
      sendResponse({ ok: true }); return true;
    }
    if (msg.action === 'resume') {
      state = 'running'; sendLog('▶️ 재개');
      sendResponse({ ok: true }); return true;
    }
    if (msg.action === 'stop') {
      state = 'stopped'; automationRunning = false;
      stopCompletionWatcher(); sendLog('🛑 정지');
      sendResponse({ ok: true }); return true;
    }
    if (msg.action === 'reset') {
      stopCompletionWatcher(); fullReset();
      sendLog('🔄 상태 완전 초기화');
      sendResponse({ ok: true }); return true;
    }
    if (msg.action === 'debug') {
      sendResponse({
        ok: true,
        editorType: getEditorType(),
        generateBtn: !!getGenerateButton(),
        knownTiles: knownTileIds.size,
        currentTiles: getCurrentTileIds().size,
        activeSlots: activeGenerations.length,
        activeInfo: activeGenerations.map(g => ({
          id: g.item.id,
          tiles: g.tileIds.length,
          resolved: g.resolved,
          states: Object.values(g.tileStates).map(s => s.settled ? (s.success ? '✅' : '❌') : '⏳')
        })),
        automationRunning,
        state
      });
      return true;
    }
    sendResponse({ ok: false }); return true;
  }

  window.__NB2_MESSAGE_HANDLER__ = messageHandler;
  chrome.runtime.onMessage.addListener(messageHandler);

  console.log('[NB2 Auto] Content script loaded (v17 - Universal DOM Detection)');
  sendLog('✅ NB2 Auto v17 로드 (범용 DOM 감지)');
})();
