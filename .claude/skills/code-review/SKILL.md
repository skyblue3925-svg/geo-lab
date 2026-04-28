---
name: code-review
description: Performs thorough code review focusing on quality, performance, security, and best practices. Activated when reviewing code or suggesting improvements.
---

# Code Review Skill

## Purpose
Provide comprehensive code reviews with actionable feedback.

## Review Checklist
1. **Code Quality**
   - Naming conventions
   - Function length (<20 lines)
   - Single responsibility principle

2. **Performance**
   - Algorithm efficiency (O(n) analysis)
   - Memory usage
   - Database query optimization

3. **Security**
   - Input validation
   - SQL injection prevention
   - XSS prevention

4. **Best Practices**
   - Type hints (Python)
   - Error handling
   - Logging

## Output Format
```
## 코드 리뷰 결과

### ✅ 잘된 점
- [항목]

### ⚠️ 개선 필요
- [항목]: [이유] → [제안]

### 🔴 필수 수정
- [항목]: [이유] → [수정 코드]
```

## Examples
When asked "이 코드 리뷰해줘":
1. Analyze code structure
2. Check for common issues
3. Suggest improvements with code examples
