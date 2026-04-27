import numpy as np
from dataclasses import dataclass, field
from typing import Tuple, Optional

@dataclass
class WorldGrid:
    """
    지구 시스템 통합 그리드 (World Grid)
    
    모든 물리적 상태(고도, 물, 퇴적물)를 통합 관리하는 중앙 데이터 구조입니다.
    기존의 개별 시뮬레이션 그리드와 달리, 전지구적 해수면(Sea Level)과 연동됩니다.
    """
    width: int = 100
    height: int = 100
    cell_size: float = 10.0  # 미터 (m)
    sea_level: float = 0.0   # 해수면 고도 (m)
    
    # --- 상태 레이어 (State Layers) ---
    # 기반암 고도 (Bedrock Elevation)
    bedrock: np.ndarray = field(default=None)
    # 퇴적층 두께 (Sediment Thickness)
    sediment: np.ndarray = field(default=None)
    # 수심 (Water Depth) - 표면 유출수
    water_depth: np.ndarray = field(default=None)
    # 유량 (Discharge)
    discharge: np.ndarray = field(default=None)
    # 유향 (Flow Direction)
    flow_dir: np.ndarray = field(default=None)
    
    # --- 파생 레이어 (Derived Layers) ---
    # 지표면 고도 (Topography = Bedrock + Sediment)
    elevation: np.ndarray = field(default=None)
    
    def __post_init__(self):
        """그리드 초기화"""
        shape = (self.height, self.width)
        
        if self.bedrock is None:
            self.bedrock = np.zeros(shape)
        if self.sediment is None:
            self.sediment = np.zeros(shape)
        if self.water_depth is None:
            self.water_depth = np.zeros(shape)
        if self.discharge is None:
            self.discharge = np.zeros(shape)
        if self.flow_dir is None:
            self.flow_dir = np.zeros(shape, dtype=int)
        if self.elevation is None:
            self.update_elevation()
            
    def update_elevation(self):
        """지표면 고도 갱신 (기반암 + 퇴적층)"""
        self.elevation = self.bedrock + self.sediment

    def get_gradient(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        경사도(Slope)와 경사향(Aspect) 계산
        Returns:
            slope (m/m): 경사도
            aspect (rad): 경사 방향 (0=East, pi/2=North)
        """
        dy, dx = np.gradient(self.elevation, self.cell_size)
        slope = np.sqrt(dx**2 + dy**2)
        aspect = np.arctan2(dy, dx)
        return slope, aspect

    def get_water_surface(self) -> np.ndarray:
        """수면 고도 반환 (지표면 + 수심)"""
        return self.elevation + self.water_depth

    def is_underwater(self) -> np.ndarray:
        """해수면 기준 침수 여부 확인"""
        # 해수면보다 낮거나, 지표면에 물이 흐르고 있는 경우
        # 여기서는 간단히 '해수면' 기준과 '담수' 존재 여부를 분리해서 생각할 수 있음.
        # 일단 해수면(Sea Level) 기준 침수 지역 반환
        return self.elevation < self.sea_level

    def apply_uplift(self, rate: float, dt: float = 1.0):
        """지반 융기 적용"""
        self.bedrock += rate * dt
        self.update_elevation()

    def add_sediment(self, amount: np.ndarray):
        """퇴적물 추가/제거"""
        self.sediment += amount
        # 퇴적물은 0보다 작을 수 없음 (기반암 침식은 별도 로직)
        self.sediment = np.maximum(self.sediment, 0)
        self.update_elevation()
