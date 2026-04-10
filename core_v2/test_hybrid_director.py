from video_director_standalone import generate_hybrid_video
import os
import glob

def test_hybrid():
    d = os.path.join(os.path.expanduser("~"), "Downloads")
    subdirs = glob.glob(os.path.join(d, "무협_생성_*"))
    if not subdirs:
        print("❌ 폴더 없음")
        return
    
    latest_dir = max(subdirs, key=os.path.getmtime)
    images = sorted(glob.glob(os.path.join(latest_dir, "*.png")))
    
    if len(images) < 2:
        print("❌ 테스트할 이미지가 부족합니다.")
        return

    # 테스트 1: 인물이 확실한 096번 (또는 뒷번호)
    img_pro = images[-1]
    out_pro = "test_hybrid_parallax.mp4"
    print(f"🧪 테스트 1 (패럴랙스 예상): {os.path.basename(img_pro)}")
    generate_hybrid_video(img_pro, out_pro, 96, duration=5.0)
    
    # 테스트 2: 인물이 없을 수도 있는 001번 (스케치/나레이션 위주)
    img_std = images[0]
    out_std = "test_hybrid_standard.mp4"
    print(f"🧪 테스트 2 (일반 fallback 예상): {os.path.basename(img_std)}")
    generate_hybrid_video(img_std, out_std, 1, duration=5.0)

if __name__ == "__main__":
    test_hybrid()
