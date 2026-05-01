import mysql.connector
import requests
import json
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

# --- 1. 초기 설정 ---
GEMINI_API_KEY = "AIzaSyDriKtRpmH1hkV7FSfrLPZ7X2OHVPEEGfc"

# --- 2. DB에서 상품 정보 가져오기 ---
def prepare_products_for_rag():
    try:
        conn = mysql.connector.connect(
            host='localhost', 
            user='root', 
            password='1234',
            database='bank'
        )
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT product_name, description, base_interest_rate, product_category 
            FROM financial_product 
            WHERE is_active = 1
        """)
        products = cursor.fetchall()
        
        product_texts = []
        for p in products:
            text = f"상품명: {p['product_name']}, 카테고리: {p['product_category']}, 금리: {p['base_interest_rate']}%, 설명: {p['description']}"
            product_texts.append(text)
        
        cursor.close()
        conn.close()
        return product_texts
    except Exception as e:
        print(f"DB Error: {e}")
        return ["기본 상품: BankScope 안심 예금, 금리 3.5%"]

# --- 3. 임베딩 및 벡터 DB 구축 ---
product_texts = prepare_products_for_rag()
embeddings = HuggingFaceEmbeddings(
    model_name="jhgan/ko-sroberta-multitask",
    model_kwargs={'device': 'cpu'}
)

print(f"데이터 확인: {len(product_texts)}개의 상품 로드됨")
vector_db = FAISS.from_texts(product_texts, embeddings)

# --- 4. 챗봇 응답 함수 ---
def get_chat_response(user_message):
    try:
        # 벡터 DB에서 관련 상품 검색
        docs = vector_db.similarity_search(user_message, k=3)
        context = "\n".join([doc.page_content for doc in docs])
        
        
        model_name = "gemini-3-flash-preview"
        url = f"https://generativelanguage.googleapis.com/v1alpha/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
        
        headers = {'Content-Type': 'application/json'}
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"당신은 친절한 은행 상담원입니다. 아래 정보를 바탕으로 질문에 답하세요.\n\n[상품 정보]\n{context}\n\n[사용자 질문]\n{user_message}"
                }]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "topP": 0.8,
                "topK": 40
            }
        }

        # 구글 서버로 요청 전송
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        result = response.json()

        # 정상 응답 처리
        if response.status_code == 200:
            # Gemini 3 Preview의 응답 구조에 맞춰 텍스트 추출
            return result['candidates'][0]['content']['parts'][0]['text']
        else:
            error_msg = result.get('error', {}).get('message', '알 수 없는 오류')
            print(f"!!! API 에러: {error_msg}")
            return f"상담 중 오류가 발생했습니다. (원인: {error_msg})"

    except Exception as e:
        print(f"!!! 시스템 에러: {str(e)}")
        return f"통신 중 오류가 발생했습니다: {str(e)}"