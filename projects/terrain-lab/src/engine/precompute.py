"""
Geo-Lab AI: 프리컴퓨팅 + 캐싱 시스템
시뮬레이션을 미리 돌려놓고 슬라이더로 탐색
"""
import numpy as np
import pickle
import hashlib
import os
from pathlib import Path
from typing import Dict, Any, Optional, Callable
import threading
from concurrent.futures import ThreadPoolExecutor


class PrecomputeCache:
    """프리컴퓨팅 결과 캐시"""
    
    def __init__(self, cache_dir: str = None):
        if cache_dir is None:
            cache_dir = Path(__file__).parent.parent / "cache"
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # 메모리 캐시
        self.memory_cache: Dict[str, Any] = {}
    
    def _get_key(self, sim_type: str, params: dict) -> str:
        """파라미터 기반 캐시 키 생성"""
        param_str = f"{sim_type}_{sorted(params.items())}"
        return hashlib.md5(param_str.encode()).hexdigest()[:16]
    
    def get(self, sim_type: str, params: dict) -> Optional[Any]:
        """캐시에서 조회"""
        key = self._get_key(sim_type, params)
        
        # 메모리 캐시 확인
        if key in self.memory_cache:
            return self.memory_cache[key]
        
        # 디스크 캐시 확인
        cache_file = self.cache_dir / f"{key}.pkl"
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    data = pickle.load(f)
                self.memory_cache[key] = data
                return data
            except:
                pass
        
        return None
    
    def set(self, sim_type: str, params: dict, data: Any):
        """캐시에 저장"""
        key = self._get_key(sim_type, params)
        
        # 메모리 캐시
        self.memory_cache[key] = data
        
        # 디스크 캐시
        cache_file = self.cache_dir / f"{key}.pkl"
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(data, f)
        except:
            pass
    
    def get_or_compute(self, sim_type: str, params: dict, 
                       compute_fn: Callable, force_recompute: bool = False) -> Any:
        """캐시 또는 계산"""
        if not force_recompute:
            cached = self.get(sim_type, params)
            if cached is not None:
                return cached
        
        # 계산
        result = compute_fn()
        self.set(sim_type, params, result)
        return result


class SimulationManager:
    """시뮬레이션 매니저
    
    파라미터별 시뮬레이션을 백그라운드에서 프리컴퓨팅하고
    UI에서는 캐시된 결과를 조회
    """
    
    def __init__(self):
        self.cache = PrecomputeCache()
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.computing: Dict[str, bool] = {}
    
    def get_v_valley(self, rock_hardness: float = 0.5, 
                     K: float = 1e-5,
                     max_time: int = 10000) -> Dict:
        """V자곡 시뮬레이션 결과"""
        from engine.physics_engine import VValleySimulation
        
        # 파라미터 양자화 (캐시 효율)
        rock_hardness = round(rock_hardness, 1)
        K = round(K, 6)
        
        params = {
            'rock_hardness': rock_hardness,
            'K': K,
            'max_time': max_time
        }
        
        def compute():
            sim = VValleySimulation(width=100, height=100)
            sim.erosion.K = K
            sim.initialize_terrain(rock_hardness=rock_hardness)
            history = sim.run(max_time, save_interval=max_time // 100)
            
            # 각 스냅샷의 단면과 깊이 저장
            cross_sections = []
            depths = []
            for elev in history:
                temp_sim = VValleySimulation()
                temp_sim.terrain.elevation = elev
                x, z = temp_sim.get_cross_section()
                depth = temp_sim.measure_valley_depth()
                cross_sections.append((x, z))
                depths.append(depth)
            
            return {
                'history': history,
                'cross_sections': cross_sections,
                'depths': depths,
                'n_frames': len(history)
            }
        
        return self.cache.get_or_compute('v_valley', params, compute)
    
    def get_meander(self, initial_sinuosity: float = 1.3,
                    max_time: int = 10000) -> Dict:
        """곡류 시뮬레이션 결과"""
        from engine.meander_physics import MeanderSimulation
        
        initial_sinuosity = round(initial_sinuosity, 1)
        
        params = {
            'initial_sinuosity': initial_sinuosity,
            'max_time': max_time
        }
        
        def compute():
            sim = MeanderSimulation(initial_sinuosity=initial_sinuosity)
            history = sim.run(max_time, save_interval=max_time // 100)
            
            # 굴곡도 히스토리
            sinuosities = []
            for x, y in history:
                temp_channel = type(sim.channel)(x=x, y=y)
                sinuosities.append(temp_channel.calculate_sinuosity())
            
            return {
                'history': history,
                'oxbow_lakes': sim.oxbow_lakes,
                'sinuosities': sinuosities,
                'n_frames': len(history)
            }
        
        return self.cache.get_or_compute('meander', params, compute)
    
    def get_delta(self, river_energy: float = 60,
                  wave_energy: float = 25,
                  tidal_energy: float = 15,
                  max_time: int = 10000) -> Dict:
        """삼각주 시뮬레이션 결과"""
        from engine.delta_physics import DeltaSimulation
        
        # 정규화
        total = river_energy + wave_energy + tidal_energy + 0.01
        river_energy = round(river_energy / total, 2)
        wave_energy = round(wave_energy / total, 2)
        tidal_energy = round(tidal_energy / total, 2)
        
        params = {
            'river_energy': river_energy,
            'wave_energy': wave_energy,
            'tidal_energy': tidal_energy,
            'max_time': max_time
        }
        
        def compute():
            sim = DeltaSimulation()
            sim.set_energy_balance(river_energy, wave_energy, tidal_energy)
            history = sim.run(max_time, save_interval=max_time // 100)
            
            return {
                'history': history,
                'delta_type': sim.get_delta_type().value,
                'delta_area': sim.get_delta_area(),
                'n_frames': len(history)
            }
        
        return self.cache.get_or_compute('delta', params, compute)
    
    def precompute_common_scenarios(self):
        """자주 사용되는 시나리오 미리 계산"""
        scenarios = [
            # V자곡
            {'type': 'v_valley', 'rock_hardness': 0.3, 'K': 1e-5},
            {'type': 'v_valley', 'rock_hardness': 0.5, 'K': 1e-5},
            {'type': 'v_valley', 'rock_hardness': 0.7, 'K': 1e-5},
            # 곡류
            {'type': 'meander', 'initial_sinuosity': 1.2},
            {'type': 'meander', 'initial_sinuosity': 1.5},
            # 삼각주
            {'type': 'delta', 'river': 0.7, 'wave': 0.2, 'tidal': 0.1},
            {'type': 'delta', 'river': 0.3, 'wave': 0.5, 'tidal': 0.2},
            {'type': 'delta', 'river': 0.2, 'wave': 0.2, 'tidal': 0.6},
        ]
        
        for scenario in scenarios:
            if scenario['type'] == 'v_valley':
                self.executor.submit(
                    self.get_v_valley,
                    rock_hardness=scenario['rock_hardness'],
                    K=scenario['K']
                )
            elif scenario['type'] == 'meander':
                self.executor.submit(
                    self.get_meander,
                    initial_sinuosity=scenario['initial_sinuosity']
                )
            elif scenario['type'] == 'delta':
                self.executor.submit(
                    self.get_delta,
                    river_energy=scenario['river'],
                    wave_energy=scenario['wave'],
                    tidal_energy=scenario['tidal']
                )


# 글로벌 인스턴스
_manager = None

def get_simulation_manager() -> SimulationManager:
    global _manager
    if _manager is None:
        _manager = SimulationManager()
    return _manager
