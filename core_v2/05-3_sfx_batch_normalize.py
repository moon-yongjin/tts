import os
import shutil
from pydub import AudioSegment

def batch_normalize_sfx():
    print("\n==========================================")
    print("🔊 [효과음 폴더 일괄 밸런스 정렬 시스템]")
    print("==========================================")

    BASE_DIR = "/Users/a12/projects/tts/core_v2"
    
    # 🚀 사용자 피드백 반영: 여러 sfx 폴더를 순회하도록 리스트화
    SFX_DIRS = [
        os.path.join(BASE_DIR, "Library", "sfx"),
        os.path.join(BASE_DIR, "sfx")
    ]
    
    # 1. 백업 폴더 생성
    backup_dir = os.path.join(BASE_DIR, "sfx_original_backup")
    os.makedirs(backup_dir, exist_ok=True)
    print(f"📂 원본 백업용 임시 보관소 생성: {backup_dir}")

    # 2. 파일 목록 수집
    supported_exts = (".mp3", ".wav", ".m4a")
    sfx_files_with_dir = []
    
    for sfx_dir in SFX_DIRS:
        if os.path.exists(sfx_dir):
            # (폴더경로, 파일명) 튜플로 수집
            files = [(sfx_dir, f) for f in os.listdir(sfx_dir) if f.lower().endswith(supported_exts)]
            sfx_files_with_dir.extend(files)
    
    if not sfx_files_with_dir:
        print("ℹ️ 대상 확장자 파일이 없습니다.")
        return

    print(f"📄 총 {len(sfx_files_with_dir)}개의 효과음 파일을 볼륨 정렬합니다.")
    print("--- 🤖 가동 작동 ---")

    TARGET_DBFS = -20.0  # 🚀 표준 평균 음량 (나레이션 핏)
    success_count = 0

    for sfx_dir, filename in sfx_files_with_dir:
        file_path = os.path.join(sfx_dir, filename)
        backup_path = os.path.join(backup_dir, filename)

        try:
            # A. 가변 타입 로드
            sound = AudioSegment.from_file(file_path)
            
            # 음량이 너무 0에 수렴하면 연산 에러가 나므로 가드
            if sound.dBFS == float('-inf'):
                print(f"⚠️ {filename} : 무음 파일로 분류되어 스킵합니다.")
                continue

            # B. 백업 (이미 백업이 있으면 덮어쓰지 않음으로써 원본 사수)
            if not os.path.exists(backup_path):
                 shutil.copy2(file_path, backup_path)

            # C. 노멀라이즈 연산 (dBFS 매칭)
            gain_to_apply = TARGET_DBFS - sound.dBFS
            normalized_sound = sound.apply_gain(gain_to_apply)

            # D. 원본 덮어쓰기 저장
            fmt = os.path.splitext(filename)[1].replace('.', '').lower()
            if fmt == 'm4a': fmt = 'mp4'

            normalized_sound.export(file_path, format=fmt)
            print(f"✅ 볼륨 보충 [정렬]: {filename} ({sound.dBFS:.1f} dB ➡️ {TARGET_DBFS} dB)")
            success_count += 1

        except Exception as e:
            print(f"❌ {filename} 처리 실패: {str(e)}")

    print("\n==========================================")
    print(f"🎉 정리 완료! 총 {success_count}개의 효과음 볼륨이 -20dBFS 로 연성되었습니다.")
    print(f"💡 기존 원본들은 'sfx_original_backup' 에 보존되어 안심하셔도 됩니다.")
    print("==========================================")

if __name__ == "__main__":
    batch_normalize_sfx()
