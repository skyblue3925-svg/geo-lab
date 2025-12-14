import numpy as np
from .grid import WorldGrid

try:
    from numba import jit
    HAS_NUMBA = True
except ImportError:
    HAS_NUMBA = False
    # Dummy decorator if numba is missing
    def jit(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

@jit(nopython=True)
def _d8_flow_kernel(elev, discharge, flow_dir, underwater, h, w):
    """
    Numba-optimized D8 Flow Routing
    """
    # Flatten elevation to sort
    flat_elev = elev.ravel()
    # Sort indices descending (Source -> Sink)
    # Note: argsort in numba supports 1D array
    flat_indices = np.argsort(flat_elev)[::-1]
    
    # 8-neighbor offsets
    # Numba doesn't like list of tuples in loops sometimes, simple arrays are better
    dr = np.array([-1, -1, -1,  0,  0,  1,  1,  1])
    dc = np.array([-1,  0,  1, -1,  1, -1,  0,  1])
    
    for i in range(len(flat_indices)):
        idx = flat_indices[i]
        r = idx // w
        c = idx % w
        
        # Check underwater
        if underwater[r, c]:
            continue
            
        current_z = elev[r, c]
        min_z = current_z
        target_r = -1
        target_c = -1
        target_k = -1
        
        # Find steepest descent
        for k in range(8):
            nr = r + dr[k]
            nc = c + dc[k]
            
            if 0 <= nr < h and 0 <= nc < w:
                n_elev = elev[nr, nc]
                if n_elev < min_z:
                    min_z = n_elev
                    target_r = nr
                    target_c = nc
                    target_k = k
        
        # Pass flow to lowest neighbor
        if target_r != -1:
            discharge[target_r, target_c] += discharge[r, c]
            flow_dir[r, c] = target_k # Store direction (0-7)

class HydroKernel:
    """
    수력학 커널 (Hydro Kernel)
    
    물의 흐름과 분포를 시뮬레이션합니다.
    - D8 알고리즘: 하천 네트워크 형성 (Numba 가속 적용)
    - Shallow Water (간소화): 홍수 및 해수면 침수
    """
    
    def __init__(self, grid: WorldGrid):
        self.grid = grid
        
    def route_flow_d8(self, precipitation: float = 0.001) -> np.ndarray:
        """
        D8 알고리즘으로 유량(Discharge) 계산 (Numba 가속)
        """
        h, w = self.grid.height, self.grid.width
        elev = self.grid.elevation
        
        # 1. 초기 강수 분포
        discharge = np.full((h, w), precipitation * (self.grid.cell_size ** 2), dtype=np.float64)
        
        # 2. 해수면 마스크
        underwater = self.grid.is_underwater()
        
        # 3. Numba Kernel 호출
        if HAS_NUMBA:
            _d8_flow_kernel(elev, discharge, self.grid.flow_dir, underwater, h, w)
        else:
            # Fallback (Slow Python) if numba somehow fails to import
            self._route_flow_d8_python(discharge, self.grid.flow_dir, elev, underwater, h, w)
            
        return discharge

    def route_flow_mfd(self, precipitation: float = 0.001, p: float = 1.1) -> np.ndarray:
        """
        MFD (Multiple Flow Direction) 유량 분배
        
        D8과 달리 낮은 모든 이웃에게 경사 비례로 유량 분배.
        망류(Braided Stream) 및 분기류 표현에 적합.
        
        Args:
            precipitation: 강수량
            p: 분배 지수 (1.0=선형, >1.0=가파른 곳에 집중)
            
        Returns:
            discharge: 유량 배열
        """
        h, w = self.grid.height, self.grid.width
        elev = self.grid.elevation
        
        # 초기 강수
        discharge = np.full((h, w), precipitation * (self.grid.cell_size ** 2), dtype=np.float64)
        
        # 해수면 마스크
        underwater = self.grid.is_underwater()
        
        # D8 방향 벡터
        dr = np.array([-1, -1, -1,  0,  0,  1,  1,  1])
        dc = np.array([-1,  0,  1, -1,  1, -1,  0,  1])
        dist = np.array([1.414, 1.0, 1.414, 1.0, 1.0, 1.414, 1.0, 1.414])  # 대각 거리
        
        # 정렬 (높은 곳 -> 낮은 곳)
        flat_indices = np.argsort(elev.ravel())[::-1]
        
        for idx in flat_indices:
            r, c = idx // w, idx % w
            
            if underwater[r, c]:
                continue
                
            current_z = elev[r, c]
            current_q = discharge[r, c]
            
            if current_q <= 0:
                continue
            
            # 낮은 이웃들의 경사 계산
            slopes = []
            targets = []
            
            for k in range(8):
                nr, nc = r + dr[k], c + dc[k]
                if 0 <= nr < h and 0 <= nc < w:
                    dz = current_z - elev[nr, nc]
                    if dz > 0:  # 하강하는 방향만
                        slope = dz / (dist[k] * self.grid.cell_size)
                        slopes.append(slope ** p)
                        targets.append((nr, nc))
            
            if not slopes:
                continue
                
            # 경사 비례 분배
            total_slope = sum(slopes)
            for i, (nr, nc) in enumerate(targets):
                fraction = slopes[i] / total_slope
                discharge[nr, nc] += current_q * fraction
                
        return discharge

    def _route_flow_d8_python(self, discharge, flow_dir, elev, underwater, h, w):
        """Legacy Python implementation for fallback"""
        flat_indices = np.argsort(elev.ravel())[::-1]
        neighbors = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
        
        for idx in flat_indices:
            r, c = idx // w, idx % w
            if underwater[r, c]: continue
            
            min_z = elev[r, c]
            target = None
            target_k = -1
            
            for k, (dr, dc) in enumerate(neighbors):
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w:
                    if elev[nr, nc] < min_z:
                        min_z = elev[nr, nc]
                        target = (nr, nc)
                        target_k = k
            
            if target:
                tr, tc = target
                discharge[tr, tc] += discharge[r, c]
                flow_dir[r, c] = target_k

    def calculate_water_depth(self, discharge: np.ndarray, manning_n: float = 0.03) -> np.ndarray:
        """
        Manning 공식을 이용한 하천 수심 추정 (정상 등류 가정)
        Depth = (Q * n / (Width * S^0.5))^(3/5)
        
        * 경사(S)가 0인 경우 최소 경사 적용
        * 하폭(W)은 유량(Q)의 함수로 가정 (W ~ Q^0.5)
        """
        slope, _ = self.grid.get_gradient()
        slope = np.maximum(slope, 0.001) # 최소 경사 설정
        
        # 하폭 추정: W = 5 * Q^0.5 (경험식)
        # Q가 매우 작으면 W도 작아짐
        width = 5.0 * np.sqrt(discharge)
        width = np.maximum(width, 1.0) # 최소 폭 1m
        
        # 수심 계산
        # Q = V * Area = (1/n * R^(2/3) * S^(1/2)) * (W * D)
        # 직사각형 단면 가정 시 R approx D (넓은 하천)
        # Q = (1/n) * D^(5/3) * W * S^(1/2)
        # D = (Q * n / (W * S^0.5)) ^ (3/5)
        
        val = (discharge * manning_n) / (width * np.sqrt(slope))
        depth = np.power(val, 0.6)
        
        return depth
    
    def simulate_inundation(self):
        """해수면 상승에 따른 침수 시뮬레이션"""
        # 해수면보다 낮은 곳은 바다로 간주하고 수심을 채움
        underwater = self.grid.is_underwater()
        
        # 바다 수심 = 해수면 - 지표면고도
        sea_depth = np.maximum(0, self.grid.sea_level - self.grid.elevation)
        
        # 기존 수심(하천)과 바다 수심 중 큰 값 선택
        # (하천이 바다로 들어가면 바다 수심에 묻힘)
        self.grid.water_depth = np.where(underwater, sea_depth, self.grid.water_depth)

    def fill_sinks(self, max_iterations: int = 100, tolerance: float = 0.001):
        """
        싱크(웅덩이) 채우기 - 호수 형성
        
        물이 갇히는 곳을 찾아 채워서 월류(Overflow)가 가능하도록 함.
        간단한 반복 스무딩 방식 (Priority-Flood 근사)
        
        Args:
            max_iterations: 최대 반복 횟수
            tolerance: 수렴 허용 오차
        """
        h, w = self.grid.height, self.grid.width
        elev = self.grid.elevation.copy()
        
        # 경계는 고정 (물이 빠져나감)
        # 내부 싱크만 채움
        
        dr = [-1, -1, -1,  0,  0,  1,  1,  1]
        dc = [-1,  0,  1, -1,  1, -1,  0,  1]
        
        for iteration in range(max_iterations):
            changed = False
            new_elev = elev.copy()
            
            for r in range(1, h - 1):
                for c in range(1, w - 1):
                    current = elev[r, c]
                    
                    # 이웃 중 최소값 찾기
                    min_neighbor = current
                    for k in range(8):
                        nr, nc = r + dr[k], c + dc[k]
                        if 0 <= nr < h and 0 <= nc < w:
                            min_neighbor = min(min_neighbor, elev[nr, nc])
                    
                    # 모든 이웃보다 낮으면 (싱크) → 최소 이웃 높이로 맞춤
                    if current < min_neighbor:
                        # 살짝 높여서 흐름 유도
                        new_elev[r, c] = min_neighbor + tolerance
                        changed = True
                        
            elev = new_elev
            
            if not changed:
                break
                
        # 채워진 양 = 새 고도 - 기존 고도
        fill_amount = elev - self.grid.elevation
        
        # 물로 채워진 것으로 처리 (water_depth 증가)
        self.grid.water_depth += np.maximum(fill_amount, 0)
        
        # bedrock은 그대로, sediment도 그대로 (물만 채움)
        # 또는 sediment로 채울 수도 있음 (호수 퇴적)
        
        return fill_amount

