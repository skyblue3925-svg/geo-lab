"""
Geo-Lab AI: 진짜 물리 시뮬레이션 엔진
Stream Power Law 기반 실제 침식 시뮬레이션
"""
import numpy as np
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
from scipy.ndimage import gaussian_filter, uniform_filter


@dataclass
class TerrainGrid:
    """2D 지형 그리드"""
    width: int = 100
    height: int = 100
    cell_size: float = 10.0  # 미터
    
    elevation: np.ndarray = field(default=None)
    bedrock: np.ndarray = field(default=None)  # 기반암 (침식 불가 레벨)
    rock_hardness: np.ndarray = field(default=None)  # 0-1
    
    def __post_init__(self):
        if self.elevation is None:
            self.elevation = np.zeros((self.height, self.width))
        if self.bedrock is None:
            self.bedrock = np.full((self.height, self.width), -100.0)
        if self.rock_hardness is None:
            self.rock_hardness = np.full((self.height, self.width), 0.5)
    
    def get_slope(self) -> np.ndarray:
        """경사도 계산 (m/m)"""
        dy, dx = np.gradient(self.elevation, self.cell_size)
        return np.sqrt(dx**2 + dy**2)
    
    def get_slope_direction(self) -> Tuple[np.ndarray, np.ndarray]:
        """최대 경사 방향 (단위 벡터)"""
        dy, dx = np.gradient(self.elevation, self.cell_size)
        magnitude = np.sqrt(dx**2 + dy**2) + 1e-10
        return -dx / magnitude, -dy / magnitude


@dataclass
class WaterFlow:
    """수문 시뮬레이션"""
    terrain: TerrainGrid
    
    # 유량 (m³/s per cell)
    discharge: np.ndarray = field(default=None)
    # 유속 (m/s)
    velocity: np.ndarray = field(default=None)
    # 수심 (m)
    depth: np.ndarray = field(default=None)
    # 전단응력 (Pa)
    shear_stress: np.ndarray = field(default=None)
    
    manning_n: float = 0.03  # Manning 조도계수
    
    def __post_init__(self):
        shape = (self.terrain.height, self.terrain.width)
        if self.discharge is None:
            self.discharge = np.zeros(shape)
        if self.velocity is None:
            self.velocity = np.zeros(shape)
        if self.depth is None:
            self.depth = np.zeros(shape)
        if self.shear_stress is None:
            self.shear_stress = np.zeros(shape)
    
    def flow_accumulation_d8(self, precipitation: float = 0.001):
        """D8 알고리즘 기반 유량 누적"""
        h, w = self.terrain.height, self.terrain.width
        elev = self.terrain.elevation
        
        # 초기 강수
        acc = np.full((h, w), precipitation)
        
        # 높은 곳에서 낮은 곳으로 정렬
        flat_elev = elev.ravel()
        sorted_indices = np.argsort(flat_elev)[::-1]
        
        # D8 방향 (8방향 이웃)
        neighbors = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
        
        for idx in sorted_indices:
            y, x = idx // w, idx % w
            current_elev = elev[y, x]
            
            # 가장 낮은 이웃 찾기
            min_elev = current_elev
            min_neighbor = None
            
            for dy, dx in neighbors:
                ny, nx = y + dy, x + dx
                if 0 <= ny < h and 0 <= nx < w:
                    if elev[ny, nx] < min_elev:
                        min_elev = elev[ny, nx]
                        min_neighbor = (ny, nx)
            
            # 하류로 유량 전달
            if min_neighbor is not None:
                acc[min_neighbor] += acc[y, x]
        
        self.discharge = acc
        return acc
    
    def calculate_hydraulics(self):
        """Manning 방정식 기반 수리학 계산"""
        slope = self.terrain.get_slope() + 0.0001  # 0 방지
        
        # 가정: 채널 폭 = 유량의 함수
        channel_width = 2 * np.power(self.discharge + 0.01, 0.4)
        
        # Manning 방정식: V = (1/n) * R^(2/3) * S^(1/2)
        # 단순화: R ≈ depth
        # Q = V * A, A = width * depth
        # depth = (Q * n / (width * S^0.5))^(3/5)
        
        self.depth = np.power(
            self.discharge * self.manning_n / (channel_width * np.sqrt(slope) + 0.01),
            0.6
        )
        self.depth = np.clip(self.depth, 0, 50)
        
        # 유속
        hydraulic_radius = self.depth  # 단순화
        self.velocity = (1 / self.manning_n) * np.power(hydraulic_radius, 2/3) * np.sqrt(slope)
        self.velocity = np.clip(self.velocity, 0, 10)
        
        # 전단응력 τ = ρgRS
        rho_water = 1000  # kg/m³
        g = 9.81
        self.shear_stress = rho_water * g * self.depth * slope


class StreamPowerErosion:
    """Stream Power Law 기반 침식
    
    E = K * A^m * S^n
    - E: 침식률 (m/yr)
    - K: 침식 계수 (암석 특성 반영)
    - A: 유역 면적 (≈ 유량)
    - S: 경사
    - m: 면적 지수 (typically 0.3-0.6)
    - n: 경사 지수 (typically 1.0-2.0)
    """
    
    def __init__(self, K: float = 1e-5, m: float = 0.5, n: float = 1.0):
        self.K = K
        self.m = m
        self.n = n
    
    def calculate_erosion(self, terrain: TerrainGrid, water: WaterFlow, dt: float = 1.0) -> np.ndarray:
        """침식량 계산"""
        slope = terrain.get_slope()
        
        # Stream Power Law
        # K는 암석 경도에 반비례
        effective_K = self.K * (1 - terrain.rock_hardness * 0.9)
        
        erosion_rate = effective_K * np.power(water.discharge, self.m) * np.power(slope + 0.001, self.n)
        
        erosion = erosion_rate * dt
        
        # 기반암 이하로 침식 불가
        max_erosion = terrain.elevation - terrain.bedrock
        erosion = np.minimum(erosion, np.maximum(max_erosion, 0))
        
        return np.clip(erosion, 0, 5.0)  # 연간 최대 5m


class HillslopeProcess:
    """사면 프로세스 (Mass Wasting)
    
    V자곡 형성의 핵심 - 하방 침식 후 사면 붕괴
    """
    
    def __init__(self, critical_slope: float = 0.7, diffusion_rate: float = 0.01):
        self.critical_slope = critical_slope  # 임계 경사 (tan θ)
        self.diffusion_rate = diffusion_rate  # 확산 계수
    
    def mass_wasting(self, terrain: TerrainGrid, dt: float = 1.0) -> np.ndarray:
        """사면 붕괴 (급경사 → 물질 이동)"""
        h, w = terrain.height, terrain.width
        change = np.zeros((h, w))
        
        elev = terrain.elevation
        slope = terrain.get_slope()
        
        # 임계 경사 초과 지점
        unstable = slope > self.critical_slope
        
        # 불안정 지점에서 이웃으로 물질 분배
        for y in range(1, h-1):
            for x in range(1, w-1):
                if not unstable[y, x]:
                    continue
                
                current = elev[y, x]
                excess = (slope[y, x] - self.critical_slope) * terrain.cell_size
                
                # 8방향 이웃 중 낮은 곳으로 분배
                neighbors = [(y-1,x), (y+1,x), (y,x-1), (y,x+1)]
                lower_neighbors = [(ny, nx) for ny, nx in neighbors 
                                   if elev[ny, nx] < current]
                
                if lower_neighbors:
                    transfer = excess * 0.2 * dt  # 전달량
                    change[y, x] -= transfer
                    per_neighbor = transfer / len(lower_neighbors)
                    for ny, nx in lower_neighbors:
                        change[ny, nx] += per_neighbor
        
        return change
    
    def soil_creep(self, terrain: TerrainGrid, dt: float = 1.0) -> np.ndarray:
        """토양 크리프 (느린 확산)"""
        # 라플라시안 확산
        laplacian = (
            np.roll(terrain.elevation, 1, axis=0) +
            np.roll(terrain.elevation, -1, axis=0) +
            np.roll(terrain.elevation, 1, axis=1) +
            np.roll(terrain.elevation, -1, axis=1) -
            4 * terrain.elevation
        )
        
        return self.diffusion_rate * laplacian * dt


class VValleySimulation:
    """V자곡 시뮬레이션 - 실제 물리 기반
    
    프로세스:
    1. 강수 → 유출 (D8 flow accumulation)
    2. Stream Power Law 침식
    3. 사면 붕괴 (Mass Wasting)
    4. 토양 크리프
    """
    
    def __init__(self, width: int = 100, height: int = 100):
        self.terrain = TerrainGrid(width=width, height=height)
        self.water = WaterFlow(terrain=self.terrain)
        self.erosion = StreamPowerErosion()
        self.hillslope = HillslopeProcess()
        
        self.history: List[np.ndarray] = []
        self.time = 0.0
    
    def initialize_terrain(self, max_elevation: float = 500.0, 
                           initial_channel_depth: float = 10.0,
                           rock_hardness: float = 0.5):
        """초기 지형 설정"""
        h, w = self.terrain.height, self.terrain.width
        
        # 북→남 경사
        for y in range(h):
            base = max_elevation * (1 - y / h)
            self.terrain.elevation[y, :] = base
        
        # 중앙에 초기 하천 채널
        center = w // 2
        for x in range(center - 3, center + 4):
            if 0 <= x < w:
                depth = initial_channel_depth * (1 - abs(x - center) / 4)
                self.terrain.elevation[:, x] -= depth
        
        # 암석 경도
        self.terrain.rock_hardness[:] = rock_hardness
        
        # 기반암
        self.terrain.bedrock[:] = self.terrain.elevation.min() - 200
        
        self.history = [self.terrain.elevation.copy()]
        self.time = 0.0
    
    def step(self, dt: float = 1.0, precipitation: float = 0.001):
        """1 타임스텝 진행"""
        # 1. 수문 계산
        self.water.flow_accumulation_d8(precipitation)
        self.water.calculate_hydraulics()
        
        # 2. Stream Power 침식
        erosion = self.erosion.calculate_erosion(self.terrain, self.water, dt)
        self.terrain.elevation -= erosion
        
        # 3. 사면 붕괴
        wasting = self.hillslope.mass_wasting(self.terrain, dt)
        self.terrain.elevation += wasting
        
        # 4. 토양 크리프
        creep = self.hillslope.soil_creep(self.terrain, dt)
        self.terrain.elevation += creep
        
        self.time += dt
    
    def run(self, total_time: float, save_interval: float = 100.0, dt: float = 1.0):
        """시뮬레이션 실행 및 히스토리 저장"""
        steps = int(total_time / dt)
        save_every = int(save_interval / dt)
        
        for i in range(steps):
            self.step(dt)
            if (i + 1) % save_every == 0:
                self.history.append(self.terrain.elevation.copy())
        
        return self.history
    
    def get_cross_section(self, y_position: int = None) -> Tuple[np.ndarray, np.ndarray]:
        """단면 추출"""
        if y_position is None:
            y_position = self.terrain.height // 2
        
        x = np.arange(self.terrain.width) * self.terrain.cell_size
        z = self.terrain.elevation[y_position, :]
        
        return x, z
    
    def measure_valley_depth(self) -> float:
        """V자곡 깊이 측정"""
        center = self.terrain.width // 2
        y_mid = self.terrain.height // 2
        
        # 중앙과 양쪽 20셀 떨어진 곳의 고도 차이
        left = self.terrain.elevation[y_mid, max(0, center-20)]
        right = self.terrain.elevation[y_mid, min(self.terrain.width-1, center+20)]
        center_elev = self.terrain.elevation[y_mid, center]
        
        return max(0, (left + right) / 2 - center_elev)


# 프리컴퓨팅 함수
def precompute_v_valley(max_time: int = 10000, 
                        rock_hardness: float = 0.5,
                        K: float = 1e-5,
                        precipitation: float = 0.001,
                        save_every: int = 100) -> List[np.ndarray]:
    """V자곡 시뮬레이션 프리컴퓨팅"""
    sim = VValleySimulation(width=100, height=100)
    sim.erosion.K = K
    sim.initialize_terrain(rock_hardness=rock_hardness)
    
    history = sim.run(
        total_time=max_time,
        save_interval=save_every,
        dt=1.0
    )
    
    return history


if __name__ == "__main__":
    print("V자곡 물리 시뮬레이션 테스트")
    print("=" * 50)
    
    sim = VValleySimulation()
    sim.initialize_terrain(rock_hardness=0.3)
    
    print(f"초기 상태: 깊이 = {sim.measure_valley_depth():.1f}m")
    
    for year in [1000, 2000, 5000, 10000]:
        sim.run(1000, save_interval=1000)
        depth = sim.measure_valley_depth()
        print(f"Year {year}: 깊이 = {depth:.1f}m")
    
    print("=" * 50)
    print("테스트 완료!")
