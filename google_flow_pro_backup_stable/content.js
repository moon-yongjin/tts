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
    try { chrome.runtime.sendMessage({ type: 'done' }); } catch(e) {}
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
    await humanDelay(200, 400);
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
    await humanDelay(200, 400);
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
  async function downloadImages(imageSrcs, promptItem) {
    const folderName = settings.folderName || 'NB2_output';
    const nameMode = settings.nameMode || 'id';
    for (let i = 0; i < imageSrcs.length; i++) {
      if (state === 'stopped') return;
      const src = imageSrcs[i];
      let filename;
      if (nameMode === 'memo' && promptItem.memo && promptItem.memo.trim()) {
        const baseName = promptItem.memo.trim();
        filename = imageSrcs.length === 1
          ? `${folderName}/${baseName}.png`
          : `${folderName}/${baseName}_${i + 1}.png`;
      } else {
        filename = `${folderName}/${promptItem.id}_${i + 1}.png`;
      }
      try {
        chrome.runtime.sendMessage({ type: 'download', url: src, filename });
        sendLog(`💾 저장: ${filename}`);
        await humanDelay(300, 600);
      } catch (e) {
        sendLog(`❌ 다운로드 실패: ${e.message}`);
      }
    }
  }

  // ========== 완료 감시 워커 ==========
  async function startCompletionWatcher() {
    if (watcherRunning) return;
    watcherRunning = true;
    sendLog('👁 완료 감시 워커 시작');

    const batchCount = settings.batchCount || 2;

    while (watcherRunning) {
      if (state === 'stopped') {
        activeGenerations = [];
        notifySlotFree();
        watcherRunning = false;
        return;
      }

      for (let i = activeGenerations.length - 1; i >= 0; i--) {
        const gen = activeGenerations[i];
        if (gen.resolved) continue;

        if (gen.tileIds.length < batchCount) {
          const newIds = findNewTileIds();
          for (const nid of newIds) {
            if (gen.tileIds.length >= batchCount) break;
            gen.tileIds.push(nid);
            gen.tileStates[nid] = { hadPct: false, settled: false, success: false, imgSrc: null };
            sendLog(`🔖 [${gen.item.id}] 타일 감지: ${nid.substring(6, 22)} (${gen.tileIds.length}/${batchCount})`);
          }
        }

        if (gen.tileIds.length === 0) {
          if (Date.now() - gen.requestTime > (settings.genTimeout || 120) * 1000) {
            sendLog(`⏰ [${gen.item.id}] 타일 미감지 타임아웃 → 실패`);
            gen.resolved = true;
            failedPrompts.push(gen.item.id);
            activeGenerations.splice(i, 1);
            notifySlotFree();
          }
          continue;
        }

        let allSettled = true;
        let minPct = 999;

        for (const tid of gen.tileIds) {
          const ts = gen.tileStates[tid];
          if (ts.settled) continue;

          const info = getTileInfo(tid);
          if (!info.found) {
            allSettled = false;
            continue;
          }

          if (info.pct >= 0) {
            ts.hadPct = true;
            if (info.pct < minPct) minPct = info.pct;
          }

          if (info.hasImg && info.pct < 0) {
            ts.settled = true;
            ts.success = true;
            ts.imgSrc = info.imgSrc;
            sendLog(`✅ [${gen.item.id}] 배치 완성: ${tid.substring(6, 22)}`);
            continue;
          }

          if (ts.hadPct && info.pct < 0 && !info.hasImg) {
            ts.settled = true;
            ts.success = false;
            sendLog(`❌ [${gen.item.id}] 배치 실패: ${tid.substring(6, 22)}`);
            continue;
          }

          allSettled = false;
        }

        if (gen.tileIds.length < batchCount) {
          allSettled = false;
        }

        if (allSettled) {
          const successImgs = [];
          for (const tid of gen.tileIds) {
            const ts = gen.tileStates[tid];
            if (ts.success && ts.imgSrc) {
              successImgs.push(ts.imgSrc);
            }
            knownTileIds.add(tid);
          }

          if (successImgs.length > 0) {
            sendLog(`🖼 [${gen.item.id}] ${successImgs.length}/${gen.tileIds.length}장 성공`);
            await downloadImages(successImgs, gen.item);
            sendLog(`✅ [${gen.item.id}] 다운로드 완료`);
          } else {
            sendLog(`❌ [${gen.item.id}] 전체 실패`);
            failedPrompts.push(gen.item.id);
          }

          gen.resolved = true;
          activeGenerations.splice(i, 1);
          notifySlotFree();
          continue;
        }

        if (!gen._lastLog || Date.now() - gen._lastLog > 5000) {
          if (minPct < 999) {
            sendLog(`🔄 [${gen.item.id}] ${minPct}% (타일 ${gen.tileIds.length}/${batchCount})`);
          }
          gen._lastLog = Date.now();
        }

        if (Date.now() - gen.requestTime > (settings.genTimeout || 120) * 1000) {
          sendLog(`⏰ [${gen.item.id}] 타임아웃 → 있는 것만 저장`);

          const successImgs = [];
          for (const tid of gen.tileIds) {
            const ts = gen.tileStates[tid];
            if (ts.success && ts.imgSrc) {
              successImgs.push(ts.imgSrc);
            } else if (!ts.settled) {
              const info = getTileInfo(tid);
              if (info.hasImg && info.imgSrc) {
                successImgs.push(info.imgSrc);
              }
            }
            knownTileIds.add(tid);
          }

          if (successImgs.length > 0) {
            sendLog(`⚠️ [${gen.item.id}] ${successImgs.length}장만 저장`);
            await downloadImages(successImgs, gen.item);
          } else {
            sendLog(`❌ [${gen.item.id}] 타임아웃 실패`);
            failedPrompts.push(gen.item.id);
          }

          gen.resolved = true;
          activeGenerations.splice(i, 1);
          notifySlotFree();
        }
      }

      await sleep(1000);
    }
  }

  function stopCompletionWatcher() {
    watcherRunning = false;
    activeGenerations = [];
    notifySlotFree();
  }

  // ========== 활성 생성의 최소 진행률 대기 ==========
  async function waitForActiveProgress(gen, targetPct, timeoutSec) {
    const maxWait = timeoutSec * 1000;
    const startTime = Date.now();
    let lastLog = '';

    while (Date.now() - startTime < maxWait) {
      if (state === 'stopped') return 'stopped';
      if (gen.resolved) return 'finished';

      let minPct = -1;

      for (const tid of gen.tileIds) {
        const info = getTileInfo(tid);
        if (info.found) {
          if (info.hasImg && info.pct < 0) {
            continue;
          }
          if (info.pct >= 0) {
            if (minPct < 0 || info.pct < minPct) minPct = info.pct;
          }
        }
      }

      if (minPct >= targetPct) {
        sendLog(`⚡ [${gen.item.id}] ${minPct}% ≥ ${targetPct}%`);
        return 'reached';
      }

      if (gen.tileIds.length === 0) {
        await sleep(500);
        continue;
      }

      if (minPct >= 0 && `${minPct}%` !== lastLog) {
        lastLog = `${minPct}%`;
      }

      await sleep(500);
    }

    sendLog(`⏰ [${gen.item.id}] ${targetPct}% 대기 타임아웃`);
    return 'timeout';
  }

  // ========== 에셋 관련 (v17 범용 DOM 감지) ==========
  function findAssetSearchInput() {
    const inputs = document.querySelectorAll('input');
    for (const inp of inputs) {
      if (inp.placeholder && inp.placeholder.includes('애셋') && isVisible(inp)) return inp;
      if (inp.placeholder && inp.placeholder.includes('검색') && isVisible(inp)) return inp;
      if (inp.placeholder && inp.placeholder.toLowerCase().includes('search') && isVisible(inp)) return inp;
    }
    for (const inp of inputs) {
      const r = inp.getBoundingClientRect();
      if (r.width > 100 && r.top > 200 && r.top < 500 && isVisible(inp)) return inp;
    }
    return null;
  }

  async function waitForAssetPopup() {
    for (let i = 0; i < 20; i++) {
      if (findAssetSearchInput()) return true;
      // 범용: role="dialog" 안에 이미지가 있으면 팝업 열린 것
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
    await humanDelay(200, 400);

    // 검색창 클리어
    searchInput.value = '';
    searchInput.dispatchEvent(new Event('input', { bubbles: true }));
    await humanDelay(200, 400);

    // 타이핑
    for (const char of assetName) {
      searchInput.value += char;
      searchInput.dispatchEvent(new Event('input', { bubbles: true }));
      await typingDelay();
    }

    sendLog(`🔍 "${assetName}" 검색 중...`);
    await humanDelay(1500, 2500);

    // 검색 결과 대기 & 선택 (최대 10회 재시도)
    for (let retry = 0; retry < 10; retry++) {

      // ===== 범용 감지: 에셋 팝업 내 클릭 가능한 이미지 아이템 =====
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

        // 텍스트 추출: 자식 중 텍스트만 가진 leaf div
        let name = '';
        div.querySelectorAll('div').forEach(child => {
          if (child.children.length === 0 && child.textContent.trim().length > 0) {
            if (!name) name = child.textContent.trim();
          }
        });
        if (!name) name = div.textContent.replace(/\s+/g, ' ').trim().substring(0, 50);

        candidates.push({ el: div, name, rect });
      });

      if (candidates.length > 0) {
        // 1차: 정확 매칭
        for (const c of candidates) {
          if (c.name === assetName) {
            sendLog(`📌 에셋 정확 매칭: "${c.name}"`);
            await humanDelay(200, 500);
            c.el.click();
            await humanDelay(500, 800);
            return true;
          }
        }

        // 2차: 부분 매칭
        for (const c of candidates) {
          if (c.name.includes(assetName) || assetName.includes(c.name)) {
            sendLog(`📌 에셋 부분 매칭: "${c.name}"`);
            await humanDelay(200, 500);
            c.el.click();
            await humanDelay(500, 800);
            return true;
          }
        }

        // 3차: 검색 결과 적으면 첫 번째
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
      // 검색창이 사라지거나, 다이얼로그가 닫히면 완료
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
        await humanDelay(500, 1000);
        await insertTextSlate('@');
        sendLog(`🔗 @ 입력 → "${token.value}" 검색`);
        await humanDelay(1500, 2500);
        const opened = await waitForAssetPopup();
        if (!opened) { sendLog('⚠️ 에셋 팝업 안 열림'); continue; }
        await humanDelay(500, 1000);
        const selected = await searchAndSelectAsset(token.value);
        if (selected) sendLog(`✅ "${token.value}" 선택 완료`);
        else sendLog(`⚠️ "${token.value}" 선택 실패`);
        await waitForPopupClose();
        await humanDelay(800, 1500);
        editor.focus();
        editor.click();
        await humanDelay(500, 1000);
      } else {
        await insertTextSlate(token.value);
        await humanDelay(200, 400);
      }
    }
    await humanDelay(300, 600);
    return true;
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
    sendLog(`📝 [${item.id}] "${item.prompt.substring(0, 50)}"`);
    try {
      const inputOk = await inputPrompt(item.prompt);
      if (!inputOk) { sendLog(`❌ [${item.id}] 입력 실패`); return false; }
    } catch(e) {
      sendLog(`❌ [${item.id}] 입력 에러: ${e.message}`);
      return false;
    }
    await humanDelay(500, 1000);
    const currentText = (editor.textContent || '').replace('무엇을 만들고 싶으신가요?', '').trim();
    sendLog(`📋 입력 확인: "${currentText.substring(0, 50)}"`);
    return currentText.length > 0;
  }

  // ========== 메인 루프 (v17 Slot Pipeline) ==========
  async function runAutomation() {
    if (automationRunning) {
      sendLog('⚠️ 이미 자동화가 실행 중입니다');
      return;
    }
    automationRunning = true;
    state = 'running';
    const total = prompts.length;
    failedPrompts = [];
    activeGenerations = [];

    const batchCount = settings.batchCount || 2;

    sendLog(`🚀 자동화 시작: ${total}개 프롬프트 (슬롯 파이프라인, 배치 ${batchCount})`);

    const editor = getEditor();
    if (!editor) {
      sendLog('❌ 에디터를 찾을 수 없습니다!');
      automationRunning = false;
      state = 'idle';
      sendDone();
      return;
    }
    sendLog(`✅ 에디터 발견: ${getEditorType()}`);

    knownTileIds = getCurrentTileIds();
    sendLog(`📸 기존 타일: ${knownTileIds.size}개 등록`);

    startCompletionWatcher();

    for (let i = 0; i < total; i++) {
      if (state === 'stopped') break;
      while (state === 'paused') await sleep(500);

      const item = prompts[i];
      currentIndex = i;
      sendProgress(i + 1, total);
      sendLog(`\n━━━ [${item.id}] ${item.memo || ''} (${i+1}/${total}) ━━━`);

      if (activeGenerations.length >= MAX_SLOTS) {
        sendLog(`⏳ 슬롯 꽉참 (${activeGenerations.length}/${MAX_SLOTS}) → 완료 대기`);
        const slotTimeout = (settings.genTimeout || 120) * 1000 + 10000;
        const slotStart = Date.now();

        while (activeGenerations.length >= MAX_SLOTS) {
          if (state === 'stopped') break;
          if (Date.now() - slotStart > slotTimeout) {
            sendLog('⚠️ 슬롯 대기 타임아웃 → 강제 해제');
            const oldest = activeGenerations[0];
            if (oldest && !oldest.resolved) {
              oldest.resolved = true;
              failedPrompts.push(oldest.item.id);
              for (const tid of oldest.tileIds) knownTileIds.add(tid);
            }
            activeGenerations.shift();
            notifySlotFree();
            break;
          }
          await Promise.race([waitForSlotFree(), sleep(2000)]);
        }
        if (state === 'stopped') break;
        sendLog(`✅ 슬롯 확보 (${activeGenerations.length}/${MAX_SLOTS})`);
      }

      if (activeGenerations.length > 0) {
        const lastGen = activeGenerations[activeGenerations.length - 1];
        if (!lastGen.resolved) {
          sendLog(`⏳ [${lastGen.item.id}] 30% 대기...`);
          await waitForActiveProgress(lastGen, 30, settings.genTimeout || 120);
          if (state === 'stopped') break;
        }
      }

      const inputOk = await prepareAndVerifyPrompt(item);
      if (!inputOk) {
        failedPrompts.push(item.id);
        continue;
      }

      if (activeGenerations.length > 0) {
        const lastGen = activeGenerations[activeGenerations.length - 1];
        if (!lastGen.resolved) {
          sendLog(`⏳ [${lastGen.item.id}] 80% 대기...`);
          await waitForActiveProgress(lastGen, 80, settings.genTimeout || 120);
          if (state === 'stopped') break;
        }
      }

      await humanDelay(300, 700);
      const btn = getGenerateButton();
      if (!btn) {
        sendLog(`❌ [${item.id}] Generate 버튼 없음`);
        failedPrompts.push(item.id);
        continue;
      }

      btn.click();
      const gen = {
        item,
        tileIds: [],
        tileStates: {},
        requestTime: Date.now(),
        resolved: false,
        _lastLog: 0
      };
      activeGenerations.push(gen);
      sendLog(`🎨 [${item.id}] Generate! (슬롯 ${activeGenerations.length}/${MAX_SLOTS})`);

      // 🏁 [보완] 바로 다음 프롬프트를 처리하기 전, 현재 프롬프트의 '타일'이 최소 1개는 나타날 때까지 대기
      // 이렇게 하면 5개 슬롯을 돌려도 파일 순서가 꼬이지 않고 안정적으로 매핑됩니다.
      sendLog(`⏳ [${item.id}] 타일 매핑 대기...`);
      let waitStart = Date.now();
      while (gen.tileIds.length === 0 && Date.now() - waitStart < 15000) {
        if (state === 'stopped' || gen.resolved) break;
        await sleep(500);
      }
      if (gen.tileIds.length > 0) {
        sendLog(`✅ [${item.id}] 타일 매핑 완료. 다음 프롬프트 준비.`);
      }
    }

    if (state !== 'stopped' && activeGenerations.length > 0) {
      sendLog(`\n⏳ 남은 ${activeGenerations.length}개 생성 완료 대기...`);
      const drainTimeout = (settings.genTimeout || 120) * 1000 + 10000;
      const drainStart = Date.now();

      while (activeGenerations.length > 0 && Date.now() - drainStart < drainTimeout) {
        if (state === 'stopped') break;
        const remaining = activeGenerations.filter(g => !g.resolved).length;
        if (remaining === 0) break;
        sendLog(`⏳ 남은 생성: ${remaining}개`);
        await sleep(3000);
      }

      for (const gen of activeGenerations) {
        if (!gen.resolved) {
          failedPrompts.push(gen.item.id);
          for (const tid of gen.tileIds) knownTileIds.add(tid);
        }
      }
      activeGenerations = [];
    }

    stopCompletionWatcher();

    state = 'idle';
    automationRunning = false;
    const successCount = total - failedPrompts.length;
    sendLog('\n━━━━━━━━━━━━━━━━━━━━');
    sendLog('🎉 자동화 완료! (v17 범용 DOM 감지)');
    sendLog(`✅ 성공: ${successCount}개`);
    if (failedPrompts.length > 0) {
      sendLog(`❌ 실패: ${failedPrompts.length}개 (${failedPrompts.join(', ')})`);
    }
    sendLog('━━━━━━━━━━━━━━━━━━━━');
    sendDone();
  }

  // ========== 메시지 수신 ==========
  function messageHandler(msg, sender, sendResponse) {
    if (msg.action === 'ping') {
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
