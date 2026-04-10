#!/usr/bin/env python3
"""
영상 생성 스크립트
음성 길이에 맞춰 이미지를 자동으로 배치하여 영상 생성
"""

import os
import subprocess
from pathlib import Path
import json

class VideoGenerator:
    def __init__(self, audio_path, images_dir, output_path, num_images=48):
        """
        Args:
            audio_path: 음성 파일 경로 (MP3)
            images_dir: 이미지 폴더 경로
            output_path: 출력 영상 경로 (MP4)
            num_images: 이미지 수량 (기본 48장)
        """
        self.audio_path = Path(audio_path)
        self.images_dir = Path(images_dir)
        self.output_path = Path(output_path)
        self.num_images = num_images
        
    def get_audio_duration(self):
        """음성 파일 길이 측정 (초)"""
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'json',
            str(self.audio_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(result.stdout)
        duration = float(data['format']['duration'])
        print(f"🎵 음성 길이: {duration:.2f}초")
        return duration
    
    def get_image_files(self):
        """이미지 파일 목록 가져오기 (정렬)"""
        images = sorted(self.images_dir.glob("Scene_*.png"))
        print(f"🖼️  이미지 수: {len(images)}장")
        return images[:self.num_images]
    
    def create_video_basic(self):
        """기본 영상 생성 (키프레임만)"""
        print("\n🎬 영상 생성 시작...")
        
        # 1. 음성 길이 측정
        audio_duration = self.get_audio_duration()
        
        # 2. 이미지 목록
        images = self.get_image_files()
        if len(images) == 0:
            print("❌ 이미지가 없습니다!")
            return False
        
        # 3. 이미지당 시간 계산
        duration_per_image = audio_duration / len(images)
        print(f"📊 이미지당 시간: {duration_per_image:.2f}초")
        
        # 4. 이미지 리스트 파일 생성
        concat_file = self.images_dir / "concat_list.txt"
        with open(concat_file, 'w') as f:
            for img in images:
                f.write(f"file '{img.absolute()}'\n")
                f.write(f"duration {duration_per_image}\n")
            # 마지막 이미지는 duration 없이
            f.write(f"file '{images[-1].absolute()}'\n")
        
        # 5. FFmpeg로 영상 생성
        cmd = [
            'ffmpeg',
            '-y',  # 덮어쓰기
            '-f', 'concat',
            '-safe', '0',
            '-i', str(concat_file),
            '-i', str(self.audio_path),
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-c:a', 'aac',
            '-shortest',
            str(self.output_path)
        ]
        
        print("⚙️  FFmpeg 실행 중...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ 영상 생성 완료: {self.output_path}")
            # 파일 크기 확인
            size_mb = self.output_path.stat().st_size / (1024 * 1024)
            print(f"📦 파일 크기: {size_mb:.2f}MB")
            return True
        else:
            print(f"❌ FFmpeg 에러:\n{result.stderr}")
            return False
    
    def create_video_with_transitions(self):
        """전환 효과 포함 영상 생성 (차후 구현)"""
        # TODO: fade, slide, zoom 효과 추가
        pass
    
    def add_subtitles(self, srt_path):
        """자막 추가 (차후 구현)"""
        # TODO: SRT 파일 기반 자막 오버레이
        pass
    
    def add_bgm(self, bgm_path, volume=0.3):
        """배경음악 믹싱 (차후 구현)"""
        # TODO: BGM 믹싱
        pass

def main():
    import sys
    
    # 사용법: python video_generator.py [이미지수량]
    num_images = int(sys.argv[1]) if len(sys.argv) > 1 else 48
    
    # 경로 설정
    audio_path = "~/Downloads/Final_Turbo_Qwen_0210_1600.mp3"
    images_dir = "~/Downloads/Drama48"
    output_path = "~/Downloads/Final_Drama_Video.mp4"
    
    # 경로 확장
    audio_path = os.path.expanduser(audio_path)
    images_dir = os.path.expanduser(images_dir)
    output_path = os.path.expanduser(output_path)
    
    # 영상 생성
    generator = VideoGenerator(audio_path, images_dir, output_path, num_images)
    success = generator.create_video_basic()
    
    if success:
        print("\n🎉 완료!")
        print(f"📁 출력: {output_path}")
    else:
        print("\n❌ 실패!")
        sys.exit(1)

if __name__ == "__main__":
    main()
