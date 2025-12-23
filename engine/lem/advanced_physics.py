"""
🔬 Advanced Landlab Physics - 고급 물리 모델 (구조화 버전)

모듈:
- DiffusionModels: 확산 모델들 (Nonlinear, Depth-Dependent, Taylor)
- FlowRouting: 유향/유역 계산 (D8, MFD, Priority Flood)
- ErosionModels: 침식 모델 (SPACE, Fastscape)
- ChannelAnalysis: 하천 분석 (Profiler, Chi)
"""
import numpy as np
from scipy import ndimage
from typing import Tuple, Optional, List, Dict
from dataclasses import dataclass
import heapq


# ================================================
# 🌊 확산 모델 (Diffusion Models)
# ================================================
class DiffusionModels:
    """
    사면 확산 모델 모음
    
    - Linear: 선형 확산 (기본)
    - Nonlinear: 비선형 확산 (급경사)
    - DepthDependent: 토양 깊이 의존
    - Taylor: Taylor 근사 비선형
    """
    
    def __init__(self, grid_size: int, cell_size: float = 100.0):
        self.grid_size = grid_size
        self.cell_size = cell_size
    
    def linear(self, elevation: np.ndarray, D: float = 0.01, dt: float = 1.0) -> np.ndarray:
        """선형 확산: ∂z/∂t = D × ∇²z"""
        laplacian = ndimage.laplace(elevation) / (self.cell_size ** 2)
        dz = D * laplacian * dt
        self._fix_boundaries(dz)
        return dz
    
    def nonlinear(self, elevation: np.ndarray, 
                  D: float = 0.01, Sc: float = 1.0, dt: float = 1.0) -> np.ndarray:
        """
        비선형 확산: ∂z/∂t = ∇·(D/(1-(|∇z|/Sc)²) ∇z)
        급경사에서 확산 급증
        """
        dy, dx = np.gradient(elevation, self.cell_size)
        slope_mag = np.sqrt(dx**2 + dy**2)
        slope_ratio = np.clip(slope_mag / Sc, 0, 0.99)
        D_eff = D / (1 - slope_ratio**2)
        
        laplacian = ndimage.laplace(elevation) / (self.cell_size**2)
        dz = D_eff * laplacian * dt
        self._fix_boundaries(dz)
        return dz
    
    def depth_dependent(self, elevation: np.ndarray, soil_depth: np.ndarray,
                        D0: float = 0.01, H_star: float = 1.0, dt: float = 1.0) -> np.ndarray:
        """토양 깊이 의존 확산: D = D₀ × exp(-H/H*)"""
        D = D0 * np.exp(-soil_depth / H_star)
        laplacian = ndimage.laplace(elevation) / (self.cell_size**2)
        dz = D * laplacian * dt
        self._fix_boundaries(dz)
        return dz
    
    def taylor_nonlinear(self, elevation: np.ndarray, 
                         D: float = 0.01, Sc: float = 1.0, n: int = 2, dt: float = 1.0) -> np.ndarray:
        """Taylor 근사 비선형: D_eff = D × (1 + Σ(|∇z|/Sc)^2k)"""
        dy, dx = np.gradient(elevation, self.cell_size)
        slope_ratio = np.sqrt(dx**2 + dy**2) / Sc
        D_eff = D * (1 + sum(slope_ratio ** (2*k) for k in range(1, n+1)))
        
        laplacian = ndimage.laplace(elevation) / (self.cell_size**2)
        dz = D_eff * laplacian * dt
        self._fix_boundaries(dz)
        return dz
    
    def _fix_boundaries(self, arr: np.ndarray):
        arr[0, :] = 0; arr[-1, :] = 0
        arr[:, 0] = 0; arr[:, -1] = 0


# ================================================
# 🌀 유향/유역 계산 (Flow Routing)
# ================================================
class FlowRouting:
    """
    유향 및 유역면적 계산
    
    - steepest_descent: D8 최대경사 유향
    - accumulate_d8: D8 유역면적
    - accumulate_mfd: MFD 유역면적
    - priority_flood: 싱크홀 채우기
    - breach_depressions: 싱크홀 뚫기
    """
    
    # 8방향 (N, NE, E, SE, S, SW, W, NW)
    DIRECTIONS = [(-1,0), (-1,1), (0,1), (1,1), (1,0), (1,-1), (0,-1), (-1,-1)]
    DISTANCES = [1.0, np.sqrt(2), 1.0, np.sqrt(2), 1.0, np.sqrt(2), 1.0, np.sqrt(2)]
    
    def __init__(self, grid_size: int, cell_size: float = 100.0):
        self.grid_size = grid_size
        self.cell_size = cell_size
        self.h = grid_size
        self.w = grid_size
    
    def steepest_descent(self, elevation: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """D8 최대경사 유향 결정. Returns: (flow_dir 0-7, slope_to_receiver)"""
        flow_dir = np.full((self.h, self.w), -1, dtype=int)
        slope_recv = np.zeros((self.h, self.w))
        
        for i in range(1, self.h-1):
            for j in range(1, self.w-1):
                max_slope, max_dir = 0, -1
                for d, (di, dj) in enumerate(self.DIRECTIONS):
                    ni, nj = i + di, j + dj
                    slope = (elevation[i, j] - elevation[ni, nj]) / (self.DISTANCES[d] * self.cell_size)
                    if slope > max_slope:
                        max_slope, max_dir = slope, d
                flow_dir[i, j] = max_dir
                slope_recv[i, j] = max_slope
        
        return flow_dir, slope_recv
    
    def accumulate_d8(self, elevation: np.ndarray) -> np.ndarray:
        """D8 유역면적 계산"""
        drainage = np.ones_like(elevation)
        sorted_idx = np.argsort(elevation.ravel())[::-1]
        
        for idx in sorted_idx:
            i, j = divmod(idx, self.w)
            if i == 0 or i == self.h-1 or j == 0 or j == self.w-1:
                continue
            
            min_elev, min_n = elevation[i, j], None
            for di, dj in self.DIRECTIONS:
                ni, nj = i + di, j + dj
                if 0 <= ni < self.h and 0 <= nj < self.w and elevation[ni, nj] < min_elev:
                    min_elev, min_n = elevation[ni, nj], (ni, nj)
            
            if min_n:
                drainage[min_n] += drainage[i, j]
        
        return drainage
    
    def accumulate_mfd(self, elevation: np.ndarray, p: float = 1.1) -> np.ndarray:
        """MFD (다중유향) 유역면적"""
        drainage = np.ones_like(elevation)
        sorted_idx = np.argsort(elevation.ravel())[::-1]
        
        for idx in sorted_idx:
            i, j = divmod(idx, self.w)
            if i == 0 or i == self.h-1 or j == 0 or j == self.w-1:
                continue
            
            slopes, neighbors = [], []
            for d, (di, dj) in enumerate(self.DIRECTIONS):
                ni, nj = i + di, j + dj
                if 0 <= ni < self.h and 0 <= nj < self.w:
                    s = (elevation[i, j] - elevation[ni, nj]) / (self.DISTANCES[d] * self.cell_size)
                    if s > 0:
                        slopes.append(s ** p)
                        neighbors.append((ni, nj))
            
            if slopes:
                total = sum(slopes)
                for sl, (ni, nj) in zip(slopes, neighbors):
                    drainage[ni, nj] += drainage[i, j] * (sl / total)
        
        return drainage
    
    def priority_flood(self, elevation: np.ndarray, epsilon: float = 1e-6) -> np.ndarray:
        """Priority Flood - 싱크홀 채우기"""
        filled = elevation.copy()
        closed = np.zeros((self.h, self.w), dtype=bool)
        open_heap = []
        
        # 경계 초기화
        for i in range(self.h):
            heapq.heappush(open_heap, (elevation[i, 0], i, 0))
            heapq.heappush(open_heap, (elevation[i, self.w-1], i, self.w-1))
            closed[i, 0] = closed[i, self.w-1] = True
        for j in range(self.w):
            heapq.heappush(open_heap, (elevation[0, j], 0, j))
            heapq.heappush(open_heap, (elevation[self.h-1, j], self.h-1, j))
            closed[0, j] = closed[self.h-1, j] = True
        
        neighbors4 = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        
        while open_heap:
            elev, i, j = heapq.heappop(open_heap)
            for di, dj in neighbors4:
                ni, nj = i + di, j + dj
                if 0 <= ni < self.h and 0 <= nj < self.w and not closed[ni, nj]:
                    closed[ni, nj] = True
                    if filled[ni, nj] < elev:
                        filled[ni, nj] = elev + epsilon
                    heapq.heappush(open_heap, (filled[ni, nj], ni, nj))
        
        return filled
    
    def breach_depressions(self, elevation: np.ndarray, max_depth: float = 10.0) -> np.ndarray:
        """싱크홀 뚫기 (Breach)"""
        result = elevation.copy()
        for i in range(1, self.h-1):
            for j in range(1, self.w-1):
                neighbors = [elevation[i-1,j], elevation[i+1,j], elevation[i,j-1], elevation[i,j+1]]
                min_n = min(neighbors)
                if elevation[i, j] < min_n:
                    breach = min(min_n - elevation[i, j], max_depth)
                    for di, dj in [(-1,0), (1,0), (0,-1), (0,1)]:
                        if elevation[i+di, j+dj] == min_n:
                            result[i+di, j+dj] -= breach / 2
                            break
        return result


# ================================================
# ⛰️ 침식 모델 (Erosion Models)
# ================================================
@dataclass
class SPACEResult:
    """SPACE 모델 결과"""
    bedrock_erosion: np.ndarray
    sediment_erosion: np.ndarray
    deposition: np.ndarray
    net_change: np.ndarray


class ErosionModels:
    """
    침식 모델
    
    - stream_power: Stream Power Law
    - space: SPACE (침식+퇴적 통합)
    - fastscape: Fastscape Implicit
    """
    
    def __init__(self, grid_size: int, cell_size: float = 100.0):
        self.grid_size = grid_size
        self.cell_size = cell_size
        self.flow = FlowRouting(grid_size, cell_size)
    
    def stream_power(self, elevation: np.ndarray, drainage_area: np.ndarray,
                     K: float = 0.0001, m: float = 0.5, n: float = 1.0, dt: float = 1.0) -> np.ndarray:
        """Stream Power Law: E = K × A^m × S^n"""
        dy, dx = np.gradient(elevation, self.cell_size)
        slope = np.maximum(np.sqrt(dx**2 + dy**2), 1e-6)
        Q = drainage_area * self.cell_size**2
        erosion = K * (Q ** m) * (slope ** n) * dt
        erosion[0,:] = erosion[-1,:] = erosion[:,0] = erosion[:,-1] = 0
        return erosion
    
    def space(self, elevation: np.ndarray, sediment: np.ndarray, drainage_area: np.ndarray,
              K_br: float = 0.0001, K_sed: float = 0.001, Vs: float = 1.0,
              m: float = 0.5, n: float = 1.0, dt: float = 1.0) -> SPACEResult:
        """SPACE: 기반암+퇴적물 통합 모델"""
        dy, dx = np.gradient(elevation, self.cell_size)
        slope = np.maximum(np.sqrt(dx**2 + dy**2), 1e-6)
        Q = drainage_area * self.cell_size**2
        stream_power = (Q ** m) * (slope ** n)
        
        cover = 1 - np.exp(-sediment / 0.1)
        Er_br = K_br * stream_power * (1 - cover) * dt
        Er_sed = K_sed * stream_power * cover * dt
        dep = Vs * sediment * np.exp(-slope * 10) * dt
        dep = np.minimum(dep, sediment)
        
        return SPACEResult(Er_br, Er_sed, dep, -Er_br - Er_sed + dep)
    
    def fastscape(self, elevation: np.ndarray, drainage_area: np.ndarray,
                  K: float = 0.0001, m: float = 0.5, n: float = 1.0,
                  dt: float = 100.0, max_iter: int = 10) -> np.ndarray:
        """Fastscape Implicit - 큰 dt 안정"""
        result = elevation.copy()
        flow_dir, _ = self.flow.steepest_descent(elevation)
        
        for _ in range(max_iter):
            new_result = result.copy()
            for idx in np.argsort(result.ravel()):
                i, j = divmod(idx, self.grid_size)
                if i == 0 or i == self.grid_size-1 or j == 0 or j == self.grid_size-1:
                    continue
                d = flow_dir[i, j]
                if d < 0:
                    continue
                di, dj = self.flow.DIRECTIONS[d]
                ni, nj = i + di, j + dj
                if not (0 <= ni < self.grid_size and 0 <= nj < self.grid_size):
                    continue
                
                L = self.flow.DISTANCES[d] * self.cell_size
                Q = drainage_area[i, j] * self.cell_size**2
                z_recv = new_result[ni, nj]
                if result[i, j] > z_recv:
                    slope = (result[i, j] - z_recv) / L
                    erosion = K * (Q ** m) * (slope ** n) * dt
                    erosion = min(erosion, result[i, j] - z_recv - 0.001)
                    new_result[i, j] = result[i, j] - erosion
            result = new_result
        return result


# ================================================
# 📊 하천 분석 (Channel Analysis)
# ================================================
@dataclass
class ChannelProfile:
    """하천 종단면"""
    distance: np.ndarray
    elevation: np.ndarray
    slope: np.ndarray
    drainage_area: np.ndarray
    chi: np.ndarray


class ChannelAnalysis:
    """
    하천 분석 도구
    
    - extract_profile: 종단면 추출
    - chi_analysis: Chi 분석
    """
    
    DIRECTIONS = [(-1,0), (-1,1), (0,1), (1,1), (1,0), (1,-1), (0,-1), (-1,-1)]
    DIST_MULT = [1.0, np.sqrt(2), 1.0, np.sqrt(2), 1.0, np.sqrt(2), 1.0, np.sqrt(2)]
    
    def __init__(self, grid_size: int, cell_size: float = 100.0):
        self.grid_size = grid_size
        self.cell_size = cell_size
    
    def extract_profile(self, elevation: np.ndarray, drainage_area: np.ndarray,
                        outlet: Tuple[int, int], threshold: float = 100.0,
                        concavity: float = 0.45) -> ChannelProfile:
        """하천 종단면 추출"""
        distances, elevations, slopes, areas = [], [], [], []
        current, total_dist, visited = outlet, 0.0, set()
        
        while current not in visited:
            i, j = current
            visited.add(current)
            distances.append(total_dist)
            elevations.append(elevation[i, j])
            areas.append(drainage_area[i, j])
            slopes.append((elevations[-1] - elevations[-2]) / (distances[-1] - distances[-2] + 1e-10) if len(elevations) > 1 else 0.0)
            
            max_area, next_cell, step = 0, None, 0
            for d, (di, dj) in enumerate(self.DIRECTIONS):
                ni, nj = i + di, j + dj
                if 0 <= ni < self.grid_size and 0 <= nj < self.grid_size:
                    if drainage_area[ni, nj] > max_area and (ni, nj) not in visited and drainage_area[ni, nj] >= threshold:
                        max_area, next_cell, step = drainage_area[ni, nj], (ni, nj), self.DIST_MULT[d] * self.cell_size
            
            if not next_cell:
                break
            total_dist += step
            current = next_cell
        
        # Chi 계산
        distances, elevations, areas, slopes = map(np.array, [distances, elevations, areas, slopes])
        chi = np.zeros_like(distances)
        A0 = max(areas[0], 1)
        for i in range(1, len(distances)):
            chi[i] = chi[i-1] + (A0 / areas[i]) ** concavity * (distances[i] - distances[i-1])
        
        return ChannelProfile(distances, elevations, slopes, areas, chi)


# ================================================
# 🪨 퇴적 모델 (Sediment Models)
# ================================================
@dataclass
class ExnerResult:
    """Exner 방정식 결과"""
    bedload_flux: np.ndarray
    bed_change: np.ndarray
    suspended_load: np.ndarray

class SedimentModels:
    """
    퇴적물 운반/퇴적 모델
    
    - exner: Exner 방정식 (하상 변동)
    - bedload_mpm: Meyer-Peter-Müller 소류사
    - suspended_rouse: Rouse 부유사
    """
    
    def __init__(self, grid_size: int, cell_size: float = 100.0):
        self.grid_size = grid_size
        self.cell_size = cell_size
    
    def exner(self, elevation: np.ndarray, 
              sediment_flux: np.ndarray,
              porosity: float = 0.4,
              dt: float = 1.0) -> ExnerResult:
        """
        Exner 방정식: 하상 변동
        
        ∂η/∂t = -1/(1-λ) × ∂qs/∂x
        
        Args:
            elevation: 하상 고도
            sediment_flux: 퇴적물 플럭스 (m³/m/s)
            porosity: 공극률
            dt: 시간 간격
            
        Returns:
            ExnerResult (소류사, 하상변화, 부유사)
        """
        # 플럭스 발산 계산
        dqs_dx = np.gradient(sediment_flux, self.cell_size, axis=1)
        dqs_dy = np.gradient(sediment_flux, self.cell_size, axis=0)
        divergence = dqs_dx + dqs_dy
        
        # 하상 변화
        bed_change = -1.0 / (1 - porosity) * divergence * dt
        
        # 부유사 (간단한 근사)
        velocity = np.sqrt(np.abs(sediment_flux)) * 0.1
        suspended = sediment_flux * 0.2  # 20%가 부유
        
        return ExnerResult(
            bedload_flux=sediment_flux * 0.8,
            bed_change=bed_change,
            suspended_load=suspended
        )
    
    def bedload_mpm(self, slope: np.ndarray, 
                    depth: np.ndarray,
                    grain_size: float = 0.01,  # 10mm
                    rho_s: float = 2650.0,
                    rho_w: float = 1000.0) -> np.ndarray:
        """
        Meyer-Peter-Müller 소류사 공식
        
        qs = 8 × (τ* - τ*c)^1.5 × √((ρs/ρw - 1) × g × D³)
        
        Args:
            slope: 수면 경사
            depth: 수심
            grain_size: 입자 크기 (m)
            
        Returns:
            소류사 운반률 (m²/s)
        """
        g = 9.81
        tau = rho_w * g * depth * slope  # 전단응력
        tau_star = tau / ((rho_s - rho_w) * g * grain_size)  # 무차원 전단응력
        tau_star_c = 0.047  # 임계값 (Shields)
        
        excess = np.maximum(0, tau_star - tau_star_c)
        qs = 8 * (excess ** 1.5) * np.sqrt((rho_s/rho_w - 1) * g * grain_size**3)
        
        return qs
    
    def suspended_rouse(self, velocity: np.ndarray,
                        depth: np.ndarray,
                        settling_velocity: float = 0.01) -> np.ndarray:
        """
        Rouse 부유사 농도 프로파일
        
        C/Ca = ((d-z)/z × a/(d-a))^P
        P = ws/(κ×u*)
        
        Returns:
            부유사 농도 그리드
        """
        kappa = 0.41  # von Karman 상수
        u_star = velocity * 0.1  # 마찰 속도 근사
        
        P = settling_velocity / (kappa * u_star + 1e-10)
        P = np.clip(P, 0.1, 5.0)  # 합리적 범위
        
        # 깊이 평균 농도
        concentration = (1 / (P + 1)) * (velocity / (settling_velocity + 0.01))
        
        return np.clip(concentration, 0, 1)


# ================================================
# ⛰️ 사면 안정성 (Slope Stability)
# ================================================
@dataclass
class StabilityResult:
    """사면 안정성 결과"""
    factor_of_safety: np.ndarray
    failure_probability: np.ndarray
    critical_zones: np.ndarray

class SlopeStability:
    """
    사면 안정성 분석
    
    - infinite_slope: 무한사면 모델
    - factor_of_safety: 안정계수 계산
    """
    
    def __init__(self, grid_size: int, cell_size: float = 100.0):
        self.grid_size = grid_size
        self.cell_size = cell_size
    
    def infinite_slope(self, slope: np.ndarray,
                       soil_depth: np.ndarray,
                       cohesion: float = 5000.0,  # Pa
                       friction_angle: float = 30.0,  # degrees
                       soil_density: float = 1800.0,  # kg/m³
                       water_table_ratio: float = 0.5) -> StabilityResult:
        """
        무한사면 안정 분석
        
        FS = (c' + (γ-m×γw)×z×cos²β×tanφ') / (γ×z×sinβ×cosβ)
        
        Args:
            slope: 사면 경사 (m/m)
            soil_depth: 토양 깊이 (m)
            cohesion: 점착력 (Pa)
            friction_angle: 내부마찰각 (도)
            soil_density: 토양 밀도 (kg/m³)
            water_table_ratio: 지하수면 비율 (0-1)
            
        Returns:
            StabilityResult
        """
        g = 9.81
        gamma = soil_density * g  # 단위중량
        gamma_w = 1000 * g  # 물 단위중량
        
        phi_rad = np.radians(friction_angle)
        beta = np.arctan(slope)  # 경사각
        
        # 분자: 저항력
        m = water_table_ratio
        effective_stress = (gamma - m * gamma_w) * soil_depth * np.cos(beta)**2
        resistance = cohesion + effective_stress * np.tan(phi_rad)
        
        # 분모: 활동력
        driving = gamma * soil_depth * np.sin(beta) * np.cos(beta)
        driving = np.maximum(driving, 1e-6)  # 0 방지
        
        # 안전율
        fs = resistance / driving
        
        # 파괴 확률 (log-normal 가정 간소화)
        failure_prob = 1 / (1 + np.exp(2 * (fs - 1)))
        
        # 임계 구역 (FS < 1.3)
        critical = fs < 1.3
        
        return StabilityResult(
            factor_of_safety=fs,
            failure_probability=failure_prob,
            critical_zones=critical.astype(float)
        )


# ================================================
# 🌊 해안 모델 (Coastal Models)
# ================================================
class CoastalModels:
    """
    해안 지형 모델
    
    - wave_ravinement: 파랑 침식 (해수면 변동)
    - longshore_drift: 연안류 퇴적
    - cliff_retreat: 해식애 후퇴
    """
    
    def __init__(self, grid_size: int, cell_size: float = 100.0):
        self.grid_size = grid_size
        self.cell_size = cell_size
    
    def wave_ravinement(self, elevation: np.ndarray,
                        sea_level: float = 0.0,
                        wave_height: float = 2.0,
                        erosion_rate: float = 0.01,
                        dt: float = 1.0) -> np.ndarray:
        """
        파랑 침식 (Wave Ravinement)
        
        해수면 부근에서 파도에 의한 침식
        해수면 변동 시 ravinement surface 형성
        
        Args:
            elevation: 고도
            sea_level: 해수면 (m)
            wave_height: 파고 (m)
            erosion_rate: 침식률 (m/yr)
            dt: 시간 간격
            
        Returns:
            침식량 그리드
        """
        # 파도 영향권: sea_level ± wave_height
        wave_zone = np.abs(elevation - sea_level) < wave_height
        
        # 침식량: 해수면에 가까울수록 강함
        distance_from_sl = np.abs(elevation - sea_level)
        intensity = np.exp(-distance_from_sl / (wave_height / 2))
        
        erosion = erosion_rate * intensity * wave_zone * dt
        
        return erosion
    
    def longshore_drift(self, elevation: np.ndarray,
                        sediment: np.ndarray,
                        sea_level: float = 0.0,
                        wave_angle: float = 45.0,  # degrees from north
                        transport_rate: float = 0.1) -> np.ndarray:
        """
        연안류 퇴적물 이동
        
        Args:
            elevation: 고도
            sediment: 현재 퇴적물
            sea_level: 해수면
            wave_angle: 파향 (도)
            transport_rate: 운반률
            
        Returns:
            퇴적물 변화량
        """
        # 해안선 마스크
        coastal = np.abs(elevation - sea_level) < 5.0
        
        angle_rad = np.radians(wave_angle)
        dy = int(np.cos(angle_rad) * 2)
        dx = int(np.sin(angle_rad) * 2)
        
        change = np.zeros_like(elevation)
        
        for i in range(2, self.grid_size - 2):
            for j in range(2, self.grid_size - 2):
                if coastal[i, j]:
                    # 상류에서 퇴적물 가져오기
                    ni, nj = i - dy, j - dx
                    if 0 <= ni < self.grid_size and 0 <= nj < self.grid_size:
                        transport = sediment[ni, nj] * transport_rate
                        change[i, j] += transport
                        change[ni, nj] -= transport
        
        return change
    
    def cliff_retreat(self, elevation: np.ndarray,
                      sea_level: float = 0.0,
                      retreat_rate: float = 0.5,
                      cliff_threshold: float = 0.5,
                      dt: float = 1.0) -> np.ndarray:
        """
        해식애 후퇴
        
        Args:
            elevation: 고도
            sea_level: 해수면
            retreat_rate: 후퇴율 (m/yr)
            cliff_threshold: 절벽 판단 경사
            dt: 시간 간격
            
        Returns:
            침식량
        """
        dy, dx = np.gradient(elevation, self.cell_size)
        slope = np.sqrt(dx**2 + dy**2)
        
        # 해수면 부근의 급경사 = 절벽
        near_sea = np.abs(elevation - sea_level) < 10.0
        is_cliff = (slope > cliff_threshold) & near_sea
        
        erosion = retreat_rate * is_cliff * dt
        
        return erosion


# ================================================
# 🌍 지각 평형 (Isostasy)
# ================================================
class Isostasy:
    """
    등압 조절 모델
    
    - flexural: 탄성판 flexure
    - airy: Airy 모델
    """
    
    def __init__(self, grid_size: int, cell_size: float = 100.0):
        self.grid_size = grid_size
        self.cell_size = cell_size
    
    def flexural(self, load: np.ndarray,
                 elastic_thickness: float = 25000.0,  # m
                 mantle_density: float = 3300.0,
                 crust_density: float = 2700.0) -> np.ndarray:
        """
        Flexural Isostasy (탄성판 모델)
        
        D × ∇⁴w + (ρm - ρc) × g × w = q(x,y)
        
        Args:
            load: 표면 하중 (kg/m²)
            elastic_thickness: 탄성 두께 (m)
            mantle_density: 맨틀 밀도
            crust_density: 지각 밀도
            
        Returns:
            지각 변형량 (m)
        """
        g = 9.81
        E = 7e10  # Young's modulus (Pa)
        nu = 0.25  # Poisson's ratio
        
        # Flexural rigidity
        D = E * elastic_thickness**3 / (12 * (1 - nu**2))
        
        # Flexural parameter
        alpha = ((mantle_density - crust_density) * g / D) ** 0.25 if (mantle_density - crust_density) > 0 else 1e-6
        
        # 간소화: 가우시안 필터로 하중 분산
        from scipy.ndimage import gaussian_filter
        flexural_wavelength = 1.0 / alpha
        sigma = flexural_wavelength / self.cell_size / 4
        
        deflection = gaussian_filter(load / ((mantle_density - crust_density) * g), sigma)
        
        return deflection
    
    def airy(self, elevation: np.ndarray,
             crust_density: float = 2700.0,
             mantle_density: float = 3300.0) -> np.ndarray:
        """
        Airy 등압 모델
        
        지형 고도에 비례하여 뿌리 깊이 결정
        
        Returns:
            모호면 깊이 (m, 양수 = 아래)
        """
        # 산 높이에 비례한 뿌리
        root_depth = elevation * crust_density / (mantle_density - crust_density)
        
        return root_depth

