"""
Geo-Lab AI: 곡류 & 우각호 시뮬레이션
중류 하천의 측방 침식으로 굽이치는 하천과 우각호 형성
"""
import numpy as np
from dataclasses import dataclass, field
from typing import List, Tuple, Optional

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from engine.base import Terrain, Water
from engine.erosion import lateral_erosion, apply_erosion
from engine.deposition import apply_deposition


@dataclass
class MeanderSimulator:
    """곡류 하천 시뮬레이션
    
    핵심 원리:
    1. 측방 침식 (Lateral Erosion) - 바깥쪽(공격사면)
    2. 측방 퇴적 (Point Bar) - 안쪽(퇴적사면)
    3. 유로 절단 (Cutoff) - 우각호 형성
    
    결과: 굽이치는 하천, 우각호(Oxbow Lake)
    """
    
    # 지형 크기
    width: int = 150
    height: int = 150
    
    # 시뮬레이션 파라미터
    initial_sinuosity: float = 1.2  # 초기 굴곡도
    discharge: float = 50.0  # 유량
    
    # 침식/퇴적 계수
    k_lateral: float = 0.0003
    k_deposition: float = 0.0002
    
    # 우각호 형성 조건
    cutoff_threshold: float = 10.0  # 유로 간 거리가 이 이하면 절단
    
    # 내부 상태
    terrain: Terrain = field(default=None)
    water: Water = field(default=None)
    channel_path: List[Tuple[int, int]] = field(default_factory=list)
    oxbow_lakes: List[np.ndarray] = field(default_factory=list)
    history: List[np.ndarray] = field(default_factory=list)
    current_step: int = 0
    
    def __post_init__(self):
        self.reset()
    
    def reset(self):
        """시뮬레이션 초기화"""
        self.terrain = Terrain(width=self.width, height=self.height)
        
        # 평탄한 범람원 (약간의 경사)
        for y in range(self.height):
            self.terrain.elevation[y, :] = 100 - y * 0.2  # 완만한 경사
        
        # 초기 곡류 하천 경로 생성
        self._create_initial_channel()
        
        # 수문 초기화
        self.water = Water(terrain=self.terrain)
        self._update_water_from_channel()
        
        self.oxbow_lakes = []
        self.history = [self.terrain.elevation.copy()]
        self.current_step = 0
    
    def _create_initial_channel(self):
        """초기 사인파 형태의 곡류 하천 생성"""
        self.channel_path = []
        
        amplitude = self.width * 0.15 * self.initial_sinuosity
        frequency = 3  # 굽이 수
        
        center = self.width // 2
        
        for y in range(self.height):
            # 사인파 곡선
            x = int(center + amplitude * np.sin(2 * np.pi * frequency * y / self.height))
            x = max(5, min(self.width - 5, x))
            self.channel_path.append((y, x))
            
            # 하천 채널 파기 (주변도 약간)
            for dx in range(-3, 4):
                nx = x + dx
                if 0 <= nx < self.width:
                    depth = 5 * (1 - abs(dx) / 4)
                    self.terrain.elevation[y, nx] -= depth
    
    def _update_water_from_channel(self):
        """하천 경로를 기반으로 수문 데이터 업데이트"""
        self.water.discharge[:] = 0
        self.water.velocity[:] = 0
        
        for y, x in self.channel_path:
            self.water.discharge[y, x] = self.discharge
            self.water.velocity[y, x] = 2.0  # 기본 유속
        
        # 주변으로 확산
        from scipy.ndimage import gaussian_filter
        self.water.discharge = gaussian_filter(self.water.discharge, sigma=1)
        self.water.velocity = gaussian_filter(self.water.velocity, sigma=1)
    
    def step(self, n_steps: int = 1) -> np.ndarray:
        """시뮬레이션 n스텝 진행"""
        for _ in range(n_steps):
            # 1. 측방 침식 (바깥쪽)
            erosion = self._calculate_bank_erosion()
            apply_erosion(self.terrain, erosion)
            
            # 2. Point Bar 퇴적 (안쪽)
            deposition = self._calculate_point_bar_deposition()
            apply_deposition(self.terrain, deposition)
            
            # 3. 하천 경로 업데이트 (가장 낮은 곳으로 이동)
            self._update_channel_path()
            
            # 4. 우각호 체크
            self._check_cutoff()
            
            # 5. 수문 업데이트
            self._update_water_from_channel()
            
            self.current_step += 1
            
            if self.current_step % 10 == 0:
                self.history.append(self.terrain.elevation.copy())
        
        return self.terrain.elevation
    
    def _calculate_bank_erosion(self) -> np.ndarray:
        """공격사면(바깥쪽) 침식 계산"""
        erosion = np.zeros((self.height, self.width))
        
        for i in range(1, len(self.channel_path) - 1):
            y, x = self.channel_path[i]
            y_prev, x_prev = self.channel_path[i - 1]
            y_next, x_next = self.channel_path[i + 1]
            
            # 곡률 계산 (방향 변화)
            dx1, dy1 = x - x_prev, y - y_prev
            dx2, dy2 = x_next - x, y_next - y
            
            # 외적으로 회전 방향 판단
            cross = dx1 * dy2 - dy1 * dx2
            
            # 바깥쪽 결정
            if cross > 0:  # 오른쪽으로 회전 → 왼쪽이 바깥
                outer_x = x - 1
            else:  # 왼쪽으로 회전 → 오른쪽이 바깥
                outer_x = x + 1
            
            if 0 <= outer_x < self.width:
                curvature = abs(cross) / (np.sqrt(dx1**2+dy1**2+0.1) * np.sqrt(dx2**2+dy2**2+0.1) + 0.1)
                erosion[y, outer_x] = self.k_lateral * self.discharge * curvature
        
        return erosion
    
    def _calculate_point_bar_deposition(self) -> np.ndarray:
        """퇴적사면(안쪽) 퇴적 계산"""
        deposition = np.zeros((self.height, self.width))
        
        for i in range(1, len(self.channel_path) - 1):
            y, x = self.channel_path[i]
            y_prev, x_prev = self.channel_path[i - 1]
            y_next, x_next = self.channel_path[i + 1]
            
            dx1, dy1 = x - x_prev, y - y_prev
            dx2, dy2 = x_next - x, y_next - y
            cross = dx1 * dy2 - dy1 * dx2
            
            # 안쪽 (바깥쪽 반대)
            if cross > 0:
                inner_x = x + 1
            else:
                inner_x = x - 1
            
            if 0 <= inner_x < self.width:
                curvature = abs(cross) / (np.sqrt(dx1**2+dy1**2+0.1) * np.sqrt(dx2**2+dy2**2+0.1) + 0.1)
                deposition[y, inner_x] = self.k_deposition * self.discharge * curvature
        
        return deposition
    
    def _update_channel_path(self):
        """하천 경로를 가장 낮은 지점으로 이동"""
        new_path = [self.channel_path[0]]  # 시작점 유지
        
        for i in range(1, len(self.channel_path) - 1):
            y, x = self.channel_path[i]
            
            # 주변 중 가장 낮은 곳 탐색
            min_elev = self.terrain.elevation[y, x]
            best_x = x
            
            for dx in [-1, 0, 1]:
                nx = x + dx
                if 0 <= nx < self.width:
                    if self.terrain.elevation[y, nx] < min_elev:
                        min_elev = self.terrain.elevation[y, nx]
                        best_x = nx
            
            new_path.append((y, best_x))
        
        new_path.append(self.channel_path[-1])  # 끝점 유지
        self.channel_path = new_path
    
    def _check_cutoff(self):
        """우각호 형성 조건 체크"""
        # 가까운 두 유로 지점 찾기
        for i in range(len(self.channel_path)):
            for j in range(i + 20, len(self.channel_path)):  # 최소 20셀 떨어진 것만
                y1, x1 = self.channel_path[i]
                y2, x2 = self.channel_path[j]
                
                dist = np.sqrt((x1 - x2)**2 + (y1 - y2)**2)
                
                if dist < self.cutoff_threshold:
                    # Cutoff 발생! 우각호 생성
                    self._create_oxbow_lake(i, j)
                    return
    
    def _create_oxbow_lake(self, start_idx: int, end_idx: int):
        """우각호 생성"""
        # 고립될 구간 추출
        cutoff_section = self.channel_path[start_idx:end_idx]
        
        # 우각호로 저장
        oxbow = np.zeros((self.height, self.width), dtype=bool)
        for y, x in cutoff_section:
            oxbow[y, x] = True
        self.oxbow_lakes.append(oxbow)
        
        # 하천 경로 단축 (직선으로)
        self.channel_path = (
            self.channel_path[:start_idx+1] + 
            self.channel_path[end_idx:]
        )
        
        print(f"🌊 우각호 형성! (Step {self.current_step})")
    
    def get_cross_section(self, y_position: int = None) -> Tuple[np.ndarray, np.ndarray]:
        """특정 위치의 단면도"""
        if y_position is None:
            y_position = self.height // 2
        
        x = np.arange(self.width) * self.terrain.cell_size
        z = self.terrain.elevation[y_position, :]
        
        return x, z
    
    def get_sinuosity(self) -> float:
        """현재 굴곡도 계산"""
        if len(self.channel_path) < 2:
            return 1.0
        
        # 실제 경로 길이
        path_length = 0
        for i in range(1, len(self.channel_path)):
            y1, x1 = self.channel_path[i-1]
            y2, x2 = self.channel_path[i]
            path_length += np.sqrt((x2-x1)**2 + (y2-y1)**2)
        
        # 직선 거리
        y_start, x_start = self.channel_path[0]
        y_end, x_end = self.channel_path[-1]
        straight_length = np.sqrt((x_end-x_start)**2 + (y_end-y_start)**2) + 0.1
        
        return path_length / straight_length
    
    def get_info(self) -> dict:
        """현재 상태 정보"""
        return {
            "step": self.current_step,
            "sinuosity": self.get_sinuosity(),
            "oxbow_lakes": len(self.oxbow_lakes),
            "channel_length": len(self.channel_path)
        }


if __name__ == "__main__":
    sim = MeanderSimulator(initial_sinuosity=1.5)
    
    print("곡류 하천 시뮬레이션 시작")
    print(f"초기 굴곡도: {sim.get_sinuosity():.2f}")
    
    for i in range(20):
        sim.step(50)
        info = sim.get_info()
        print(f"Step {info['step']}: 굴곡도 {info['sinuosity']:.2f}, "
              f"우각호 {info['oxbow_lakes']}개")
    
    print("시뮬레이션 완료!")
