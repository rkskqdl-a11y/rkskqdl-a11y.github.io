import os
import hmac
import hashlib
import requests
import json
from time import gmtime, strftime
import random
from urllib.parse import urlencode, quote_plus

# 쿠팡 API 키는 깃허브 Secrets에서 가져옴
ACCESS_KEY = os.environ.get('COUPANG_ACCESS_KEY')
SECRET_KEY = os.environ.get('COUPANG_SECRET_KEY')

if not ACCESS_KEY or not SECRET_KEY:
    print("Error: COUPANG_ACCESS_KEY or COUPANG_SECRET_KEY not found in environment variables.")
    raise ValueError("Missing Coupang API keys. Please set COUPANG_ACCESS_KEY and COUPANG_SECRET_KEY in GitHub Secrets.")

DOMAIN = "https://api-gateway.coupang.com"

# 쿠팡 파트너스 공식 문서에 있는 HMAC 서명 생성 함수 그대로 사용
def generateHmac(method, url_for_hmac, secretKey, accessKey):
    path, *query = url_for_hmac.split("?")
    datetimeGMT = strftime('%y%m%d', gmtime()) + 'T' + strftime('%H%M%S', gmtime()) + 'Z'
    message = datetimeGMT + method + path + (query[0] if query else "")

    signature = hmac.new(bytes(secretKey, "utf-8"),
                         message.encode("utf-8"),
                         hashlib.sha256).hexdigest()

    return "CEA algorithm=HmacSHA256, access-key={}, signed-date={}, signature={}".format(accessKey, datetimeGMT, signature)

def call_coupang_partners_api(method, api_path, query_params=None, body_payload=None):
    
    url_for_hmac_sign = api_path
    if query_params:
        encoded_query_string = urlencode(query_params, quote_via=quote_plus)
        url_for_hmac_sign = f"{api_path}?{encoded_query_string}"

    authorization = generateHmac(method, url_for_hmac_sign, SECRET_KEY, ACCESS_KEY)
    
    full_request_url = f"{DOMAIN}{url_for_hmac_sign}"
    
    headers = {
        "Authorization": authorization,
        "Content-Type": "application/json" if body_payload else "application/json"
    }

    if method == "GET":
        response = requests.request(method="GET", url=full_request_url, headers=headers)
    elif method == "POST":
        response = requests.request(method="POST", url=full_request_url, headers=headers, data=json.dumps(body_payload))
    
    response.raise_for_status()
    return response.json()

def search_products_api(keyword, page=1, limit=50):
    api_path = "/v2/providers/affiliate_open_api/apis/openapi/products/search"
    query_params = {
        "keyword": keyword,
        "limit": limit,
        "offset": (page-1)*limit
    }
    return call_coupang_partners_api("GET", api_path, query_params=query_params)

# -------- 딥링크 생성 API는 이제 필요 없어졌으니 이 함수를 호출하지 않도록 할 거야! --------
# def create_deeplinks_api(coupang_urls_list):
#     api_path = "/v2/providers/affiliate_open_api/apis/openapi/v1/deeplink"
#     body_payload = { 
#         "coupangUrls": coupang_urls_list
#     }
#     return call_coupang_partners_api("POST", api_path, body_payload=body_payload)


# -------- 메인 함수 --------
if __name__ == "__main__":
    try:
        SEARCH_KEYWORDS_LIST = [
            "노트북", "캠핑용품", "아이폰15", "무선 이어폰", "게이밍 마우스",
            "에어프라이어", "로봇청소기", "캡슐커피머신", "전기 주전자", "토스터기",
            "믹서기", "제습기", "가습기", "선풍기", "에어컨", "온수매트",
            "블루투스 스피커", "태블릿", "스마트워치", "외장하드", "USB 메모리",
            "핸드폰 케이스", "무선 충전기", "차량용 거치대", "블랙박스", "네비게이션",
            "가정용 빔프로젝터", "사운드바", "TV 스탠드", "모니터암", "키보드", "마우스",
            "게이밍 헤드셋", "웹캠", "콘덴서 마이크", "LED 스탠드", "의자", "책상",
            "선반", "수납함", "커튼", "러그", "침구세트", "베개", "이불", "매트리스 커버",
            "욕실 용품", "주방 용품", "프라이팬", "냄비", "도마", "칼 세트", "식기건조대",
            "세탁세제", "섬유유연제", "청소기", "물걸레 청소기", "스팀다리미", "드라이기",
            "고데기", "전동 칫솔", "구강세정기", "영양제", "비타민", "유산균", "콜라겐",
            "단백질 보충제", "운동복", "요가매트", "덤벨", "자전거", "런닝머신",
            "골프채", "낚싯대", "드론", "액션캠", "미러리스 카메라", "렌즈", "삼각대",
            "백팩", "캐리어", "여행용 파우치", "목베개", "보조배터리", "등산화",
            "운동화", "슬리퍼", "샌들", "선글라스", "모자", "장갑", "양말", "속옷",
            "청바지", "티셔츠", "가디건", "자켓", "코트", "원피스", "스커트", "바지",
            "구두", "워커", "로퍼", "향수", "화장품 세트", "수분 크림", "선크림",
            "샴푸", "린스", "바디워시", "핸드크림", "마스크팩", "네일", "헤어 에센스",
            "공기청정기 필터", "정수기 필터", "세탁기 청소 세제", "세면대 청소 세제",
            "자동차 와이퍼", "에어 필터", "엔진 오일", "타이어 광택제", "세차 용품",
            "장난감", "인형", "블록", "퍼즐", "보드게임", "유모차", "카시트", "아기띠",
            "분유", "기저귀", "물티슈", "젖병", "턱받이", "온도계", "체온계",
            "강아지 사료", "고양이 사료", "배변 패드", "고양이 모래", "캣타워", "강아지 집",
            "책", "소설", "에세이", "자기계발서", "아동 도서", "만화책", "잡지",
            "연필", "볼펜", "노트", "다이어리", "형광펜", "지우개", "파일", "클립"
        ]
        
        selected_keyword = random.choice(SEARCH_KEYWORDS_LIST)
        FETCH_PRODUCT_LIMIT = 2 # 테스트니까 2개! (나중에 30개로 바꿀거임)

        print(f"랜덤 키워드 선택: '{selected_keyword}'")
        print(f"'{selected_keyword}' 상품 검색 시도...")
        
        search_results = search_products_api(selected_keyword, limit=FETCH_PRODUCT_LIMIT)
        
        if not search_results or not search_results.get('data') or not search_results['data'].get('productData'):
            print(f"'{selected_keyword}' 검색 결과 없음. 또는 데이터 구조 문제.")
            exit(0)

        product_items = search_results['data']['productData'] 
        
        # <<<<<<<<<<<< 딥링크 생성 API 호출 없이 바로 파트너스 URL 출력!  >>>>>>>>>>>>>
        print("\n--- 최종 파트너스 URL ---")
        if product_items:
            for item in product_items:
                product_name = item.get('productName', '이름 없음')
                partner_url = item.get('productUrl') # 이미 이게 파트너스 URL이야!
                if partner_url:
                    print(f"상품명: {product_name}")
                    print(f"파트너스 URL: {partner_url}\n")
                else:
                    print(f"상품명: {product_name}, 파트너스 URL 없음.")
        else:
            print("검색된 상품이 없습니다.")

        # # 딥링크 생성 API 관련 코드는 모두 삭제 또는 주석 처리!
        # # ... (이전의 딥링크 생성 API 호출 및 처리 로직들) ...
        # # 이제는 이 부분이 필요 없음!

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP 오류 발생: {http_err.response.status_code} - {http_err.response.text}")
        print(f"응답 본문: {http_err.response.text}")
        raise
    except Exception as e:
        print(f"API 호출 중 예기치 않은 오류 발생: {e}")
        raise
