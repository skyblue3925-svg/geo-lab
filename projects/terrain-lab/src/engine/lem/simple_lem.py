"""
🌊 Simple Landscape Evolution Model (LEM)
경량화된 지형 발달 모형 - Stream Power Law + Hillslope Diffusion + Weathering

물리 법칙:
1. Stream Power Law: E = K × A^m × S^n (하천 침식)
2. Linear Diffusion: ∂z/∂t = D × ∇²z (사면 확산)
3. Exponential Weathering: W = W0 × exp(-H/H*) (지수적 풍화)

확장 모듈:
- ClimateSystem: 강우 이벤트, 기후 변화, 해수면 변동
- HumanActivity: 댐 건설, 삼림 벌채
- LEMVisualizer: 실시간 그래프, A/B 비교
"""
import numpy as np
from scipy import ndimage
from typing import Tuple, Optional, List, Dict

# 확장 모듈 (선택적 import)
try:
    from engine.lem.climate import ClimateSystem, ClimateState
    from engine.lem.human import HumanActivity
    from engine.lem.visualization import LEMVisualizer
    EXTENSIONS_AVAILABLE = True
except ImportError:
    EXTENSIONS_AVAILABLE = False



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
        precipitation: float = 1.0, # 강수량 배율
        # 풍화 파라미터
        W0: float = 0.001,         # 최대 풍화율 (m/year)
        H_star: float = 1.0,       # 특성 토양 깊이 (m)
        enable_weathering: bool = True,  # 풍화 활성화 여부
        # 퇴적물 운반 파라미터
        Vs: float = 1.0,           # 퇴적 속도 (settling velocity, m/year)
        enable_sediment_transport: bool = True,  # 퇴적물 운반 활성화
        # 측방 침식 파라미터
        Kl: float = 0.00001,       # 측방 침식계수 (lateral erosion coefficient)
        enable_lateral_erosion: bool = False,  # 측방 침식 활성화 (곡류 형성)
        # 빙하 침식 파라미터
        Kg: float = 0.0001,        # 빙하 침식계수
        glacier_ela: float = 200.0, # 평형선 고도 (ELA, m)
        enable_glacial: bool = False,  # 빙하 침식 활성화
        # 해안 침식 파라미터
        Km: float = 0.001,         # 해안 침식계수
        sea_level: float = 0.0,    # 해수면 고도 (m)
        enable_marine: bool = False,  # 해안 침식 활성화
        # 산사태 파라미터
        critical_slope: float = 0.6, # 임계 경사 (rad)
        enable_landslides: bool = False,  # 산사태 활성화
        # 단층 파라미터
        fault_rate: float = 0.001,  # 단층 변위율 (m/year)
        fault_position: float = 0.5, # 단층 위치 (0-1)
        enable_faulting: bool = False,  # 단층 활성화
        # 카르스트 파라미터
        Kk: float = 0.0001,        # 용해율
        enable_karst: bool = False,  # 카르스트 용해 활성화
        # 바람 침식 파라미터 (사막 사구)
        Ka: float = 0.0001,        # 바람 침식계수
        wind_direction: float = 0.0, # 풍향 (라디안)
        enable_aeolian: bool = False,  # 바람 침식 활성화
        # 화산 파라미터
        volcanic_rate: float = 0.01,  # 분출량 (m/year)
        volcanic_position: tuple = (0.5, 0.5),  # 화구 위치
        enable_volcanic: bool = False,  # 화산 활성화
        # 지하수 파라미터
        water_table: float = 50.0,  # 지하수면 고도 (m)
        spring_rate: float = 0.001,  # 용천 침식률
        enable_groundwater: bool = False,  # 지하수 활성화
        # 동결파쇄 파라미터
        Kf: float = 0.0005,        # 동결파쇄 계수
        freeze_elevation: float = 300.0, # 동결 고도 (m)
        enable_freeze_thaw: bool = False,  # 동결파쇄 활성화
        # 생물 침식 파라미터
        vegetation_factor: float = 0.5,  # 식생 보호 계수 (0-1)
        enable_bioerosion: bool = False,  # 생물 침식 활성화
        # 호수 파라미터
        lake_threshold: float = 0.001,  # 호수 형성 임계값
        enable_lake: bool = False,  # 호수 형성 활성화
        # 빙하 퇴적 파라미터
        moraine_rate: float = 0.3,  # 모레인 퇴적률
        enable_glacial_deposit: bool = False,  # 빙하 퇴적 활성화
        # === Landlab 추가 기능 ===
        # Overland Flow (지표수 흐름)
        manning_n: float = 0.03,  # Manning 조도계수
        enable_overland_flow: bool = False,
        # Cellular Automata (사면 붕괴)
        ca_threshold: float = 0.5,  # 임계 경사비
        enable_cellular_automata: bool = False,
        # Flexure (지각 등압 조절)
        flexural_rigidity: float = 1e23,  # 등가 탄성 두께
        enable_flexure: bool = False,
        # Chi Analysis (하천 분석)
        chi_concavity: float = 0.45,  # 하천 오목도
        enable_chi_analysis: bool = False,
        # Landslide Probability (산사태 확률)
        cohesion: float = 10000.0,  # 점착력 (Pa)
        friction_angle: float = 30.0,  # 내부마찰각 (도)
        enable_landslide_prob: bool = False
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
            W0: 최대 풍화율 - 토양이 없을 때 기반암 풍화 속도
            H_star: 특성 토양 깊이 - 풍화가 e^-1로 감소하는 깊이
            enable_weathering: 풍화 과정 활성화 여부
            Vs: 퇴적 속도 - 높을수록 퇴적물이 빨리 가라앉음
            enable_sediment_transport: 퇴적물 운반/퇴적 과정 활성화
        """
        self.grid_size = grid_size
        self.cell_size = cell_size
        self.K = K
        self.D = D
        self.U = U
        self.m = m
        self.n = n
        self.precipitation = precipitation
        
        # 풍화 파라미터
        self.W0 = W0
        self.H_star = H_star
        self.enable_weathering = enable_weathering
        
        # 퇴적물 운반 파라미터
        self.Vs = Vs
        self.enable_sediment_transport = enable_sediment_transport
        
        # 측방 침식 파라미터
        self.Kl = Kl
        self.enable_lateral_erosion = enable_lateral_erosion
        
        # 빙하 침식 파라미터
        self.Kg = Kg
        self.glacier_ela = glacier_ela
        self.enable_glacial = enable_glacial
        
        # 해안 침식 파라미터
        self.Km = Km
        self.sea_level = sea_level
        self.enable_marine = enable_marine
        
        # 산사태 파라미터
        self.critical_slope = critical_slope
        self.enable_landslides = enable_landslides
        
        # 단층 파라미터
        self.fault_rate = fault_rate
        self.fault_position = fault_position
        self.enable_faulting = enable_faulting
        
        # 카르스트 파라미터
        self.Kk = Kk
        self.enable_karst = enable_karst
        
        # 바람 침식 파라미터
        self.Ka = Ka
        self.wind_direction = wind_direction
        self.enable_aeolian = enable_aeolian
        
        # 화산 파라미터
        self.volcanic_rate = volcanic_rate
        self.volcanic_position = volcanic_position
        self.enable_volcanic = enable_volcanic
        
        # 지하수 파라미터
        self.water_table = water_table
        self.spring_rate = spring_rate
        self.enable_groundwater = enable_groundwater
        
        # 동결파쇄 파라미터
        self.Kf = Kf
        self.freeze_elevation = freeze_elevation
        self.enable_freeze_thaw = enable_freeze_thaw
        
        # 생물 침식 파라미터
        self.vegetation_factor = vegetation_factor
        self.enable_bioerosion = enable_bioerosion
        
        # 호수 파라미터
        self.lake_threshold = lake_threshold
        self.enable_lake = enable_lake
        self.lake_depth = np.zeros((grid_size, grid_size))  # 호수 수심
        
        # 빙하 퇴적 파라미터
        self.moraine_rate = moraine_rate
        self.enable_glacial_deposit = enable_glacial_deposit
        
        # === Landlab 추가 기능 ===
        # Overland Flow
        self.manning_n = manning_n
        self.enable_overland_flow = enable_overland_flow
        self.flow_velocity = np.zeros((grid_size, grid_size))
        
        # Cellular Automata
        self.ca_threshold = ca_threshold
        self.enable_cellular_automata = enable_cellular_automata
        
        # Flexure
        self.flexural_rigidity = flexural_rigidity
        self.enable_flexure = enable_flexure
        self.flexural_deflection = np.zeros((grid_size, grid_size))
        
        # Chi Analysis
        self.chi_concavity = chi_concavity
        self.enable_chi_analysis = enable_chi_analysis
        self.chi_index = np.zeros((grid_size, grid_size))
        
        # Landslide Probability
        self.cohesion = cohesion
        self.friction_angle = friction_angle
        self.enable_landslide_prob = enable_landslide_prob
        self.factor_of_safety = np.ones((grid_size, grid_size))
        
        # 그리드 초기화
        self.elevation = np.zeros((grid_size, grid_size))  # 전체 고도 (기반암 + 토양)
        self.bedrock = np.zeros((grid_size, grid_size))    # 기반암 고도
        self.soil_depth = np.zeros((grid_size, grid_size)) # 토양(레골리스) 두께
        self.sediment_flux = np.zeros((grid_size, grid_size))  # 퇴적물 플럭스
        self.deposition_rate = np.zeros((grid_size, grid_size)) # 퇴적률
        self.lateral_erosion_rate = np.zeros((grid_size, grid_size))  # 측방 침식률
        self.glacial_erosion_rate = np.zeros((grid_size, grid_size))  # 빙하 침식률
        self.marine_erosion_rate = np.zeros((grid_size, grid_size))   # 해안 침식률
        self.landslide_rate = np.zeros((grid_size, grid_size))        # 산사태율
        self.aeolian_rate = np.zeros((grid_size, grid_size))          # 바람 침식률
        self.freeze_thaw_rate = np.zeros((grid_size, grid_size))      # 동결파쇄율
        self.drainage_area = np.ones((grid_size, grid_size))
        self.erosion_rate = np.zeros((grid_size, grid_size))
        self.weathering_rate = np.zeros((grid_size, grid_size))
        
        # 이력 저장
        self.history: List[np.ndarray] = []
        self.time_steps: List[float] = []
        
    def set_initial_topography(self, elevation: np.ndarray, initial_soil: float = 0.5):
        """초기 지형 설정
        
        Args:
            elevation: 초기 고도 배열
            initial_soil: 초기 토양 두께 (m)
        """
        self.elevation = elevation.copy()
        self.grid_size = elevation.shape[0]
        self.soil_depth = np.full_like(elevation, initial_soil)
        self.bedrock = self.elevation - self.soil_depth
        self.drainage_area = np.ones_like(elevation)
        self.erosion_rate = np.zeros_like(elevation)
        self.weathering_rate = np.zeros_like(elevation)
        
    def create_initial_mountain(self, peak_height: float = 500.0, noise_amp: float = 10.0, initial_soil: float = 0.5):
        """초기 산지 지형 생성
        
        Args:
            peak_height: 봉우리 높이 (m)
            noise_amp: 노이즈 진폭 (m)
            initial_soil: 초기 토양 두께 (m)
        """
        y, x = np.mgrid[0:self.grid_size, 0:self.grid_size]
        center = self.grid_size / 2
        
        # 돔 형태 기본 지형
        dist = np.sqrt((y - center)**2 + (x - center)**2)
        self.elevation = peak_height * np.exp(-dist**2 / (2 * (self.grid_size/4)**2))
        
        # 노이즈 추가
        self.elevation += noise_amp * np.random.randn(self.grid_size, self.grid_size)
        
        # 토양층 초기화
        self.soil_depth = np.full((self.grid_size, self.grid_size), initial_soil)
        self.bedrock = self.elevation - self.soil_depth
        
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
    
    def exponential_weathering(self, dt: float = 1.0) -> np.ndarray:
        """
        Exponential Weathering (지수적 풍화)
        W = W0 × exp(-H/H*)
        
        기반암이 토양으로 변환되는 과정.
        토양이 두꺼울수록 풍화가 느려진다.
        
        Args:
            dt: 시간 간격 (년)
        Returns: 풍화량 배열 (m) - 기반암에서 토양으로 변환된 두께
        """
        if not self.enable_weathering:
            return np.zeros_like(self.elevation)
        
        # 지수적 풍화: W = W0 * exp(-H/H*)
        # H: 토양 두께, H*: 특성 깊이
        weathering = self.W0 * np.exp(-self.soil_depth / self.H_star) * dt
        
        # 기반암보다 더 많이 풍화할 수 없음
        weathering = np.minimum(weathering, np.maximum(self.bedrock, 0))
        
        # 경계 고정
        weathering[0, :] = 0
        weathering[-1, :] = 0
        weathering[:, 0] = 0
        weathering[:, -1] = 0
        
        self.weathering_rate = weathering / dt
        return weathering
    
    def sediment_transport(self, erosion: np.ndarray, dt: float = 1.0) -> np.ndarray:
        """
        Sediment Transport (퇴적물 운반 및 퇴적)
        
        침식된 토양이 하류로 운반되고, 경사가 완만한 곳에서 퇴적된다.
        Davy & Lague (2009) 간소화 모델 기반
        
        Args:
            erosion: 현재 스텝의 침식량 (m)
            dt: 시간 간격 (년)
        Returns: 퇴적량 배열 (m)
        """
        if not self.enable_sediment_transport:
            return np.zeros_like(self.elevation)
        
        slope = self.calculate_slope()
        
        # 운반 용량: Tc = k * Q * S (유량 × 경사에 비례)
        Q = self.drainage_area * self.precipitation * self.cell_size**2
        transport_capacity = self.K * (Q ** self.m) * (slope ** self.n)
        
        # 퇴적물 플럭스 계산 (간단한 근사)
        # 침식된 물질이 하류 방향으로 누적
        sediment = np.zeros_like(self.elevation)
        
        # 고도 순서대로 정렬 (높은 곳부터)
        sorted_indices = np.argsort(self.elevation.ravel())[::-1]
        
        for idx in sorted_indices:
            i, j = divmod(idx, self.grid_size)
            if i == 0 or i == self.grid_size-1 or j == 0 or j == self.grid_size-1:
                continue
            
            # 현재 셀의 침식량 + 상류에서 온 퇴적물
            local_sediment = erosion[i, j] + sediment[i, j]
            
            # 운반 용량과 비교
            if local_sediment > transport_capacity[i, j] * dt:
                # 운반 용량 초과 → 퇴적
                deposition = (local_sediment - transport_capacity[i, j] * dt)
                local_sediment -= deposition
            else:
                deposition = 0
            
            # 가장 낮은 이웃에 퇴적물 전달
            neighbors = [
                (i-1, j), (i+1, j), (i, j-1), (i, j+1)
            ]
            
            min_elev = self.elevation[i, j]
            min_neighbor = None
            
            for ni, nj in neighbors:
                if 0 <= ni < self.grid_size and 0 <= nj < self.grid_size:
                    if self.elevation[ni, nj] < min_elev:
                        min_elev = self.elevation[ni, nj]
                        min_neighbor = (ni, nj)
            
            # 하류로 퇴적물 전달
            if min_neighbor is not None:
                sediment[min_neighbor] += local_sediment
        
        # 경계에서 퇴적물 제거 (바다로 유출)
        sediment[0, :] = 0
        sediment[-1, :] = 0
        sediment[:, 0] = 0
        sediment[:, -1] = 0
        
        # 퇴적률 계산: 경사가 완만할수록 퇴적 증가
        deposition = self.Vs * sediment * np.exp(-slope * 10) * dt
        deposition = np.minimum(deposition, sediment)  # 퇴적물보다 더 많이 퇴적 불가
        
        self.sediment_flux = sediment
        self.deposition_rate = deposition / dt
        
        return deposition
    
    def lateral_erosion(self, dt: float = 1.0) -> np.ndarray:
        """
        Lateral Erosion (측방 침식)
        
        하천이 옆으로 침식하여 골짜기를 넓힌다.
        유역면적이 크고 고도 차이가 큰 곳에서 측방 침식이 활발.
        
        Args:
            dt: 시간 간격 (년)
        Returns: 측방 침식량 배열 (m)
        """
        if not self.enable_lateral_erosion:
            return np.zeros_like(self.elevation)
        
        lateral = np.zeros_like(self.elevation)
        
        # 하천 위치 식별 (유역면적이 큰 곳)
        threshold = np.percentile(self.drainage_area, 90)  # 상위 10%
        
        for i in range(1, self.grid_size-1):
            for j in range(1, self.grid_size-1):
                if self.drainage_area[i, j] < threshold:
                    continue
                
                # 이웃과의 고도 차이 계산
                neighbors = [(i-1, j), (i+1, j), (i, j-1), (i, j+1)]
                
                for ni, nj in neighbors:
                    elev_diff = self.elevation[ni, nj] - self.elevation[i, j]
                    
                    # 하천보다 높은 이웃에서 측방 침식
                    if elev_diff > 0:
                        # 측방 침식량: Kl * Q * 고도차이
                        Q = self.drainage_area[i, j] * self.precipitation * self.cell_size**2
                        erosion = self.Kl * (Q ** 0.5) * elev_diff * dt
                        
                        # 침식량 제한
                        erosion = min(erosion, elev_diff * 0.1)  # 고도차의 10%까지만
                        
                        lateral[ni, nj] += erosion
        
        # 경계 고정
        lateral[0, :] = 0
        lateral[-1, :] = 0
        lateral[:, 0] = 0
        lateral[:, -1] = 0
        
        self.lateral_erosion_rate = lateral / dt
        return lateral
    
    def glacial_erosion(self, dt: float = 1.0) -> np.ndarray:
        """
        Glacial Erosion (빙하 침식) - U자곡 형성
        ELA(평형선 고도) 이상에서 빙하가 형성되어 침식
        """
        if not self.enable_glacial:
            return np.zeros_like(self.elevation)
        
        glacial = np.zeros_like(self.elevation)
        
        # ELA 이상 지역에서 빙하 침식
        ice_mask = self.elevation > self.glacier_ela
        
        # 빙하 두께 근사 (고도에 비례)
        ice_thickness = np.maximum(0, self.elevation - self.glacier_ela)
        
        # 빙하 침식: E = Kg * H * S (두께 × 경사)
        slope = self.calculate_slope()
        glacial = self.Kg * ice_thickness * slope * dt * ice_mask
        
        # U자곡 효과: 측면도 침식
        from scipy import ndimage
        glacial += ndimage.uniform_filter(glacial, size=3) * 0.3
        
        self._fix_boundary_erosion(glacial)
        self.glacial_erosion_rate = glacial / dt
        return glacial
    
    def marine_erosion(self, dt: float = 1.0) -> np.ndarray:
        """
        Marine Erosion (해안 침식) - 해식애, 파식대 형성
        해수면 부근에서 파도에 의한 침식
        """
        if not self.enable_marine:
            return np.zeros_like(self.elevation)
        
        marine = np.zeros_like(self.elevation)
        
        # 해수면 부근 지역 (±10m)
        coastal_mask = np.abs(self.elevation - self.sea_level) < 10.0
        
        # 침식량: 노출된 경사면에서 강함
        slope = self.calculate_slope()
        marine = self.Km * slope * dt * coastal_mask
        
        self._fix_boundary_erosion(marine)
        self.marine_erosion_rate = marine / dt
        return marine
    
    def landslide_process(self, dt: float = 1.0) -> np.ndarray:
        """
        Landslides (산사태) - 급경사면 붕괴
        임계 경사 초과 시 토양이 하류로 이동
        """
        if not self.enable_landslides:
            return np.zeros_like(self.elevation)
        
        landslide = np.zeros_like(self.elevation)
        slope = self.calculate_slope()
        
        # 임계 경사 초과 지역
        failure_mask = slope > self.critical_slope
        
        # 붕괴량: 초과 경사에 비례
        excess_slope = np.maximum(0, slope - self.critical_slope)
        landslide = excess_slope * self.soil_depth * failure_mask * 0.1  # 토양의 10%
        
        self._fix_boundary_erosion(landslide)
        self.landslide_rate = landslide / dt
        return landslide
    
    def tectonic_faulting(self, dt: float = 1.0) -> np.ndarray:
        """
        Tectonic Faulting (단층 운동) - 단층 변위
        단층선을 기준으로 한쪽이 융기
        """
        if not self.enable_faulting:
            return np.zeros_like(self.elevation)
        
        fault_movement = np.zeros_like(self.elevation)
        
        # 단층선 위치 계산
        fault_line_idx = int(self.fault_position * self.grid_size)
        
        # 단층 한쪽만 융기 (footwall)
        fault_movement[:, fault_line_idx:] = self.fault_rate * dt
        
        return fault_movement
    
    def karst_dissolution(self, dt: float = 1.0) -> np.ndarray:
        """
        Karst Dissolution (카르스트 용해) - 석회암 지형
        지하수에 의한 용해, 돌리네/우발레 형성
        """
        if not self.enable_karst:
            return np.zeros_like(self.elevation)
        
        dissolution = np.zeros_like(self.elevation)
        
        # 용해량: 배수면적에 비례 (물이 모이는 곳)
        dissolution = self.Kk * np.log10(self.drainage_area + 1) * dt
        
        # 무작위 싱크홀 효과
        sinkhole_chance = 0.001
        sinkholes = np.random.random(self.elevation.shape) < sinkhole_chance
        dissolution += sinkholes * 0.5 * dt  # 급격한 함몰
        
        self._fix_boundary_erosion(dissolution)
        return dissolution
    
    def _fix_boundary_erosion(self, erosion_array: np.ndarray):
        """경계 침식량 0으로 설정"""
        erosion_array[0, :] = 0
        erosion_array[-1, :] = 0
        erosion_array[:, 0] = 0
        erosion_array[:, -1] = 0
    
    def aeolian_erosion(self, dt: float = 1.0) -> np.ndarray:
        """
        Aeolian Erosion (바람 침식) - 사막 사구 형성
        바람에 의한 모래 이동 및 사구 형성
        """
        if not self.enable_aeolian:
            return np.zeros_like(self.elevation)
        
        aeolian = np.zeros_like(self.elevation)
        
        # 풍향에 따른 침식/퇴적 패턴
        # 바람이 부는 쪽(windward) 침식, 반대쪽(leeward) 퇴적
        dx = int(np.cos(self.wind_direction) * 2)
        dy = int(np.sin(self.wind_direction) * 2)
        
        for i in range(2, self.grid_size-2):
            for j in range(2, self.grid_size-2):
                # 풍상측 침식
                aeolian[i, j] = self.Ka * self.soil_depth[i, j] * dt
                
                # 풍하측 퇴적 (이동된 물질)
                ni, nj = i + dy, j + dx
                if 0 < ni < self.grid_size-1 and 0 < nj < self.grid_size-1:
                    aeolian[ni, nj] -= self.Ka * self.soil_depth[i, j] * dt * 0.8
        
        self._fix_boundary_erosion(aeolian)
        self.aeolian_rate = np.abs(aeolian) / dt
        return aeolian
    
    def volcanic_activity(self, dt: float = 1.0) -> np.ndarray:
        """
        Volcanic Activity (화산 활동) - 용암류, 화산체 형성
        화구에서 물질 분출 및 사면 흘러내림
        """
        if not self.enable_volcanic:
            return np.zeros_like(self.elevation)
        
        volcanic = np.zeros_like(self.elevation)
        
        # 화구 위치
        ci = int(self.volcanic_position[0] * self.grid_size)
        cj = int(self.volcanic_position[1] * self.grid_size)
        
        # 화구 주변 융기 (원추형)
        y, x = np.mgrid[0:self.grid_size, 0:self.grid_size]
        dist = np.sqrt((y - ci)**2 + (x - cj)**2)
        
        # 분출물 분포 (거리에 반비례)
        volcanic = self.volcanic_rate * np.exp(-dist / (self.grid_size * 0.1)) * dt
        
        self._fix_boundary_erosion(volcanic)
        return volcanic
    
    def groundwater_erosion(self, dt: float = 1.0) -> np.ndarray:
        """
        Groundwater Erosion (지하수 침식) - 용천, 파이핑
        지하수면 부근에서 침식 증가
        """
        if not self.enable_groundwater:
            return np.zeros_like(self.elevation)
        
        gw_erosion = np.zeros_like(self.elevation)
        
        # 지하수면 부근 (±5m) 침식 증가
        near_water_table = np.abs(self.elevation - self.water_table) < 5.0
        
        gw_erosion = self.spring_rate * near_water_table * dt
        
        self._fix_boundary_erosion(gw_erosion)
        return gw_erosion
    
    def freeze_thaw_weathering(self, dt: float = 1.0) -> np.ndarray:
        """
        Freeze-thaw Weathering (동결파쇄) - 고산 풍화
        동결 고도 이상에서 암석 파쇄
        """
        if not self.enable_freeze_thaw:
            return np.zeros_like(self.elevation)
        
        freeze = np.zeros_like(self.elevation)
        
        # 동결 고도 이상
        above_freeze = self.elevation > self.freeze_elevation
        
        # 동결파쇄: 고도가 높을수록 강함
        excess_elev = np.maximum(0, self.elevation - self.freeze_elevation)
        freeze = self.Kf * excess_elev * above_freeze * dt
        
        self._fix_boundary_erosion(freeze)
        self.freeze_thaw_rate = freeze / dt
        return freeze
    
    def apply_vegetation_protection(self, erosion: np.ndarray) -> np.ndarray:
        """
        Bioerosion/Vegetation (식생 보호) - 침식 감소
        식생이 있는 곳에서 침식률 감소
        """
        if not self.enable_bioerosion:
            return erosion
        
        # 식생 밀도: 중간 고도에서 최대 (0-300m 선형 증가, 300m 이상 감소)
        veg_density = np.clip(1 - np.abs(self.elevation - 150) / 300, 0.1, 1.0)
        
        # 식생 보호 효과
        protection = 1 - (self.vegetation_factor * veg_density)
        
        return erosion * protection
    
    def lake_formation(self, dt: float = 1.0) -> np.ndarray:
        """
        Lake Formation (호수 형성) - 저지대 침수
        배수가 막힌 저지대에 물이 고임
        """
        if not self.enable_lake:
            return np.zeros_like(self.elevation)
        
        # 주변보다 낮은 지역 찾기 (sink)
        from scipy import ndimage
        local_min = ndimage.minimum_filter(self.elevation, size=5)
        is_sink = (self.elevation == local_min) & (self.drainage_area > 10)
        
        # 호수 수심 업데이트
        self.lake_depth += is_sink * self.lake_threshold * self.precipitation * dt
        self.lake_depth = np.minimum(self.lake_depth, 50)  # 최대 50m
        
        # 호수 침식 (해안선 침식과 유사)
        lake_erosion = np.zeros_like(self.elevation)
        lake_edge = (self.lake_depth > 0) & (self.lake_depth < 5)
        lake_erosion = lake_edge * 0.0001 * dt
        
        self._fix_boundary_erosion(lake_erosion)
        return lake_erosion
    
    def glacial_deposition(self, glacial_erosion: np.ndarray, dt: float = 1.0) -> np.ndarray:
        """
        Glacial Deposition (빙하 퇴적) - 모레인, 드럼린
        빙하가 녹으면 운반된 물질 퇴적
        """
        if not self.enable_glacial_deposit or not self.enable_glacial:
            return np.zeros_like(self.elevation)
        
        deposition = np.zeros_like(self.elevation)
        
        # 빙하 가장자리 (ELA 근처) 퇴적
        near_ela = np.abs(self.elevation - self.glacier_ela) < 20
        
        # 종단 모레인: 빙하 침식물의 일부가 ELA 부근에 퇴적
        deposition = near_ela * glacial_erosion * self.moraine_rate
        
        self._fix_boundary_erosion(deposition)
        return deposition
    
    # === Landlab 추가 기능 메서드 ===
    
    def overland_flow(self, dt: float = 1.0) -> np.ndarray:
        """
        Overland Flow (지표수 흐름) - Manning 방정식 기반
        v = (1/n) * R^(2/3) * S^(1/2)
        
        Returns: 유속 배열 (m/s)
        """
        if not self.enable_overland_flow:
            return np.zeros_like(self.elevation)
        
        slope = self.calculate_slope()
        
        # 수심 근사 (배수면적 기반)
        flow_depth = np.sqrt(self.drainage_area * self.precipitation) * 0.01  # 간소화
        flow_depth = np.maximum(flow_depth, 0.001)  # 최소 수심
        
        # Manning 방정식: v = (1/n) * R^(2/3) * S^(1/2)
        # 수력반경 R ≈ 수심 (넓은 수로)
        velocity = (1.0 / self.manning_n) * (flow_depth ** (2/3)) * np.sqrt(slope)
        
        self.flow_velocity = velocity
        return velocity
    
    def cellular_automata_erosion(self, dt: float = 1.0) -> np.ndarray:
        """
        Cellular Automata (사면 붕괴) - 규칙 기반
        임계 경사 초과 시 물질이 이웃 셀로 분배
        
        Returns: 침식량 배열 (m)
        """
        if not self.enable_cellular_automata:
            return np.zeros_like(self.elevation)
        
        ca_change = np.zeros_like(self.elevation)
        
        for i in range(1, self.grid_size-1):
            for j in range(1, self.grid_size-1):
                # 4방향 이웃
                neighbors = [(i-1, j), (i+1, j), (i, j-1), (i, j+1)]
                
                for ni, nj in neighbors:
                    slope_diff = (self.elevation[i, j] - self.elevation[ni, nj]) / self.cell_size
                    
                    if slope_diff > self.ca_threshold:
                        # 초과 물질 계산
                        excess = (slope_diff - self.ca_threshold) * self.cell_size * 0.25
                        ca_change[i, j] -= excess
                        ca_change[ni, nj] += excess
        
        self._fix_boundary_erosion(ca_change)
        return ca_change
    
    def isostatic_flexure(self, load_change: np.ndarray, dt: float = 1.0) -> np.ndarray:
        """
        Flexure (지각 등압 조절) - 탄성판 모델
        빙하/퇴적물 하중에 의한 지각 변형
        
        Args:
            load_change: 하중 변화 (kg/m²)
        Returns: 지각 변형량 배열 (m)
        """
        if not self.enable_flexure:
            return np.zeros_like(self.elevation)
        
        from scipy import ndimage
        
        # 간소화된 등압 반응
        # 실제로는 FlexureCompact 사용 필요
        rho_m = 3300  # 맨틀 밀도 (kg/m³)
        g = 9.8
        
        # 저주파 필터로 광역적 변형 근사
        deflection = ndimage.gaussian_filter(load_change, sigma=10) / (rho_m * g)
        deflection *= 0.1  # 스케일링
        
        self.flexural_deflection = deflection
        return deflection
    
    def calculate_chi_index(self) -> np.ndarray:
        """
        Chi Analysis (하천 분석) - χ 지수 계산
        지각 융기 패턴 추정에 사용
        
        Returns: χ 지수 배열
        """
        if not self.enable_chi_analysis:
            return np.zeros_like(self.elevation)
        
        chi = np.zeros_like(self.elevation)
        
        # χ = ∫(A0/A)^m dx
        A0 = 1.0  # 기준 면적
        m = self.chi_concavity
        
        # 간소화: 배수면적 역수 적분 근사
        chi = (A0 / (self.drainage_area + 1)) ** m * self.cell_size
        
        # 누적 (하류 → 상류)
        from scipy import ndimage
        chi = ndimage.uniform_filter(chi, size=5) * self.grid_size * 0.1
        
        self.chi_index = chi
        return chi
    
    def calculate_landslide_probability(self) -> np.ndarray:
        """
        Landslide Probability (산사태 확률) - 무한 사면 안정성
        Factor of Safety (FS) 계산
        
        FS = (c' + (γ - γw * m) * z * cos²β * tanφ') / (γ * z * sinβ * cosβ)
        
        Returns: 안전율 배열 (FS < 1이면 불안정)
        """
        if not self.enable_landslide_prob:
            return np.ones_like(self.elevation)
        
        slope = self.calculate_slope()
        slope = np.maximum(slope, 0.01)  # 0 방지
        
        # 간소화된 FS 계산
        # FS = tanφ / tanβ + c / (γ * z * sinβ)
        gamma = 18000  # 단위중량 (N/m³)
        z = self.soil_depth + 0.1  # 토양 두께
        phi_rad = np.radians(self.friction_angle)
        
        # 경사각
        beta = np.arctan(slope)
        sin_beta = np.sin(beta)
        cos_beta = np.cos(beta)
        
        # 안전율
        fs = (self.cohesion / (gamma * z * sin_beta * cos_beta + 0.001)) + (np.tan(phi_rad) / (np.tan(beta) + 0.001))
        fs = np.clip(fs, 0.1, 10)  # 범위 제한
        
        self.factor_of_safety = fs
        return fs
    
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
        
        # 4. 풍화 (Weathering) - 기반암 → 토양 변환
        weathering = self.exponential_weathering(dt)
        
        # 5. 퇴적물 운반 및 퇴적
        deposition = self.sediment_transport(erosion, dt)
        
        # 6. 측방 침식 (Lateral Erosion) - 곡류 형성
        lateral = self.lateral_erosion(dt)
        
        # 7. 빙하 침식 (Glacial) - U자곡
        glacial = self.glacial_erosion(dt)
        
        # 8. 해안 침식 (Marine) - 해식애
        marine = self.marine_erosion(dt)
        
        # 9. 산사태 (Landslides)
        landslide = self.landslide_process(dt)
        
        # 10. 단층 운동 (Faulting)
        fault_uplift = self.tectonic_faulting(dt)
        
        # 11. 카르스트 용해 (Karst)
        karst = self.karst_dissolution(dt)
        
        # 12. 바람 침식 (Aeolian) - 사막 사구
        aeolian = self.aeolian_erosion(dt)
        
        # 13. 화산 활동 (Volcanic) - 용암류
        volcanic = self.volcanic_activity(dt)
        
        # 14. 지하수 침식 (Groundwater)
        groundwater = self.groundwater_erosion(dt)
        
        # 15. 동결파쇄 (Freeze-thaw)
        freeze_thaw = self.freeze_thaw_weathering(dt)
        
        # 16. 호수 형성 (Lake)
        lake = self.lake_formation(dt)
        
        # 17. 빙하 퇴적 (Moraine)
        moraine = self.glacial_deposition(glacial, dt)
        
        # 18. 지각 융기
        uplift = self.U * dt
        
        # 19. 토양층 업데이트
        # 모든 침식 합산
        total_erosion = erosion + lateral + glacial + marine + landslide + karst + aeolian + groundwater + freeze_thaw + lake
        
        # 식생 보호 효과 적용
        total_erosion = self.apply_vegetation_protection(total_erosion)
        
        soil_erosion = np.minimum(total_erosion, self.soil_depth)
        bedrock_erosion = total_erosion - soil_erosion
        
        # 토양에 풍화 추가, 퇴적물 추가, 화산물질 추가, 모레인 추가
        self.soil_depth = self.soil_depth - soil_erosion + weathering + deposition + moraine
        self.bedrock = self.bedrock - bedrock_erosion + uplift + fault_uplift + volcanic
        
        # 20. 전체 고도 업데이트
        self.elevation = self.bedrock + self.soil_depth + diffusion
        
        # 21. 경계 조건 적용
        self._fix_boundaries()
        
        # 22. 음수 방지
        self.elevation = np.maximum(self.elevation, 0)
        self.soil_depth = np.maximum(self.soil_depth, 0)
        self.bedrock = np.maximum(self.bedrock, 0)
        
        # 통계 반환
        return {
            'mean_elevation': float(self.elevation.mean()),
            'max_elevation': float(self.elevation.max()),
            'mean_erosion_rate': float(self.erosion_rate.mean()),
            'max_erosion_rate': float(self.erosion_rate.max()),
            'mean_weathering_rate': float(self.weathering_rate.mean()),
            'mean_deposition_rate': float(self.deposition_rate.mean()),
            'mean_lateral_erosion': float(self.lateral_erosion_rate.mean()),
            'mean_glacial': float(self.glacial_erosion_rate.mean()),
            'mean_marine': float(self.marine_erosion_rate.mean()),
            'mean_landslide': float(self.landslide_rate.mean()),
            'mean_soil_depth': float(self.soil_depth.mean()),
            'total_erosion': float(total_erosion.sum()),
            'total_deposition': float(deposition.sum()),
            'total_weathering': float(weathering.sum()),
            'total_uplift': float((uplift + fault_uplift.sum()) * self.grid_size**2)
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
    
    def get_soil_depth_map(self) -> np.ndarray:
        """토양 두께 맵 반환"""
        return self.soil_depth
    
    def get_weathering_map(self) -> np.ndarray:
        """풍화율 맵 반환"""
        return self.weathering_rate
    
    def get_bedrock_map(self) -> np.ndarray:
        """기반암 고도 맵 반환"""
        return self.bedrock
    
    def get_sediment_flux_map(self) -> np.ndarray:
        """퇴적물 플럭스 맵 반환"""
        return self.sediment_flux
    
    def get_deposition_map(self) -> np.ndarray:
        """퇴적률 맵 반환"""
        return self.deposition_rate


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
