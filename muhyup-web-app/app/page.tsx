"use client";

import { useState } from "react";
import ImageGenerator from "@/components/ImageGenerator";
import VideoGenerator from "@/components/VideoGenerator";

export default function Home() {
  const [activeTab, setActiveTab] = useState<"image" | "video">("image");

  return (
    <main className="min-h-screen bg-black text-slate-200 p-4 md:p-8 font-sans selection:bg-indigo-500/30">
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Header */}
        <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 py-4 border-b border-slate-800">
          <div>
            <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-cyan-400">
              무협 비디오 스튜디오
            </h1>

          </div>
          <div className="flex items-center gap-2">
            <span className="px-3 py-1 bg-indigo-500/10 text-indigo-400 rounded-full text-xs font-bold border border-indigo-500/20">
              v2.0 Beta
            </span>
          </div>
        </header>

        {/* Tabs */}
        <div className="flex p-1 bg-slate-900/50 backdrop-blur-sm rounded-xl border border-slate-800 w-full md:w-fit">
          <button
            onClick={() => setActiveTab("image")}
            className={`flex-1 md:flex-none px-6 py-2.5 rounded-lg text-sm font-bold transition-all duration-200 ${activeTab === "image"
              ? "bg-slate-800 text-white shadow-sm ring-1 ring-slate-700"
              : "text-slate-500 hover:text-slate-300 hover:bg-slate-800/50"
              }`}
          >
            🎨 이미지 생성
          </button>
          <button
            onClick={() => setActiveTab("video")}
            className={`flex-1 md:flex-none px-6 py-2.5 rounded-lg text-sm font-bold transition-all duration-200 ${activeTab === "video"
              ? "bg-slate-800 text-white shadow-sm ring-1 ring-slate-700"
              : "text-slate-500 hover:text-slate-300 hover:bg-slate-800/50"
              }`}
          >
            🎥 영상 변환
          </button>
        </div>

        {/* Content Area */}
        <div className="min-h-[600px] transition-all duration-300 ease-in-out">
          {activeTab === "image" ? (
            <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
              <ImageGenerator />
            </div>
          ) : (
            <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 h-full">
              <VideoGenerator />
            </div>
          )}
        </div>


      </div>
    </main >
  );
}
