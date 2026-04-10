#!/bin/bash
cd "$(dirname "$0")"
chmod +x ./07_최종_마스터_통합.sh
./07_최종_마스터_통합.sh
echo ""
echo "최종 렌더링이 완료되었습니다. 엔터를 누르면 종료됩니다."
read
