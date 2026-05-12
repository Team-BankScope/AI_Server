-- BankScope financial_product 초기 데이터 삽입
-- 실행 전 확인: USE bank;
-- product_category ENUM: CHECKING(입출금), DEPOSIT(예금), SAVINGS(적금), LOAN(대출)
-- target_type: INDIVIDUAL(개인), CORPORATE(법인), ALL(공통)

SET FOREIGN_KEY_CHECKS = 0;
DELETE FROM `bank`.`financial_product`;
SET FOREIGN_KEY_CHECKS = 1;

INSERT INTO `bank`.`financial_product`
    (product_category, target_type, product_name, base_interest_rate, max_interest_rate,
     min_duration_months, max_duration_months, min_amount, max_amount, description, is_active)
VALUES

-- 예금 (DEPOSIT)
('DEPOSIT', 'INDIVIDUAL', 'BankScope 정기예금',
 3.20, 4.00, 1, 36, 1000000, 500000000,
 '안정적인 금리를 제공하는 개인 정기예금 상품입니다. 가입 기간이 길수록 우대금리가 적용됩니다.', 1),

('DEPOSIT', 'INDIVIDUAL', 'BankScope 시니어 우대예금',
 3.50, 4.50, 12, 24, 1000000, 300000000,
 '만 60세 이상 고객을 위한 우대금리 정기예금입니다. 자동이체 실적 시 추가 우대금리가 제공됩니다.', 1),

('DEPOSIT', 'CORPORATE', 'BankScope 기업 정기예금',
 3.00, 3.80, 1, 24, 10000000, 2000000000,
 '법인 및 사업자를 위한 고액 정기예금 상품입니다. 거래 실적에 따라 우대금리가 적용됩니다.', 1),

-- 적금 (SAVINGS)
('SAVINGS', 'INDIVIDUAL', 'BankScope 자유적금',
 3.80, 5.00, 6, 36, 10000, 3000000,
 '매월 자유롭게 납입할 수 있는 적금 상품입니다. 급여이체 및 카드 실적에 따라 최고 5.00% 금리를 제공합니다.', 1),

('SAVINGS', 'INDIVIDUAL', 'BankScope 청년 희망적금',
 4.50, 6.00, 12, 24, 10000, 500000,
 '만 19세~34세 청년 고객 전용 적금입니다. 정부 지원 이자를 포함하여 최고 6.00% 혜택을 받을 수 있습니다.', 1),

('SAVINGS', 'INDIVIDUAL', 'BankScope 주택 마련 적금',
 4.00, 5.50, 24, 60, 50000, 1000000,
 '내 집 마련을 목표로 하는 장기 적금입니다. 청약저축 연계 시 추가 우대금리가 적용됩니다.', 1),

('SAVINGS', 'CORPORATE', 'BankScope 기업 정기적금',
 3.20, 4.00, 12, 60, 1000000, 100000000,
 '소상공인 및 중소기업을 위한 정기적금입니다. 세금 우대 혜택이 적용됩니다.', 1),

-- 대출 (LOAN)
('LOAN', 'INDIVIDUAL', 'BankScope 신용대출',
 5.50, 15.00, 1, 60, 1000000, 50000000,
 '신용등급에 따라 최대 5천만 원까지 대출 가능한 개인 신용대출 상품입니다. 별도의 담보 없이 빠르게 신청하실 수 있습니다.', 1),

('LOAN', 'INDIVIDUAL', 'BankScope 주택담보대출',
 3.80, 6.50, 12, 360, 30000000, 1000000000,
 '주택을 담보로 장기 저금리로 이용할 수 있는 대출 상품입니다. LTV·DTI 기준 내에서 최대 10억 원까지 대출 가능합니다.', 1),

('LOAN', 'INDIVIDUAL', 'BankScope 전세자금대출',
 3.20, 5.00, 6, 24, 10000000, 300000000,
 '전세 계약자를 위한 보증 대출 상품입니다. HUG·HF 보증 연계로 최대 3억 원까지 지원합니다.', 1),


('LOAN', 'ALL', 'BankScope 소상공인 대출',
 4.00, 8.00, 6, 60, 5000000, 500000000,
 '소상공인 및 자영업자를 위한 운전자금·시설자금 대출입니다. 정책자금 연계 시 저금리 혜택을 받을 수 있습니다.', 1),

('LOAN', 'CORPORATE', 'BankScope 기업대출',
 4.50, 9.00, 12, 120, 10000000, 3000000000,
 '중소·중견기업의 운영 및 시설 투자를 위한 기업금융 대출 상품입니다. 최대 30억 원까지 지원합니다.', 1),

-- 공통 (ALL)
('CHECKING', 'INDIVIDUAL', 'BankScope 개인 입출금 통장',
 0.10, 0.50, NULL, NULL, 0, NULL,
 '개인 고객을 위한 기본 입출금 통장입니다. 급여이체, 공과금 자동납부, 카드 결제 등 일상적인 금융 거래에 최적화되어 있습니다.', 1),

('CHECKING', 'ALL', 'BankScope 자유입출금 통장',
 0.10, 1.00, NULL, NULL, 0, NULL,
 '개인과 법인 모두 이용 가능한 기본 입출금 통장입니다. 언제든지 자유롭게 입출금할 수 있으며 인터넷·모바일뱅킹을 통한 이체 서비스를 제공합니다.', 1),

('DEPOSIT', 'ALL', 'BankScope 단기 정기예금',
 2.50, 3.50, 1, 12, 100000, NULL,
 '개인·법인 모두 가입 가능한 단기 정기예금입니다. 1개월 이상 단기 자금 운용에 적합하며 만기 시 자동 연장 옵션이 제공됩니다.', 1),

('SAVINGS', 'ALL', 'BankScope 목표 적금',
 3.50, 4.50, 6, 36, 10000, 2000000,
 '개인·법인 구분 없이 목표 금액을 정해두고 자유롭게 적립하는 적금입니다. 목표 달성 시 추가 우대금리가 적용됩니다.', 1);
