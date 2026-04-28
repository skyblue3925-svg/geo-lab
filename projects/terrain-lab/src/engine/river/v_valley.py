"""
Geo-Lab AI: V자곡 시뮬레이션
상류 하천의 하방 침식으로 V자 모양 골짜기 형성
"""
import numpy as np
from dataclasses import dataclass, field
from typing import List, Tuple

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from engine.base import Terrain, Water, SimulationState
from engine.erosion import vertical_erosion, headward_erosion, mass_wasting, apply_erosion


@dataclass
class VValleySimulator:
    """V자곡 시뮬레이션
    
    핵심 원리:
    1. 하방 침식 (Stream Power Law)
    2. 사면 붕괴 (Mass Wasting)
    
    결과: V자 형태의 깊은 골짜기
    """
    
    # 지형 크기
    width: int = 100
    height: int = 100
    
    # 시뮬레이션 파라미터
    rock_hardness: float = 0.5  # 0=무름, 1=단단함
    slope_gradient: float = 0.1  # 초기 경사
    initial_discharge: float = 10.0  # 초기 유량
    
    # 침식 계수
    k_vertical: float = 0.0005  # 하방 침식 계수
    k_headward: float = 0.0003  # 두부 침식 계수
    
    # 내부 상태
    terrain: Terrain = field(default=None)
    water: Water = field(default=None)
    history: List[np.ndarray] = field(default_factory=list)
    current_step: int = 0
    
    def __post_init__(self):
        self.reset()
    
    def reset(self):
        """시뮬레이션 초기화"""
        # 초기 지형: 북쪽이 높은 경사면
        self.terrain = Terrain(width=self.width, height=self.height)
        
        # 경사 설정
        for y in range(self.height):
            base_elevation = 500 * (1 - y / self.height)
            self.terrain.elevation[y, :] = base_elevation
        
        # 중앙에 초기 하천 채널 (약간 낮게)
        center = self.width // 2
        channel_width = 3
        for x in range(center - channel_width, center + channel_width):
            if 0 <= x < self.width:
                self.terrain.elevation[:, x] -= 10
        
        # 암석 경도 설정
        self.terrain.rock_hardness[:] = self.rock_hardness
        
        # 수문 초기화
        self.water = Water(terrain=self.terrain)
        self.water.discharge[0, center] = self.initial_discharge  # 상류에서 유입
        self.water.accumulate_flow()
        
        self.history = [self.terrain.elevation.copy()]
        self.current_step = 0
    
    def step(self, n_steps: int = 1) -> np.ndarray:
        """시뮬레이션 n스텝 진행"""
        for _ in range(n_steps):
            # 1. 유량 계산
            self.water.add_precipitation(rate=0.001)
            self.water.accumulate_flow()
            
            # 2. 하방 침식
            v_erosion = vertical_erosion(
                self.terrain, self.water,
                k_erosion=self.k_vertical * (1 - self.rock_hardness)
            )
            apply_erosion(self.terrain, v_erosion)
            
            # 3. 두부 침식
            h_erosion = headward_erosion(
                self.terrain, self.water,
                k_headward=self.k_headward
            )
            apply_erosion(self.terrain, h_erosion)
            
            # 4. 사면 붕괴 (V자 형성의 핵심!)
            mass_change = mass_wasting(self.terrain)
            self.terrain.elevation += mass_change
            
            # 5. 흐름 방향 업데이트
            self.water.flow_x, self.water.flow_y = self.terrain.get_flow_direction()
            
            self.current_step += 1
            
            # 히스토리 저장 (매 10스텝)
            if self.current_step % 10 == 0:
                self.history.append(self.terrain.elevation.copy())
        
        return self.terrain.elevation
    
    def get_cross_section(self, y_position: int = None) -> Tuple[np.ndarray, np.ndarray]:
        """특정 위치의 단면도 반환"""
        if y_position is None:
            y_position = self.height // 2
        
        x = np.arange(self.width) * self.terrain.cell_size
        z = self.terrain.elevation[y_position, :]
        
        return x, z
    
    def get_valley_depth(self) -> float:
        """현재 V자곡 깊이 측정"""
        center = self.width // 2
        y_mid = self.height // 2
        
        # 좌우 고도 평균 vs 중앙 고도
        left_elev = self.terrain.elevation[y_mid, center - 20]
        right_elev = self.terrain.elevation[y_mid, center + 20]
        center_elev = self.terrain.elevation[y_mid, center]
        
        depth = (left_elev + right_elev) / 2 - center_elev
        return max(0, depth)
    
    def get_info(self) -> dict:
        """현재 시뮬레이션 상태 정보"""
        return {
            "step": self.current_step,
            "valley_depth": self.get_valley_depth(),
            "max_elevation": float(self.terrain.elevation.max()),
            "min_elevation": float(self.terrain.elevation.min()),
            "total_erosion": float(self.history[0].sum() - self.terrain.elevation.sum())
        }


# 테스트 코드
if __name__ == "__main__":
    sim = VValleySimulator(rock_hardness=0.3)
    
    print("V자곡 시뮬레이션 시작")
    print(f"초기 깊이: {sim.get_valley_depth():.1f}m")
    
    for i in range(10):
        sim.step(100)
        info = sim.get_info()
        print(f"Step {info['step']}: 깊이 {info['valley_depth']:.1f}m, "
              f"총 침식량 {info['total_erosion']:.0f}m³")
    
    print("시뮬레이션 완료!")
