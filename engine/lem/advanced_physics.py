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
