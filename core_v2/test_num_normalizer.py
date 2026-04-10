import re

def number_to_korean(num_str):
    """숫자 문자열을 한국어(한자어)로 변환"""
    # 쉼표 등 제거
    num_str = num_str.replace(',', '')
    if not num_str.isdigit():
        return num_str

    try:
        num = int(num_str)
    except ValueError:
        return num_str

    if num == 0:
        return "영"

    units = ["", "십", "백", "천"]
    large_units = ["", "만", "억", "조", "경"]
    digits = ["", "일", "이", "삼", "사", "오", "육", "칠", "팔", "구"]

    result = ""
    str_num = str(num)
    length = len(str_num)

    for i, d in enumerate(str_num):
        digit = int(d)
        if digit != 0:
            # 십, 백, 천 자리에 '일'이 오면 생략 (예: 일십 -> 십, 단 1억 등은 '일억'도 허용되지만 일반적 축약)
            pos = length - 1 - i
            unit_pos = pos % 4
            large_unit_pos = pos // 4

            digit_str = digits[digit]
            if unit_pos > 0 and digit == 1:
                digit_str = "" # 십, 백, 천 앞의 '일'은 생략 (십, 백, 천으로 읽음)

            result += digit_str + units[unit_pos]

        # 4자리마다 '만', '억' 단위 추가
        pos = length - 1 - i
        if pos > 0 and pos % 4 == 0:
            # 해당 4자리 블록에 숫자가 하나라도 있었거나, 0이 아닌 경우에만 만/억 추가
            # 단순 구현을 위해 끝에 단위 추가하는 보정
            current_block = str_num[max(0, i-3):i+1]
            # 만약 4자리 블록이 모두 0이면 단위 생략 (예: 1,0000,0000 -> 일억)
            if large_unit_pos > 0 and any(int(x) > 0 for x in str_num[max(0, length - (large_unit_pos+1)*4) : length - large_unit_pos*4]):
                 if not result.endswith(large_units[large_unit_pos]):
                      result += large_units[large_unit_pos]

    # 예외 보정: "일십" -> "십", "백", "천" 맨 앞 단독 1 생략
    if result.startswith("일십"): result = result[1:]
    if result.startswith("일백"): result = result[1:]
    if result.startswith("일천"): result = result[1:]
    # 만 단위 이상에서 앞자리 1일억 등 부자연스러운 문구 보정 (모델에 따라 다름)

    return result

def normalize_numbers(text):
    # 숫자 패턴 찾기 (쉼표 포함된 숫자도 처리 가능하도록)
    pattern = r'\d+(?:,\d+)*'
    
    def replacer(match):
        return number_to_korean(match.group(0))
        
    return re.sub(pattern, replacer, text)

# 테스트
if __name__ == "__main__":
    tests = ["1234", "10000", "100000000", "2026", "전화번호는 123-456 입니다.", "1,234원"]
    for t in tests:
        # 단, 하이픈 있는 번호 등은 normalize_numbers 패턴이 단순하여 123-456 에서 숫자로 찢어짐.
        # 일반 대본 설명(문맥 용)으로는 충분함.
        print(f"{t} -> {normalize_numbers(t)}")
