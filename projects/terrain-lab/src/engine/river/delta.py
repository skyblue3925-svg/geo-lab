"""
Geo-Lab AI: 삼각주 시뮬레이션
하류에서 3가지 에너지 균형에 따른 삼각주 형태 형성
"""
import numpy as np
from dataclasses import dataclass, field
from typing import List, Tuple
from enum import Enum

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from engine.base import Terrain, Water
from engine.deposition import delta_deposition, apply_deposition


class DeltaType(Enum):
    """삼각주 분류 (Galloway's Classification)"""
    RIVER_DOMINATED = "조족상 (Bird's Foot)"  # 미시시피형
    WAVE_DOMINATED = "원호상 (Arcuate)"       # 나일형
    TIDE_DOMINATED = "첨각상 (Cuspate)"       # 티베르형


@dataclass
class DeltaSimulator:
    """삼각주 시뮬레이션
    
    핵심 원리:
    하천 에너지 vs 파랑 에너지 vs 조류 에너지의 균형
    
    결과:
    - 하천 우세: 길게 뻗은 조족상 (미시시피강)
    - 파랑 우세: 넓게 퍼진 원호상 (나일강)
    - 조류 우세: 뾰족한 첨각상 (티베르강)
    """
    
    # 지형 크기
    width: int = 120
    height: int = 100
    
    # 에너지 파라미터 (0-100)
    river_energy: float = 50.0
    wave_energy: float = 30.0
    tidal_energy: float = 20.0
    
    # 환경
    sea_level: float = 10.0
    sediment_supply: float = 1.0  # 퇴적물 공급량 계수
    
    # 내부 상태
    terrain: Terrain = field(default=None)
    water: Water = field(default=None)
    delta_mask: np.ndarray = field(default=None)  # 삼각주 영역
    history: List[np.ndarray] = field(default_factory=list)
    current_step: int = 0
    
    def __post_init__(self):
        self.reset()
    
    def reset(self):
        """시뮬레이션 초기화"""
        self.terrain = Terrain(width=self.width, height=self.height)
        
        # 지형 설정: 상류(육지) → 하류(바다)
        for y in range(self.height):
            if y < self.height * 0.4:
                # 육지 (경사)
                elev = 50 - y * 0.5
            else:
                # 바다 (해수면 아래)
                elev = self.sea_level - (y - self.height * 0.4) * 0.3
            self.terrain.elevation[y, :] = elev
        
        # 중앙에 하천 채널
        center = self.width // 2
        for y in range(int(self.height * 0.5)):
            for dx in range(-3, 4):
                x = center + dx
                if 0 <= x < self.width:
                    self.terrain.elevation[y, x] -= 5
        
        # 수문 초기화
        self.water = Water(terrain=self.terrain)
        self.water.discharge[0, center] = 100  # 상류 유입
        self.water.accumulate_flow()
        
        self.delta_mask = np.zeros((self.height, self.width), dtype=bool)
        self.history = [self.terrain.elevation.copy()]
        self.current_step = 0
    
    def set_energy_balance(self, river: float, wave: float, tidal: float):
        """에너지 균형 설정 (0-100)"""
        self.river_energy = max(0, min(100, river))
        self.wave_energy = max(0, min(100, wave))
        self.tidal_energy = max(0, min(100, tidal))
    
    def step(self, n_steps: int = 1) -> np.ndarray:
        """시뮬레이션 n스텝 진행"""
        for _ in range(n_steps):
            # 1. 유량 계산
            self.water.accumulate_flow()
            
            # 2. 삼각주 퇴적
            deposition = self._calculate_delta_deposition()
            apply_deposition(self.terrain, deposition)
            
            # 3. 파랑/조류에 의한 재분배
            redistribution = self._calculate_redistribution()
            self.terrain.elevation += redistribution
            
            # 4. 삼각주 영역 업데이트
            self._update_delta_mask()
            
            self.current_step += 1
            
            if self.current_step % 10 == 0:
                self.history.append(self.terrain.elevation.copy())
        
        return self.terrain.elevation
    
    def _calculate_delta_deposition(self) -> np.ndarray:
        """에너지 균형 기반 삼각주 퇴적 계산"""
        deposition = delta_deposition(
            self.terrain, self.water,
            river_energy=self.river_energy / 50,  # 정규화
            wave_energy=self.wave_energy / 50,
            tidal_energy=self.tidal_energy / 50,
            sea_level=self.sea_level
        )
        
        return deposition * self.sediment_supply
    
    def _calculate_redistribution(self) -> np.ndarray:
        """파랑/조류에 의한 퇴적물 재분배"""
        redistribution = np.zeros((self.height, self.width))
        
        # 하구 영역 (해수면 근처)
        estuary = (self.terrain.elevation > self.sea_level - 5) & \
                  (self.terrain.elevation < self.sea_level + 5)
        
        if not np.any(estuary):
            return redistribution
        
        # 파랑: 좌우로 퍼뜨림
        if self.wave_energy > 20:
            from scipy.ndimage import uniform_filter1d
            for y in range(self.height):
                if np.any(estuary[y, :]):
                    # 좌우 방향 평활화
                    row = self.terrain.elevation[y, :].copy()
                    smoothed = uniform_filter1d(row, size=5)
                    redistribution[y, :] = (smoothed - row) * (self.wave_energy / 100) * 0.1
        
        # 조류: 바다 방향으로 쓸어냄
        if self.tidal_energy > 20:
            for y in range(1, self.height):
                factor = self.tidal_energy / 100 * 0.05
                if np.any(estuary[y, :]):
                    # 아래로 이동
                    redistribution[y, :] += self.terrain.elevation[y-1, :] * factor * 0.1
                    redistribution[y-1, :] -= self.terrain.elevation[y-1, :] * factor * 0.1
        
        return redistribution
    
    def _update_delta_mask(self):
        """삼각주 영역 업데이트"""
        # 해수면보다 약간 높고 하구 근처인 영역
        self.delta_mask = (
            (self.terrain.elevation > self.sea_level) & 
            (self.terrain.elevation < self.sea_level + 20) &
            (np.arange(self.height)[:, None] > self.height * 0.4)  # 하류
        )
    
    def get_delta_type(self) -> DeltaType:
        """현재 삼각주 유형 판별"""
        total = self.river_energy + self.wave_energy + self.tidal_energy + 0.01
        
        r_ratio = self.river_energy / total
        w_ratio = self.wave_energy / total
        t_ratio = self.tidal_energy / total
        
        if r_ratio >= w_ratio and r_ratio >= t_ratio:
            return DeltaType.RIVER_DOMINATED
        elif w_ratio >= t_ratio:
            return DeltaType.WAVE_DOMINATED
        else:
            return DeltaType.TIDE_DOMINATED
    
    def get_delta_area(self) -> float:
        """삼각주 면적 (셀 수)"""
        return float(np.sum(self.delta_mask))
    
    def get_delta_extent(self) -> Tuple[float, float]:
        """삼각주 가로/세로 범위"""
        if not np.any(self.delta_mask):
            return 0, 0
        
        cols = np.any(self.delta_mask, axis=0)
        rows = np.any(self.delta_mask, axis=1)
        
        width = np.sum(cols) * self.terrain.cell_size
        length = np.sum(rows) * self.terrain.cell_size
        
        return width, length
    
    def get_info(self) -> dict:
        """현재 상태 정보"""
        delta_type = self.get_delta_type()
        width, length = self.get_delta_extent()
        
        return {
            "step": self.current_step,
            "delta_type": delta_type.value,
            "delta_area": self.get_delta_area(),
            "delta_width": width,
            "delta_length": length,
            "energy_balance": {
                "river": self.river_energy,
                "wave": self.wave_energy,
                "tidal": self.tidal_energy
            }
        }


if __name__ == "__main__":
    # 시나리오 1: 미시시피형 (하천 우세)
    print("=" * 50)
    print("시나리오 1: 조족상 삼각주 (미시시피형)")
    sim1 = DeltaSimulator()
    sim1.set_energy_balance(river=80, wave=10, tidal=10)
    
    for i in range(10):
        sim1.step(50)
    info = sim1.get_info()
    print(f"유형: {info['delta_type']}")
    print(f"면적: {info['delta_area']:.0f}, 폭: {info['delta_width']:.0f}m, 길이: {info['delta_length']:.0f}m")
    
    # 시나리오 2: 나일형 (파랑 우세)
    print("\n" + "=" * 50)
    print("시나리오 2: 원호상 삼각주 (나일형)")
    sim2 = DeltaSimulator()
    sim2.set_energy_balance(river=30, wave=60, tidal=10)
    
    for i in range(10):
        sim2.step(50)
    info = sim2.get_info()
    print(f"유형: {info['delta_type']}")
    print(f"면적: {info['delta_area']:.0f}, 폭: {info['delta_width']:.0f}m, 길이: {info['delta_length']:.0f}m")
    
    print("\n시뮬레이션 완료!")
