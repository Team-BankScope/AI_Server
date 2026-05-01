import pandas as pd
import numpy as np

print("1. BankScope 고도화 데이터 생성 및 CSV 추출 중...")
np.random.seed(42)
data_size = 5000

# 1. 피처(Feature) 데이터 생성
data = {
    'age': np.random.randint(20, 80, data_size),
    'is_corporate': np.random.choice([0, 1], data_size, p=[0.9, 0.1]),
    'total_balance': np.random.randint(0, 100000000, data_size),
    'has_active_loan': np.random.choice([0, 1], data_size, p=[0.8, 0.2]),
    'recent_tx_count': np.random.randint(0, 50, data_size)
}
df = pd.DataFrame(data)

# 2. 타겟(Target) 생성 로직 (Score & Noise)
def realistic_target(row):
    noise = np.random.normal(0, 10, 3)
    score_0 = 50 + (row['recent_tx_count'] * 1.5) - (row['age'] * 0.5) + noise[0]
    score_1 = (row['age'] * 0.8) + (row['has_active_loan'] * 30) + (row['total_balance'] / 1000000) * 0.5 + noise[1]
    score_2 = (row['is_corporate'] * 150) + noise[2]

    scores = [score_0, score_1, score_2]
    return np.argmax(scores)

df['target'] = df.apply(realistic_target, axis=1)

# 3. 완성된 데이터를 CSV 파일로 저장 (팀장님 기존 세팅 파일명으로 매칭)
csv_filename = 'bank_customers_real.csv'
df.to_csv(csv_filename, index=False)

print(f"✅ 현실 로직이 반영된 데이터 {len(df)}건을 '{csv_filename}'로 저장 완료!")