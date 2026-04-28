"""
🏗️ Human Activity - 인간 활동 모듈
댐 건설, 삼림 벌채, 토지 이용 변화
"""
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class Dam:
    """댐 정보"""
    position: Tuple[int, int]
    height: float
    width: int
    name: str
    capacity: float = 0.0
    current_level: float = 0.0

@dataclass
class DeforestationZone:
    """삼림 벌채 구역"""
    center: Tuple[int, int]
    radius: int
    intensity: float  # 0-1

class HumanActivity:
    """
    인간 활동 시뮬레이션
    
    - 댐 건설 및 저수지
    - 삼림 벌채
    - 토지 이용 변화
    """
    
    def __init__(self, grid_size: int):
        self.grid_size = grid_size
        
        # 댐 목록
        self.dams: List[Dam] = []
        
        # 삼림 벌채 구역
        self.deforestation_zones: List[DeforestationZone] = []
        
        # 식생 밀도 그리드 (0-1)
        self.vegetation_grid = np.ones((grid_size, grid_size))
        
        # 토지 이용 그리드 (0: 자연, 1: 농지, 2: 도시)
        self.land_use_grid = np.zeros((grid_size, grid_size), dtype=int)
    
    # ========== 댐 건설 ==========
    def build_dam(self, position: Tuple[int, int], 
                  height: float = 50.0, 
                  width: int = 5,
                  name: str = "Dam") -> Dam:
        """
        댐 건설
        
        Args:
            position: (row, col) 위치
            height: 댐 높이 (m)
            width: 댐 너비 (셀)
            name: 댐 이름
            
        Returns:
            생성된 댐 객체
        """
        dam = Dam(
            position=position,
            height=height,
            width=width,
            name=name,
            capacity=height * width * 1000  # 간단한 용량 계산
        )
        self.dams.append(dam)
        return dam
    
    def apply_dam_effects(self, elevation: np.ndarray, 
                          water_depth: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        댐 효과 적용 (지형 변경 + 저수지)
        
        Args:
            elevation: 고도 그리드
            water_depth: 수심 그리드
            
        Returns:
            (변경된 고도, 변경된 수심)
        """
        new_elevation = elevation.copy()
        new_water = water_depth.copy()
        
        for dam in self.dams:
            row, col = dam.position
            half_w = dam.width // 2
            
            # 댐 구조물
            for c in range(max(0, col - half_w), min(self.grid_size, col + half_w + 1)):
                if 0 <= row < self.grid_size:
                    # 댐 높이만큼 고도 상승 (폭이 1셀인 벽)
                    new_elevation[row, c] = max(new_elevation[row, c], 
                                                new_elevation[row, c] + dam.height)
            
            # 상류 저수지 형성 (댐 뒤편에 물이 참)
            for r in range(max(0, row - 20), row):
                for c in range(max(0, col - 10), min(self.grid_size, col + 10)):
                    if new_elevation[r, c] < new_elevation[row, col] + dam.height:
                        water_level = new_elevation[row, col] + dam.height - new_elevation[r, c]
                        new_water[r, c] = max(new_water[r, c], water_level * 0.5)
            
            dam.current_level = np.mean(new_water[max(0, row-10):row, 
                                                  max(0, col-5):min(self.grid_size, col+5)])
        
        return new_elevation, new_water
    
    # ========== 삼림 벌채 ==========
    def deforest(self, center: Tuple[int, int], 
                 radius: int = 10, 
                 intensity: float = 0.8) -> np.ndarray:
        """
        삼림 벌채
        
        Args:
            center: (row, col) 중심
            radius: 벌채 반경 (셀)
            intensity: 벌채 강도 (0-1)
            
        Returns:
            업데이트된 식생 그리드
        """
        zone = DeforestationZone(center=center, radius=radius, intensity=intensity)
        self.deforestation_zones.append(zone)
        
        y, x = np.ogrid[:self.grid_size, :self.grid_size]
        dist = np.sqrt((x - center[1])**2 + (y - center[0])**2)
        
        # 반경 내 식생 감소
        mask = dist <= radius
        self.vegetation_grid[mask] *= (1 - intensity)
        
        return self.vegetation_grid
    
    def get_erosion_multiplier(self) -> np.ndarray:
        """
        식생에 따른 침식 배율
        식생이 적을수록 침식 증가
        
        Returns:
            침식 배율 그리드 (1.0 = 정상, >1 = 침식 증가)
        """
        # 식생 100% → 배율 0.5, 식생 0% → 배율 3.0
        return 3.0 - 2.5 * self.vegetation_grid
    
    # ========== 토지 이용 변화 ==========
    def convert_land(self, center: Tuple[int, int], 
                     radius: int, 
                     land_type: int) -> np.ndarray:
        """
        토지 이용 변화
        
        Args:
            center: 중심 위치
            radius: 반경
            land_type: 0=자연, 1=농지, 2=도시
            
        Returns:
            업데이트된 토지 이용 그리드
        """
        y, x = np.ogrid[:self.grid_size, :self.grid_size]
        dist = np.sqrt((x - center[1])**2 + (y - center[0])**2)
        
        mask = dist <= radius
        self.land_use_grid[mask] = land_type
        
        # 도시화 → 식생 감소
        if land_type == 2:
            self.vegetation_grid[mask] *= 0.1
        # 농지 → 식생 중간
        elif land_type == 1:
            self.vegetation_grid[mask] *= 0.5
        
        return self.land_use_grid
    
    def get_summary(self) -> Dict:
        """현재 인간 활동 요약"""
        return {
            'num_dams': len(self.dams),
            'deforested_area': np.sum(self.vegetation_grid < 0.5),
            'urban_area': np.sum(self.land_use_grid == 2),
            'farm_area': np.sum(self.land_use_grid == 1),
            'avg_vegetation': np.mean(self.vegetation_grid)
        }
