#!/bin/bash
cd "/Users/a12/projects/tts"
echo "🔄 [이미지 번호 역순 정렬] 가동 중..."
echo "지정된 폴더 내의 이미지 번호를 1번부터 이쁘게 뒤집습니다."
echo ""
/Users/a12/miniforge3/bin/python "00_이미지_번호_역순정렬.py"
echo ""
echo "✅ 번호 뒤집기가 완료되었습니다!"
read -p "엔터를 누르면 종료됩니다..."
