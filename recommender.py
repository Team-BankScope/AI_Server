import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler

class ProductRecommender:
    def __init__(self, csv_path):
        # 1. 파일명 확인 및 데이터 로드        
        self.df = pd.read_csv(csv_path)
     
        self.feature_cols = ['age', 'is_corporate', 'total_balance', 'has_active_loan', 'recent_tx_count']
        
        # 2. 스케일링 (수치형 데이터 정규화)
        self.scaler = MinMaxScaler()
        self.features_scaled = self.scaler.fit_transform(self.df[self.feature_cols])

    def get_recommendations(self, user_profile, top_k=20): 
        # 3. 입력 유저 데이터 전처리
        input_df = pd.DataFrame([user_profile])[self.feature_cols]
        input_scaled = self.scaler.transform(input_df)

        # 4. 코사인 유사도 계산
        sim_scores = cosine_similarity(input_scaled, self.features_scaled)[0]

        # 5. 유사도 상위 K명 인덱스 추출
        similar_indices = sim_scores.argsort()[-top_k:][::-1]
        
        # 6. 유사 고객들이 가진 상품 리스트 반환
        recommended_products = self.df.iloc[similar_indices]['target_product'].unique().tolist()
        
        return recommended_products