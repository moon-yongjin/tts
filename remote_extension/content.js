let socket = null;

chrome.runtime.onMessage.addListener((request) => {
    if (request.action === 'CONNECT_SERVER') {
        connectToWebSocket(request.url);
    }
});

function connectToWebSocket(url) {
    if (socket) socket.close();

    console.log(`📡 Connecting to Remote Control Server: ${url}`);
    socket = new WebSocket(url);

    socket.onopen = () => {
        console.log('✅ Connected to Mac Controller');
        alert('Mac 본부와 연결되었습니다! 이제 맥에서 명령을 보낼 수 있습니다.');
    };

    socket.onmessage = async (event) => {
        const command = json.parse(event.data);
        console.log('📥 Received command:', command);

        if (command.action === 'EXECUTE_GENERATION') {
            await executeWhiskTask(command.prompt);
        }
    };

    socket.onclose = () => {
        console.log('🔌 Disconnected from Server');
    };

    socket.onerror = (err) => {
        console.error('❌ Socket Error:', err);
    };
}

async function executeWhiskTask(prompt) {
    try {
        const textarea = document.querySelector('textarea') || document.querySelector('[contenteditable="true"]');
        if (!textarea) return;

        textarea.focus();
        textarea.value = prompt;
        textarea.dispatchEvent(new Event('input', { bubbles: true }));
        await new Promise(r => setTimeout(r, 1000));

        const submitBtn = document.querySelector('button[aria-label*="Generate"]') ||
            document.querySelector('button:has(i:contains("arrow_forward"))');
        if (submitBtn) submitBtn.click();

        console.log(`🚀 Task Executed: ${prompt}`);
    } catch (e) {
        console.error('Task Error:', e);
    }
}
