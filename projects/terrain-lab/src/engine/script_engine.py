
import numpy as np
import math
from .grid import WorldGrid
from .fluids import HydroKernel
from .erosion_process import ErosionProcess

class ScriptExecutor:
    """
    사용자 정의 스크립트 실행 엔진
    보안을 위해 제한된 환경에서 Python 코드를 실행합니다.
    """
    def __init__(self, grid: WorldGrid):
        self.grid = grid
        self.hydro = HydroKernel(grid)
        self.erosion = ErosionProcess(grid)
        
    def execute(self, script: str, dt: float = 1.0, allowed_modules: list = ['numpy', 'math']):
        """
        스크립트 실행
        
        Args:
            script: 실행할 Python 코드 문자열
            dt: 시간 간격 (Time Step)
            allowed_modules: 허용할 모듈 리스트 (기본: numpy, math)
        
        Available Variables in Context:
            - grid: WorldGrid 객체
            - elevation: grid.elevation (Numpy Array)
            - bedrock: grid.bedrock
            - sediment: grid.sediment
            - water_depth: grid.water_depth
            - dt: Delta Time
            - np: numpy module
            - math: math module
            - hydro: HydroKernel 객체
            - erosion: ErosionProcess 객체
        """
        
        # 1. 실행 컨텍스트(Namespace) 준비
        context = {
            'grid': self.grid,
            'elevation': self.grid.elevation,
            'bedrock': self.grid.bedrock,
            'sediment': self.grid.sediment,
            'water_depth': self.grid.water_depth,
            'dt': dt,
            'np': np,
            'math': math,
            'hydro': self.hydro,
            'erosion': self.erosion,
            # Helper functions
            'max': max,
            'min': min,
            'abs': abs,
            'pow': pow,
            'print': print,  # 디버깅용
            'range': range,
            'len': len,
            'int': int,
            'float': float,
            'round': round,
            'sum': sum,
            'enumerate': enumerate,
            'zip': zip,
            'list': list,
            'tuple': tuple,
            'dict': dict,
            'set': set,
            'str': str,
            'bool': bool,
            'True': True,
            'False': False,
            'None': None,
        }
        
        # 2. 금지된 키워드 체크 (기본적인 보안)
        # 완벽한 샌드박스는 아니지만, 실수 방지용
        forbidden = ['import os', 'import sys', 'open(', 'exec(', 'eval(', '__import__']
        for bad in forbidden:
            if bad in script:
                raise ValueError(f"보안 경고: 허용되지 않는 키워드 '{bad}'가 포함되어 있습니다.")
                
        # 3. 코드 실행
        try:
            exec(script, {"__builtins__": {}}, context)
            
            # 4. 변경 사항 반영 (Elevation은 derived property지만, 직접 수정했을 수 있으므로)
            # 사용자가 elevation을 수정했다면 bedrock/sediment 업데이트가 모호해짐.
            # Grid 클래스의 update_elevation()은 bedrock+sediment -> elevation이므로,
            # 사용자가 elevation을 수정하면 무시될 수 있음.
            # 가이드: "bedrock"이나 "sediment"를 수정하세요.
            # 하지만 편의를 위해 elevation이 바뀌었으면 bedrock에 반영하는 로직 추가
            
            # 변경 전 elevation과 비교해야 하나?
            # 일단 grid.update_elevation()을 호출하여 동기화
            # (만약 사용자가 bedrock을 바꿨다면 반영됨)
            self.grid.update_elevation()
            
            return True, "실행 성공"
            
        except Exception as e:
            return False, f"실행 오류: {str(e)}"

