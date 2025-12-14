"""
Climate Kernel (기후 커널)

기후 조건에 따른 강수/기온 분포 생성
- 위도 기반 강수 패턴
- 고도 기반 지형성 강수
- 기온에 따른 풍화율 조절
"""

import numpy as np
from .grid import WorldGrid


class ClimateKernel:
    """
    기후 커널
    
    강수와 기온 분포를 생성하여 다른 프로세스에 영향.
    """
    
    def __init__(self, grid: WorldGrid,
                 base_precipitation: float = 1000.0,   # mm/year
                 base_temperature: float = 15.0,       # °C
                 lapse_rate: float = 6.5):             # °C/km (고도 감률)
        self.grid = grid
        self.base_precipitation = base_precipitation
        self.base_temperature = base_temperature
        self.lapse_rate = lapse_rate
        
    def generate_precipitation(self, 
                               orographic_factor: float = 0.5,
                               latitude_effect: bool = True) -> np.ndarray:
        """
        강수 분포 생성
        
        Args:
            orographic_factor: 지형성 강수 강도 (0~1)
            latitude_effect: 위도 효과 적용 여부
            
        Returns:
            precipitation: 강수량 배열 (mm/year → m/timestep으로 변환 필요)
        """
        h, w = self.grid.height, self.grid.width
        elev = self.grid.elevation
        
        # 기본 강수 (균일)
        precip = np.ones((h, w)) * self.base_precipitation
        
        # 1. 위도 효과 (적도 > 극지방)
        if latitude_effect:
            # 그리드 Y축을 위도로 근사 (0=적도, h=극)
            # 열대 = 가장 많음, 아열대 건조, 온대 증가, 극 감소
            lat_factor = np.zeros(h)
            for r in range(h):
                # 정규화된 위도 (0~1)
                normalized_lat = r / h
                # 간단한 위도-강수 관계 (삼봉 패턴 근사)
                lat_factor[r] = 1.0 - 0.3 * abs(normalized_lat - 0.5) * 2
                
            precip *= lat_factor[:, np.newaxis]
            
        # 2. 지형성 강수 (바람받이 vs 그늘)
        if orographic_factor > 0:
            # 동쪽에서 바람이 분다고 가정
            # 고도 증가 구간 = 강수 증가 (상승 기류)
            # 고도 감소 구간 = 강수 감소 (하강 기류)
            
            # X 방향 경사
            _, dx = self.grid.get_gradient()
            
            # 음의 경사 = 동쪽으로 상승 = 강수 증가
            orographic = 1.0 + orographic_factor * (-dx) * 0.1
            orographic = np.clip(orographic, 0.2, 2.0)
            
            precip *= orographic
            
        # 3. 고도 효과 (일정 고도까지는 증가, 이후 감소)
        # 최대 강수 고도 (예: 2000m)
        optimal_elev = 2000.0
        elev_effect = 1.0 - 0.2 * np.abs(elev - optimal_elev) / optimal_elev
        elev_effect = np.clip(elev_effect, 0.3, 1.2)
        
        precip *= elev_effect
        
        return precip
        
    def get_temperature(self) -> np.ndarray:
        """
        기온 분포 생성
        
        Returns:
            temperature: 기온 배열 (°C)
        """
        h, w = self.grid.height, self.grid.width
        elev = self.grid.elevation
        
        # 기본 기온
        temp = np.ones((h, w)) * self.base_temperature
        
        # 1. 위도 효과 (적도 > 극)
        for r in range(h):
            normalized_lat = r / h
            # 적도(0.5) = 기본, 극(0, 1) = -30°C
            lat_temp_diff = 30.0 * abs(normalized_lat - 0.5) * 2
            temp[r, :] -= lat_temp_diff
            
        # 2. 고도 효과 (체감 온도 감률)
        # 해수면 기준에서 km당 lapse_rate만큼 감소
        temp -= (elev / 1000.0) * self.lapse_rate
        
        return temp
        
    def get_weathering_rate(self, temperature: np.ndarray = None) -> np.ndarray:
        """
        기온에 따른 풍화율 계산
        
        화학적 풍화: 온난 다습 → 빠름
        물리적 풍화: 동결-융해 (-10~10°C) → 빠름
        
        Args:
            temperature: 기온 배열 (없으면 생성)
            
        Returns:
            weathering_rate: 상대 풍화율 (0~1)
        """
        if temperature is None:
            temperature = self.get_temperature()
            
        h, w = self.grid.height, self.grid.width
        
        # 화학적 풍화 (온도 높을수록)
        chemical = np.clip((temperature + 10) / 40.0, 0, 1)
        
        # 물리적 풍화 (동결-융해 범위에서 최대)
        freeze_thaw = np.exp(-((temperature - 0) ** 2) / (2 * 10 ** 2))
        
        # 통합 풍화율
        weathering = chemical * 0.5 + freeze_thaw * 0.5
        
        return weathering
