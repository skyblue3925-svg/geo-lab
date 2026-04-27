import numpy as np
from dataclasses import dataclass
from .grid import WorldGrid
from .fluids import HydroKernel
from .erosion_process import ErosionProcess
from .lateral_erosion import LateralErosionKernel
from .mass_movement import MassMovementKernel
from .climate import ClimateKernel
from .wave import WaveKernel
from .glacier import GlacierKernel
from .wind import WindKernel

class EarthSystem:
    """
    Project Genesis: Unified Earth System Engine
    
    통합 지구 시스템 엔진
    - 기후(Climate) -> 수문(Hydro) -> 지형(Erosion/Tectonics) 상호작용을
      단일 루프(step) 내에서 처리합니다.
    """
    def __init__(self, grid: WorldGrid):
        self.grid = grid
        self.time = 0.0
        
        # Core Kernels
        self.hydro = HydroKernel(self.grid)
        self.erosion = ErosionProcess(self.grid)
        self.lateral = LateralErosionKernel(self.grid, k=0.01)
        self.mass_movement = MassMovementKernel(self.grid, friction_angle=35.0)
        self.climate = ClimateKernel(self.grid)
        
        # Phase 2 Kernels (Optional, enabled via settings)
        self.wave = WaveKernel(self.grid)
        self.glacier = GlacierKernel(self.grid)
        self.wind = WindKernel(self.grid)
        
        # State History (Optional for analysis)
        self.history = []

    def step(self, dt: float = 1.0, settings: dict = None):
        """
        시스템 1단계 진행 (Time Step)
        
        Process Chain:
        1. Tectonics (Endogenous): Uplift, subsidence based on scenario settings
        2. Climate (Exogenous): Generate precipitation
        3. Hydro (Physics): Route flow, calculate discharge/depth
        4. Morphodynamics (Response): Erode, transport, deposit
        """
        if settings is None:
            settings = {}
            
        # 1. Tectonics (지구조 운동)
        # Simple vertical uplift logic if provided
        uplift_rate = settings.get('uplift_rate', 0.0)
        tile_uplift = settings.get('uplift_mask', None)
        
        if uplift_rate > 0:
            if tile_uplift is not None:
                self.grid.apply_uplift(tile_uplift * uplift_rate, dt)
            else:
                self.grid.apply_uplift(uplift_rate, dt)
                
        # 2. Climate (기후)
        # Generate precipitation map
        # Default: Uniform rain + randomness
        base_precip = settings.get('precipitation', 0.01)
        precip_map = np.ones((self.grid.height, self.grid.width)) * base_precip
        
        # Apply rain source if specified (e.g., river mouth)
        rain_source = settings.get('rain_source', None) # (y, x, radius, amount)
        if rain_source:
             y, x, r, amount = rain_source
             # Simplified box source for speed
             y_min, y_max = max(0, int(y-r)), min(self.grid.height, int(y+r+1))
             x_min, x_max = max(0, int(x-r)), min(self.grid.width, int(x+r+1))
             precip_map[y_min:y_max, x_min:x_max] += amount
        
        # 3. Hydro (수문)
        # Route flow based on current topography + precip
        discharge = self.hydro.route_flow_d8(precipitation=precip_map)
        
        # Update grid state
        self.grid.discharge = discharge
        self.grid.water_depth = self.hydro.calculate_water_depth(discharge)
        
        # 4. Erosion / Deposition (지형 변화)
        # Using the ErosionKernel (ErosionProcess wrapper)
        # Need to update K, m, n parameters dynamically?
        # For now, use instance defaults or allow overrides
        
        # Execute Transport & Deposition
        sediment_influx_map = None
        sediment_source = settings.get('sediment_source', None) # (y, x, radius, amount)
        if sediment_source:
             y, x, r, amount = sediment_source
             sediment_influx_map = np.zeros((self.grid.height, self.grid.width))
             y_min, y_max = max(0, int(y-r)), min(self.grid.height, int(y+r+1))
             x_min, x_max = max(0, int(x-r)), min(self.grid.width, int(x+r+1))
             sediment_influx_map[y_min:y_max, x_min:x_max] += amount
             
        self.erosion.simulate_transport(discharge, dt=dt, sediment_influx_map=sediment_influx_map)
        
        # 5. Lateral Erosion (측방 침식) - 곡류 형성
        lateral_enabled = settings.get('lateral_erosion', True)
        if lateral_enabled:
            self.lateral.step(discharge, dt=dt)
        
        # 6. Hillslope Diffusion (사면 안정화)
        diff_rate = settings.get('diffusion_rate', 0.01)
        if diff_rate > 0:
            self.erosion.hillslope_diffusion(dt=dt * diff_rate)
        
        # 7. Mass Movement (매스무브먼트) - 산사태
        mass_movement_enabled = settings.get('mass_movement', True)
        if mass_movement_enabled:
            self.mass_movement.step(dt=dt)
            
        # Update Time
        self.time += dt
        
    def get_state(self):
        """현재 시스템 상태 반환"""
        self.grid.update_elevation()
        return {
            'elevation': self.grid.elevation.copy(),
            'water_depth': self.grid.water_depth.copy(),
            'discharge': self.grid.discharge.copy(),
            'sediment': self.grid.sediment.copy(),
            'time': self.time
        }
