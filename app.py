# Geo-Lab AI - 이상적 지형 갤러리
# HuggingFace Spaces Entry Point

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run main app
from app.main import main

if __name__ == "__main__":
    main()
