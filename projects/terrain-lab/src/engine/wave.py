"""
Wave Kernel (파랑 커널)

해안 지형 형성 프로세스
- 파랑 침식 (Wave Erosion): 해식절벽 후퇴
- 연안 퇴적 (Coastal Deposition): 사주, 사취 형성
- 연안류 (Longshore Drift): 측방 퇴적물 이동

핵심 공식:
침식률 E = K * H^2 * (1/R)
- H: 파고 (Wave Height)
- R: 암석 저항력 (Rock Resistance)
"""

import numpy as np
from .grid import WorldGrid


class WaveKernel:
    """
    파랑 커널
    
    해안선에서의 파랑 작용을 시뮬레이션.
    침식과 퇴적을 동시에 처리.
    """
    
    def __init__(self, grid: WorldGrid,
                 wave_height: float = 2.0,      # m
                 wave_period: float = 8.0,      # s
                 wave_direction: float = 0.0,   # degrees from N
                 K_erosion: float = 0.001):
        self.grid = grid
        self.wave_height = wave_height
        self.wave_period = wave_period
        self.wave_direction = np.radians(wave_direction)
        self.K = K_erosion
        
    def identify_coastline(self) -> np.ndarray:
        """
        해안선 식별
        
        육지-바다 경계선을 찾음
        
        Returns:
            coastline_mask: 해안선 셀 마스크
        """
        underwater = self.grid.is_underwater()
        
        # 해안선 = 육지인데 인접 셀에 바다가 있는 곳
        h, w = self.grid.height, self.grid.width
        coastline = np.zeros((h, w), dtype=bool)
        
        for r in range(h):
            for c in range(w):
                if underwater[r, c]:
                    continue  # 바다는 해안선 아님
                    
                # 인접 셀 확인
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < h and 0 <= nc < w:
                            if underwater[nr, nc]:
                                coastline[r, c] = True
                                break
                    if coastline[r, c]:
                        break
                        
        return coastline
        
    def calculate_wave_energy(self) -> np.ndarray:
        """
        파랑 에너지 분포 계산
        
        Returns:
            energy: 각 셀의 파랑 에너지
        """
        h, w = self.grid.height, self.grid.width
        
        # 기본 에너지 = H^2 (파고 제곱에 비례)
        base_energy = self.wave_height ** 2
        
        # 수심에 따른 감쇠
        # 깊은 바다: 에너지 유지, 얕은 곳: 에너지 집중 후 쇄파
        sea_depth = np.maximum(0, self.grid.sea_level - self.grid.elevation)
        
        # 천해 효과: 수심 < 파장/2 일 때 에너지 증가
        wavelength = 1.56 * (self.wave_period ** 2)  # 심해 파장 근사
        depth_factor = np.ones((h, w))
        
        shallow = sea_depth < wavelength / 2
        depth_factor[shallow] = 1.0 + 0.5 * (1 - sea_depth[shallow] / (wavelength / 2))
        
        energy = base_energy * depth_factor
        
        # 육지는 에너지 0
        energy[~self.grid.is_underwater()] = 0
        
        return energy
        
    def erode_coast(self, coastline: np.ndarray, 
                    wave_energy: np.ndarray,
                    rock_resistance: np.ndarray = None,
                    dt: float = 1.0) -> np.ndarray:
        """
        해안 침식
        
        Args:
            coastline: 해안선 마스크
            wave_energy: 파랑 에너지 배열
            rock_resistance: 암석 저항력 (0~1, 높을수록 저항)
            dt: 시간 간격
            
        Returns:
            erosion: 침식량 배열
        """
        h, w = self.grid.height, self.grid.width
        
        if rock_resistance is None:
            rock_resistance = np.ones((h, w)) * 0.5
            
        erosion = np.zeros((h, w), dtype=np.float64)
        
        # 해안선 셀에 대해 침식 계산
        coast_coords = np.argwhere(coastline)
        
        for r, c in coast_coords:
            # 인접 바다 셀의 평균 에너지
            adjacent_energy = 0
            count = 0
            
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w:
                        if self.grid.is_underwater()[nr, nc]:
                            adjacent_energy += wave_energy[nr, nc]
                            count += 1
                            
            if count > 0:
                avg_energy = adjacent_energy / count
                # 침식률 = K * Energy / Resistance
                resistance = rock_resistance[r, c]
                erosion[r, c] = self.K * avg_energy * (1 - resistance) * dt
                
        return erosion
        
    def longshore_drift(self, coastline: np.ndarray,
                        sediment_available: np.ndarray,
                        dt: float = 1.0) -> np.ndarray:
        """
        연안류에 의한 퇴적물 이동
        
        Args:
            coastline: 해안선 마스크
            sediment_available: 이동 가능한 퇴적물
            dt: 시간 간격
            
        Returns:
            change: 퇴적물 변화량
        """
        h, w = self.grid.height, self.grid.width
        change = np.zeros((h, w), dtype=np.float64)
        
        # 파랑 방향에 따른 연안류 방향
        # 0 = N, 90 = E, etc.
        drift_dx = np.sin(self.wave_direction)
        drift_dy = -np.cos(self.wave_direction)  # Y축 반전
        
        coast_coords = np.argwhere(coastline)
        
        for r, c in coast_coords:
            available = sediment_available[r, c]
            if available <= 0:
                continue
                
            # 이동량
            move_amount = min(available * 0.1 * dt, available)
            
            # 목표 셀 (연안류 방향)
            tr = int(r + drift_dy)
            tc = int(c + drift_dx)
            
            if 0 <= tr < h and 0 <= tc < w:
                if coastline[tr, tc] or self.grid.is_underwater()[tr, tc]:
                    change[r, c] -= move_amount
                    change[tr, tc] += move_amount
                    
        return change
        
    def step(self, dt: float = 1.0, 
             rock_resistance: np.ndarray = None) -> dict:
        """
        1단계 파랑 작용 실행
        
        Args:
            dt: 시간 간격
            rock_resistance: 암석 저항력 배열
            
        Returns:
            result: 침식/퇴적 결과
        """
        # 1. 해안선 식별
        coastline = self.identify_coastline()
        
        if not np.any(coastline):
            return {'erosion': np.zeros_like(self.grid.elevation),
                    'drift': np.zeros_like(self.grid.elevation)}
        
        # 2. 파랑 에너지 계산
        wave_energy = self.calculate_wave_energy()
        
        # 3. 해안 침식
        erosion = self.erode_coast(coastline, wave_energy, rock_resistance, dt)
        
        # 침식 적용 (bedrock 감소)
        self.grid.bedrock -= erosion
        
        # 침식된 양은 퇴적물로 변환
        self.grid.sediment += erosion * 0.8  # 일부 유실
        
        # 4. 연안류 (Longshore Drift)
        drift = self.longshore_drift(coastline, self.grid.sediment, dt)
        self.grid.sediment += drift
        
        # 고도 동기화
        self.grid.update_elevation()
        
        return {
            'erosion': erosion,
            'drift': drift
        }
