/**
 * inject.js (최고 강화 버전 - Pro-Level GI Formula v2)
 * This script runs in the Main World (page context)
 */
window.gf_doMainWorldInject = async function(text) {
  console.log("🎯 [Pro-Level Injection] Targeting Google Flow (Nano Banana 2)...");

  // 1. 에디터 타겟팅 (가장 깊숙한 곳까지 조준)
  // .ProseMirror는 구글 랩스 서비스의 공통 입력창 클래스입니다.
  const editor = document.querySelector('.ProseMirror') || document.querySelector('[contenteditable="true"]');
  if (!editor) {
    console.error("❌ 에디터를 못 찾았습니다. 페이지를 새로고침 하세요.");
    return false;
  }

  // 2. 텍스트 주입 (인간의 타이핑 시뮬레이션)
  editor.focus();
  
  // Selection/Range 강제 조절 (더 정확한 주입을 위해 필수)
  const range = document.createRange();
  const sel = window.getSelection();
  range.selectNodeContents(editor);
  range.collapse(false);
  sel.removeAllRanges();
  sel.addRange(range);

  // 기존 텍스트 청소 후 주입
  document.execCommand('selectAll', false, null);
  document.execCommand('delete', false, null);
  document.execCommand('insertText', false, text);

  // 3. 구글 엔진 강제 동기화 (유료 툴의 핵심 기법)
  // InputEvent를 날려주어야 React/ProseMirror 스테이트가 업데이트됩니다.
  const inputEvent = new InputEvent('input', {
    bubbles: true, cancelable: true, inputType: 'insertText', data: text, composed: true
  });
  editor.dispatchEvent(inputEvent);

  // [GI Formula 핵심] 브라우저 렌더링 프레임(requestAnimationFrame)에 맞춰 대기
  await new Promise(r => requestAnimationFrame(() => setTimeout(r, 600)));

  // 4. 전송 버튼 '정밀 저격' (아이콘 및 라벨 기반)
  const pressSubmit = () => {
    const allButtons = Array.from(document.querySelectorAll('button'));
    const sendBtn = allButtons.find(b => {
      const html = b.innerHTML.toLowerCase();
      const label = (b.getAttribute('aria-label') || "").toLowerCase();
      
      // 메뉴(more_vert)는 철저히 배제, 오직 전송과 관련된 키워드만 타겟
      // arrow_forward: 구글의 대표적인 전송 아이콘 이름
      return (label.includes('run') || label.includes('generate') || label.includes('send') || 
              html.includes('arrow_forward') || html.includes('send') || html.includes('play_arrow')) 
             && !html.includes('more_vert') && !label.includes('menu');
    });

    if (sendBtn && !sendBtn.disabled) {
      console.log("✅ 전송 버튼 발견. 물리적 클릭 시뮬레이션:", sendBtn.getAttribute('aria-label') || 'Submit');
      // 단순 click() 대신 mousedown -> mouseup -> click 순으로 이벤트를 날립니다.
      ['mousedown', 'mouseup', 'click'].forEach(type => {
        sendBtn.dispatchEvent(new MouseEvent(type, { bubbles: true, cancelable: true, view: window, composed: true }));
      });
      return true;
    }
    return false;
  };

  const success = pressSubmit();

  // 5. 버튼 클릭 실패 시 최후의 수단 (엔터 키)
  if (!success) {
    console.warn("⚠️ 전송 버튼 클릭 실패, 엔터 키 강제 주입.");
    const enterEvt = new KeyboardEvent('keydown', {
      key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true, cancelable: true, composed: true
    });
    editor.dispatchEvent(enterEvt);
  }

  return true;
};

// 통신 리스너 (기존과 동일)
if (window._gf_handler) {
  window.removeEventListener('gf_trigger_inject', window._gf_handler);
}

window._gf_handler = async (e) => {
  const { prompt } = e.detail;
  const res = await window.gf_doMainWorldInject(prompt);
  // 작업 완료 후 결과 보고
  window.dispatchEvent(new CustomEvent('gf_injected_done', { detail: { success: res } }));
};

window.addEventListener('gf_trigger_inject', window._gf_handler);
