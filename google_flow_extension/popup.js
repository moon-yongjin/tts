const startBtn = document.getElementById('start');
const stopBtn = document.getElementById('stop');
const promptList = document.getElementById('promptList');
const statusText = document.getElementById('statusText');
const statusIndicator = document.getElementById('statusIndicator');
const totalCount = document.getElementById('totalCount');
const progressCount = document.getElementById('progressCount');

function updateUI(isRunning, progress, total) {
  if (isRunning) {
    statusText.innerText = `RUNNING (${progress}/${total})`;
    statusIndicator.classList.add('running');
    startBtn.disabled = true;
    startBtn.style.opacity = '0.5';
    stopBtn.classList.add('active');
  } else {
    statusText.innerText = "READY";
    statusIndicator.classList.remove('running');
    startBtn.disabled = false;
    startBtn.style.opacity = '1';
    stopBtn.classList.remove('active');
  }
  totalCount.innerText = total || 0;
  progressCount.innerText = progress || 0;
}

startBtn.addEventListener('click', () => {
  const text = promptList.value.trim();
  if (!text) return;

  const prompts = text.split('\n').map(p => p.trim()).filter(p => p);
  
  chrome.tabs.query({active: true, currentWindow: true}, async (tabs) => {
    const tab = tabs[0];
    if (!tab || !tab.url.includes("labs.google/fx")) {
      statusText.innerText = "INVALID TAB";
      return;
    }

    // Inject logic
    try {
      await chrome.scripting.executeScript({ target: { tabId: tab.id }, files: ['inject.js'], world: 'MAIN' });
      await chrome.scripting.executeScript({ target: { tabId: tab.id }, files: ['content.js'] });
    } catch (e) {}

    chrome.tabs.sendMessage(tab.id, { action: "start", prompts: prompts }, (response) => {
      chrome.storage.local.set({ isRunning: true, promptList: text, total: prompts.length, current: 0 });
      updateUI(true, 0, prompts.length);
    });
  });
});

stopBtn.addEventListener('click', () => {
  chrome.tabs.query({active: true, currentWindow: true}, (tabs) => {
    chrome.tabs.sendMessage(tabs[0].id, { action: "stop" }, () => {
      chrome.storage.local.set({ isRunning: false, current: 0 });
      updateUI(false, 0, totalCount.innerText);
    });
  });
});

// Periodic status sync
setInterval(() => {
  chrome.storage.local.get(['isRunning', 'current', 'total', 'promptList'], (res) => {
    updateUI(res.isRunning, res.current, res.total);
    if (res.promptList && !promptList.value) promptList.value = res.promptList;
  });
}, 1000);

// Initial load
chrome.storage.local.get(['isRunning', 'current', 'total', 'promptList'], (res) => {
  if (res.promptList) promptList.value = res.promptList;
  updateUI(res.isRunning, res.current, res.total);
});
