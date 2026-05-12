-- BankScope product_subscription 샘플 데이터
-- 실행 전 확인: financial_product, user 테이블에 데이터가 있어야 합니다.
-- product_id는 상품명 서브쿼리로 참조하므로 ID 변경에 영향 없음
-- user_id는 실제 DB의 user 테이블 기준으로 서브쿼리 사용

INSERT INTO `bank`.`product_subscription`
    (user_id, product_id, task_id, amount, duration_months, status, applied_interest_rate, created_at)
VALUES

-- 개인 고객 - 예금
((SELECT id FROM `bank`.`user` WHERE user_type = 'customer' LIMIT 1 OFFSET 0),
 (SELECT product_id FROM `bank`.`financial_product` WHERE product_name = 'BankScope 정기예금'),
 NULL, 5000000, 12, 'ACTIVE', 3.50, NOW()),

((SELECT id FROM `bank`.`user` WHERE user_type = 'customer' LIMIT 1 OFFSET 1),
 (SELECT product_id FROM `bank`.`financial_product` WHERE product_name = 'BankScope 시니어 우대예금'),
 NULL, 10000000, 24, 'ACTIVE', 4.00, NOW()),

((SELECT id FROM `bank`.`user` WHERE user_type = 'customer' LIMIT 1 OFFSET 2),
 (SELECT product_id FROM `bank`.`financial_product` WHERE product_name = 'BankScope 단기 정기예금'),
 NULL, 3000000, 6, 'ACTIVE', 3.00, NOW()),

-- 개인 고객 - 적금
((SELECT id FROM `bank`.`user` WHERE user_type = 'customer' LIMIT 1 OFFSET 0),
 (SELECT product_id FROM `bank`.`financial_product` WHERE product_name = 'BankScope 자유적금'),
 NULL, 300000, 24, 'ACTIVE', 4.20, NOW()),

((SELECT id FROM `bank`.`user` WHERE user_type = 'customer' LIMIT 1 OFFSET 1),
 (SELECT product_id FROM `bank`.`financial_product` WHERE product_name = 'BankScope 청년 희망적금'),
 NULL, 500000, 24, 'ACTIVE', 5.50, NOW()),

((SELECT id FROM `bank`.`user` WHERE user_type = 'customer' LIMIT 1 OFFSET 3),
 (SELECT product_id FROM `bank`.`financial_product` WHERE product_name = 'BankScope 주택 마련 적금'),
 NULL, 1000000, 36, 'ACTIVE', 4.80, NOW()),

((SELECT id FROM `bank`.`user` WHERE user_type = 'customer' LIMIT 1 OFFSET 4),
 (SELECT product_id FROM `bank`.`financial_product` WHERE product_name = 'BankScope 목표 적금'),
 NULL, 200000, 12, 'ACTIVE', 3.80, NOW()),

-- 개인 고객 - 대출
((SELECT id FROM `bank`.`user` WHERE user_type = 'customer' LIMIT 1 OFFSET 2),
 (SELECT product_id FROM `bank`.`financial_product` WHERE product_name = 'BankScope 신용대출'),
 NULL, 10000000, 24, 'ACTIVE', 7.50, NOW()),

((SELECT id FROM `bank`.`user` WHERE user_type = 'customer' LIMIT 1 OFFSET 3),
 (SELECT product_id FROM `bank`.`financial_product` WHERE product_name = 'BankScope 주택담보대출'),
 NULL, 200000000, 120, 'ACTIVE', 4.20, NOW()),

((SELECT id FROM `bank`.`user` WHERE user_type = 'customer' LIMIT 1 OFFSET 5),
 (SELECT product_id FROM `bank`.`financial_product` WHERE product_name = 'BankScope 전세자금대출'),
 NULL, 150000000, 24, 'ACTIVE', 3.80, NOW()),

-- 개인 고객 - 입출금
((SELECT id FROM `bank`.`user` WHERE user_type = 'customer' LIMIT 1 OFFSET 0),
 (SELECT product_id FROM `bank`.`financial_product` WHERE product_name = 'BankScope 개인 입출금 통장'),
 NULL, 1000000, NULL, 'ACTIVE', 0.10, NOW()),

((SELECT id FROM `bank`.`user` WHERE user_type = 'customer' LIMIT 1 OFFSET 1),
 (SELECT product_id FROM `bank`.`financial_product` WHERE product_name = 'BankScope 자유입출금 통장'),
 NULL, 500000, NULL, 'ACTIVE', 0.10, NOW()),

-- 법인 고객 - 예금/적금
((SELECT id FROM `bank`.`user` WHERE user_type = 'CORPORATE' LIMIT 1 OFFSET 0),
 (SELECT product_id FROM `bank`.`financial_product` WHERE product_name = 'BankScope 기업 정기예금'),
 NULL, 100000000, 12, 'ACTIVE', 3.30, NOW()),

((SELECT id FROM `bank`.`user` WHERE user_type = 'CORPORATE' LIMIT 1 OFFSET 0),
 (SELECT product_id FROM `bank`.`financial_product` WHERE product_name = 'BankScope 기업 정기적금'),
 NULL, 5000000, 24, 'ACTIVE', 3.60, NOW()),

-- 법인 고객 - 대출
((SELECT id FROM `bank`.`user` WHERE user_type = 'CORPORATE' LIMIT 1 OFFSET 1),
 (SELECT product_id FROM `bank`.`financial_product` WHERE product_name = 'BankScope 소상공인 대출'),
 NULL, 30000000, 36, 'ACTIVE', 5.50, NOW()),

((SELECT id FROM `bank`.`user` WHERE user_type = 'CORPORATE' LIMIT 1 OFFSET 1),
 (SELECT product_id FROM `bank`.`financial_product` WHERE product_name = 'BankScope 기업대출'),
 NULL, 500000000, 60, 'ACTIVE', 6.00, NOW()),

-- 법인 고객 - 입출금
((SELECT id FROM `bank`.`user` WHERE user_type = 'CORPORATE' LIMIT 1 OFFSET 0),
 (SELECT product_id FROM `bank`.`financial_product` WHERE product_name = 'BankScope 자유입출금 통장'),
 NULL, 50000000, NULL, 'ACTIVE', 0.10, NOW());
