"""
Geo-Lab AI: 삼각주 물리 시뮬레이션
Galloway 분류 기반 3가지 에너지 균형
"""
import numpy as np
from dataclasses import dataclass, field
from typing import List, Tuple
from enum import Enum
from scipy.ndimage import gaussian_filter


class DeltaType(Enum):
    RIVER_DOMINATED = "조족상 (Bird's Foot)"
    WAVE_DOMINATED = "원호상 (Arcuate)"
    TIDE_DOMINATED = "첨각상 (Cuspate)"


@dataclass
class DeltaGrid:
    """삼각주 2D 그리드"""
    width: int = 150
    height: int = 150
    cell_size: float = 50.0  # m
    
    # 지형 (해수면 기준 고도, m)
    elevation: np.ndarray = field(default=None)
    # 퇴적물 (m)
    sediment: np.ndarray = field(default=None)
    # 수심 (바다 부분)
    water_depth: np.ndarray = field(default=None)
    
    sea_level: float = 0.0
    
    def __post_init__(self):
        if self.elevation is None:
            self.elevation = np.zeros((self.height, self.width))
        if self.sediment is None:
            self.sediment = np.zeros((self.height, self.width))
        if self.water_depth is None:
            self.water_depth = np.zeros((self.height, self.width))
    
    @classmethod
    def create_initial(cls, width: int = 150, height: int = 150,
                       land_fraction: float = 0.3):
        """초기 지형 - 상류(육지) → 하류(바다)"""
        grid = cls(width=width, height=height)
        
        land_rows = int(height * land_fraction)
        
        for y in range(height):
            if y < land_rows:
                # 육지: 경사
                grid.elevation[y, :] = 10 - y * 0.3
            else:
                # 바다: 해수면 아래
                depth = (y - land_rows) * 0.2
                grid.elevation[y, :] = -depth
        
        # 하천 채널
        center = width // 2
        for x in range(center - 5, center + 6):
            if 0 <= x < width:
                grid.elevation[:land_rows, x] -= 2
        
        # 수심 계산
        grid.water_depth = np.maximum(0, grid.sea_level - grid.elevation)
        
        return grid


class RiverMouthDeposition:
    """하구 퇴적 (하천 주도)"""
    
    def __init__(self, sediment_flux: float = 1000.0,  # m³/yr
                 settling_velocity: float = 0.01):  # m/s
        self.sediment_flux = sediment_flux
        self.settling_velocity = settling_velocity
    
    def deposit(self, grid: DeltaGrid, river_energy: float, 
                channel_x: int, dt: float = 1.0) -> np.ndarray:
        """하천 퇴적물 분배"""
        h, w = grid.height, grid.width
        deposition = np.zeros((h, w))
        
        # 하구 위치
        estuary_y = np.argmax(grid.elevation[:, channel_x] < grid.sea_level)
        if estuary_y == 0:
            estuary_y = h // 2
        
        # 하천 우세: 길게 뻗어나가는 패턴 (jet 확산)
        spread_angle = np.radians(15 + (1 - river_energy) * 30)  # 하천 에너지 높으면 좁게
        
        for y in range(estuary_y, h):
            dy = y - estuary_y + 1
            spread = int(dy * np.tan(spread_angle))
            
            for x in range(channel_x - spread, channel_x + spread + 1):
                if 0 <= x < w:
                    # 거리에 따른 감소
                    dist = np.sqrt((x - channel_x)**2 + dy**2)
                    dep_rate = self.sediment_flux * river_energy * np.exp(-dist / 50) * 0.001
                    deposition[y, x] += dep_rate * dt
        
        return deposition


class WaveRedistribution:
    """파랑에 의한 재분배"""
    
    def __init__(self, wave_power: float = 1.0):
        self.wave_power = wave_power
    
    def redistribute(self, grid: DeltaGrid, wave_energy: float,
                     dt: float = 1.0) -> np.ndarray:
        """파랑에 의한 퇴적물 좌우 확산"""
        # 해안선 부근에서 좌우로 퍼뜨림
        shoreline = np.abs(grid.elevation - grid.sea_level) < 2
        
        # 가우시안 필터로 좌우 확산 (x축 방향)
        sediment_change = np.zeros_like(grid.sediment)
        
        if np.any(shoreline):
            # 해안선 부근 퇴적물만 확산
            coastal_sediment = grid.sediment * shoreline.astype(float)
            smoothed = gaussian_filter(coastal_sediment, sigma=[0.5, 3 * wave_energy])
            
            # 변화량
            sediment_change = (smoothed - coastal_sediment) * wave_energy * dt * 0.1
        
        return sediment_change


class TidalScouring:
    """조류에 의한 침식"""
    
    def __init__(self, tidal_range: float = 2.0):  # m
        self.tidal_range = tidal_range
    
    def scour(self, grid: DeltaGrid, tidal_energy: float,
              dt: float = 1.0) -> np.ndarray:
        """조류에 의한 하구 확대 (세굴)"""
        h, w = grid.height, grid.width
        erosion = np.zeros((h, w))
        
        # 하구 부근 (해수면 근처)
        tidal_zone = np.abs(grid.elevation - grid.sea_level) < self.tidal_range
        
        # 채널 방향으로 세굴
        for y in range(1, h):
            for x in range(1, w-1):
                if tidal_zone[y, x] and grid.sediment[y, x] > 0:
                    # 바다 방향으로 퇴적물 이동
                    erosion[y, x] = grid.sediment[y, x] * tidal_energy * 0.01 * dt
        
        return erosion


class DeltaSimulation:
    """삼각주 시뮬레이션"""
    
    def __init__(self, width: int = 150, height: int = 150):
        self.grid = DeltaGrid.create_initial(width=width, height=height)
        
        self.river_dep = RiverMouthDeposition()
        self.wave_redis = WaveRedistribution()
        self.tidal_scour = TidalScouring()
        
        self.river_energy = 0.5
        self.wave_energy = 0.3
        self.tidal_energy = 0.2
        
        self.history: List[np.ndarray] = []
        self.time = 0.0
    
    def set_energy_balance(self, river: float, wave: float, tidal: float):
        """에너지 균형 설정 (0-1로 정규화)"""
        total = river + wave + tidal + 0.01
        self.river_energy = river / total
        self.wave_energy = wave / total
        self.tidal_energy = tidal / total
    
    def step(self, dt: float = 1.0):
        """1 타임스텝"""
        center_x = self.grid.width // 2
        
        # 1. 하천 퇴적
        river_dep = self.river_dep.deposit(
            self.grid, self.river_energy, center_x, dt
        )
        
        # 2. 파랑 재분배
        wave_change = self.wave_redis.redistribute(
            self.grid, self.wave_energy, dt
        )
        
        # 3. 조류 세굴
        tidal_erosion = self.tidal_scour.scour(
            self.grid, self.tidal_energy, dt
        )
        
        # 적용
        self.grid.sediment += river_dep + wave_change - tidal_erosion
        self.grid.sediment = np.maximum(0, self.grid.sediment)
        
        # 지형 업데이트
        self.grid.elevation = self.grid.elevation + self.grid.sediment * 0.01
        self.grid.water_depth = np.maximum(0, self.grid.sea_level - self.grid.elevation)
        
        self.time += dt
    
    def run(self, total_time: float, save_interval: float = 100.0, dt: float = 1.0):
        """시뮬레이션 실행"""
        steps = int(total_time / dt)
        save_every = max(1, int(save_interval / dt))
        
        self.history = [self.grid.elevation.copy()]
        
        for i in range(steps):
            self.step(dt)
            if (i + 1) % save_every == 0:
                self.history.append(self.grid.elevation.copy())
        
        return self.history
    
    def get_delta_type(self) -> DeltaType:
        """현재 삼각주 유형 판별"""
        if self.river_energy >= self.wave_energy and self.river_energy >= self.tidal_energy:
            return DeltaType.RIVER_DOMINATED
        elif self.wave_energy >= self.tidal_energy:
            return DeltaType.WAVE_DOMINATED
        else:
            return DeltaType.TIDE_DOMINATED
    
    def get_delta_area(self) -> float:
        """삼각주 면적 (해수면 위 새 땅)"""
        initial_land = self.history[0] > self.grid.sea_level
        current_land = self.grid.elevation > self.grid.sea_level
        new_land = current_land & ~initial_land
        return float(np.sum(new_land)) * self.grid.cell_size**2 / 1e6  # km²


# 프리컴퓨팅
def precompute_delta(max_time: int = 10000,
                     river_energy: float = 60,
                     wave_energy: float = 25,
                     tidal_energy: float = 15,
                     save_every: int = 100) -> dict:
    """삼각주 시뮬레이션 프리컴퓨팅"""
    sim = DeltaSimulation()
    sim.set_energy_balance(river_energy, wave_energy, tidal_energy)
    
    history = sim.run(
        total_time=max_time,
        save_interval=save_every,
        dt=1.0
    )
    
    return {
        'history': history,
        'delta_type': sim.get_delta_type().value,
        'delta_area': sim.get_delta_area()
    }


if __name__ == "__main__":
    print("삼각주 물리 시뮬레이션 테스트")
    print("=" * 50)
    
    # 시나리오 1: 하천 우세
    sim1 = DeltaSimulation()
    sim1.set_energy_balance(80, 10, 10)
    sim1.run(5000, save_interval=1000)
    print(f"하천 우세: {sim1.get_delta_type().value}, 면적 {sim1.get_delta_area():.2f} km²")
    
    # 시나리오 2: 파랑 우세
    sim2 = DeltaSimulation()
    sim2.set_energy_balance(30, 60, 10)
    sim2.run(5000, save_interval=1000)
    print(f"파랑 우세: {sim2.get_delta_type().value}, 면적 {sim2.get_delta_area():.2f} km²")
    
    print("=" * 50)
    print("테스트 완료!")
