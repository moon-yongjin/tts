"use client";

import { useState } from "react";

export default function VideoGenerator() {
    const [isConverting, setIsConverting] = useState(false);

    return (
        <div className="flex flex-col gap-6 p-6 bg-slate-900 rounded-xl border border-slate-800 shadow-2xl h-full flex-1">
            <div className="flex flex-col gap-2">
                <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                    🎥 영상 변환 스튜디오
                </h2>
                <p className="text-slate-400 text-sm">
                    생성된 이미지를 시네마틱 영상으로 변환합니다.
                </p>
            </div>

            <div className="flex items-center justify-center flex-1 min-h-[400px] border-2 border-dashed border-slate-800 rounded-xl bg-slate-950/50">
                <div className="text-center p-10">
                    <div className="text-6xl mb-4">🎬</div>
                    <h3 className="text-xl font-medium text-slate-300 mb-2">이미지 폴더 선택</h3>
                    <p className="text-slate-500 mb-6 max-w-sm mx-auto">
                        변환할 이미지가 담긴 폴더를 선택하거나 드래그하세요.
                    </p>
                    <button className="py-3 px-8 bg-slate-800 hover:bg-slate-700 text-white rounded-lg transition-colors border border-slate-700">
                        폴더 찾아보기
                    </button>
                </div>
            </div>
        </div>
    );
}
