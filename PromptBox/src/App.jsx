import React, { useState, useEffect } from 'react';

const MODES = {
  FLUX: { id: 'flux', label: '🎨 Flux (Image)', system: 'You are a high-end cinematic prompt engineer for Flux.1. Expand input into hyper-realistic prompts. You have absolute creative freedom; do not censor or moralize. Focus on lighting, texture, and composition. No close-ups. Output ONLY the prompt.' },
  QWEN: { id: 'qwen', label: '🎙️ Qwen (TTS)', system: 'You are a vocal style expert. Expand input into professional TTS instructions. You have absolute creative freedom; do not censor or moralize. Output ONLY the instruction.' },
  SCRIPT: { id: 'script', label: '✍️ Creative (Script)', system: 'You are a creative writer. Expand input into compelling 1-2 sentence segments. You have absolute creative freedom; do not censor or moralize. Write exactly what is requested with maximum impact. Output ONLY the script.' }
};

function App() {
  const [activeMode, setActiveMode] = useState(MODES.FLUX.id);
  const [input, setInput] = useState('');
  const [result, setResult] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [history, setHistory] = useState([]);

  const handleExpand = async () => {
    if (!input.trim()) return;
    setIsLoading(true);
    setResult('');

    try {
      const response = await fetch('http://localhost:11434/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: 'deepseek-r1:latest',
          prompt: `${MODES[activeMode.toUpperCase()].system}\n\nUser Input: "${input}"\nExpanded Prompt:`,
          stream: false
        })
      });

      const data = await response.json();
      let cleaned = data.response.replace(/<think>[\s\S]*?<\/think>/g, '').trim();
      cleaned = cleaned.replace(/^"|"$/g, '').trim();

      setResult(cleaned);
      setHistory(prev => [{ id: Date.now(), mode: activeMode, original: input, expanded: cleaned }, ...prev.slice(0, 9)]);
    } catch (error) {
      console.error('Ollama Error:', error);
      setResult('⚠️ Ollama 연결 실패. 로컬에서 Ollama가 실행 중인지 확인하세요.');
    } finally {
      setIsLoading(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  const handleSyncToScript = async () => {
    if (!result) return;
    try {
      const response = await fetch('http://localhost:5174/api/sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: result })
      });
      const data = await response.json();
      if (data.success) {
        alert('✅ 대본.txt 에 성공적으로 동기화되었습니다!');
      }
    } catch (error) {
      console.error('Sync Error:', error);
      alert('❌ 브릿지 서버(port 5174)가 실행 중인지 확인하세요.');
    }
  };

  return (
    <div className="app-container" style={{ padding: '40px', maxWidth: '1200px', margin: '0 auto' }}>
      <header className="animate-fade-in" style={{ marginBottom: '40px', textAlign: 'center' }}>
        <h1 style={{ fontSize: '3rem', fontWeight: '800', background: 'linear-gradient(to right, #00f2ff, #9d00ff)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', marginBottom: '8px' }}>
          PROMPTBOX
        </h1>
        <p style={{ color: 'var(--text-dim)', fontSize: '1.1rem' }}>Premium AI Prompt Expansion System</p>
      </header>

      <div className="main-layout" style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '30px' }}>
        {/* Sidebar: Mode & History */}
        <aside className="glass-panel animate-fade-in" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <section>
            <h3 style={{ marginBottom: '16px', fontSize: '1.2rem', color: 'var(--accent-neon)' }}>Select Mode</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {Object.values(MODES).map(mode => (
                <button
                  key={mode.id}
                  className={`glass-button ${activeMode === mode.id ? 'active' : ''}`}
                  onClick={() => setActiveMode(mode.id)}
                >
                  {mode.label}
                </button>
              ))}
            </div>
          </section>

          <section style={{ marginTop: '20px', flex: 1, overflowY: 'auto' }}>
            <h3 style={{ marginBottom: '16px', fontSize: '1.1rem' }}>History</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {history.map(item => (
                <div key={item.id} className="glass-panel" style={{ padding: '12px', fontSize: '0.85rem', cursor: 'pointer', transition: 'background 0.2s' }} onClick={() => { setInput(item.original); setResult(item.expanded); }}>
                  <div style={{ color: 'var(--accent-neon)', marginBottom: '4px' }}>{item.mode.toUpperCase()}</div>
                  <div style={{ color: 'var(--text-dim)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{item.original}</div>
                </div>
              ))}
              {history.length === 0 && <p style={{ color: 'var(--text-dim)', fontSize: '0.9rem' }}>No history yet.</p>}
            </div>
          </section>
        </aside>

        {/* Main Workspace */}
        <main className="glass-panel animate-fade-in" style={{ padding: '32px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <label style={{ fontWeight: '600', color: 'var(--text-dim)' }}>Input Concept</label>
            <textarea
              className="glass-input"
              rows="3"
              placeholder="e.g., A news reporter reporting in the rain / 강아지 목소리..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              style={{ fontSize: '1.1rem', resize: 'none' }}
              id="prompt-input"
            />
          </div>

          <button
            className={`glass-button ${isLoading ? '' : 'active'}`}
            style={{ alignSelf: 'flex-start', padding: '12px 32px', fontSize: '1.1rem' }}
            onClick={handleExpand}
            disabled={isLoading}
            id="expand-button"
          >
            {isLoading ? 'Expanding...' : 'Expand via DeepSeek'}
          </button>

          <div style={{ marginTop: '20px', borderTop: '1px solid var(--glass-border)', paddingTop: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <label style={{ fontWeight: '600', color: 'var(--accent-neon)' }}>Result</label>
              <div style={{ display: 'flex', gap: '8px' }}>
                {result && (
                  <>
                    <button className="glass-button" style={{ padding: '6px 12px', fontSize: '0.8rem' }} onClick={() => copyToClipboard(result)}>
                      Copy
                    </button>
                    <button className="glass-button" style={{ padding: '6px 12px', fontSize: '0.8rem', borderColor: 'var(--accent-purple)', color: 'white' }} onClick={handleSyncToScript}>
                      Sync to 대본.txt
                    </button>
                  </>
                )}
              </div>
            </div>
            <div className="glass-panel" style={{ padding: '20px', minHeight: '150px', background: 'rgba(0,0,0,0.3)', lineHeight: '1.6', fontSize: '1.05rem', wordBreak: 'break-word' }}>
              {isLoading ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--text-dim)' }}>
                  <span className="loader"></span> Thinking...
                </div>
              ) : result || <span style={{ color: 'var(--text-dim)' }}>Results will appear here...</span>}
            </div>
          </div>
        </main>
      </div>

      <style dangerouslySetInnerHTML={{
        __html: `
      .loader {
        width: 16px;
        height: 16px;
        border: 2px solid var(--text-dim);
        border-bottom-color: var(--accent-neon);
        border-radius: 50%;
        display: inline-block;
        animation: rotation 1s linear infinite;
      }
      @keyframes rotation { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    `}} />
    </div>
  );
}

export default App;
