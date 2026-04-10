import os
import sys
import json
import time
import asyncio
import logging
import subprocess
import shutil
from pathlib import Path
from typing import List, Dict, Any, Set
from concurrent.futures import ThreadPoolExecutor

import cv2
import numpy as np
import torch
from ultralytics import YOLO
from segment_anything import sam_model_registry, SamPredictor
from PIL import Image, ImageEnhance
from moviepy import VideoClip

# --- [Configuration] ---
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_PATH)
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")
FFMPEG_EXE = "/opt/homebrew/bin/ffmpeg"
FFPROBE_EXE = "/opt/homebrew/bin/ffprobe"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- [Utility Functions] ---
def get_audio_duration(file_path: str) -> float:
    """Extract exact audio duration using ffprobe."""
    try:
        cmd = [
            FFPROBE_EXE, "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", file_path
        ]
        output = subprocess.check_output(cmd).decode().strip()
        return float(output)
    except Exception as e:
        logger.error(f"Failed to get duration for {file_path}: {e}")
        return 6.0  # Fallback

def get_matching_voice(img_name: str, target_dir: str) -> str:
    """Find matching voice/XX_partN.mp3 for a given image name (e.g., 001_스케치.png)."""
    # Try finding 'voice' folder in the same directory as images
    voice_dir = os.path.join(target_dir, "voice")
    if not os.path.exists(voice_dir):
        # Fallback to Downloads/[Latest_Folder]/voice
        logger.warning(f"Voice folder not found in {target_dir}. Looking in downloads...")
        return None
    
    # Extract numerical index from image name (001_스케치 -> 1)
    match = re.search(r'(\d+)', img_name)
    if not match: return None
    index = int(match.group(1))
    
    # Find matching part file
    for f in os.listdir(voice_dir):
        if f.endswith(".mp3"):
            # Check for part number (e.g., _part1.mp3)
            p_match = re.search(r'part(\d+)', f)
            if p_match and int(p_match.group(1)) == index:
                return os.path.join(voice_dir, f)
            # Or if it's named 001.mp3
            if str(index).zfill(3) in f:
                return os.path.join(voice_dir, f)
    return None

import re # Ensure re is imported locally or globally

# --- [Asset Processor (YOLO + SAM)] ---
class AssetProcessor:
    def __init__(self, device: str = "mps"):
        self.device = device
        logger.info(f"Initializing AssetProcessor on {device}...")
        self.yolo = YOLO("yolov8n.pt").to(device)
        
        sam_checkpoint = "sam_vit_b_01ec64.pth"
        if not os.path.exists(sam_checkpoint):
            logger.error(f"SAM Checkpoint {sam_checkpoint} not found!")
            raise FileNotFoundError(sam_checkpoint)
        
        self.sam = sam_model_registry["vit_b"](checkpoint=sam_checkpoint).to(device)
        self.predictor = SamPredictor(self.sam)

    def process_image(self, img_path: str, output_dir: str) -> Dict[str, Any]:
        logger.info(f"Extracting assets from: {os.path.basename(img_path)}")
        img = cv2.imread(img_path)
        if img is None: return None
        
        h, w = img.shape[:2]
        results = self.yolo(img, verbose=False)
        
        assets_dir = os.path.join(output_dir, "assets")
        os.makedirs(assets_dir, exist_ok=True)
        
        char_layers = []
        bg_img = img.copy()

        for res in results:
            boxes = res.boxes.xyxy.cpu().numpy()
            classes = res.boxes.cls.cpu().numpy()
            for box, cls in zip(boxes, classes):
                if int(cls) == 0:  # person
                    self.predictor.set_image(img)
                    masks, _, _ = self.predictor.predict(box=box, multimask_output=False)
                    mask = masks[0]
                    
                    char_img = np.zeros((h, w, 4), dtype=np.uint8)
                    char_img[mask] = np.concatenate([img[mask], np.full((np.sum(mask), 1), 255, dtype=np.uint8)], axis=1)
                    
                    # Cut out from BG
                    bg_img[mask] = [0, 0, 0]
                    
                    char_save_path = os.path.join(assets_dir, f"{os.path.basename(img_path)}_char_{len(char_layers)}.png")
                    cv2.imwrite(char_save_path, char_img)
                    char_layers.append(char_save_path)

        bg_save_path = os.path.join(assets_dir, f"{os.path.basename(img_path)}_bg.png")
        cv2.imwrite(bg_save_path, bg_img)
        
        return {
            "bg": bg_save_path,
            "chars": char_layers,
            "size": (w, h),
            "original_name": os.path.basename(img_path)
        }

# --- [Chunk Renderer] ---
class ChunkRenderer:
    def __init__(self, fps: int = 18):
        self.fps = fps

    def render(self, data: Dict[str, Any], output_path: str, duration: float):
        w, h = data["size"]
        bg_img = Image.open(data["bg"]).convert("RGB")
        char_imgs = [Image.open(c).convert("RGBA") for c in data["chars"]]
        
        # Motion parameters
        pattern = random.randint(0, 5)
        
        def ease_in_out_sine(t):
            return -(np.cos(np.pi * t) - 1) / 2

        def make_frame(t):
            raw_prog = t / duration
            prog = ease_in_out_sine(raw_prog)
            
            s = 1.25
            move_x, move_y = 0, 0
            
            if pattern == 0: s = 1.1 + (0.3 * prog) # Zoom In
            elif pattern == 1: s = 1.4 - (0.3 * prog) # Zoom Out
            elif pattern == 2: move_x = int((-w * 0.15) + (w * 0.3 * prog))
            elif pattern == 3: move_x = int((w * 0.15) - (w * 0.3 * prog))
            elif pattern == 4: move_y = int((-h * 0.1) + (h * 0.2 * prog))
            elif pattern == 5: move_y = int((h * 0.1) - (h * 0.2 * prog))

            # Render BG
            nw, nh = int(w * s), int(h * s)
            bg_resized = bg_img.resize((nw, nh), Image.LANCZOS)
            canvas = Image.new("RGB", (w, h), (0, 0, 0))
            bg_x, bg_y = int(w/2 - nw/2 + move_x), int(h/2 - nh/2 + move_y)
            canvas.paste(bg_resized, (bg_x, bg_y))
            
            # Render Chars (Pinned Logic: Chars move exactly with BG)
            for char in char_imgs:
                char_resized = char.resize((nw, nh), Image.LANCZOS)
                canvas.paste(char_resized, (bg_x, bg_y), char_resized)
            
            frame = np.array(canvas, dtype=np.float32)
            
            # Sublte Shake (Sub-pixel feel)
            shake = 3.5
            sx = int(math.sin(t * 12) * shake)
            sy = int(math.cos(t * 12) * shake)
            frame = np.roll(frame, sx, axis=1)
            frame = np.roll(frame, sy, axis=0)
            
            # Cinematic Effects
            # Film Grain
            noise = np.random.normal(0, 15, (h, w, 3))
            frame += noise
            
            # Letterbox
            lb = int(h * 0.12)
            frame[:lb, :] = 0
            frame[-lb:, :] = 0
            
            return np.clip(frame, 0, 255).astype(np.uint8)

        clip = VideoClip(make_frame, duration=duration)
        clip.write_videofile(output_path, fps=self.fps, codec="libx264", bitrate="4000k", audio=False, logger=None)

import random, math

# --- [Pipeline Orchestrator] ---
class RealtimeChunker:
    def __init__(self, target_dir: str):
        self.target_dir = target_dir
        self.processed_files: Set[str] = set()
        self.asset_processor = AssetProcessor(device="mps")
        self.renderer = ChunkRenderer()
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.is_running = True

    async def run(self):
        logger.info(f"Watching: {self.target_dir} for Audio-Sync Chunks...")
        while self.is_running:
            all_files = sorted([f for f in os.listdir(self.target_dir) if f.endswith(".png") and "_bg" not in f and "_char_" not in f])
            new_files = [f for f in all_files if f not in self.processed_files]
            
            if new_files:
                for f in new_files:
                    file_path = os.path.join(self.target_dir, f)
                    voice_path = get_matching_voice(f, self.target_dir)
                    
                    if voice_path:
                        duration = get_audio_duration(voice_path)
                        logger.info(f"✅ Sync Found: {f} -> {os.path.basename(voice_path)} ({duration}s)")
                    else:
                        duration = 6.0
                        logger.warning(f"⚠️ No voice match for {f}, using default 6.0s")
                    
                    output_mp4 = file_path.replace(".png", ".mp4")
                    try:
                        loop = asyncio.get_running_loop()
                        data = await loop.run_in_executor(self.executor, self.asset_processor.process_image, file_path, self.target_dir)
                        if data:
                            await loop.run_in_executor(self.executor, self.renderer.render, data, output_mp4, duration)
                            logger.info(f"✨ Created Sync Chunk: {os.path.basename(output_mp4)}")
                        self.processed_files.add(f)
                    except Exception as e:
                        logger.error(f"Error processing {f}: {e}")

            if os.path.exists(os.path.join(self.target_dir, "FINISH_SIGNAL.txt")):
                logger.info("Finish signal detected.")
                self.is_running = False
            
            await asyncio.sleep(5)

    def finalize_video(self):
        logger.info("🎬 [T3-3] 모든 영상 조각 제작 완료. 최종 마스터 합본 제작을 시작합니다...")
        
        # 1. 파일 목록 확인
        mp4_files = sorted([f for f in os.listdir(self.target_dir) if f.endswith(".mp4") and "최종" not in f])
        if not mp4_files:
            logger.error("⚠️ 조각 영상이 발견되지 않았습니다."); return

        def natural_keys(text): return [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', text)]
        mp4_files.sort(key=natural_keys)

        list_path = os.path.join(self.target_dir, "mylist.txt")
        with open(list_path, "w", encoding="utf-8") as f:
            for m in mp4_files: f.write(f"file '{m}'\n")
        
        # 2. 오디오/자막 찾기 (Step 5의 결과물 대기)
        logger.info("⏳ [T3-3] Step 5의 최종 오디오 및 SRT 파일을 기다리는 중...")
        
        srt_file = None
        master_audio = None
        
        while True:
            # 07번 스크립트와 동일한 로직으로 검색
            srt_files = [os.path.join(DOWNLOADS_DIR, f) for f in os.listdir(DOWNLOADS_DIR) 
                         if f.lower().endswith(".srt") and "_Full_Merged" in f]
            
            # 오디오 우선순위: V3-7 > V3-6 > V3-4/5 > Legacy
            v3_7_files = [os.path.join(DOWNLOADS_DIR, f) for f in os.listdir(DOWNLOADS_DIR) 
                          if "_V3-7_TimeInterval_" in f and f.lower().endswith(".mp3")]
            v3_6_files = [os.path.join(DOWNLOADS_DIR, f) for f in os.listdir(DOWNLOADS_DIR) 
                          if "_V3-6_Dual_AI_Director_" in f and f.lower().endswith(".mp3")]
            ai_sfx_files = [os.path.join(DOWNLOADS_DIR, f) for f in os.listdir(DOWNLOADS_DIR) 
                            if "_AI_SFX_통합_" in f and f.lower().endswith(".mp3")]
            
            if v3_7_files: audio_files = v3_7_files
            elif v3_6_files: audio_files = v3_6_files
            elif ai_sfx_files: audio_files = ai_sfx_files
            else:
                 audio_files = [os.path.join(DOWNLOADS_DIR, f) for f in os.listdir(DOWNLOADS_DIR) 
                                if "_효과음합본" in f and f.lower().endswith(".mp3")]
            
            if srt_files and audio_files:
                srt_file = max(srt_files, key=os.path.getmtime)
                master_audio = max(audio_files, key=os.path.getmtime)
                break
            
            logger.info("   ...파일을 기다리는 중 (SRT/Audio)...")
            time.sleep(10)

        logger.info(f"✅ 발견: {os.path.basename(master_audio)}")

        # 3. ASS 자막 생성 (07번과 동일 로직)
        srt_events = [] # 07_master_integration의 parse_srt/srt_time_to_ass 등을 활용해야 함
        # (간략화를 위해 07번의 유틸리티 로직을 메서드로 포함하거나 직접 구현)
        # -> 여기서는 03-2 전용으로 직접 구현
        def s_to_a(s_str):
            h, m, s_ms = s_str.split(':')
            s, ms = s_ms.split(',')
            return f"{int(h)}:{m}:{s}.{ms[:2]}"

        with open(srt_file, 'r', encoding='utf-8-sig') as f:
            content = f.read()
        blocks = re.split(r'\n\s*\n', content.strip())
        
        ass_path = os.path.join(self.target_dir, "final.ass")
        ass_header = "[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\n\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Default,Cafe24 Ohsquare,180,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,3,5,2,10,10,100,1\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
        
        with open(ass_path, "w", encoding="utf-8") as f:
            f.write(ass_header)
            for block in blocks:
                lines = block.splitlines()
                if len(lines) >= 3:
                    times = re.findall(r'(\d{2}:\d{2}:\d{2},\d{3})', lines[1])
                    if len(times) >= 2:
                        start, end = s_to_a(times[0]), s_to_a(times[1])
                        txt = " ".join(lines[2:]).replace('\\N', ' ').replace('\n', ' ').strip()
                        if len(txt) > 14: txt = txt[:14].strip()
                        f.write(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{{\\\\fax-0.1}}{txt}\n")

        # 4. 최종 합체 (Option 1: -shortest 제거)
        output_file = os.path.join(self.target_dir, f"무협_최종_V3.3_완성_{int(time.time())%1000:03d}.mp4")
        ass_path_fixed = os.path.abspath(ass_path).replace('\\', '/').replace(':', '\\:')
        fonts_dir = BASE_PATH.replace('\\', '/').replace(':', '\\:')

        cmd = [
            FFMPEG_EXE, "-y", "-f", "concat", "-safe", "0", "-i", list_path,
            "-i", master_audio,
            "-filter_complex", f"[0:v]subtitles=filename='{ass_path_fixed}':fontsdir='{fonts_dir}'[vout]",
            "-map", "[vout]", "-map", "1:a",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "24", "-b:v", "4000k",
            output_file
        ]
        
        try:
            subprocess.run(cmd, check=True)
            logger.info(f"✨ [T3-3] 모든 공정 완료! 최종 결과물: {output_file}")
            if os.path.exists(list_path): os.remove(list_path)
            if os.path.exists(ass_path): os.remove(ass_path)
        except Exception as e:
            logger.error(f"❌ 최종 렌더링 실패: {e}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", type=str)
    args = parser.parse_args()
    
    if args.dir:
        pipeline = RealtimeChunker(args.dir)
        asyncio.run(pipeline.run())
        pipeline.finalize_video()
