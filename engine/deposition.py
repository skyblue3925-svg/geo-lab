"""
Geo-Lab AI Engine: 퇴적 로직
유속 감소에 따른 입자별 퇴적 구현
"""
import numpy as np
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import Terrain, Water


def settling_deposition(terrain: 'Terrain', water: 'Water',
                        sediment_load: np.ndarray,
                        critical_velocity: float = 0.5,
                        dt: float = 1.0) -> tuple:
    """
    유속 감소에 따른 퇴적 (Stokes' Law 기반)
    유속이 임계값 이하로 떨어지면 퇴적물이 쌓임
    
    Parameters:
    -----------
    terrain : Terrain
        지형 객체
    water : Water
        수문 객체
    sediment_load : np.ndarray
        현재 운반 중인 퇴적물량
    critical_velocity : float
        퇴적이 시작되는 임계 유속
    dt : float
        시간 단위
    
    Returns:
    --------
    deposition_amount : np.ndarray
        퇴적량
    remaining_sediment : np.ndarray
        남은 퇴적물량
    """
    # 유속이 낮은 곳에서 퇴적
    velocity_ratio = water.velocity / (critical_velocity + 0.01)
    deposition_rate = np.maximum(0, 1 - velocity_ratio)
    
    deposition_amount = sediment_load * deposition_rate * dt
    remaining_sediment = sediment_load - deposition_amount
    
    return deposition_amount, np.maximum(remaining_sediment, 0)


def alluvial_fan_deposition(terrain: 'Terrain', water: 'Water',
                            sediment_load: np.ndarray,
                            slope_threshold: float = 0.1,
                            dt: float = 1.0) -> np.ndarray:
    """
    선상지(Alluvial Fan) 퇴적
    급격한 경사 변화 지점(산지→평지)에서 부채꼴 퇴적
    
    Returns:
    --------
    deposition_amount : np.ndarray
    """
    slope = terrain.get_slope()
    
    # 경사 변화율 계산
    slope_change = np.gradient(slope, axis=0) + np.gradient(slope, axis=1)
    
    # 경사가 급격히 줄어드는 곳(음의 변화율)에서 퇴적
    fan_zone = slope_change < -slope_threshold
    
    deposition = np.zeros_like(sediment_load)
    deposition[fan_zone] = sediment_load[fan_zone] * 0.8 * dt
    
    return deposition


def levee_backswamp_deposition(terrain: 'Terrain', water: 'Water',
                                flood_level: float = 1.0,
                                dt: float = 1.0) -> tuple:
    """
    자연제방(Levee) & 배후습지(Backswamp) 퇴적
    홍수 시 하천 가까이에 굵은 입자, 멀리에 미립 입자 퇴적
    
    Returns:
    --------
    levee_deposition : np.ndarray
        자연제방 퇴적량 (모래 - 두꺼움)
    backswamp_deposition : np.ndarray  
        배후습지 퇴적량 (점토 - 얇음)
    """
    h, w = terrain.height, terrain.width
    
    # 하천 위치 (높은 유량)
    channel_mask = water.discharge > np.percentile(water.discharge, 80)
    
    levee = np.zeros((h, w))
    backswamp = np.zeros((h, w))
    
    # 하천으로부터의 거리 계산 (간단한 확산)
    from scipy.ndimage import distance_transform_edt
    if np.any(channel_mask):
        distance = distance_transform_edt(~channel_mask)
        
        # 자연제방: 하천 바로 옆 (2-5셀)
        levee_zone = (distance > 1) & (distance < 5)
        levee[levee_zone] = flood_level * 0.3 * (5 - distance[levee_zone]) / 4 * dt
        
        # 배후습지: 더 먼 곳 (5-15셀)
        backswamp_zone = (distance >= 5) & (distance < 15)
        backswamp[backswamp_zone] = flood_level * 0.05 * dt
    
    return levee, backswamp


def delta_deposition(terrain: 'Terrain', water: 'Water',
                     river_energy: float = 1.0,
                     wave_energy: float = 0.5,
                     tidal_energy: float = 0.3,
                     sea_level: float = 0.0,
                     dt: float = 1.0) -> np.ndarray:
    """
    삼각주(Delta) 퇴적
    3가지 에너지(하천/파랑/조류) 균형에 따라 형태 결정
    
    - 하천 우세: 조족상(Bird's foot) - 미시시피형
    - 파랑 우세: 원호상(Arcuate) - 나일형
    - 조류 우세: 첨각상(Cuspate) - 티베르형
    
    Returns:
    --------
    deposition_amount : np.ndarray
    """
    h, w = terrain.height, terrain.width
    deposition = np.zeros((h, w))
    
    # 해수면 근처 (하구)
    estuary_zone = (terrain.elevation > sea_level - 5) & (terrain.elevation < sea_level + 10)
    channel_mask = water.discharge > np.percentile(water.discharge, 70)
    delta_zone = estuary_zone & channel_mask
    
    if not np.any(delta_zone):
        return deposition
    
    # 에너지 비율 정규화
    total_energy = river_energy + wave_energy + tidal_energy + 0.01
    r_ratio = river_energy / total_energy
    w_ratio = wave_energy / total_energy
    t_ratio = tidal_energy / total_energy
    
    # 하천 우세: 길게 뻗어나가는 패턴
    if r_ratio > 0.5:
        # 흐름 방향으로 퇴적물 확장
        deposition[delta_zone] = water.discharge[delta_zone] * r_ratio * 0.1 * dt
    
    # 파랑 우세: 넓게 퍼지는 원호 패턴
    elif w_ratio > 0.4:
        # 좌우로 퍼지게
        from scipy.ndimage import gaussian_filter
        base = np.zeros((h, w))
        base[delta_zone] = water.discharge[delta_zone] * 0.1
        deposition = gaussian_filter(base, sigma=3) * w_ratio * dt
    
    # 조류 우세: 작은 섬 형태
    else:
        # 좁은 영역에 집중
        deposition[delta_zone] = water.discharge[delta_zone] * t_ratio * 0.05 * dt
    
    return deposition


def apply_deposition(terrain: 'Terrain', deposition_amount: np.ndarray):
    """
    지형에 퇴적 적용
    """
    terrain.elevation += deposition_amount
