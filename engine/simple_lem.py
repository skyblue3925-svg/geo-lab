"""
🌊 Simple Landscape Evolution Model (LEM)
경량화된 지형 발달 모형 - Stream Power Law + Hillslope Diffusion

물리 법칙:
1. Stream Power Law: E = K × A^m × S^n (하천 침식)
2. Linear Diffusion: ∂z/∂t = D × ∇²z (사면 확산)
"""
import numpy as np
from scipy import ndimage
from typing import Tuple, Optional, List, Dict


class SimpleLEM:
    """
    경량 지형 발달 모형 (Landscape Evolution Model)
    
    Stream Power Law + Hillslope Diffusion 기반
    """
    
    def __init__(
        self,
        grid_size: int = 100,
        cell_size: float = 100.0,  # meters
        K: float = 0.0001,         # 침식계수 (erodibility)
        D: float = 0.01,           # 확산계수 (diffusivity, m²/year)
        U: float = 0.0005,         # 융기율 (uplift rate, m/year)
        m: float = 0.5,            # 유역면적 지수
        n: float = 1.0,            # 경사 지수
        precipitation: float = 1.0  # 강수량 배율
    ):
        """
        Args:
            grid_size: 그리드 크기 (정사각형)
            cell_size: 셀 크기 (미터)
            K: 침식계수 - 높을수록 침식 빠름
            D: 확산계수 - 높을수록 사면 평탄화 빠름
            U: 융기율 - 지각 융기 속도
            m: 유역면적 지수 (보통 0.3-0.6)
            n: 경사 지수 (보통 0.7-1.5)
            precipitation: 강수량 배율
        """
        self.grid_size = grid_size
        self.cell_size = cell_size
        self.K = K
        self.D = D
        self.U = U
        self.m = m
        self.n = n
        self.precipitation = precipitation
        
        # 그리드 초기화
        self.elevation = np.zeros((grid_size, grid_size))
        self.drainage_area = np.ones((grid_size, grid_size))
        self.erosion_rate = np.zeros((grid_size, grid_size))
        
        # 이력 저장
        self.history: List[np.ndarray] = []
        self.time_steps: List[float] = []
        
    def set_initial_topography(self, elevation: np.ndarray):
        """초기 지형 설정"""
        self.elevation = elevation.copy()
        self.grid_size = elevation.shape[0]
        self.drainage_area = np.ones_like(elevation)
        self.erosion_rate = np.zeros_like(elevation)
        
    def create_initial_mountain(self, peak_height: float = 500.0, noise_amp: float = 10.0):
        """초기 산지 지형 생성"""
        y, x = np.mgrid[0:self.grid_size, 0:self.grid_size]
        center = self.grid_size / 2
        
        # 돔 형태 기본 지형
        dist = np.sqrt((y - center)**2 + (x - center)**2)
        self.elevation = peak_height * np.exp(-dist**2 / (2 * (self.grid_size/4)**2))
        
        # 노이즈 추가
        self.elevation += noise_amp * np.random.randn(self.grid_size, self.grid_size)
        
        # 경계 고정 (해수면)
        self._fix_boundaries()
        
    def create_inclined_surface(self, slope: float = 0.01, noise_amp: float = 5.0):
        """경사면 지형 생성 (하천 발달 테스트용)"""
        y, x = np.mgrid[0:self.grid_size, 0:self.grid_size]
        
        # 경사면
        self.elevation = slope * y * self.cell_size
        
        # 노이즈 추가
        self.elevation += noise_amp * np.random.randn(self.grid_size, self.grid_size)
        
        # 경계 고정
        self._fix_boundaries()
        
    def _fix_boundaries(self):
        """경계 조건: 테두리를 해수면(0)으로 고정"""
        self.elevation[0, :] = 0
        self.elevation[-1, :] = 0
        self.elevation[:, 0] = 0
        self.elevation[:, -1] = 0
        
    def calculate_slope(self) -> np.ndarray:
        """
        경사 계산 (Steepest Descent)
        Returns: 경사 배열 (m/m)
        """
        # Sobel 필터로 경사 계산
        dy = ndimage.sobel(self.elevation, axis=0) / (8 * self.cell_size)
        dx = ndimage.sobel(self.elevation, axis=1) / (8 * self.cell_size)
        slope = np.sqrt(dx**2 + dy**2)
        
        # 최소값 방지 (0으로 나누기 방지)
        slope = np.maximum(slope, 1e-6)
        
        return slope
    
    def calculate_drainage_area(self) -> np.ndarray:
        """
        유역면적 계산 (간단한 D8 flow routing 근사)
        Returns: 유역면적 배열 (셀 수)
        """
        # 간단한 근사: 높은 곳에서 낮은 곳으로 물이 흐른다고 가정
        # 실제 D8보다 단순하지만 교육용으로 충분
        
        drainage = np.ones_like(self.elevation)
        
        # 고도 순서대로 정렬
        sorted_indices = np.argsort(self.elevation.ravel())[::-1]
        
        for idx in sorted_indices:
            i, j = divmod(idx, self.grid_size)
            if i == 0 or i == self.grid_size-1 or j == 0 or j == self.grid_size-1:
                continue
                
            # 이웃 중 가장 낮은 곳 찾기
            neighbors = [
                (i-1, j), (i+1, j), (i, j-1), (i, j+1),
                (i-1, j-1), (i-1, j+1), (i+1, j-1), (i+1, j+1)
            ]
            
            min_elev = self.elevation[i, j]
            min_neighbor = None
            
            for ni, nj in neighbors:
                if 0 <= ni < self.grid_size and 0 <= nj < self.grid_size:
                    if self.elevation[ni, nj] < min_elev:
                        min_elev = self.elevation[ni, nj]
                        min_neighbor = (ni, nj)
            
            # 하류로 유역면적 전달
            if min_neighbor is not None:
                drainage[min_neighbor] += drainage[i, j]
        
        self.drainage_area = drainage
        return drainage
    
    def stream_power_erosion(self, dt: float = 1.0) -> np.ndarray:
        """
        Stream Power Law에 의한 침식
        E = K × A^m × S^n
        
        Args:
            dt: 시간 간격 (년)
        Returns: 침식량 배열 (m)
        """
        slope = self.calculate_slope()
        
        # Stream Power Law
        # E = K * (Q^m) * (S^n)
        # Q ≈ A * precipitation (유량 ≈ 유역면적 × 강수량)
        Q = self.drainage_area * self.precipitation * self.cell_size**2
        
        erosion = self.K * (Q ** self.m) * (slope ** self.n) * dt
        
        # 최대 침식량 제한 (숫자 안정성)
        max_erosion = 0.1 * self.elevation.max()
        erosion = np.minimum(erosion, max_erosion)
        
        # 경계는 침식 안 함
        erosion[0, :] = 0
        erosion[-1, :] = 0
        erosion[:, 0] = 0
        erosion[:, -1] = 0
        
        self.erosion_rate = erosion / dt
        return erosion
    
    def hillslope_diffusion(self, dt: float = 1.0) -> np.ndarray:
        """
        Hillslope Diffusion (사면 확산)
        ∂z/∂t = D × ∇²z
        
        Args:
            dt: 시간 간격 (년)
        Returns: 고도 변화량 배열 (m)
        """
        # 라플라시안 계산
        laplacian = ndimage.laplace(self.elevation) / (self.cell_size ** 2)
        
        # 확산
        dz = self.D * laplacian * dt
        
        # 경계 고정
        dz[0, :] = 0
        dz[-1, :] = 0
        dz[:, 0] = 0
        dz[:, -1] = 0
        
        return dz
    
    def step(self, dt: float = 100.0) -> Dict[str, float]:
        """
        한 시간 단계 진행
        
        Args:
            dt: 시간 간격 (년)
        Returns: 통계 딕셔너리
        """
        # 1. 유역면적 계산
        self.calculate_drainage_area()
        
        # 2. 하천 침식 (Stream Power)
        erosion = self.stream_power_erosion(dt)
        
        # 3. 사면 확산 (Diffusion)
        diffusion = self.hillslope_diffusion(dt)
        
        # 4. 지각 융기
        uplift = self.U * dt
        
        # 5. 고도 업데이트
        self.elevation = self.elevation - erosion + diffusion + uplift
        
        # 6. 경계 조건 적용
        self._fix_boundaries()
        
        # 7. 음수 방지
        self.elevation = np.maximum(self.elevation, 0)
        
        # 통계 반환
        return {
            'mean_elevation': float(self.elevation.mean()),
            'max_elevation': float(self.elevation.max()),
            'mean_erosion_rate': float(self.erosion_rate.mean()),
            'max_erosion_rate': float(self.erosion_rate.max()),
            'total_erosion': float(erosion.sum()),
            'total_uplift': float(uplift * self.grid_size**2)
        }
    
    def run(
        self,
        total_time: float = 100000.0,  # 총 시뮬레이션 시간 (년)
        dt: float = 100.0,              # 시간 간격 (년)
        save_interval: int = 100,       # 저장 간격 (스텝 수)
        verbose: bool = True
    ) -> Tuple[List[np.ndarray], List[float]]:
        """
        시뮬레이션 실행
        
        Args:
            total_time: 총 시간 (년)
            dt: 시간 간격 (년)
            save_interval: 저장 간격
            verbose: 진행 상황 출력
            
        Returns:
            (고도 이력, 시간 이력)
        """
        n_steps = int(total_time / dt)
        
        self.history = [self.elevation.copy()]
        self.time_steps = [0.0]
        
        current_time = 0.0
        
        for i in range(n_steps):
            stats = self.step(dt)
            current_time += dt
            
            # 저장
            if (i + 1) % save_interval == 0:
                self.history.append(self.elevation.copy())
                self.time_steps.append(current_time)
                
                if verbose:
                    print(f"[{current_time:,.0f}년] "
                          f"최고 고도: {stats['max_elevation']:.1f}m, "
                          f"평균 침식률: {stats['mean_erosion_rate']:.4f} m/yr")
        
        return self.history, self.time_steps
    
    def get_erosion_map(self) -> np.ndarray:
        """침식률 맵 반환"""
        return self.erosion_rate
    
    def get_drainage_map(self) -> np.ndarray:
        """유역면적 맵 반환 (로그 스케일)"""
        return np.log10(self.drainage_area + 1)


def create_demo_simulation(
    grid_size: int = 100,
    total_time: float = 50000,
    K: float = 0.0001,
    D: float = 0.01,
    U: float = 0.0005
) -> Tuple[List[np.ndarray], List[float], SimpleLEM]:
    """
    데모 시뮬레이션 실행
    
    Returns:
        (고도 이력, 시간 이력, LEM 객체)
    """
    lem = SimpleLEM(
        grid_size=grid_size,
        K=K, D=D, U=U
    )
    
    # 초기 산지 생성
    lem.create_initial_mountain(peak_height=300.0, noise_amp=5.0)
    
    # 시뮬레이션 실행
    history, times = lem.run(
        total_time=total_time,
        dt=100.0,
        save_interval=50,
        verbose=False
    )
    
    return history, times, lem
