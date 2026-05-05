import pandas as pd
import numpy as np

np.random.seed(42)
data_size = 10000 

data = {
    'age': np.random.randint(20, 80, data_size),
    'is_corporate': np.random.choice([0, 1], data_size, p=[0.9, 0.1]),
    'total_balance': np.random.randint(0, 100000000, data_size),
    'has_active_loan': np.random.choice([0, 1], data_size, p=[0.8, 0.2]),
    'recent_tx_count': np.random.randint(0, 50, data_size)
}

df = pd.DataFrame(data)

def assign_product(row):
    noise = np.random.normal(0, 35, 3)

    score_deposit = (row['total_balance'] / 1000000) * 0.5 + (row['age'] * 0.15) + noise[0]
    score_savings = (row['recent_tx_count'] * 1.0) + ((80 - row['age']) * 0.3) + noise[1]
    score_loan = (row['has_active_loan'] * 30) + ((100000000 - row['total_balance']) / 1000000) * 0.3 + noise[2]

    if row['is_corporate'] == 1:
        return 'BankScope 법인 시설자금 대출' if score_loan > score_deposit else 'BankScope 법인 단기 예금'

    scores = {'DEPOSIT': score_deposit, 'SAVINGS': score_savings, 'LOAN': score_loan}
    best = max(scores, key=scores.get)

    if best == 'DEPOSIT':
        if row['age'] >= 55:
            return 'BankScope 시니어 플러스 예금'
        elif row['total_balance'] >= 20000000:
            return 'BankScope 복리 자산 예금'
        else:
            return 'BankScope 프리미엄 정기예금'

    elif best == 'SAVINGS':
        if row['age'] <= 34:
            return 'Scope 청년 드림 적금'
        elif row['recent_tx_count'] >= 15:
            return 'Scope 재테크 챌린지 적금'
        else:
            return 'BankScope 직장인 우대 적금'

    else:
        if row['age'] <= 39 and row['total_balance'] < 30000000:
            return 'Scope 청년 전세 대출'
        elif row['total_balance'] < 15000000:
            return 'Scope 비상금 소액 대출'
        elif row['has_active_loan'] == 1:
            return 'BankScope 직장인 신용 대출'
        else:
            return 'Scope 긴급 생활안정 대출'

df['product_name'] = df.apply(assign_product, axis=1)
df.to_csv('bank_data2.csv', index=False)

print("bank_data2.csv 생성 완료!")
print(df['product_name'].value_counts())
print(f"\n총 상품 종류: {df['product_name'].nunique()}개")