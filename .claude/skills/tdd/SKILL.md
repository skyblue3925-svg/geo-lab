---
name: tdd
description: Guides Test-Driven Development workflow. Red-Green-Refactor cycle. Activated when building features with tests first.
---

# TDD (Test-Driven Development) Skill

## Purpose
Guide the TDD workflow: Red → Green → Refactor

## TDD Cycle

### 1️⃣ RED: 실패하는 테스트 작성
```python
def test_add_returns_sum():
    # Given - 준비
    a, b = 1, 2
    
    # When - 실행
    result = add(a, b)
    
    # Then - 검증
    assert result == 3
```

### 2️⃣ GREEN: 최소한의 코드로 통과
```python
def add(a, b):
    return a + b  # 가장 간단한 구현
```

### 3️⃣ REFACTOR: 리팩토링
```python
def add(a: int, b: int) -> int:
    """두 정수의 합을 반환"""
    return a + b
```

## TDD Rules
1. 실패하는 테스트 없이 프로덕션 코드 작성 금지
2. 한 번에 하나의 테스트만 실패하도록
3. 테스트가 통과하면 바로 리팩토링

## Output Format
```
## TDD 사이클

### 🔴 RED - 실패 테스트
[테스트 코드]

### 🟢 GREEN - 최소 구현
[구현 코드]

### 🔵 REFACTOR - 개선
[리팩토링 코드]
```

## When to Activate
- "TDD로 개발해줘"
- "테스트 먼저 작성해줘"
- "Red-Green-Refactor"
