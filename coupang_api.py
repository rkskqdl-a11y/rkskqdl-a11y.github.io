import os
import hmac
import hashlib
import requests
import json
from time import gmtime, strftime
import random
from urllib.parse import urlencode, quote_plus
from datetime import datetime
import re

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

def search_products_api(keyword, page=1, limit=50): # limit 기본값 50으로 변경 (API 최대)
    api_path = "/v2/providers/affiliate_open_api/apis/openapi/products/search"
    query_params = {
        "keyword": keyword,
        "limit": limit,
        "offset": (page-1)*limit
    }
    return call_coupang_partners_api("GET", api_path, query_params=query_params)

# -------- HTML 페이지 생성 함수 --------
def create_html_page(product_info):
    product_name = product_info['productName']
    partner_url = product_info['partnerUrl']
    product_image = product_info['productImage']
    product_price = product_info['productPrice']
    
    # 대가성 문구 (쿠팡 가이드라인 준수)
    disclosure = "이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다."

    # 파일명으로 사용할 수 없는 문자 제거 및 공백 대체
    safe_product_name = re.sub(r'[\\/*?:"<>|]', '', product_name)
    safe_product_name = safe_product_name.replace(' ', '_')
    filename_base = safe_product_name[:50].strip('_')
    if not filename_base:
        filename_base = "product_" + str(hash(product_name + partner_url))[:8]

    html_filename = f"{filename_base}.html"

    html_content = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{product_name} | 상품 정보</title>
    <meta name="description" content="{product_name} 상세 정보 및 최저가 확인">
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; background-color: #f4f7f6; color: #333; }}
        .container {{ max-width: 800px; margin: auto; background: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }}
        h1 {{ color: #2c3e50; text-align: center; margin-bottom: 30px; font-size: 2.2em; }}
        .product-image {{ text-align: center; margin-bottom: 30px; }}
        .product-image img {{ max-width: 100%; height: auto; border-radius: 8px; border: 1px solid #eee; }}
        .product-detail p {{ font-size: 1.1em; line-height: 1.6; margin-bottom: 10px; }}
        .product-detail strong {{ color: #2980b9; }}
        .buy-button {{ display: block; width: 80%; max-width: 300px; margin: 30px auto; padding: 15px 25px; background-color: #ff5722; color: white; text-align: center; text-decoration: none; border-radius: 8px; font-size: 1.3em; font-weight: bold; transition: background-color 0.3s ease; box-shadow: 0 4px 8px rgba(255,87,34,0.3); }}
        .buy-button:hover {{ background-color: #e64a19; transform: translateY(-2px); }}
        .disclosure {{ text-align: center; font-size: 0.9em; color: #7f8c8d; margin-top: 40px; border-top: 1px solid #eee; padding-top: 20px; }}
        /* 모바일 반응형 */
        @media (max-width: 600px) {{
            .container {{ margin: 10px; padding: 15px; }}
            h1 {{ font-size: 1.8em; }}
            .buy-button {{ width: 95%; padding: 12px 20px; font-size: 1.1em; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{product_name}</h1>
        <div class="product-image">
            <img src="{product_image}" alt="{product_name}">
        </div>
        <div class="product-detail">
            <p><strong>가격:</strong> {product_price:,}원</p>
            <p>쿠팡에서 {product_name}의 최신 가격 및 상세 정보를 확인해보세요.</p>
        </div>
        <a href="{partner_url}" target="_blank" class="buy-button">쿠팡에서 {product_name} 구매하기</a>
        <div class="disclosure">
            {disclosure}
        </div>
    </div>
</body>
</html>
"""
    with open(html_filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return html_filename

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
        FETCH_PRODUCT_LIMIT = 30 # <<<<<<<< 여기 30으로 바꿨어!!!!!!

        print(f"랜덤 키워드 선택: '{selected_keyword}'")
        print(f"'{selected_keyword}' 상품 검색 시도...")
        
        search_results = search_products_api(selected_keyword, limit=FETCH_PRODUCT_LIMIT)
        
        if not search_results or not search_results.get('data') or not search_results['data'].get('productData'):
            print(f"'{selected_keyword}' 검색 결과 없음. 또는 데이터 구조 문제.")
            exit(0)

        product_items = search_results['data']['productData'] 
        
        generated_html_files = []
        
        print(f"\n--- {len(product_items)}개 HTML 페이지 생성 중 ---")
        if product_items:
            for item in product_items:
                product_name = item.get('productName', '이름 없음')
                partner_url = item.get('productUrl')
                product_image = item.get('productImage', '')
                product_price = item.get('productPrice', 0)
                
                if partner_url:
                    product_info_for_html = {
                        "productName": product_name,
                        "partnerUrl": partner_url,
                        "productImage": product_image,
                        "productPrice": product_price
                    }
                    html_file = create_html_page(product_info_for_html)
                    generated_html_files.append(html_file)
                    print(f"-> '{html_file}' 생성 완료")
                else:
                    print(f"상품명: {product_name}, 파트너스 URL 없음. HTML 생성 건너뜀.")
        else:
            print("검색된 상품이 없습니다.")
        
        if generated_html_files:
            print(f"\n총 {len(generated_html_files)}개의 HTML 파일이 생성되었습니다.")
        else:
            print("\n생성된 HTML 파일이 없습니다.")

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP 오류 발생: {http_err.response.status_code} - {http_err.response.text}")
        print(f"응답 본문: {http_err.response.text}")
        raise
    except Exception as e:
        print(f"API 호출 중 예기치 않은 오류 발생: {e}")
        raise
