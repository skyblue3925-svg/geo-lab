"""
Glacier Kernel (빙하 커널)

빙하 지형 형성 프로세스
- 빙하 침식: Plucking (뜯어내기), Abrasion (마식)
- U자곡 형성
- 모레인(Moraine) 퇴적

핵심:
- 빙하 두께에 비례한 침식
- 측면보다 중앙 침식이 강함 → U자 형태
"""

import numpy as np
from .grid import WorldGrid


class GlacierKernel:
    """
    빙하 커널
    
    빙하가 존재하는 지역에서 침식과 퇴적을 시뮬레이션.
    """
    
    def __init__(self, grid: WorldGrid,
                 ice_threshold_temp: float = 0.0,  # 빙하 형성 기온 (°C)
                 K_erosion: float = 0.0001,
                 sliding_velocity: float = 10.0):  # m/year
        self.grid = grid
        self.ice_threshold = ice_threshold_temp
        self.K = K_erosion
        self.sliding_velocity = sliding_velocity
        
        # 빙하 두께 배열
        self.ice_thickness = np.zeros((grid.height, grid.width))
        
    def accumulate_ice(self, temperature: np.ndarray, 
                       precipitation: np.ndarray,
                       dt: float = 1.0):
        """
        빙하 축적
        
        기온 < 임계값인 곳에 눈/빙하 축적
        
        Args:
            temperature: 기온 배열
            precipitation: 강수량 배열
            dt: 시간 간격
        """
        h, w = self.grid.height, self.grid.width
        
        # 빙하 축적 조건: 기온 < 0°C
        cold_mask = temperature < self.ice_threshold
        
        # 축적률 = 강수량 * (기온이 낮을수록 더 많이)
        accumulation_rate = precipitation * np.clip(-temperature / 10.0, 0, 1) * 0.001
        
        # 축적
        self.ice_thickness[cold_mask] += accumulation_rate[cold_mask] * dt
        
        # 빙하 소멸 (기온 > 0°C)
        warm_mask = temperature > self.ice_threshold
        melt_rate = temperature * 0.01  # 기온당 융해율
        self.ice_thickness[warm_mask] -= np.minimum(
            melt_rate[warm_mask] * dt, 
            self.ice_thickness[warm_mask]
        )
        
        self.ice_thickness = np.maximum(self.ice_thickness, 0)
        
    def flow_ice(self, dt: float = 1.0):
        """
        빙하 흐름 (중력에 의한 하강)
        
        높은 곳에서 낮은 곳으로 빙하 이동
        """
        h, w = self.grid.height, self.grid.width
        
        slope, _ = self.grid.get_gradient()
        
        # 빙하 흐름 속도 = 기본 속도 * 경사 * 두께
        flow_speed = self.sliding_velocity * slope * np.sqrt(self.ice_thickness + 0.1)
        
        # D8 방향으로 빙하 이동 (간단한 근사)
        dr = np.array([-1, -1, -1,  0,  0,  1,  1,  1])
        dc = np.array([-1,  0,  1, -1,  1, -1,  0,  1])
        
        new_ice = self.ice_thickness.copy()
        elev = self.grid.elevation
        
        for r in range(1, h - 1):
            for c in range(1, w - 1):
                if self.ice_thickness[r, c] <= 0:
                    continue
                    
                # 가장 낮은 이웃 찾기
                min_z = elev[r, c]
                target = None
                
                for k in range(8):
                    nr, nc = r + dr[k], c + dc[k]
                    if 0 <= nr < h and 0 <= nc < w:
                        if elev[nr, nc] < min_z:
                            min_z = elev[nr, nc]
                            target = (nr, nc)
                            
                if target:
                    tr, tc = target
                    # 이동량 (속도에 비례, 최대 10%)
                    move = min(self.ice_thickness[r, c] * 0.1 * dt, self.ice_thickness[r, c])
                    new_ice[r, c] -= move
                    new_ice[tr, tc] += move
                    
        self.ice_thickness = new_ice
        
    def erode(self, dt: float = 1.0) -> np.ndarray:
        """
        빙하 침식
        
        U자곡 형성을 위한 차별 침식
        - 중앙(빙하 두꺼운 곳): 강한 침식
        - 측면: 약한 침식
        
        Returns:
            erosion: 침식량 배열
        """
        h, w = self.grid.height, self.grid.width
        
        # 빙하가 있는 곳만 침식
        glacier_mask = self.ice_thickness > 0.1
        
        erosion = np.zeros((h, w), dtype=np.float64)
        
        if not np.any(glacier_mask):
            return erosion
            
        # 침식률 = K * 두께 * 속도 * 경사
        slope, _ = self.grid.get_gradient()
        
        erosion_rate = self.K * self.ice_thickness * self.sliding_velocity * slope
        erosion[glacier_mask] = erosion_rate[glacier_mask] * dt
        
        # 침식 적용
        self.grid.bedrock -= erosion
        self.grid.update_elevation()
        
        return erosion
        
    def deposit_moraine(self, dt: float = 1.0) -> np.ndarray:
        """
        모레인 퇴적
        
        빙하 말단(thickness 급감 지점)에 퇴적
        
        Returns:
            deposition: 퇴적량 배열
        """
        h, w = self.grid.height, self.grid.width
        
        deposition = np.zeros((h, w), dtype=np.float64)
        
        # 빙하 두께 감소 지점 = 말단
        # Gradient of ice thickness
        dy, dx = np.gradient(self.ice_thickness)
        ice_gradient = np.sqrt(dx**2 + dy**2)
        
        # 말단 조건: 빙하 있고, gradient 큼
        terminal_mask = (self.ice_thickness > 0.1) & (ice_gradient > 0.1)
        
        # 퇴적량 = gradient에 비례
        deposition[terminal_mask] = ice_gradient[terminal_mask] * 0.01 * dt
        
        # 퇴적 적용
        self.grid.add_sediment(deposition)
        
        return deposition
        
    def step(self, temperature: np.ndarray = None,
             precipitation: np.ndarray = None,
             dt: float = 1.0) -> dict:
        """
        1단계 빙하 작용 실행
        
        Args:
            temperature: 기온 배열 (없으면 기본값 사용)
            precipitation: 강수량 배열
            dt: 시간 간격
            
        Returns:
            result: 빙하 상태 및 변화량
        """
        h, w = self.grid.height, self.grid.width
        
        # 기본 기온/강수
        if temperature is None:
            # 고도 기반 간단한 기온 계산
            temperature = 15.0 - (self.grid.elevation / 1000.0) * 6.5
            
        if precipitation is None:
            precipitation = np.ones((h, w)) * 1000.0  # mm/year
            
        # 1. 빙하 축적/소멸
        self.accumulate_ice(temperature, precipitation, dt)
        
        # 2. 빙하 흐름
        self.flow_ice(dt)
        
        # 3. 침식
        erosion = self.erode(dt)
        
        # 4. 모레인 퇴적
        moraine = self.deposit_moraine(dt)
        
        return {
            'ice_thickness': self.ice_thickness.copy(),
            'erosion': erosion,
            'moraine': moraine
        }
