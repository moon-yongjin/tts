#!/bin/bash

# 📱 폰팜(Phone Farm) 일괄 미러링 및 제어 스크립트

echo "=================================================="
echo "   📱 다중 스마트폰 그리드 미러링 (scrcpy) 가동"
echo "=================================================="

# 1. 연결된 ADB 디바이스 목록 추출
DEVICES=$(adb devices | grep -w "device" | awk '{print $1}')

if [ -z "$DEVICES" ]; then
    echo "❌ 연결된 스마트폰이 없습니다."
    echo "💡 [조치 방법] 기기에서 'USB 디버깅'이 켜져 있는지, 케이블이 잘 꼽혔는지 확인하세요."
    exit 1
fi

echo "✅ 감지된 디바이스 목록:"
echo "$DEVICES"
echo "--------------------------------------------------"

# 2. 각 기기별로 scrcpy 구동 (그리드 정렬 등 옵션 적용 가능)
COUNT=0
for DEV in $DEVICES; do
    COUNT=$((COUNT+1))
    echo "▶️ [$COUNT] 디바이스 미러링 시작: $DEV"
    
    # scrcpy 실행 옵션: 
    # -s: 특정 디바이스 지정
    # --window-title: 윈도우 제목에 디바이스 ID 표시
    # --max-size: 해상도 제한 (렉 방지 및 프레임 최적화)
    # --max-fps: 프레임 제한
    
    scrcpy -s "$DEV" \
           --window-title "Phone-$COUNT ($DEV)" \
           --max-size 1024 \
           --max-fps 30 \
           --always-on-top \
           &
done

echo "--------------------------------------------------"
echo "🎉 총 $COUNT 대의 스마트폰 미러링이 백그라운드에서 실행되었습니다."
echo "💡 각 화면을 클릭하여 마우스/키보드로 제어할 수 있습니다."
echo "=================================================="
