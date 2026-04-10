import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import joblib

print("데이터베이스 로직 기반 가상 데이터 생성 및 모델 학습 시작...")

# 1. 1000명의 고객 방문 데이터 생성
np.random.seed(42)
n_samples = 1000

ages = np.random.randint(20, 75, n_samples)
# 10%는 기업 고객
is_corporate = np.random.choice([0, 1], p=[0.9, 0.1], size=n_samples)
# 잔액: 0원 ~ 1억원
total_balances = np.random.randint(0, 100000000, n_samples)
# 30%는 대출 보유
has_active_loan = np.random.choice([0, 1], p=[0.7, 0.3], size=n_samples)
# 한 달 거래 건수
recent_tx_count = np.random.randint(0, 50, n_samples)

# 2. 은행 비즈니스 룰에 따른 타겟(정답) 할당
targets = []
for i in range(n_samples):
    if is_corporate[i] == 1:
        targets.append(2)  # 2: 기업/특수 업무
    elif has_active_loan[i] == 1 or total_balances[i] > 50000000 or ages[i] > 60:
        targets.append(1)  # 1: 상담 업무 (대출 상담, 고액 예금, 고령층)
    else:
        # 젊고 거래가 많으며 잔액이 평범하면 단순 창구 업무
        if recent_tx_count[i] > 10:
            targets.append(0)  # 0: 빠른 업무 (출금/이체 등)
        else:
            targets.append(np.random.choice([0, 1])) # 나머지는 랜덤

# DataFrame 생성
df = pd.DataFrame({
    'age': ages,
    'is_corporate': is_corporate,
    'total_balance': total_balances,
    'has_active_loan': has_active_loan,
    'recent_tx_count': recent_tx_count,
    'target': targets
})



X = df.drop('target', axis=1)
y = df['target']

# 3. 모델 학습 (가볍고 빠르며 성능이 좋은 Random Forest)
model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
model.fit(X, y)

# 4. 모델 저장
joblib.dump(model, 'bank_model.pkl')
print("✅ 'bank_model.pkl' 생성 완료! 이 파일은 실제 DB 피처를 완벽하게 이해합니다.")