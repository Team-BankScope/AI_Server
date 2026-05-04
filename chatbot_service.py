import os
import mysql.connector
import requests
import json
import numpy as np
from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import Embeddings

# --- [설정 및 API 키 (본인 거 넣으면 됩니다)] ---
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"

# --- [1단계: 문서 벡터화 (Embedding)] ---
class RAGEmbedder(Embeddings):
    def embed_documents(self, texts):
        embeddings = []
        for text in texts:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-04:embedContent?key={GEMINI_API_KEY}"
            payload = {"model": "models/text-embedding-04", "content": {"parts": [{"text": text}]}}
            try:
                res = requests.post(url, json=payload, timeout=3)
                data = res.json()
                if res.status_code == 200 and 'embedding' in data:
                    embeddings.append(data['embedding']['values'])
                else:
                    embeddings.append([0.01] * 768) 
            except:
                embeddings.append([0.01] * 768)
        return embeddings

    def embed_query(self, text):
        return self.embed_documents([text])[0]

# --- [2단계: 벡터 DB 저장 (Vector DB)] ---
def build_vector_db():
    print("RAG 시스템 구축 중")
    try:
        conn = mysql.connector.connect(host='localhost', user='root', password='1234', database='bank')
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT product_name, description, base_interest_rate, product_category FROM financial_product WHERE is_active = 1")
        products = cursor.fetchall()
        product_texts = [f"상품명: {p['product_name']}, 카테고리: {p['product_category']}, 금리: {p['base_interest_rate']}%, 설명: {p['description']}" for p in products]
        cursor.close()
        conn.close()
    except:
        product_texts = ["DB 로드 실패: 예시 상품 정보"]

    custom_embedder = RAGEmbedder()
    vector_db = FAISS.from_texts(product_texts, custom_embedder)
    print("벡터 DB 적재 완료")
    return vector_db

vector_db = build_vector_db()

# --- [3단계 & 4단계: 유사도 검색 및 응답 생성] ---
def get_chat_response(user_message):
    try:
    
        docs = vector_db.similarity_search(user_message, k=3)
        context = "\n".join([doc.page_content for doc in docs])
        
      
        model_path = "gemini-3-flash-preview"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_path}:generateContent?key={GEMINI_API_KEY}"
        
        prompt = f"""당신은 은행 AI 상담원입니다. 아래 정보를 기반으로만 답변하세요.
[참조 데이터]
{context}

[질문]
{user_message}"""
        
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        response = requests.post(url, json=payload)
        result = response.json()
        
        if response.status_code == 200:
            return result['candidates'][0]['content']['parts'][0]['text']
        else:
            
            err_msg = result.get('error', {}).get('message', 'Unknown Error')
            print(f"❌ {model_path} 에러: {err_msg}")
            return f"죄송합니다. 서비스 응답 실패 (사유: {err_msg})"
            
    except Exception as e:
        return f"처리 중 시스템 오류: {str(e)}"