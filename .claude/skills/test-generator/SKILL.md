---
name: test-generator
description: Generates unit tests for Python code using pytest. Activated when testing is needed.
---

# Test Generator Skill

## Purpose
Auto-generate comprehensive pytest test cases.

## Test Structure
```python
import pytest
from module import function_to_test

class TestFunctionName:
    """function_name에 대한 테스트 클래스"""
    
    def test_basic_case(self):
        """기본 동작 테스트"""
        result = function_to_test(input)
        assert result == expected
    
    def test_edge_case(self):
        """엣지 케이스 테스트"""
        result = function_to_test(edge_input)
        assert result == edge_expected
    
    def test_error_case(self):
        """에러 케이스 테스트"""
        with pytest.raises(ValueError):
            function_to_test(invalid_input)

    @pytest.mark.parametrize("input,expected", [
        (1, 2),
        (2, 4),
        (3, 6),
    ])
    def test_parametrized(self, input, expected):
        """파라미터화된 테스트"""
        assert function_to_test(input) == expected
```

## Test Categories
1. **Happy Path** - 정상 동작
2. **Edge Cases** - 경계값
3. **Error Cases** - 예외 처리
4. **Integration** - 통합 테스트

## When to Activate
- "테스트 코드 만들어줘"
- "이 함수 테스트해줘"
- "pytest 작성해줘"
