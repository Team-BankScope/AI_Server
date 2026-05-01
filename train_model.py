import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib

print("2. 랜덤 포레스트 모델 학습 시작...")

# 1. 저장해둔 CSV 파일 불러오기
df_loaded = pd.read_csv('bank_customers_real.csv')

# 테스트해볼 피처 조합 (필요시 여기서 넣고 빼면서 테스트 가능)
SELECTED_FEATURES = [
    'age',
    'is_corporate',
    'total_balance',
    'has_active_loan',
    'recent_tx_count'
]

# 2. 데이터 분리
X = df_loaded[SELECTED_FEATURES]
y = df_loaded['target']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# 3. 모델 하이퍼파라미터 세팅 및 학습
model = RandomForestClassifier(
    n_estimators=500,
    max_depth=15,
    min_samples_split=5,
    min_samples_leaf=3,
    max_features='sqrt',
    criterion='entropy',
    random_state=42
)
model.fit(X_train, y_train)

# 4. 정확도 확인
y_pred = model.predict(X_test)
print(f"\n🎯 최종 모델 정확도: {accuracy_score(y_test, y_pred) * 100:.2f}%")
print("\n[상세 보고서]")
print(classification_report(y_test, y_pred, target_names=['빠른업무(0)', '상담업무(1)', '특수업무(2)']))

# 5. 완성된 모델을 파일로 저장 (기존 파일명 매칭)
model_filename = 'bank_model.pkl'
joblib.dump(model, model_filename)
print(f"\n💾 학습된 모델을 '{model_filename}'로 저장 완료!")