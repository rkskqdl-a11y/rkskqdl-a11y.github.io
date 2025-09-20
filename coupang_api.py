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

# 쿠팡 API 키 환경변수에서 불러옴 (GitHub Secrets에 설정!)
ACCESS_KEY = os.environ.get('COUPANG_ACCESS_KEY')
SECRET_KEY = os.environ.get('COUPANG_SECRET_KEY')

if not ACCESS_KEY or not SECRET_KEY:
    raise ValueError("COUPANG_ACCESS_KEY와 COUPANG_SECRET_KEY를 GitHub Secrets에 꼭 설정해라!")

DOMAIN = "https://api-gateway.coupang.com"

# HMAC 서명 생성 함수
def generate_hmac(method, url_for_hmac, secret_key, access_key):
    path, *query = url_for_hmac.split("?")
    datetime_gmt = strftime('%y%m%d', gmtime()) + 'T' + strftime('%H%M%S', gmtime()) + 'Z'
    message = datetime_gmt + method + path + (query[0] if query else "")
    signature = hmac.new(bytes(secret_key, 'utf-8'), message.encode('utf-8'), hashlib.sha256).hexdigest()
    return f"CEA algorithm=HmacSHA256, access-key={access_key}, signed-date={datetime_gmt}, signature={signature}"

# 쿠팡 API 호출 함수
def call_coupang_api(method, api_path, query_params=None, body=None):
    url_for_hmac = api_path
    if query_params:
        query_str = urlencode(query_params, quote_via=quote_plus)
        url_for_hmac = f"{api_path}?{query_str}"
    authorization = generate_hmac(method, url_for_hmac, SECRET_KEY, ACCESS_KEY)
    full_url = f"{DOMAIN}{url_for_hmac}"
    headers = {"Authorization": authorization, "Content-Type": "application/json"}
    if method == "GET":
        resp = requests.get(full_url, headers=headers)
    else:
        resp = requests.post(full_url, headers=headers, data=json.dumps(body))
    resp.raise_for_status() # HTTP 에러 발생 시 예외 발생
    return resp.json()

# 상품 검색 API 함수 (limit은 API 허용 범위 내로 유지)
def search_products(keyword, page=1, limit=10): # 함수 이름: search_products (이전 오류 해결!)
    api_path = "/v2/providers/affiliate_open_api/apis/openapi/products/search"
    params = {"keyword": keyword, "limit": limit, "offset": (page-1)*limit}
    return call_coupang_api("GET", api_path, params)

# HTML 페이지 생성 함수 (세련된 스타일, 풍부한 정보, 쿠팡 글자 제거, 이미지 링크)
def create_html(product): # 함수 이름: create_html (이전 오류 해결!)
    name = product.get('productName', '상품명 없음')
    url = product.get('productUrl', '#')
    img = product.get('productImage', 'https://via.placeholder.com/400x300?text=No+Image')
    price = product.get('productPrice', 0)
    category = product.get('categoryName', '정보 없음')
    rank = product.get('rank', 'N/A')
    
    # 배송 정보는 삭제 (요청 반영)
    # 후기 개수 (요청 반영)
    review_count = product.get('reviewCount')
    review_text = f"후기 {review_count}개" if review_count is not None else "후기보기" # 후기 없으면 '후기보기'

    # 파일명으로 사용할 수 없는 문자 제거 및 공백 대체
    safe_name = re.sub(r'[\\/*?:"<>|]', '', name).replace(' ', '_')[:50].strip('_')
    if not safe_name: safe_name = f"product_{hash(name+url) % 1000000}"

    filename = f"{safe_name}.html"
    disclosure = "이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공합니다." # 대가성 문구에만 '쿠팡'

    html_content = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{name}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR&display=swap');
  body {{
    font-family: 'Noto Sans KR', Arial, sans-serif;
    max-width: 820px; margin: auto; padding: 20px; background: #fdfdfd; color: #222;
  }}
  h1 {{
    font-weight: 700; font-size: 2.3rem; color: #333; margin-bottom: 20px; text-align: center;
  }}
  .product-img {{
    text-align: center; margin-bottom: 20px;
  }}
  .product-img img {{
    max-width: 100%; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    cursor: pointer; transition: transform 0.3s ease;
  }}
  .product-img img:hover {{
    transform: scale(1.05);
  }}
  .price {{
    font-size: 1.8rem; color: #e64e32; font-weight: 800;
    margin: 15px 0; text-align: center;
  }}
  .detail-info {{
    font-size: 1rem; line-height: 1.6; color: #555;
    border-top: 1px solid #eee; padding-top: 20px; margin-bottom: 30px;
  }}
  .detail-info p {{
    margin: 6px 0;
  }}
  .detail-info strong {{
    color: #ff5a3c;
  }}
  .buy-btn {{
    display: block;
    max-width: 320px;
    margin: auto;
    padding: 16px 0;
    color: #fff;
    background: linear-gradient(90deg, #ff5a3c 0%, #ff7a5a 100%);
    box-shadow: 0 5px 15px rgba(255,90,60,0.6);
    border-radius: 14px;
    font-weight: 900;
    font-size: 1.3rem;
    text-align: center;
    text-decoration: none;
    transition: background 0.2s ease, box-shadow 0.2s ease;
  }}
  .buy-btn:hover {{
    background: linear-gradient(90deg, #ff764e 0%, #ff956e 100%);
    box-shadow: 0 8px 20px rgba(255,90,60,0.8);
  }}
  .disclosure {{
    font-size: 0.85rem;
    color: #999;
    border-top: 1px solid #eee;
    text-align: center;
    padding-top: 20px;
    margin-top: 40px;
  }}
  @media (max-width: 600px) {{
    body {{
      padding: 15px 10px;
    }}
    h1 {{
      font-size: 1.8rem;
      margin-bottom: 15px;
    }}
    .buy-btn {{
      width: 100%;
      max-width: none;
      padding: 14px 0;
      font-size: 1.1rem;
      border-radius: 10px;
    }}
  }}
</style>
</head>
<body>
  <h1>{name}</h1>
  <div class="product-img">
    <a href="{url}" target="_blank" rel="noopener noreferrer">
      <img src="{img}" alt="{name}">
    </a>
  </div>
  <div class="price">{price:,}원</div>
  <div class="detail-info">
    <p><strong>카테고리:</strong> {category}</p>
    <p><strong>검색 순위:</strong> {rank}위</p>
    <p><strong>{review_text}</strong></p>
  </div>
  <a href="{url}" class="buy-btn" target="_blank" rel="nofollow noopener sponsored">바로 구매하기</a>
  <div class="disclosure">{disclosure}</div>
</body>
</html>
"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    return filename

# 메인 실행 로직
if __name__ == "__main__":
    SEARCH_KEYWORDS_LIST = [ # <<< 네가 준 길고 긴 키워드 리스트!
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
    API_CALL_LIMIT_PER_PAGE = 10 # 한 번의 API 호출당 가져올 상품 최대 개수
    TOTAL_PRODUCTS_TO_GENERATE = 30 # 최종 목표: 총 생성할 HTML 파일 개수
    MAX_PAGES_PER_KEYWORD = 3 # 하나의 키워드당 최대 검색할 페이지 수 (30개 채울때까지)
    
    all_products_to_generate = [] # 수집된 모든 상품을 저장할 리스트
    keywords_attempted_set = set() # 이미 시도한 키워드를 저장하여 중복 방지

    # 목표 개수만큼 상품을 모을 때까지 반복
    while len(all_products_to_generate) < TOTAL_PRODUCTS_TO_GENERATE and \
          len(keywords_attempted_set) < len(SEARCH_KEYWORDS_LIST) * MAX_PAGES_PER_KEYWORD: # 무한 루프 방지용 안전 장치
        
        selected_keyword = random.choice(SEARCH_KEYWORDS_LIST)
        if selected_keyword in keywords_attempted_set: # 이미 시도한 키워드면 건너뛰고 다음 키워드 선택
            continue
        
        print(f"\n랜덤 키워드 선택: '{selected_keyword}'")
        keywords_attempted_set.add(selected_keyword) # 시도한 키워드 세트에 추가

        # 선택된 키워드로 여러 페이지를 검색하여 상품 수집
        for page_num in range(1, MAX_PAGES_PER_KEYWORD + 1):
            if len(all_products_to_generate) >= TOTAL_PRODUCTS_TO_GENERATE:
                break # 이미 목표 개수를 채웠으면 키워드/페이지 루프 중단
            
            print(f"'{selected_keyword}' 상품 검색 시도 (페이지 {page_num})...")
            
            try:
                # <<<<<<<<<<<<<<<< 여기가 'search_products_api' 에서 'search_products'로 바뀐 부분! >>>>>>>>>>>>>>>>>>
                search_results = search_products(selected_keyword, page=page_num, limit=API_CALL_LIMIT_PER_PAGE)
                
                # Debug 로그 (필요시 주석 해제해서 API 응답 확인 가능)
                # print(f"\n--- API 응답 (DEBUG) - 키워드: '{selected_keyword}' (페이지 {page_num}) ---")
                # print(json.dumps(search_results, indent=4, ensure_ascii=False))
                # print("-----------------------------------------------------------------------\n")
                
                products_on_current_page = search_results.get('data', {}).get('productData', [])
                
                if not products_on_current_page:
                    print(f"'{selected_keyword}' 키워드 (페이지 {page_num})에 더 이상 상품이 없습니다. 다음 키워드로 이동.")
                    break # 현재 키워드에 더 이상 상품이 없으면 다음 키워드로
                
                for product_item in products_on_current_page:
                    if len(all_products_to_generate) < TOTAL_PRODUCTS_TO_GENERATE:
                        all_products_to_generate.append(product_item)
                    else:
                        break # 목표 개수를 채웠으면 상품 추가 중단
                        
                if len(products_on_current_page) < API_CALL_LIMIT_PER_PAGE:
                    # 현재 페이지 상품 수가 요청 limit보다 적으면, 이 키워드에 더 이상 상품이 없다고 판단
                    break

            except requests.exceptions.HTTPError as http_err:
                print(f"HTTP 오류 ({selected_keyword}, 페이지 {page_num}): {http_err.response.status_code} - {http_err.response.text}", file=sys.stderr)
                break # HTTP 오류 발생 시 이 키워드는 포기
            except Exception as e:
                print(f"API 호출 중 예기치 않은 오류 ({selected_keyword}, 페이지 {page_num}): {e}", file=sys.stderr)
                break # 다른 오류 발생 시 이 키워드는 포기
        
        if len(all_products_to_generate) >= TOTAL_PRODUCTS_TO_GENERATE:
            print(f"최종 목표 상품 개수({TOTAL_PRODUCTS_TO_GENERATE}개) 달성!")
            break # 전체 목표 달성 시 모든 루프 종료

    # 상품 수집 결과 처리
    if not all_products_to_generate:
        print("최대 시도 후에도 상품 데이터를 하나도 확보하지 못했습니다. 키워드, API 키, 네트워크 상태 등을 확인하세요.", file=sys.stderr)
        sys.exit(1) # 상품이 하나도 없으면 스크립트 종료

    print(f"\n총 {len(all_products_to_generate)}개 상품으로 HTML 파일 생성 중...")
    generated_html_files_count = 0
    for product_data in all_products_to_generate:
        try:
            # <<<<<<<<<<<<<<<< 여기가 'create_html_page' 에서 'create_html'로 바뀐 부분! >>>>>>>>>>>>>>>>>>
            created_filename = create_html(product_data)
            print(f"-> '{created_filename}' 생성 완료")
            generated_html_files_count += 1
        except Exception as e:
            print(f"HTML 파일 생성 실패 (상품: {product_data.get('productName', '불명')}) : {e}", file=sys.stderr)

    print(f"\n총 {generated_html_files_count}개의 HTML 파일이 성공적으로 생성되었습니다.")
    print("이제 GitHub Actions 워크플로우를 실행하여 웹사이트에 반영하세요! 🎉")
