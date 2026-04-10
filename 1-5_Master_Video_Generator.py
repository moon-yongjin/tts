import os
import re
import cv2
import shutil
import unicodedata
from pathlib import Path
from datetime import datetime

DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")

class GrokVideoSorter:
    def __init__(self):
        print("\n==========================================")
        print("📁 [그록 동영상 자동 매칭 및 파일 정렬기]")
        print("   (캡컷(CapCut) 작업 전처리 전용)")
        print("==========================================")

    def normalize_name(self, n):
        return unicodedata.normalize('NFC', n)

    def find_latest_workspace(self):
        """가장 최근에 작업한 이미지 폴더 탐색"""
        candidates = []
        for d in os.listdir(DOWNLOADS_DIR):
            full_path = os.path.join(DOWNLOADS_DIR, d)
            if not os.path.isdir(full_path): continue
            norm_name = self.normalize_name(d)
            if norm_name.startswith(("AutoDirector_", "무협_", "다이어리_", "틱톡_", "Jisu_")):
                # 폴더 안에 png 파일이 하나라도 존재하는지 확인 (빈 폴더 무시)
                if any(f.endswith('.png') for f in os.listdir(full_path)):
                    candidates.append(full_path)
                
        if candidates:
            return max(candidates, key=os.path.getmtime)
        return None

    def get_best_frame_from_video(self, v_path):
        """영상에서 중간 프레임 추출 (도입부 블랙 프레임 예방)"""
        cap = cv2.VideoCapture(v_path)
        if not cap.isOpened(): return None
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames > 5:
            # 영상의 30% 지점 프레임 읽기 (안정적)
            cap.set(cv2.CAP_PROP_POS_FRAMES, max(1, total_frames // 3))
        ret, frame = cap.read()
        cap.release()
        if ret:
            return cv2.resize(frame, (256, 256))
        return None

    def compare_images(self, img1, img2):
        """OpenCV Histogram 대조로 유사도 측정"""
        try:
            hsv1 = cv2.cvtColor(img1, cv2.COLOR_BGR2HSV)
            hsv2 = cv2.cvtColor(img2, cv2.COLOR_BGR2HSV)
            hist1 = cv2.calcHist([hsv1], [0, 1], None, [32, 32], [0, 180, 0, 256])
            hist2 = cv2.calcHist([hsv2], [0, 1], None, [32, 32], [0, 180, 0, 256])
            cv2.normalize(hist1, hist1, 0, 1, cv2.NORM_MINMAX)
            cv2.normalize(hist2, hist2, 0, 1, cv2.NORM_MINMAX)
            return cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
        except: return 0.0

    def run(self):
        wp = self.find_latest_workspace()
        if not wp:
            print("❌ 작업할 이미지 폴더를 찾지 못했습니다.")
            return
        print(f"✅ 작업 폴더: {os.path.basename(wp)}")

        output_dir = os.path.join(wp, "캡컷_불러오기_폴더")
        os.makedirs(output_dir, exist_ok=True)
        print(f"📂 정렬 결과물 저장: {output_dir}/")

        grok_done_dir = DOWNLOADS_DIR
        
        # 1. 파일명 번호 추출용
        def extract_number(n):
            nums = re.findall(r'\d+', n)
            return int(nums[0]) if nums else 0

        # 원본 이미지 로드
        png_files = sorted([f for f in os.listdir(wp) if f.endswith(".png")], key=extract_number)
        
        # 그록 비디오 로드
        grok_videos = []
        is_direct_folder_mode = False
        
        # 💡 형님 요청 기능: grok-videos- 폴더명 자동 탐색
        grok_folders = [os.path.join(DOWNLOADS_DIR, d) for d in os.listdir(DOWNLOADS_DIR) 
                        if os.path.isdir(os.path.join(DOWNLOADS_DIR, d)) and "grok-videos-" in d]
        
        if grok_folders:
            grok_done_dir = max(grok_folders, key=os.path.getmtime)
            print(f"🎬 [Grok 비디오 폴더 감지] {os.path.basename(grok_done_dir)}")
            grok_videos = [os.path.join(grok_done_dir, f) for f in os.listdir(grok_done_dir) if f.endswith(".mp4")]
            # 다운로드 시간(생성시간) 순으로 정확히 정렬하여 순번 강제 매칭
            grok_videos.sort(key=os.path.getmtime)
            is_direct_folder_mode = True
        elif os.path.exists(grok_done_dir):
            grok_videos = [os.path.join(grok_done_dir, f) for f in os.listdir(grok_done_dir) if f.endswith(".mp4")]

        print(f"✅ 리소스 탐색: 원본 이미지 {len(png_files)}장 / 그록 동영상 {len(grok_videos)}개")

        # 인덱스 카운팅 (01, 02 순번 유지를 위해)
        match_count = 0
        cinema_count = 0
        
        # 다운로드 폴더 전용 인덱스
        direct_v_idx = 0 

        for i, png_name in enumerate(png_files):
            orig_num = extract_number(png_name)
            num_prefix = f"{orig_num:03d}" # 원본 이미지 번호 그대로 유지
            png_path = os.path.join(wp, png_name)
            cinematic_path = png_path.replace(".png", ".mp4") # 시네마틱 mp4
            
            p_img = cv2.imread(png_path)
            scaled_p = cv2.resize(p_img, (256, 256)) if p_img is not None else None
            
            best_match = None
            best_score = 0.0

            if scaled_p is not None:
                # [복구] 안전하고 강력한 OpenCV 시각적 유사도 매칭 수행
                for gv in grok_videos:
                    video_thumb = self.get_best_frame_from_video(gv)
                    if video_thumb is not None:
                        score = self.compare_images(scaled_p, video_thumb)
                        
                        # 파일명 기반 가산점: 숫자가 일치하면 매치 확률 상승
                        gv_num = extract_number(os.path.basename(gv))
                        if gv_num > 0 and gv_num == orig_num:
                            score += 0.35  # 가산점 (35%)
                            
                        if score > best_score and score > 0.45: # 임계값 완화
                            best_score = score
                            best_match = gv

            # [핵심] 찾았으면 정렬 복사
            if best_match:
                # 파일명 생성 e.g. 001_Grok영상.mp4
                dest_name = f"{num_prefix}_01_그록.mp4"
                dest_path = os.path.join(output_dir, dest_name)
                shutil.copy(best_match, dest_path)
                print(f"  🔗 [매치] {png_name} ➡️ {dest_name} (CV유사율: {best_score:.2f})")
                match_count += 1
                # 중복 매치 방지
                try: 
                    grok_videos.remove(best_match) 
                except: pass
            else:
                #  fallback: 시네마틱 연계
                if os.path.exists(cinematic_path):
                    dest_name = f"{num_prefix}_02_시네마틱.mp4"
                    dest_path = os.path.join(output_dir, dest_name)
                    shutil.copy(cinematic_path, dest_path)
                    print(f"  🎥 [연계] {png_name} ➡️ {dest_name}")
                    cinema_count += 1
                else:
                    print(f"  ⚠️ [유실] {png_name} 에 대응하는 비디오를 찾지 못했습니다.")

        print("\n==========================================")
        print("🎉 파일 정렬 정리가 안료되었습니다!")
        print(f"✅ 그록 배치: {match_count}개 / 시네마틱 연계: {cinema_count}개")
        print(f"📂 폴더를 열고 전체 동영상을 드래그하여 캡컷(CapCut)에 넣으세요.")
        print("==========================================")

if __name__ == "__main__":
    sorter = GrokVideoSorter()
    sorter.run()
