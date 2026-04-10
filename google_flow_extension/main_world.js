/**
 * Google Flow Auto Gen - Main World Helper
 * Runs in the same context as Google's React/ProseMirror code.
 */
(function() {
  if (window.gf_main_world_loaded) return;
  window.gf_main_world_loaded = true;

  console.log("🛠️ [MainWorld] Persistent Helper Loaded");

  window.addEventListener('gf_do_inject', async (e) => {
    const text = e.detail.prompt;
    console.log("🛠️ [MainWorld] Injecting:", text);

    let editors = Array.from(document.querySelectorAll('div[contenteditable="true"], [role="textbox"], textarea, input[type="text"]'));
    let editor = editors.find(el => {
      const ph = el.getAttribute('placeholder') || el.getAttribute('aria-label') || el.innerText || el.textContent || "";
      return ph.includes("무엇을") || ph.includes("prompt") || ph.includes("만들고");
    }) || editors[editors.length - 1];

    if (!editor) {
      window.dispatchEvent(new CustomEvent('gf_injected_done', { detail: { success: false } }));
      return;
    }

    editor.focus();
    document.execCommand('selectAll', false, null);
    document.execCommand('delete', false, null);
    document.execCommand('insertText', false, text);

    // Sync React/ProseMirror
    const eventTypes = ['beforeinput', 'input', 'change', 'keyup'];
    eventTypes.forEach(type => {
      editor.dispatchEvent(new InputEvent(type, { 
        inputType: 'insertText', 
        data: text, 
        bubbles: true, 
        cancelable: true 
      }));
    });

    await new Promise(r => setTimeout(r, 800));

    // Simulate Enter
    const enterEvt = new KeyboardEvent('keydown', { 
      key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true, cancelable: true 
    });
    editor.dispatchEvent(enterEvt);
    
    window.dispatchEvent(new CustomEvent('gf_injected_done', { detail: { success: true } }));
  });
})();
