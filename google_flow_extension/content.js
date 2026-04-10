/**
 * Google Flow Auto Gen - Orchestrator
 * Uses user-provided inject.js + web_accessible_resources strategy.
 * Includes progress tracking for the premium UI.
 */
if (!window.googleFlowInited) {
  window.googleFlowInited = true;
  
  window.gf_prompts = [];
  window.gf_currentIndex = 0;
  window.gf_isProcessing = false;
  window.gf_interval = null;
  window.gf_config = {
    checkInterval: 5000,
    generateWait: 15000 
  };

  // 1. Inject the script for Main World access (Legal CSP Bypass)
  const script = document.createElement('script');
  script.src = chrome.runtime.getURL('inject.js');
  (document.head || document.documentElement).appendChild(script);

  async function processNextPrompt() {
    if (window.gf_isProcessing || window.gf_currentIndex >= window.gf_prompts.length) {
      if (window.gf_currentIndex >= window.gf_prompts.length && window.gf_interval) {
        clearInterval(window.gf_interval);
        window.gf_interval = null;
        chrome.storage.local.set({ isRunning: false, current: window.gf_currentIndex });
      }
      return;
    }

    window.gf_isProcessing = true;
    const prompt = window.gf_prompts[window.gf_currentIndex];
    
    console.log(`🎬 [${window.gf_currentIndex + 1}/${window.gf_prompts.length}] Processing: ${prompt}`);
    
    // Update progress in storage for popup UI
    chrome.storage.local.set({ current: window.gf_currentIndex + 1 });

    // Call Main World Helper via Event
    const success = await new Promise(resolve => {
       const onDone = (e) => {
         window.removeEventListener('gf_injected_done', onDone);
         resolve(e.detail.success);
       };
       window.addEventListener('gf_injected_done', onDone);
       
       window.dispatchEvent(new CustomEvent('gf_trigger_inject', { 
         detail: { prompt: prompt } 
       }));
    });

    if (success) {
      window.gf_currentIndex++;
      await new Promise(r => setTimeout(r, window.gf_config.generateWait));
    }
    
    window.gf_isProcessing = false;
  }

  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "start") {
      window.gf_prompts = request.prompts;
      window.gf_currentIndex = 0;
      window.gf_isProcessing = false;
      if (window.gf_interval) clearInterval(window.gf_interval);
      window.gf_interval = setInterval(processNextPrompt, window.gf_config.checkInterval);
      processNextPrompt();
      sendResponse({status: "started"});
    } else if (request.action === "stop") {
      if (window.gf_interval) clearInterval(window.gf_interval);
      window.gf_interval = null;
      window.gf_isProcessing = false;
      chrome.storage.local.set({ isRunning: false });
      sendResponse({status: "stopped"});
    }
    return true;
  });
}
