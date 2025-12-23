---
name: clean-architecture
description: Guides Clean Architecture principles. Dependency inversion, layer separation, SOLID principles. Activated for architecture design.
---

# Clean Architecture Skill

## Purpose
Apply Clean Architecture and SOLID principles.

## Layer Structure
```
┌─────────────────────────────────────┐
│          Presentation              │ ← UI, Controllers
├─────────────────────────────────────┤
│          Application               │ ← Use Cases
├─────────────────────────────────────┤
│            Domain                  │ ← Entities, Business Logic
├─────────────────────────────────────┤
│         Infrastructure             │ ← DB, External APIs
└─────────────────────────────────────┘
```

## Dependency Rule
- 의존성은 항상 안쪽 (Domain) 방향으로만
- Domain은 외부 레이어를 알지 못함

## SOLID Principles
| 원칙 | 설명 |
|------|------|
| **S**ingle Responsibility | 하나의 책임만 |
| **O**pen/Closed | 확장에 열림, 수정에 닫힘 |
| **L**iskov Substitution | 하위 타입 대체 가능 |
| **I**nterface Segregation | 인터페이스 분리 |
| **D**ependency Inversion | 추상화에 의존 |

## Directory Structure
```
src/
├── domain/           # 핵심 비즈니스 로직
│   ├── entities/
│   └── repositories/  (interfaces)
├── application/      # Use Cases
│   └── use_cases/
├── infrastructure/   # 외부 의존성
│   ├── database/
│   └── api/
└── presentation/     # UI/API Layer
    ├── controllers/
    └── views/
```

## Python Example
```python
# domain/entities/user.py
@dataclass
class User:
    id: str
    name: str
    email: str

# domain/repositories/user_repository.py
class UserRepository(ABC):
    @abstractmethod
    def get_by_id(self, user_id: str) -> User:
        pass

# application/use_cases/get_user.py
class GetUserUseCase:
    def __init__(self, repo: UserRepository):
        self._repo = repo  # Dependency Injection
    
    def execute(self, user_id: str) -> User:
        return self._repo.get_by_id(user_id)
```

## When to Activate
- "클린 아키텍처로 설계해줘"
- "SOLID 원칙 적용해줘"
- "레이어 분리해줘"
