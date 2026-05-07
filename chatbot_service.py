import os
import requests
import mysql.connector
import google.generativeai as genai
from datetime import datetime
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import Embeddings

load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
genai.configure(api_key=GEMINI_API_KEY)

DB_CONFIG = {
    'host':     os.getenv('DB_HOST', 'localhost'),
    'user':     os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'bank'),
}


class RAGEmbedder(Embeddings):
    def _embed(self, text: str, task_type: str) -> list[float]:
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type=task_type,
        )
        return result['embedding']

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        result = []
        for i, text in enumerate(texts):
            vec = self._embed(text, "retrieval_document")
            result.append(vec)
            if (i + 1) % 5 == 0:
                print(f"  임베딩 진행: {i + 1}/{len(texts)}")
        return result

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text, "retrieval_query")


def load_site_guide() -> list[str]:
    guide_path = os.path.join(os.path.dirname(__file__), 'site_guide.txt')
    try:
        with open(guide_path, encoding='utf-8') as f:
            content = f.read()
        chunks = [c.strip() for c in content.split('\n\n') if c.strip()]
        print(f"[알림] 사이트 가이드 {len(chunks)}개 문단 로드 완료")
        return chunks
    except Exception as e:
        print(f"[WARN] 사이트 가이드 로드 실패: {e}")
        return []


def build_vector_db():
    global _all_texts
    print("[알림] RAG 벡터 DB를 구축합니다... (Gemini 임베딩 API 호출 중)")
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT product_name, description, base_interest_rate, max_interest_rate, "
            "product_category, target_type FROM financial_product WHERE is_active = 1"
        )
        products = cursor.fetchall()
        cursor.close()
        conn.close()

        product_texts = [
            f"상품명: {p['product_name']}, 카테고리: {p['product_category']}, "
            f"대상: {'법인' if p['target_type'] == 'CORPORATE' else '개인'}, "
            f"기본금리: {p['base_interest_rate']}%, 최고금리: {p['max_interest_rate']}%, "
            f"설명: {p['description']}"
            for p in products
        ]
    except Exception as e:
        print(f"[WARN] 상품 로드 실패: {e}")
        product_texts = []

    guide_texts = load_site_guide()
    all_texts = product_texts + guide_texts
    _all_texts = all_texts

    if not all_texts:
        print("경고: 임베딩할 데이터가 없습니다.")
        return None

    try:
        db = FAISS.from_texts(all_texts, RAGEmbedder())
        print(f"성공: 상품 {len(product_texts)}개 + 가이드 {len(guide_texts)}개 RAG 벡터 DB 구축 완료")
        return db
    except Exception as e:
        print(f"[WARN] 벡터 DB 구축 실패, 키워드 검색으로 대체합니다: {e}")
        return None


# 벡터 DB 구축 실패 시 키워드 검색 폴백용
_all_texts: list[str] = []

vector_db = build_vector_db()


def _keyword_search(query: str, k: int = 6) -> list[str]:
    scores = [(sum(1 for w in query.split() if w in t), t) for t in _all_texts]
    return [t for _, t in sorted(scores, reverse=True)[:k]]


def get_chat_response(user_id: int, user_message: str) -> dict:
    try:
        if vector_db is not None:
            docs = vector_db.similarity_search(user_message, k=6)
            context = "\n".join([doc.page_content for doc in docs])
        elif _all_texts:
            context = "\n".join(_keyword_search(user_message))
        else:
            return {
                "sender": "bot",
                "content": "서비스 초기화 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
        )
        prompt = (
            "당신은 BankScope 은행 AI 상담원입니다. "
            "아래 참조 데이터를 바탕으로 고객 질문에 친절하고 정확하게 답변하세요. "
            "참조 데이터에 없는 내용은 '직접 방문 또는 고객센터 문의'를 안내하세요.\n\n"
            f"[참조 데이터]\n{context}\n\n"
            f"[고객 질문]\n{user_message}"
        )

        response = requests.post(
            url,
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=15
        )
        result = response.json()

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
