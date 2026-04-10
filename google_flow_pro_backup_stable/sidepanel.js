const $ = id => document.getElementById(id);
let isRunning = false;
let isPaused = false;

function log(msg) {
  const logEl = $('log');
  let output = msg;
  // 만약 메시지에 이미 [시:분:초] 타임스탬프가 붙어있지 않다면 새로 붙임
  if (!/^\[\d{2}:\d{2}:\d{2}\]/.test(msg)) {
    const time = new Date().toLocaleTimeString('ko-KR', { hour12: false });
    output = `[${time}] ${msg}`;
  }
  logEl.innerHTML += `${output}\n`;
  logEl.scrollTop = logEl.scrollHeight;
}

function setStatus(text, color = '#00d2ff') {
  $('status').textContent = text;
  $('status').style.color = color;
}

function parsePrompts(text) {
  const lines = text.trim().split('\n').filter(l => l.trim());
  const result = [];
  for (const line of lines) {
    const parts = line.split('|').map(s => s.trim());
    if (parts.length >= 3) {
      result.push({ id: parts[0], memo: parts[1], prompt: parts[2] });
    } else if (parts.length === 2) {
      result.push({ id: parts[0], memo: '', prompt: parts[1] });
    }
  }
  return result;
}

// ========== UI 상태를 완전히 리셋 ==========
function resetUI() {
  isRunning = false;
  isPaused = false;
  $('btnPause').textContent = '⏸ 일시정지';
  setStatus('⏸ 대기 중', '#00d2ff');
}

$('fileBtn').addEventListener('click', () => $('fileInput').click());
$('fileInput').addEventListener('change', (e) => {
  const file = e.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = (ev) => {
    $('promptsArea').value = ev.target.result;
    log(`📂 파일 로드: ${file.name}`);
  };
  reader.readAsText(file, 'UTF-8');
});

async function getFlowTab() {
  const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
  if (tabs[0] && tabs[0].url && tabs[0].url.includes('labs.google')) return tabs[0];
  const flowTabs = await chrome.tabs.query({ url: 'https://labs.google.com/*' });
  if (flowTabs.length > 0) return flowTabs[0];
  return null;
}

async function sendToContent(action, data = {}) {
  const tab = await getFlowTab();
  if (!tab) throw new Error('Flow 탭을 찾을 수 없습니다');

  try {
    await chrome.tabs.sendMessage(tab.id, { action: 'ping' });
  } catch {
    await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      files: ['content.js']
    });
    await new Promise(r => setTimeout(r, 1000));
  }

  return new Promise((resolve, reject) => {
    chrome.tabs.sendMessage(tab.id, { action, ...data }, (response) => {
      if (chrome.runtime.lastError) {
        reject(new Error(chrome.runtime.lastError.message));
      } else {
        resolve(response);
      }
    });
  });
}

// ========== 시작 ==========
$('btnStart').addEventListener('click', async () => {
  const text = $('promptsArea').value;
  if (!text.trim()) { log('❌ 프롬프트를 입력하세요'); return; }

  const allPrompts = parsePrompts(text);
  if (allPrompts.length === 0) { log('❌ 유효한 프롬프트가 없습니다'); return; }

  const startNum = $('startNum').value.trim();
  const startIdx = allPrompts.findIndex(p => p.id === startNum);
  if (startIdx === -1) { log(`❌ 시작 번호 "${startNum}"을 찾을 수 없습니다`); return; }

  const selected = allPrompts.slice(startIdx);

  const settings = {
    folderName: $('folderName').value.trim() || 'NB2_output',
    batchCount: parseInt($('batchCount').value) || 2,
    genTimeout: parseInt($('genTimeout').value) || 120,
    nameMode: $('nameMode').value
  };

  isRunning = true;
  isPaused = false;
  setStatus('🚀 실행 중', '#0f0');
  log(`▶ 시작: ${startNum}번부터 ${selected.length}개 프롬프트`);

  try {
    const res = await sendToContent('start', { prompts: selected, settings });
    if (res && !res.ok) {
      log(`❌ ${res.error || '시작 실패'}`);
      resetUI();
    }
  } catch (e) {
    log(`❌ 오류: ${e.message}`);
    setStatus('❌ 오류', '#e94560');
    resetUI();
  }
});

// ========== 일시정지 ==========
$('btnPause').addEventListener('click', async () => {
  if (!isRunning) return;
  isPaused = !isPaused;
  $('btnPause').textContent = isPaused ? '▶ 재개' : '⏸ 일시정지';
  setStatus(isPaused ? '⏸ 일시정지' : '🚀 실행 중', isPaused ? '#e2b93b' : '#0f0');
  log(isPaused ? '⏸ 일시정지' : '▶ 재개');
  try { await sendToContent(isPaused ? 'pause' : 'resume'); } catch (e) { log(`❌ ${e.message}`); }
});

// ========== 중지 ==========
$('btnStop').addEventListener('click', async () => {
  try { await sendToContent('stop'); } catch (e) { log(`❌ ${e.message}`); }
  resetUI();
  setStatus('⏹ 중지됨', '#e94560');
  log('⏹ 중지');
});

// ========== 초기화 ==========
$('btnReset').addEventListener('click', async () => {
  // 1. content script 상태 리셋
  try {
    const res = await sendToContent('reset');
    if (res && res.ok) {
      log('🔄 Content script 상태 초기화 완료');
    }
  } catch (e) {
    log(`⚠️ Content 리셋 실패 (무시): ${e.message}`);
  }

  // 2. UI 상태 리셋
  resetUI();

  // 3. 로그 클리어
  $('log').innerHTML = '';

  log('🔄 전체 초기화 완료 — 새 프롬프트로 바로 시작 가능');
});

// ========== 메시지 수신 ==========
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === 'log') log(msg.text);
  else if (msg.type === 'status') setStatus(msg.text, msg.color || '#00d2ff');
  else if (msg.type === 'done') {
    resetUI();
    setStatus('✅ 전체 완료', '#0f0');
    log('✅ 모든 프롬프트 처리 완료');
  }
  else if (msg.type === 'progress') setStatus(`🚀 ${msg.current}/${msg.total} 처리 중`, '#0f0');
  sendResponse({ ok: true });
  return true;
});

// ========== 디버그 ==========
$('btnDebug').addEventListener('click', async () => {
  try {
    const res = await sendToContent('debug');
    log(`🔍 에디터: ${res.editorType || '없음'}`);
    log(`🔍 Generate 버튼: ${res.generateBtn ? '발견' : '없음'}`);
    log(`🔍 이미지 수: ${res.imageCount}`);
    log(`🔍 처리된 이미지: ${res.processedCount}`);
    log(`🔍 자동화 실행 중: ${res.automationRunning ? '예' : '아니오'}`);
    log(`🔍 상태: ${res.state}`);
  } catch (e) {
    log(`❌ 디버그 실패: ${e.message}`);
  }
});
