import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler


class ProductRecommender:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.feature_cols = ['age', 'is_corporate', 'total_balance', 'has_active_loan', 'recent_tx_count']
        self.scaler = MinMaxScaler()
        self.features_scaled = self.scaler.fit_transform(self.df[self.feature_cols])

    def get_recommendations(self, user_profile, top_k=20):
        input_df = pd.DataFrame([user_profile])[self.feature_cols]
        input_scaled = self.scaler.transform(input_df)
        sim_scores = cosine_similarity(input_scaled, self.features_scaled)[0]
        similar_indices = sim_scores.argsort()[-top_k:][::-1]
        return self.df.iloc[similar_indices]['target_product'].unique().tolist()
