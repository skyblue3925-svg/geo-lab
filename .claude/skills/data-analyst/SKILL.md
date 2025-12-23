---
name: data-analyst
description: Assists with data analysis tasks using Python, Pandas, NumPy, and visualization libraries. Activated for data exploration and analysis.
---

# Data Analyst Skill

## Purpose
Provide data analysis code and insights for scientific data.

## Capabilities
1. **Data Loading**
   - CSV, Excel, JSON, GeoTIFF
   - Database connections

2. **Data Exploration**
   - `.describe()`, `.info()`, `.head()`
   - Missing value analysis
   - Distribution analysis

3. **Data Transformation**
   - Filtering, grouping, pivoting
   - Merging datasets
   - Feature engineering

4. **Visualization**
   - Matplotlib (publication quality)
   - Plotly (interactive)
   - Seaborn (statistical)

## Output Template
```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 데이터 로드
df = pd.read_csv('data.csv')

# 기본 탐색
print(f"Shape: {df.shape}")
print(f"Columns: {df.columns.tolist()}")
print(df.describe())

# 시각화
fig, ax = plt.subplots(figsize=(10, 6))
# ... 차트 코드 ...
plt.tight_layout()
plt.show()
```

## When to Activate
- "데이터 분석해줘"
- "이 CSV 분석해줘"
- "통계 분석해줘"
- "차트 그려줘"
