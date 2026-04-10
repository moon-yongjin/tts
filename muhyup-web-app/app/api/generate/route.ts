import { NextRequest, NextResponse } from "next/server";
import { spawn } from "child_process";
import path from "path";
import fs from "fs";
import os from "os";

// [헬퍼] 스트림을 통해 실시간 로그 전송
function iteratorToStream(iterator: any) {
    return new ReadableStream({
        async pull(controller) {
            const { value, done } = await iterator.next();
            if (done) {
                controller.close();
            } else {
                controller.enqueue(value);
            }
        },
    });
}

// [헬퍼] 제너레이터 함수로 프로세스 출력 읽기
async function* makeIterator(process: any) {
    for await (const chunk of process.stdout) {
        yield chunk;
    }
    for await (const chunk of process.stderr) {
        yield chunk;
    }
}

export async function POST(req: NextRequest) {
    try {
        const body = await req.json();
        const { script, count, style, saveLocation } = body;

        // 1. 대본 임시 파일 저장 (필수)
        const tempScriptPath = path.join(os.tmpdir(), `script_${Date.now()}.txt`);
        fs.writeFileSync(tempScriptPath, script, "utf-8");

        // 2. 저장 경로 결정
        const timestamp = new Date().toISOString().replace(/[-:T]/g, "").slice(4, 12) + "_" + new Date().toTimeString().slice(0, 4).replace(":", ""); // MMDD_HHMM
        const baseDir = saveLocation === "desktop"
            ? path.join(os.homedir(), "Desktop")
            : path.join(os.homedir(), "Downloads");

        const outputDir = path.join(baseDir, `생성이미지_${timestamp}`);

        // 필요한 경우 폴더 생성 (Python 스크립트에서도 생성하지만 이중 안전장치)
        if (!fs.existsSync(outputDir)) {
            fs.mkdirSync(outputDir, { recursive: true });
        }

        console.log(`🚀 [API] 실행 시작: ${outputDir}, 스타일: ${style}, 수량: ${count}`);

        // 3. Python 프로세스 실행
        // 핵심: 사용자의 Python 환경 경로를 지정해야 함 (Miniforge 등)
        // fallback으로 'python3' 사용
        const pythonExe = "/Users/a12/miniforge3/envs/qwen-tts/bin/python";
        const scriptPath = "/Users/a12/projects/tts/core_v2/02_visual_director_96.py";

        const args = [
            scriptPath,
            "--style", style,
            "--count", count.toString(),
            "--output-dir", outputDir,
            "--auto-approve",
            tempScriptPath
        ];

        const child = spawn(fs.existsSync(pythonExe) ? pythonExe : "python3", args);

        // 4. 스트림 응답 반환
        const stream = iteratorToStream(makeIterator(child));

        return new Response(stream, {
            headers: {
                "Content-Type": "text/plain; charset=utf-8",
                "Transfer-Encoding": "chunked",
                "X-Content-Type-Options": "nosniff",
            },
        });

    } catch (error: any) {
        console.error("❌ API Error:", error);
        return NextResponse.json({ error: error.message }, { status: 500 });
    }
}
