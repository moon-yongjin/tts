"use client";

import { useState, useEffect } from "react";

export default function ImageGenerator() {
    const [script, setScript] = useState("");
    const [count, setCount] = useState(10);
    const [style, setStyle] = useState("스케치");
    const [saveLocation, setSaveLocation] = useState("desktop");
    const [isGenerating, setIsGenerating] = useState(false);
    const [logs, setLogs] = useState<string[]>([]);

    // Timer Logic State (Removed)
    const [resultInfo, setResultInfo] = useState<{ time: string; location: string } | null>(null);

    // Timer Effect (Removed)

    const handleGenerate = async () => {
        if (!script.trim()) {
            alert("대본을 입력해주세요!");
            return;
        }

        setIsGenerating(true);
        setResultInfo(null);
        setLogs([]);
        setLogs((prev) => [...prev, "🚀 이미지 생성을 요청합니다...", `📂 저장 위치: ${saveLocation === 'desktop' ? '바탕화면' : '다운로드'}`]);

        try {
            const response = await fetch("/api/generate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ script, count, style, saveLocation }),
            });

            if (!response.body) return;

            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                const lines = chunk.split("\n");

                for (const line of lines) {
                    if (line.trim()) setLogs(prev => [...prev, line]);

                    // Parse Final Stats
                    if (line.includes("⏱️ 총 소요 시간:")) {
                        const timeMatch = line.split(": ")[1];
                        if (timeMatch) setResultInfo(prev => ({ ...prev!, time: timeMatch.trim() }));
                    }
                    if (line.includes("📍 저장 위치:")) {
                        const locMatch = line.split(": ")[1];
                        if (locMatch) setResultInfo(prev => ({ ...prev!, location: locMatch.trim() }));
                    }
                }
            }

            setLogs((prev) => [...prev, "✅ 작업이 완료되었습니다."]);

        } catch (error) {
            console.error("Generaton failed", error);
            setLogs((prev) => [...prev, "❌ 오류 발생: " + String(error)]);
        } finally {
            setIsGenerating(false);
        }
    };

    return (
        <div className="flex flex-col gap-6 p-6 bg-slate-900 rounded-xl border border-slate-800 shadow-2xl">
            <div className="flex flex-col gap-2">
                <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                    🎨 이미지 생성 스튜디오
                </h2>

            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Left Column: Inputs */}
                <div className="flex flex-col gap-4">
                    <div className="flex flex-col gap-2">
                        <label className="text-sm font-medium text-slate-300">대본 입력</label>
                        <textarea
                            className="w-full h-64 p-4 bg-slate-950 border border-slate-800 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-slate-200 resize-none font-mono text-sm leading-relaxed"
                            placeholder="여기에 대본을 입력하세요..."
                            value={script}
                            onChange={(e) => setScript(e.target.value)}
                        />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="flex flex-col gap-2">
                            <label className="text-sm font-medium text-slate-300">화풍 선택</label>
                            <select
                                className="p-3 bg-slate-950 border border-slate-800 rounded-lg text-slate-200 focus:ring-2 focus:ring-indigo-500 outline-none"
                                value={style}
                                onChange={(e) => setStyle(e.target.value)}
                            >
                                <option value="스케치">✏️ 스케치 (Sketch)</option>
                                <option value="수묵화">🖌️ 수묵화 (Ink)</option>
                                <option value="애니메이션">🎬 애니메이션 (Anime)</option>
                                <option value="고전민화">📜 고전민화 (Folk)</option>
                            </select>
                        </div>
                        <div className="flex flex-col gap-2">
                            <label className="text-sm font-medium text-slate-300">생성 수량</label>
                            <input
                                type="number"
                                className="p-3 bg-slate-950 border border-slate-800 rounded-lg text-slate-200 focus:ring-2 focus:ring-indigo-500 outline-none"
                                value={count}
                                onChange={(e) => setCount(Number(e.target.value))}
                                min={1}
                                max={100}
                            />
                        </div>
                    </div>

                    <div className="flex flex-col gap-2">
                        <label className="text-sm font-medium text-slate-300">저장 위치</label>
                        <div className="flex gap-4 p-1 bg-slate-950 rounded-lg border border-slate-800">
                            <label className={`flex-1 cursor-pointer py-2 text-center rounded-md text-sm font-medium transition-colors ${saveLocation === 'desktop' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'}`}>
                                <input
                                    type="radio"
                                    name="saveLocation"
                                    value="desktop"
                                    checked={saveLocation === "desktop"}
                                    onChange={(e) => setSaveLocation(e.target.value)}
                                    className="hidden"
                                />
                                🖥️ 바탕화면
                            </label>
                            <label className={`flex-1 cursor-pointer py-2 text-center rounded-md text-sm font-medium transition-colors ${saveLocation === 'downloads' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'}`}>
                                <input
                                    type="radio"
                                    name="saveLocation"
                                    value="downloads"
                                    checked={saveLocation === "downloads"}
                                    onChange={(e) => setSaveLocation(e.target.value)}
                                    className="hidden"
                                />
                                📥 다운로드
                            </label>
                        </div>
                    </div>

                    <button
                        onClick={handleGenerate}
                        disabled={isGenerating}
                        className={`mt-2 py-4 px-6 rounded-lg font-bold text-white shadow-lg transition-all
              ${isGenerating
                                ? "bg-slate-700 cursor-not-allowed opacity-50"
                                : "bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 transform hover:scale-[1.02] active:scale-[0.98]"
                            }`}
                    >
                        {isGenerating ? (
                            <span className="flex items-center justify-center gap-2">
                                ⏳ 생성 중...
                                <span className="relative flex h-3 w-3">
                                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                                    <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
                                </span>
                            </span>
                        ) : "🚀 이미지 생성 시작"}
                    </button>
                </div>

                {/* Right Column: Progress & Result UI */}
                <div className="flex flex-col gap-4">
                    <div className="flex flex-col gap-2 h-full">
                        <label className="text-sm font-medium text-slate-300">
                            진행 상황
                        </label>

                        <div className="flex-1 bg-black/50 border border-slate-800 rounded-lg p-8 flex flex-col items-center justify-center min-h-[300px]">
                            {/* 1. Idle State */}
                            {!isGenerating && !resultInfo && (
                                <div className="text-slate-500 text-center">
                                    <div className="text-4xl mb-4">🎨</div>
                                    <p>대본을 입력하고<br />생성을 시작하세요</p>
                                </div>
                            )}

                            {/* 2. Generating State (Blinking Cursor & Hacker Log) */}
                            {isGenerating && (
                                <div className="w-full flex flex-col items-center justify-center gap-8 animate-in fade-in zoom-in duration-300">

                                    {/* Blinking Cursor Animation */}
                                    <div className="relative p-6">
                                        <div className="text-6xl font-mono font-bold text-green-500 tracking-widest flex items-center">
                                            PROCESSING
                                            <span className="inline-block w-4 h-12 bg-green-500 ml-2 animate-[pulse_1s_cubic-bezier(0.4,0,0.6,1)_infinite]"></span>
                                        </div>
                                    </div>

                                    {/* Hacker Style Log Stream */}
                                    <div className="w-full max-w-md bg-black/80 border-t border-green-900/50 p-3 h-16 flex items-center overflow-hidden relative rounded">
                                        <div className="absolute inset-0 bg-gradient-to-b from-transparent to-black/20 pointer-events-none"></div>
                                        <span className="text-green-500/80 font-mono text-xs truncate w-full">
                                            <span className="mr-2 opacity-50">$</span>
                                            {logs.length > 0 ? logs[logs.length - 1] : "Initializing..."}
                                            <span className="animate-pulse ml-1 inline-block w-1.5 h-3 bg-green-500/50 align-middle"></span>
                                        </span>
                                    </div>
                                </div>
                            )}

                            {/* 3. Result State */}
                            {!isGenerating && resultInfo && (
                                <div className="w-full max-w-sm bg-slate-800/50 p-6 rounded-xl border border-slate-700 animate-in slide-in-from-bottom-5 duration-500">
                                    <div className="text-center mb-6">
                                        <div className="text-5xl mb-2">✅</div>
                                        <h3 className="text-xl font-bold text-white">작업 완료!</h3>
                                    </div>

                                    <div className="space-y-4 text-sm">
                                        <div className="flex justify-between items-center border-b border-slate-700 pb-2">
                                            <span className="text-slate-400">⏱️ 소요 시간</span>
                                            <span className="text-green-400 font-mono font-bold">{resultInfo.time}</span>
                                        </div>
                                        <div className="flex flex-col gap-1">
                                            <span className="text-slate-400">📍 저장 위치</span>
                                            <span className="text-indigo-300 font-mono break-all text-xs bg-slate-900/50 p-2 rounded">
                                                {resultInfo.location}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
