import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics.pairwise import cosine_similarity

df = pd.read_csv('bank_data2.csv')

FEATURES = ['age', 'is_corporate', 'total_balance', 'has_active_loan', 'recent_tx_count']

# Min-Max 정규화 (값 크기가 다른 피처들을 0~1 범위로 통일)
scaler = MinMaxScaler()
df_scaled = scaler.fit_transform(df[FEATURES])

def get_recommendation(user_vector):
    # 입력 유저도 동일한 스케일러로 정규화
    user_scaled = scaler.transform(user_vector)

    # 10000명 가상 고객 전체와 코사인 유사도 계산
    similarities = cosine_similarity(user_scaled, df_scaled)[0]

    # 유사도 상위 20명 인덱스 추출
    top20_idx = similarities.argsort()[-20:][::-1]

    # 상위 20명이 가입한 상품 중 가장 많이 나온 상품 3개 반환 
    top20_products = df.iloc[top20_idx]['product_name']
    return top20_products.value_counts().index[:3].tolist()