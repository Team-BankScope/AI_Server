import platform
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, classification_report
import joblib
import shap
import matplotlib.pyplot as plt

# main.py 의 FEATURE_COLUMNS 와 동일한 순서 유지 (어긋나면 추론 시 예측이 틀어짐)
FEATURE_COLUMNS = ['age', 'is_corporate', 'total_balance', 'has_active_loan', 'recent_tx_count']

print("1. BankScope 현실 데이터 3000건 생성 중...")
np.random.seed(42)
n_samples = 3000

ages             = np.random.randint(18, 85, n_samples)
is_corporate     = np.random.choice([0, 1], p=[0.85, 0.15], size=n_samples)
total_balances   = np.random.exponential(scale=15000000, size=n_samples).astype(int)
has_active_loan  = np.random.choice([0, 1], p=[0.7, 0.3], size=n_samples)
recent_tx_counts = np.random.poisson(lam=15, size=n_samples)

targets = []
for i in range(n_samples):
    # 10% 확률로 노이즈 삽입 - 과적합 방지
    if np.random.rand() < 0.1:
        targets.append(np.random.choice([0, 1, 2]))
        continue

    if is_corporate[i] == 1:
        if total_balances[i] < 1000000 and recent_tx_counts[i] < 5:
            targets.append(np.random.choice([0, 2], p=[0.7, 0.3]))
        else:
            targets.append(2)  # 기업/특수 업무
    elif has_active_loan[i] == 1 or total_balances[i] > 40000000 or ages[i] > 65:
        targets.append(1)      # 상담 업무
    else:
        if recent_tx_counts[i] > 5:
            targets.append(0)  # 빠른 업무
        else:
            targets.append(1)

df = pd.DataFrame({
    'age':             ages,
    'is_corporate':    is_corporate,
    'total_balance':   total_balances,
    'has_active_loan': has_active_loan,
    'recent_tx_count': recent_tx_counts,
    'target':          targets,
})

X = df[FEATURE_COLUMNS]
y = df['target']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print("2. 랜덤 포레스트 모델 학습 중...")
model = RandomForestClassifier(
    n_estimators=200,
    max_depth=8,
    min_samples_split=5,
    class_weight='balanced',  # 클래스 불균형 보정
    random_state=42,
)
model.fit(X_train, y_train)

print("3. 5-Fold 교차 검증 수행 중...")
cv_scores = cross_val_score(model, X, y, cv=5, scoring='accuracy')
print(f"   CV 평균 정확도: {cv_scores.mean() * 100:.2f}% +- {cv_scores.std() * 100:.2f}%")

print("4. 모델 평가 (테스트 데이터셋 채점)")
y_pred   = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)

print(f"\n[OK] 최종 모델 정확도: {accuracy * 100:.2f}%")
print("\n[상세 분류 리포트]")
print(classification_report(y_test, y_pred, target_names=["빠른업무(0)", "상담업무(1)", "기업특수(2)"]))

print("[피처 중요도]")
for feat, importance in sorted(
    zip(FEATURE_COLUMNS, model.feature_importances_), key=lambda x: -x[1]
):
    print(f"  {feat}: {importance:.4f}")

if accuracy >= 0.85:
    joblib.dump(model, 'bank_model.pkl')
    print("\n[OK] 목표 달성! 'bank_model.pkl' 모델 저장 완료!")
else:
    print("\n[WARN] 정확도가 85% 미만이므로 모델을 저장하지 않습니다.")

# ---------------------------------------------------------
# [SHAP XAI] 특정 고객이 왜 해당 창구로 배정됐는지 per-instance 설명
# ---------------------------------------------------------
print("\n5. SHAP 분석 중... (수십 초 소요될 수 있습니다)")

explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_test)

# 새 버전 SHAP: shap_values shape = (n_samples, n_features, n_classes)
# 축이 맞는지 확인 후 분기
is_3d = isinstance(shap_values, np.ndarray) and shap_values.ndim == 3

class_names = ['빠른업무', '상담업무', '기업특수']
y_test_arr = np.array(y_test)
y_pred_arr = np.array(y_pred)

# SHAP waterfall 은 영문 레이블만 사용 → 기본 폰트 사용 (한글 폰트의 minus sign 미지원 문제 방지)
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = True

for class_idx, class_name in enumerate(class_names):
    correct = np.where((y_test_arr == class_idx) & (y_pred_arr == class_idx))[0]
    if len(correct) == 0:
        print(f"[WARN] {class_name} 정확 예측 샘플 없음, 건너뜀")
        continue

    idx = correct[0]
    values = shap_values[idx, :, class_idx] if is_3d else shap_values[class_idx][idx]
    base = explainer.expected_value[class_idx] if hasattr(explainer.expected_value, '__len__') else explainer.expected_value

    shap.waterfall_plot(
        shap.Explanation(
            values=values,
            base_values=base,
            data=X_test.iloc[idx],
            feature_names=FEATURE_COLUMNS
        ),
        show=False
    )
    profile = dict(X_test.iloc[idx])
    plt.title(f'[{class_name}] Why? profile={profile}', fontsize=9)
    plt.tight_layout()
    plt.savefig(f'shap_explain_{class_idx}_{class_name}.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"[OK] 'shap_explain_{class_idx}_{class_name}.png' 저장 완료!")
