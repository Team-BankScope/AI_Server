import requests
import mysql.connector
import os
from datetime import datetime
from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import Embeddings

# 1. 설정부
GEMINI_API_KEY = ""
INDEX_PATH = "faiss_bank_index"

# 2. 임베딩 클래스 정의 
class RAGEmbedder(Embeddings):
    def embed_documents(self, texts):
        embeddings = []
        for text in texts:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-04:embedContent?key={GEMINI_API_KEY}"
            payload = {
                "model": "models/text-embedding-04", 
                "content": {"parts": [{"text": text}]}
            }
            try:
                res = requests.post(url, json=payload, timeout=5)
                data = res.json()
                if res.status_code == 200 and 'embedding' in data:
                    embeddings.append(data['embedding']['values'])
                else:
                    
                    embeddings.append([0.01] * 768)
            except Exception as e:
                print(f"Embedding Error: {e}")
                embeddings.append([0.01] * 768)
        return embeddings

    def embed_query(self, text):
        return self.embed_documents([text])[0]

# 3. 벡터 DB 구축 함수
def build_vector_db():
    print("[알림] MySQL 데이터를 기반으로 벡터 DB를 구축합니다...")
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='1234',
            database='bank'
        )
        cursor = conn.cursor(dictionary=True)
        # 활성화된 상품 정보만 가져오기
        query = "SELECT product_name, description, base_interest_rate, product_category FROM financial_product WHERE is_active = 1"
        cursor.execute(query)
        products = cursor.fetchall()
        
        if not products:
            print("경고: DB에 데이터가 없습니다.")
            return None

        # 텍스트 데이터 구성
        product_texts = [
            f"상품명: {p['product_name']}, 카테고리: {p['product_category']}, 금리: {p['base_interest_rate']}%, 설명: {p['description']}"
            for p in products
        ]
        
        cursor.close()
        conn.close()
        
        # FAISS 인덱스 생성
        custom_embedder = RAGEmbedder()
        db = FAISS.from_texts(product_texts, custom_embedder)
        print(f"성공: {len(products)}개의 상품이 벡터 DB에 적재되었습니다.")
        return db

    except Exception as e:
        print(f"DB 로드 실패: {e}")
        return None


vector_db = build_vector_db()

# 4. 채팅 응답 처리 함수
def get_chat_response(user_id, user_message):
    if vector_db is None:
        return {"sender": "bot", "content": "데이터베이스 연결 오류로 상담이 불가합니다.", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

    try:
        extra_context = ""
        category_keywords = {
            "CORPORATE": ["법인", "기업", "사업자", "corporate"],
            "INDIVIDUAL": ["개인", "직장인", "청년", "시니어"],
        }

        for target_type, keywords in category_keywords.items():
            if any(kw in user_message for kw in keywords):
                conn = mysql.connector.connect(
                    host='localhost', user='root', password='1234', database='bank'
                )
                cursor = conn.cursor(dictionary=True)
                cursor.execute(
                    "SELECT product_name, description, base_interest_rate, product_category "
                    "FROM financial_product WHERE is_active = 1 AND target_type = %s",
                    (target_type,)
                )
                results = cursor.fetchall()
                cursor.close()
                conn.close()
                if results:
                    extra_context = "\n[카테고리 직접 조회 결과]\n" + "\n".join([
                        f"상품명: {r['product_name']}, 카테고리: {r['product_category']}, "
                        f"금리: {r['base_interest_rate']}%, 설명: {r['description']}"
                        for r in results
                    ])
                break  

       
        docs = vector_db.similarity_search(user_message, k=5)  
        context = "\n".join([doc.page_content for doc in docs]) + extra_context  

        model_name = "gemini-2.5-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
                
        prompt = f"""당신은 은행 AI 상담원입니다. 아래 정보를 기반으로만 답변하세요. 정보가 없다면 모른다고 답하세요.
[참조 데이터]
{context}

[질문]
{user_message}"""
        
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        response = requests.post(url, json=payload, timeout=10)
        result = response.json()
        
        # 응답 처리
        if response.status_code == 200:
            try:
                ai_content = result['candidates'][0]['content']['parts'][0]['text']
            except (KeyError, IndexError):
                print(f"응답 구조 오류: {result}")
                ai_content = "답변 생성 과정에서 오류가 발생했습니다."
        else:
            
            print(f"API 실패 ({response.status_code}): {result}")
            ai_content = "죄송합니다. 서비스 응답에 실패했습니다. 잠시 후 다시 시도해주세요."

        return {
            "sender": "bot",
            "content": ai_content,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
            
    except Exception as e:
        print(f"Chat Service Error: {e}")
        return {
            "sender": "bot",
            "content": "처리 중 일시적인 오류가 발생했습니다.",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

# 5. 실행부 (인덱스 파일 저장용)
if __name__ == "__main__":
    if vector_db:
        vector_db.save_local(INDEX_PATH)
        print(f"인덱스가 '{INDEX_PATH}' 폴더에 저장되었습니다.")