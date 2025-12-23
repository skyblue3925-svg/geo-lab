---
name: docstring-generator
description: Generates comprehensive docstrings for Python functions, classes, and modules. Activated when documentation is needed.
---

# Docstring Generator Skill

## Purpose
Auto-generate PEP 257 compliant docstrings in Korean.

## Docstring Format (Google Style)
```python
def function_name(param1: type, param2: type) -> return_type:
    """함수에 대한 간략한 설명.
    
    더 자세한 설명이 필요한 경우 여기에 작성.
    
    Args:
        param1: 첫 번째 파라미터 설명
        param2: 두 번째 파라미터 설명
        
    Returns:
        반환값에 대한 설명
        
    Raises:
        ValueError: 잘못된 값이 입력된 경우
        
    Example:
        >>> function_name(1, 2)
        3
    """
```

## Class Docstring
```python
class ClassName:
    """클래스에 대한 간략한 설명.
    
    Attributes:
        attr1: 속성 설명
        attr2: 속성 설명
    """
```

## When to Activate
- "문서화해줘"
- "docstring 추가해줘"
- "이 함수에 설명 달아줘"
