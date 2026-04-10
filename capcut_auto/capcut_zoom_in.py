import os
import json
import shutil
import re
import uuid
from pathlib import Path
from datetime import datetime

# ================== 설정 영역 ==================
MEDIA_FOLDER = Path("/Users/a12/Downloads/무협_생성")   # 이미지+영상 폴더
CAPCUT_PROJECTS_BASE = Path("/Users/a12/Movies/CapCut/User Data/Projects/com.lveditor.draft")
IMAGE_DURATION_SEC = 3.0
FPS = 30
# ===============================================

def get_latest_project():
    """가장 최근에 수정된 캡컷 프로젝트 폴더를 찾습니다."""
    projects = [p for p in CAPCUT_PROJECTS_BASE.iterdir() if p.is_dir() and not p.name.startswith('.')]
    if not projects:
        return None
    # 수정 시간 기준 정렬
    latest_project = max(projects, key=lambda p: p.stat().st_mtime)
    return latest_project

def extract_number(filename):
    numbers = re.findall(r'\d+', filename)
    return int(numbers[0]) if numbers else 999999

def get_media_type(filepath):
    ext = filepath.suffix.lower()
    if ext in ['.mp4', '.mov', '.avi', '.mkv']:
        return 'video'
    elif ext in ['.jpg', '.jpeg', '.png', '.webp']:
        return 'image'
    return None

def generate_uuid():
    return str(uuid.uuid4()).upper()

def main():
    project_folder = get_latest_project()
    if not project_folder:
        print(f"❌ '{CAPCUT_PROJECTS_BASE}'에서 프로젝트를 찾을 수 없습니다.")
        return

    print(f"🎬 CapCut Mac 자동 배치 시작")
    print(f"📁 대상 프로젝트: {project_folder.name}")
    print(f"🖼️ 미디어 폴더: {MEDIA_FOLDER.name}")

    json_path = project_folder / "draft_info.json"

    # 백업
    backup_path = json_path.with_name(f"draft_info_backup_{datetime.now().strftime('%m%d_%H%M%S')}.json")
    shutil.copy2(json_path, backup_path)
    print(f"✅ 백업 완료: {backup_path.name}")

    # 파일 수집
    media_files = []
    exts = ["*.jpg", "*.jpeg", "*.png", "*.webp", "*.mp4", "*.mov"]
    for ext in exts:
        media_files.extend(list(MEDIA_FOLDER.glob(ext.lower())))
        media_files.extend(list(MEDIA_FOLDER.glob(ext.upper())))
    
    media_files = sorted(list(set(media_files)), key=lambda f: extract_number(f.name))
    print(f"📄 총 {len(media_files)}개의 미디어 파일 발견")

    with open(json_path, 'r', encoding='utf-8') as f:
        draft = json.load(f)

    # materials/videos 섹션 확보
    if "materials" not in draft: draft["materials"] = {"videos": []}
    if "videos" not in draft["materials"]: draft["materials"]["videos"] = []
    
    video_materials = draft["materials"]["videos"]
    video_track = next((t for t in draft.get("tracks", []) if t.get("type") == "video"), None)
    
    if not video_track:
        print("❌ Video 트랙을 찾을 수 없습니다. 프로젝트를 확인하세요.")
        return

    # 기존 트랙 비우기 (새로 고침)
    video_track["segments"] = []
    
    current_time_us = 0
    pattern_idx = 0

    base_zoom = 1.10
    pan_offset = 0.05

    for file_path in media_files:
        mtype = get_media_type(file_path)
        if not mtype: continue

        material_id = generate_uuid()
        segment_id = generate_uuid()
        
        # 3초 (마이크로초 단위)
        duration_us = int(IMAGE_DURATION_SEC * 1000000)
        
        # 패턴 정의: Zoom In + Pan 교차
        patterns = [
            {"s": 1.0, "x": 0.0, "y": 0.0, "es": base_zoom, "ex": pan_offset, "ey": 0.0},        # Right
            {"s": 1.0, "x": 0.0, "y": 0.0, "es": base_zoom, "ex": -pan_offset, "ey": 0.0},       # Left
            {"s": 1.0, "x": 0.0, "y": 0.0, "es": base_zoom, "ex": 0.0, "ey": -pan_offset},      # Up
            {"s": 1.0, "x": 0.0, "y": 0.0, "es": base_zoom, "ex": 0.0, "ey": pan_offset},       # Down
        ]
        p = patterns[pattern_idx % 4]

        # 1. Material 등록
        material_entry = {
            "id": material_id,
            "path": str(file_path),
            "type": "video" if mtype == 'video' else "image",
            "duration": duration_us if mtype == 'image' else 10000000,
            "local_path": str(file_path),
            "width": 1920,
            "height": 1080
        }
        video_materials.append(material_entry)

        # 2. Segment 생성
        segment = {
            "id": segment_id,
            "material_id": material_id,
            "target_timerange": {"start": current_time_us, "duration": duration_us},
            "source_timerange": {"start": 0, "duration": duration_us},
            "render_timerange": {"start": 0, "duration": duration_us},
            "speed": 1.0,
            "volume": 1.0,
            "visible": True,
            "clip": {
                "scale": {"x": p["es"], "y": p["es"]},
                "transform": {"x": p["ex"], "y": p["ey"]},
                "rotation": 0.0,
                "flip": {"vertical": False, "horizontal": False},
                "alpha": 1.0
            },
            "uniform_scale": {"on": True, "value": p["es"]},
            "common_keyframes": [
                {
                    "id": generate_uuid(),
                    "time": 0,
                    "keyframe_list": [
                        {"id": generate_uuid(), "property_type": "scale", "value": p["s"]},
                        {"id": generate_uuid(), "property_type": "transform_x", "value": p["x"]},
                        {"id": generate_uuid(), "property_type": "transform_y", "value": p["y"]}
                    ]
                },
                {
                    "id": generate_uuid(),
                    "time": duration_us - 1,
                    "keyframe_list": [
                        {"id": generate_uuid(), "property_type": "scale", "value": p["es"]},
                        {"id": generate_uuid(), "property_type": "transform_x", "value": p["ex"]},
                        {"id": generate_uuid(), "property_type": "transform_y", "value": p["ey"]}
                    ]
                }
            ]
        }
        
        video_track["segments"].append(segment)
        current_time_us += duration_us
        pattern_idx += 1

    draft["update_time"] = int(datetime.now().timestamp() * 1000000)
    draft["duration"] = current_time_us

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(draft, f, ensure_ascii=False, indent=4)

    print(f"✅ 작업 완료! {len(media_files)}개 클립 배치됨 (총 {current_time_us/1000000:.1f}초)")

if __name__ == "__main__":
    main()
