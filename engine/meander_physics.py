"""
Geo-Lab AI: 곡류 하천 물리 시뮬레이션
Helical Flow 기반 측방 침식/퇴적
"""
import numpy as np
from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class MeanderChannel:
    """곡류 하천 채널 표현
    
    1D 중심선 기반으로 채널을 표현하고,
    각 지점에서의 곡률, 폭, 깊이를 추적
    """
    
    # 채널 중심선 좌표
    x: np.ndarray = field(default=None)
    y: np.ndarray = field(default=None)
    
    # 각 지점의 속성
    width: np.ndarray = field(default=None)   # 채널 폭 (m)
    depth: np.ndarray = field(default=None)   # 채널 깊이 (m)
    
    # 유량 및 유속
    discharge: float = 100.0  # m³/s
    velocity: np.ndarray = field(default=None)  # m/s
    
    def __post_init__(self):
        if self.x is not None and self.width is None:
            n = len(self.x)
            self.width = np.full(n, 20.0)
            self.depth = np.full(n, 3.0)
            self.velocity = np.full(n, 1.5)
    
    @classmethod
    def create_initial(cls, length: float = 1000.0, 
                       initial_sinuosity: float = 1.2,
                       n_points: int = 200,
                       discharge: float = 100.0):
        """초기 곡류 하천 생성"""
        s = np.linspace(0, 1, n_points)  # 정규화된 거리
        
        # 사인파 기반 초기 곡류
        amplitude = length * 0.1 * (initial_sinuosity - 1)
        frequency = 3  # 굽이 수
        
        x = s * length
        y = amplitude * np.sin(2 * np.pi * frequency * s)
        
        return cls(x=x, y=y, discharge=discharge)
    
    def calculate_curvature(self) -> np.ndarray:
        """곡률 계산 (1/m)
        κ = (x'y'' - y'x'') / (x'^2 + y'^2)^(3/2)
        """
        dx = np.gradient(self.x)
        dy = np.gradient(self.y)
        ddx = np.gradient(dx)
        ddy = np.gradient(dy)
        
        denominator = np.power(dx**2 + dy**2, 1.5) + 1e-10
        curvature = (dx * ddy - dy * ddx) / denominator
        
        return curvature
    
    def calculate_sinuosity(self) -> float:
        """굴곡도 = 하천 길이 / 직선 거리"""
        # 경로 길이
        ds = np.sqrt(np.diff(self.x)**2 + np.diff(self.y)**2)
        path_length = np.sum(ds)
        
        # 직선 거리
        straight_length = np.sqrt(
            (self.x[-1] - self.x[0])**2 + 
            (self.y[-1] - self.y[0])**2
        ) + 1e-10
        
        return path_length / straight_length


class HelicalFlowErosion:
    """Helical Flow 기반 곡류 침식/퇴적
    
    곡류에서 물은 나선형(helical)으로 흐름:
    - 표면: 바깥쪽으로 (원심력)
    - 바닥: 안쪽으로 (압력 구배)
    
    결과:
    - 바깥쪽 (공격사면): 침식
    - 안쪽 (퇴적사면): 퇴적
    """
    
    def __init__(self, 
                 bank_erosion_rate: float = 0.5,  # m/yr per unit stress
                 deposition_rate: float = 0.3):
        self.bank_erosion_rate = bank_erosion_rate
        self.deposition_rate = deposition_rate
    
    def calculate_bank_migration(self, channel: MeanderChannel, 
                                  dt: float = 1.0) -> Tuple[np.ndarray, np.ndarray]:
        """하안 이동 계산
        
        곡률이 큰 곳에서 바깥쪽으로 침식 → 채널 이동
        """
        curvature = channel.calculate_curvature()
        
        # 침식/퇴적 비대칭
        # 곡률 > 0: 좌측이 바깥 (침식)
        # 곡률 < 0: 우측이 바깥 (침식)
        
        # 이동 벡터 (채널에 수직)
        dx = np.gradient(channel.x)
        dy = np.gradient(channel.y)
        path_length = np.sqrt(dx**2 + dy**2) + 1e-10
        
        # 수직 방향 (왼쪽으로 90도 회전)
        normal_x = -dy / path_length
        normal_y = dx / path_length
        
        # 이동량 = 곡률 × 유량 × erosion rate
        migration_rate = curvature * channel.discharge * self.bank_erosion_rate * dt
        
        # 이동량 제한
        migration_rate = np.clip(migration_rate, -2.0, 2.0)
        
        delta_x = migration_rate * normal_x
        delta_y = migration_rate * normal_y
        
        return delta_x, delta_y
    
    def check_cutoff(self, channel: MeanderChannel, 
                     threshold_distance: float = 30.0) -> List[Tuple[int, int]]:
        """우각호 형성 조건 체크 (유로 절단)"""
        n = len(channel.x)
        cutoffs = []
        
        # 가까운 두 점 찾기 (경로상 멀리 떨어졌지만 공간적으로 가까운)
        for i in range(n):
            for j in range(i + 30, n):  # 최소 30점 간격
                dist = np.sqrt(
                    (channel.x[i] - channel.x[j])**2 +
                    (channel.y[i] - channel.y[j])**2
                )
                
                if dist < threshold_distance:
                    cutoffs.append((i, j))
                    break  # 첫 번째 cutoff만
        
        return cutoffs


class MeanderSimulation:
    """곡류 하천 시뮬레이션"""
    
    def __init__(self, length: float = 1000.0, initial_sinuosity: float = 1.3):
        self.channel = MeanderChannel.create_initial(
            length=length,
            initial_sinuosity=initial_sinuosity
        )
        self.erosion = HelicalFlowErosion()
        
        self.history: List[Tuple[np.ndarray, np.ndarray]] = []
        self.oxbow_lakes: List[Tuple[np.ndarray, np.ndarray]] = []
        self.time = 0.0
    
    def step(self, dt: float = 1.0):
        """1 타임스텝"""
        # 1. 하안 이동
        dx, dy = self.erosion.calculate_bank_migration(self.channel, dt)
        self.channel.x += dx
        self.channel.y += dy
        
        # 2. 우각호 체크
        cutoffs = self.erosion.check_cutoff(self.channel)
        for start, end in cutoffs:
            # 우각호 저장
            ox = self.channel.x[start:end+1].copy()
            oy = self.channel.y[start:end+1].copy()
            self.oxbow_lakes.append((ox, oy))
            
            # 채널 단축
            self.channel.x = np.concatenate([
                self.channel.x[:start+1],
                self.channel.x[end:]
            ])
            self.channel.y = np.concatenate([
                self.channel.y[:start+1],
                self.channel.y[end:]
            ])
            
            # 속성 배열도 조정
            n_new = len(self.channel.x)
            self.channel.width = np.full(n_new, 20.0)
            self.channel.depth = np.full(n_new, 3.0)
            self.channel.velocity = np.full(n_new, 1.5)
        
        self.time += dt
    
    def run(self, total_time: float, save_interval: float = 100.0, dt: float = 1.0):
        """시뮬레이션 실행"""
        steps = int(total_time / dt)
        save_every = max(1, int(save_interval / dt))
        
        self.history = [(self.channel.x.copy(), self.channel.y.copy())]
        
        for i in range(steps):
            self.step(dt)
            if (i + 1) % save_every == 0:
                self.history.append((self.channel.x.copy(), self.channel.y.copy()))
        
        return self.history
    
    def get_cross_section(self, position: float = 0.5) -> Tuple[np.ndarray, np.ndarray]:
        """곡류 단면 (비대칭)
        
        position: 곡류 내 위치 (0=직선부, 1=최대 굽이)
        """
        curvature = self.channel.calculate_curvature()
        max_curve = np.abs(curvature).max() + 1e-10
        asymmetry = np.abs(curvature[int(len(curvature) * 0.5)]) / max_curve
        asymmetry = min(1.0, asymmetry * position * 2)
        
        # 단면 생성
        x = np.linspace(-30, 30, 100)
        
        # 비대칭 곡선
        left_depth = 5 + asymmetry * 3  # 공격사면 (깊음)
        right_depth = 3 - asymmetry * 1  # 퇴적사면 (얕음)
        
        y = np.where(
            x < 0,
            -left_depth * (1 - np.power(x / -30, 2)),
            -right_depth * (1 - np.power(x / 30, 2))
        )
        
        return x, y


# 프리컴퓨팅
def precompute_meander(max_time: int = 10000,
                       initial_sinuosity: float = 1.3,
                       save_every: int = 100) -> dict:
    """곡류 시뮬레이션 프리컴퓨팅"""
    sim = MeanderSimulation(initial_sinuosity=initial_sinuosity)
    
    history = sim.run(
        total_time=max_time,
        save_interval=save_every,
        dt=1.0
    )
    
    return {
        'history': history,
        'oxbow_lakes': sim.oxbow_lakes,
        'final_sinuosity': sim.channel.calculate_sinuosity()
    }


if __name__ == "__main__":
    print("곡류 하천 물리 시뮬레이션 테스트")
    print("=" * 50)
    
    sim = MeanderSimulation(initial_sinuosity=1.3)
    print(f"초기 굴곡도: {sim.channel.calculate_sinuosity():.2f}")
    
    sim.run(5000, save_interval=1000)
    print(f"5000년 후 굴곡도: {sim.channel.calculate_sinuosity():.2f}")
    print(f"형성된 우각호: {len(sim.oxbow_lakes)}개")
    
    print("=" * 50)
    print("테스트 완료!")
