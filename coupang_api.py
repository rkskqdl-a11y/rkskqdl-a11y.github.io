import os
import hmac
import hashlib
import requests
import json
from time import gmtime, strftime
import random
from urllib.parse import urlencode, quote_plus
import re
import sys

ACCESS_KEY = os.environ.get('COUPANG_ACCESS_KEY')
SECRET_KEY = os.environ.get('COUPANG_SECRET_KEY')

if not ACCESS_KEY or not SECRET_KEY:
    raise ValueError("COUPANG_ACCESS_KEY와 COUPANG_SECRET_KEY를 GitHub Secrets에 설정해야 합니다.")

DOMAIN = "https://api-gateway.coupang.com"

def generate_hmac(method, url_for_hmac, secret_key, access_key):
    path, *query = url_for_hmac.split("?")
    datetime_gmt = strftime('%y%m%d', gmtime()) + 'T' + strftime('%H%M%S', gmtime()) + 'Z'
    message = datetime_gmt + method + path + (query[0] if query else "")
    signature = hmac.new(bytes(secret_key, 'utf-8'), message.encode('utf-8'), hashlib.sha256).hexdigest()
    return f"CEA algorithm=HmacSHA256, access-key={access_key}, signed-date={datetime_gmt}, signature={signature}"

def call_coupang_api(method, api_path, query_params=None, body=None):
    url_for_hmac = api_path
    if query_params:
        query_str = urlencode(query_params, quote_via=quote_plus)
        url_for_hmac = f"{api_path}?{query_str}"
    authorization = generate_hmac(method, url_for_hmac, SECRET_KEY, ACCESS_KEY)
    full_url = f"{DOMAIN}{url_for_hmac}"
    headers = {"Authorization": authorization, "Content-Type": "application/json"}
    if method == "GET":
        res = requests.get(full_url, headers=headers)
    else:
        res = requests.post(full_url, headers=headers, data=json.dumps(body))
    res.raise_for_status()
    return res.json()

def search_products(keyword, page=1, limit=10):
    api_path = "/v2/providers/affiliate_open_api/apis/openapi/products/search"
    params = {"keyword": keyword, "limit": limit, "offset": (page-1)*limit}
    return call_coupang_api("GET", api_path, params)

def create_html(product):
    name = product.get('productName', '상품명 없음')
    url = product.get('productUrl', '#')
    img = product.get('productImage', 'https://via.placeholder.com/400x300.png?text=No+Image')
    price = product.get('productPrice', 0)
    review_count = product.get('reviewCount')
    if review_count is not None:
        review_text = f"후기 {review_count}개"
    else:
        review_text = "후기보기"

    safe_name = re.sub(r'[\\/*?:"<>|]', '', name).replace(' ', '_')[:50].strip('_')
    if not safe_name:
        safe_name = f"product_{hash(name+url) % 1000000}"

    filename = f"{safe_name}.html"
    disclosure = "이 포스팅은 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다."

    html = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{name}</title>
<style>
  body {{ font-family: Arial,sans-serif; max-width: 800px; margin: auto; padding: 20px; background: #f9f9f9; color:#333; }}
  h1 {{ text-align:center; color:#2c3e50; margin-bottom:25px; font-size:2.2em; }}
  .product-img {{ text-align:center; margin-bottom:20px; }}
  .product-img img {{ max-width: 100%; border-radius: 8px; cursor:pointer; border:1px solid #eee; }}
  .price {{ font-size:1.4em; color:#e91e63; font-weight:bold; margin:15px 0; text-align:center; }}
  .detail-info {{ font-size:0.95em; color:#555; margin-bottom:20px; line-height:1.6; padding:0 10px; border-top:1px solid #eee; padding-top:20px; }}
  .detail-info p {{ margin: 5px 0; }}
  .detail-info strong {{ color:#2980b9; }}
  .buy-btn {{ display:block; width: 80%; max-width:300px; margin:20px auto; padding:15px 25px; background:#ff5722; color:#fff; text-decoration:none; border-radius:8px; font-size:1.3em; font-weight:bold; text-align:center; box-shadow:0 4px 8px rgba(255,87,34,0.3); transition:background-color 0.3s ease; }}
  .buy-btn:hover {{ background-color:#e64a19; transform:translateY(-2px); }}
  .disclosure {{ font-size:0.85em; color:#7f8c8d; text-align:center; margin-top:40px; border-top:1px solid #eee; padding-top:20px; }}
  @media (max-width:600px) {{
    body {{ padding:10px; }}
    h1 {{ font-size:1.8em; margin-bottom:15px; }}
    .buy-btn {{ width:95%; padding:12px 20px; font-size:1.1em; }}
  }}
</style>
</head>
<body>
  <div class="container">
    <h1>{name}</h1>
    <div class="product-img">
      <a href="{url}" target="_blank" rel="noopener noreferrer">
        <img src="{img}" alt="{name}" />
      </a>
    </div>
    <div class="price">{price:,}원</div>
    <div class="detail-info">
      <p><strong>{review_text}</strong></p>
    </div>
    <a href="{url}" target="_blank" rel="noopener noreferrer" class="buy-btn">바로 구매하기</a>
    <div class="disclosure">{disclosure}</div>
  </div>
</body>
</html>
"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html)
    return filename

if __name__ == "__main__":
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

    API_CALL_LIMIT_PER_PAGE = 10
    TOTAL_PRODUCTS_TO_GENERATE = 30
    MAX_PAGES_PER_KEYWORD = 3
    all_products_to_generate = []
    keywords_attempted = set()

    while len(all_products_to_generate) < TOTAL_PRODUCTS_TO_GENERATE and len(keywords_attempted) < len(SEARCH_KEYWORDS_LIST) * MAX_PAGES_PER_KEYWORD:
        selected_keyword = random.choice(SEARCH_KEYWORDS_LIST)
        if selected_keyword in keywords_attempted:
            continue
        print(f"\n랜덤 키워드 선택: '{selected_keyword}'")
        keywords_attempted.add(selected_keyword)
        current_page = 1
        products_found_for_keyword = []

        while len(products_found_for_keyword) < API_CALL_LIMIT_PER_PAGE * MAX_PAGES_PER_KEYWORD:
            print(f"'{selected_keyword}' 상품 검색 시도 (Page {current_page})...")
            try:
                search_results = search_products_api(selected_keyword, page=current_page, limit=API_CALL_LIMIT_PER_PAGE)
                if search_results and search_results.get('data') and search_results['data'].get('productData'):
                    products_on_page = search_results['data']['productData']
                    if len(products_on_page) > 0:
                        print(f"'{selected_keyword}' 키워드 (Page {current_page})에서 {len(products_on_page)}개 상품 발견!")
                        for product in products_on_page:
                            if len(all_products_to_generate) < TOTAL_PRODUCTS_TO_GENERATE:
                                all_products_to_generate.append(product)
                            else:
                                break
                        if len(products_on_page) < API_CALL_LIMIT_PER_PAGE or len(all_products_to_generate) >= TOTAL_PRODUCTS_TO_GENERATE:
                            break
                        current_page += 1
                    else:
                        print(f"'{selected_keyword}' 키워드 (Page {current_page})에서 productData가 비어있습니다. 다음 키워드로 이동.")
                        break
                else:
                    print(f"'{selected_keyword}' 키워드 (Page {current_page})로 상품을 찾지 못했습니다. 'data' 또는 'productData' 키 없음.")
                    break
            except requests.exceptions.HTTPError as http_err:
                print(f"HTTP 오류 발생 ({selected_keyword}, Page {current_page}): {http_err.response.status_code} - {http_err.response.text}")
                break
            except Exception as e:
                print(f"API 호출 중 예기치 않은 오류 발생 ({selected_keyword}, Page {current_page}): {e}")
                break
        if len(all_products_to_generate) >= TOTAL_PRODUCTS_TO_GENERATE:
            print(f"목표 상품 개수({TOTAL_PRODUCTS_TO_GENERATE}개) 달성!")
            break

    if len(all_products_to_generate) < TOTAL_PRODUCTS_TO_GENERATE:
        print(f"최대 시도 후 {len(all_products_to_generate)}개만 상품을 확보했습니다. 목표({TOTAL_PRODUCTS_TO_GENERATE}개) 미달.")
    generated_html_files = []
    print(f"\n--- {len(all_products_to_generate)}개 HTML 페이지 생성 중 ---")
    if all_products_to_generate:
        for item in all_products_to_generate:
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
