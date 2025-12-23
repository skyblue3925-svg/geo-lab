"""
🌧️ Climate System - 기후 시스템 모듈
강우 이벤트, 기후 변화, 해수면 변동
"""
import numpy as np
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

@dataclass
class ClimateState:
    """기후 상태"""
    temperature: float = 15.0  # 평균 기온 (°C)
    precipitation: float = 1.0  # 연 강수량 배율
    sea_level: float = 0.0  # 해수면 (m)
    drought_intensity: float = 0.0  # 가뭄 강도 (0-1)
    storm_intensity: float = 0.0  # 폭풍 강도 (0-1)

class ClimateSystem:
    """
    기후 시스템 관리자
    
    - 강우 이벤트 (폭우/가뭄)
    - 기후 변화 시나리오
    - 해수면 변동 (빙하기)
    """
    
    def __init__(self, grid_size: int):
        self.grid_size = grid_size
        self.state = ClimateState()
        self.time = 0.0
        
        # 강우 패턴 그리드
        self.rainfall_grid = np.ones((grid_size, grid_size))
        
        # 이벤트 히스토리
        self.event_history = []
    
    # ========== 강우 이벤트 ==========
    def rainfall_event(self, event_type: str = 'normal', 
                       duration: float = 1.0, 
                       intensity: float = 1.0) -> np.ndarray:
        """
        강우 이벤트 시뮬레이션
        
        Args:
            event_type: 'normal', 'storm', 'drought', 'monsoon'
            duration: 이벤트 지속 시간 (년)
            intensity: 강도 배율
            
        Returns:
            강우 그리드 (배율)
        """
        if event_type == 'storm':
            # 폭풍우: 국지적 집중 호우
            self.state.storm_intensity = intensity
            center = (np.random.randint(self.grid_size), 
                     np.random.randint(self.grid_size))
            y, x = np.ogrid[:self.grid_size, :self.grid_size]
            dist = np.sqrt((x - center[1])**2 + (y - center[0])**2)
            storm_pattern = np.exp(-dist / (self.grid_size * 0.3)) * intensity * 5
            self.rainfall_grid = 1.0 + storm_pattern
            
        elif event_type == 'drought':
            # 가뭄: 전체적 강수량 감소
            self.state.drought_intensity = intensity
            self.rainfall_grid = np.ones((self.grid_size, self.grid_size)) * (1 - 0.7 * intensity)
            
        elif event_type == 'monsoon':
            # 몬순: 방향성 있는 강한 비
            gradient = np.linspace(0.5, 2.0 * intensity, self.grid_size)
            self.rainfall_grid = np.tile(gradient, (self.grid_size, 1))
            
        else:
            # 정상
            self.rainfall_grid = np.ones((self.grid_size, self.grid_size))
            self.state.storm_intensity = 0
            self.state.drought_intensity = 0
        
        self.event_history.append({
            'type': event_type,
            'time': self.time,
            'duration': duration,
            'intensity': intensity
        })
        
        return self.rainfall_grid
    
    # ========== 기후 변화 ==========
    def climate_change(self, scenario: str = 'rcp45', 
                       years: float = 100.0) -> Dict[str, float]:
        """
        기후 변화 시나리오 적용
        
        Args:
            scenario: 'rcp26', 'rcp45', 'rcp60', 'rcp85', 'ice_age'
            years: 경과 년수
            
        Returns:
            변화된 기후 상태
        """
        scenarios = {
            'rcp26': {'temp_rate': 0.01, 'precip_rate': 0.002, 'sea_rate': 0.003},
            'rcp45': {'temp_rate': 0.02, 'precip_rate': 0.003, 'sea_rate': 0.005},
            'rcp60': {'temp_rate': 0.03, 'precip_rate': 0.004, 'sea_rate': 0.008},
            'rcp85': {'temp_rate': 0.05, 'precip_rate': 0.005, 'sea_rate': 0.012},
            'ice_age': {'temp_rate': -0.03, 'precip_rate': -0.002, 'sea_rate': -0.01}
        }
        
        rates = scenarios.get(scenario, scenarios['rcp45'])
        
        self.state.temperature += rates['temp_rate'] * years
        self.state.precipitation += rates['precip_rate'] * years
        self.state.sea_level += rates['sea_rate'] * years
        
        return {
            'temperature': self.state.temperature,
            'precipitation': self.state.precipitation,
            'sea_level': self.state.sea_level
        }
    
    # ========== 해수면 변동 ==========
    def sea_level_change(self, mode: str = 'glacial_cycle',
                         amplitude: float = 100.0,
                         period: float = 100000.0) -> float:
        """
        해수면 변동 시뮬레이션
        
        Args:
            mode: 'glacial_cycle', 'rising', 'falling', 'stable'
            amplitude: 변동 폭 (m)
            period: 주기 (년)
            
        Returns:
            현재 해수면 (m)
        """
        if mode == 'glacial_cycle':
            # 밀란코비치 사이클 근사
            self.state.sea_level = amplitude * np.sin(2 * np.pi * self.time / period)
        elif mode == 'rising':
            self.state.sea_level += amplitude / 10000  # 연간 상승
        elif mode == 'falling':
            self.state.sea_level -= amplitude / 10000  # 연간 하강
        # stable: 변화 없음
        
        return self.state.sea_level
    
    def step(self, dt: float = 1.0):
        """시간 진행"""
        self.time += dt
    
    def get_effective_precipitation(self) -> np.ndarray:
        """현재 유효 강수량 그리드 반환"""
        return self.rainfall_grid * self.state.precipitation
