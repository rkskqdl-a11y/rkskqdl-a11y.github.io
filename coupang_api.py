import os
import requests
import hmac
import hashlib
import json
from time import gmtime, strftime
import random 

# 쿠팡 API 키는 깃허브 Secrets에서 가져옴
ACCESS_KEY = os.environ.get('COUPANG_ACCESS_KEY')
SECRET_KEY = os.environ.get('COUPANG_SECRET_KEY')

if not ACCESS_KEY or not SECRET_KEY:
    print("Error: COUPANG_ACCESS_KEY or COUPANG_SECRET_KEY not found in environment variables.")
    raise ValueError("Missing Coupang API keys. Please set COUPANG_ACCESS_KEY and COUPANG_SECRET_KEY in GitHub Secrets.")

# 파트너스 API의 기본 도메인은 이걸로 고정
DOMAIN = "https://api-gateway.coupang.com" 

# HMAC 시그니처 생성 함수 - 파트너스 API 규칙 (DeepLink와 Product Search 모두 동일)
def generate_hmac_signature(method, url, secret_key, access_key):
    path, *query = url.split("?")
    
    datetime_gmt = strftime('%y%m%d', gmtime()) + 'T' + strftime('%H%M%S', gmtime()) + 'Z'
    
    message_content = path
    if query:
        # 쿼리가 있다면 ?와 함께 path에 붙임
        message_content += "?" + query[0]

    message = datetime_gmt + method + message_content
    
    signature = hmac.new(bytes(secret_key, "utf-8"),
                         message.encode("utf-8"),
                         hashlib.sha256).hexdigest()

    return "CEA algorithm=HmacSHA256, access-key={}, signed-date={}, signature={}".format(access_key, datetime_gmt, signature)


# 쿠팡 파트너스 API 호출 함수 (모든 파트너스 API 요청에 사용)
def call_coupang_partners_api(method, url, payload=None):
    authorization = generate_hmac_signature(method, url, SECRET_KEY, ACCESS_KEY)
    headers = {
        "Authorization": authorization,
        "Content-Type": "application/json" if payload else "application/x-www-form-urlencoded" # payload 있으면 json, 없으면 form
    }

    full_url = f"{DOMAIN}{url}"
    
    if method == "GET":
        response = requests.get(full_url, headers=headers)
    elif method == "POST":
        response = requests.post(full_url, headers=headers, data=json.dumps(payload) if payload else None)
    
    response.raise_for_status() # HTTP 4xx, 5xx 에러 발생 시 예외 throw
    return response.json()

# 상품 검색 API 호출 함수 (오직 파트너스 API에서 상품 검색에 사용!)
def search_products(keyword, page=1, limit=50): # limit 기본값 50으로 올림 (API 최대 50개)
    # 파트너스 API 상품 검색 엔드포인트!
    url_path = f"/v2/providers/affiliate_open_api/apis/openapi/products/search"
    # 쿼리 파라미터는 따로 전달
    params = {
        "keyword": keyword,
        "limit": limit,
        "offset": (page - 1) * limit
    }
    # 쿼리 스트링 만들기
    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
    
    full_url_with_query = f"{url_path}?{query_string}"
    
    return call_coupang_partners_api("GET", full_url_with_query)


# 메인 함수: 실제 상품 검색 후 딥링크 생성까지
if __name__ == "__main__":
    try:
        # 여기에 네가 검색할 "엄청 많은 키워드 리스트"를 넣어줘!
        # 매번 돌릴 때마다 이 리스트에서 '랜덤으로 하나' 뽑아서 검색할 거야.
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
        
        # 키워드 리스트에서 랜덤으로 하나 선택
        SEARCH_KEYWORD = random.choice(SEARCH_KEYWORDS_LIST)
        PRODUCTS_TO_FETCH = 2 # 일단 테스트니까 2개만 가져올게! (나중에 30개로 바꿀거임)

        print(f"랜덤으로 선택된 키워드: '{SEARCH_KEYWORD}'")
        print(f"'{SEARCH_KEYWORD}' 상품 검색 시도...")
        search_results = search_products(SEARCH_KEYWORD, limit=PRODUCTS_TO_FETCH)
        
        # 검색 결과가 있는지 확인
        if not search_results or not search_results.get('data'):
            print(f"'{SEARCH_KEYWORD}' 검색 결과 없음.")
            # 오류는 아니지만, 상품이 없으면 종료
            exit(0) # 성공적으로 종료 (상품 없음)

        product_urls_to_deeplink = []
        print("\n--- 검색된 상품 정보 ---")
        for item in search_results['data']:
            product_name = item.get('productName', '이름 없음')
            # 파트너스 API 상품 검색 결과에서는 'productUrl' 필드를 직접 제공함
            product_url = item.get('productUrl') 
            if product_url:
                print(f"상품명: {product_name}, URL: {product_url}")
                product_urls_to_deeplink.append(product_url)
            else:
                print(f"상품명: {product_name}, URL 없음.")

        if not product_urls_to_deeplink:
            print("딥링크를 생성할 상품 URL이 없습니다.")
            exit(0) # 성공적으로 종료 (URL 없음)

        # 검색된 상품 URL들로 딥링크 생성 요청
        deeplink_request_payload = { 
            "coupangUrls": product_urls_to_deeplink
        }
        
        DEEPLINK_API_URL = "/v2/providers/affiliate_open_api/apis/openapi/v1/deeplink"

        print(f"\n검색된 상품으로 딥링크 생성 시도...")
        deeplink_response = call_coupang_partners_api("POST", DEEPLINK_API_URL, deeplink_request_payload)
        
        print("\n--- 생성된 딥링크 ---")
        # 생성된 딥링크 출력
        if deeplink_response and deeplink_response.get('data'):
            for link_data in deeplink_response['data']:
                original_url = link_data.get('originalUrl')
                shorten_url = link_data.get('shortenUrl') # 이게 네가 사용할 쿠팡 파트너스 링크야!
                print(f"원본 URL: {original_url}")
                print(f"파트너스 URL: {shorten_url}\n")
        else:
            print("딥링크 생성에 실패했습니다. 응답 데이터가 유효하지 않습니다.")

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP 오류 발생: {http_err.response.status_code} - {http_err.response.text}")
        raise # 깃허브 액션 실패로 알리기 위해 다시 예외 발생
    except Exception as e:
        print(f"API 호출 중 예기치 않은 오류 발생: {e}")
        raise # 깃허브 액션 실패로 알리기 위해 다시 예외 발생
