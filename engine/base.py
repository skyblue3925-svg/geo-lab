"""
Geo-Lab AI Engine: 기본 지형 클래스
"""
import numpy as np
from dataclasses import dataclass, field
from typing import Optional, Tuple


@dataclass
class Terrain:
    """2D 높이맵 기반 지형 데이터 구조"""
    
    width: int = 100          # X 방향 셀 수
    height: int = 100         # Y 방향 셀 수
    cell_size: float = 10.0   # 셀당 실제 거리 (m)
    
    # 높이맵 (m)
    elevation: np.ndarray = field(default=None)
    
    # 암석 속성
    rock_hardness: np.ndarray = field(default=None)  # 0-1, 1이 가장 단단함
    
    def __post_init__(self):
        if self.elevation is None:
            self.elevation = np.zeros((self.height, self.width))
        if self.rock_hardness is None:
            self.rock_hardness = np.ones((self.height, self.width)) * 0.5
    
    @classmethod
    def create_slope(cls, width: int, height: int, 
                     max_elevation: float = 1000.0,
                     slope_direction: str = 'south') -> 'Terrain':
        """경사면 지형 생성"""
        terrain = cls(width=width, height=height)
        
        if slope_direction == 'south':
            # 북쪽이 높고 남쪽이 낮음
            for y in range(height):
                terrain.elevation[y, :] = max_elevation * (1 - y / height)
        elif slope_direction == 'east':
            for x in range(width):
                terrain.elevation[:, x] = max_elevation * (1 - x / width)
        
        return terrain
    
    @classmethod
    def create_v_valley_initial(cls, width: int = 100, height: int = 100,
                                 valley_depth: float = 50.0) -> 'Terrain':
        """V자곡 시뮬레이션 초기 지형"""
        terrain = cls(width=width, height=height)
        
        # 기본 경사 (북→남)
        for y in range(height):
            terrain.elevation[y, :] = 500 * (1 - y / height)
        
        # 중앙에 초기 하천 채널 (약간의 패임)
        center = width // 2
        for x in range(width):
            dist = abs(x - center)
            if dist < 5:
                terrain.elevation[:, x] -= valley_depth * (1 - dist / 5)
        
        return terrain
    
    def get_slope(self) -> np.ndarray:
        """각 셀의 경사도 계산 (라디안)"""
        dy, dx = np.gradient(self.elevation, self.cell_size)
        return np.arctan(np.sqrt(dx**2 + dy**2))
    
    def get_flow_direction(self) -> Tuple[np.ndarray, np.ndarray]:
        """물 흐름 방향 벡터 (가장 가파른 하강 방향)"""
        dy, dx = np.gradient(self.elevation, self.cell_size)
        magnitude = np.sqrt(dx**2 + dy**2) + 1e-10
        return -dx / magnitude, -dy / magnitude


@dataclass 
class Water:
    """하천 수문 데이터"""
    
    terrain: Terrain
    
    # 각 셀의 수량 (m³/s)
    discharge: np.ndarray = field(default=None)
    
    # 유속 (m/s)
    velocity: np.ndarray = field(default=None)
    
    # 흐름 방향 (단위 벡터)
    flow_x: np.ndarray = field(default=None)
    flow_y: np.ndarray = field(default=None)
    
    def __post_init__(self):
        shape = (self.terrain.height, self.terrain.width)
        if self.discharge is None:
            self.discharge = np.zeros(shape)
        if self.velocity is None:
            self.velocity = np.zeros(shape)
        if self.flow_x is None:
            self.flow_x, self.flow_y = self.terrain.get_flow_direction()
    
    def add_precipitation(self, rate: float = 0.001):
        """강수 추가 (m/s per cell)"""
        self.discharge += rate
    
    def accumulate_flow(self):
        """흐름 누적 계산 (간단한 D8 알고리즘)"""
        h, w = self.terrain.height, self.terrain.width
        accumulated = self.discharge.copy()
        
        # 높은 곳에서 낮은 곳으로 정렬
        indices = np.argsort(self.terrain.elevation.ravel())[::-1]
        
        for idx in indices:
            y, x = idx // w, idx % w
            if accumulated[y, x] <= 0:
                continue
            
            # 가장 낮은 이웃 찾기
            min_elev = self.terrain.elevation[y, x]
            min_neighbor = None
            
            for dy, dx in [(-1,0), (1,0), (0,-1), (0,1)]:
                ny, nx = y + dy, x + dx
                if 0 <= ny < h and 0 <= nx < w:
                    if self.terrain.elevation[ny, nx] < min_elev:
                        min_elev = self.terrain.elevation[ny, nx]
                        min_neighbor = (ny, nx)
            
            if min_neighbor:
                accumulated[min_neighbor] += accumulated[y, x]
        
        self.discharge = accumulated
        
        # 유속 계산 (Manning 방정식 단순화)
        slope = self.terrain.get_slope() + 0.001  # 0 방지
        self.velocity = 2.0 * np.sqrt(slope) * np.power(self.discharge + 0.1, 0.4)


@dataclass
class SimulationState:
    """시뮬레이션 상태 관리"""
    
    terrain: Terrain
    water: Water
    
    time_step: float = 1.0  # 시뮬레이션 1스텝 = 1년
    current_time: float = 0.0
    
    # 전역 변수 (Master Plan의 Global Controllers)
    climate_level: float = 1.0      # 기후 (강수량 계수)
    sea_level: float = 0.0          # 해수면 (m)
    tectonic_energy: float = 0.0    # 지각 에너지 (융기율 m/year)
    
    def step(self):
        """1 타임스텝 진행"""
        self.current_time += self.time_step
        
        # 강수 추가
        self.water.add_precipitation(rate=0.001 * self.climate_level)
        
        # 흐름 누적
        self.water.accumulate_flow()
