"""
Geo-Lab AI Engine: 침식 로직
Stream Power Law 기반 하방/측방 침식 구현
"""
import numpy as np
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import Terrain, Water


def vertical_erosion(terrain: 'Terrain', water: 'Water', 
                     k_erosion: float = 0.0001,
                     m_exponent: float = 0.5,
                     n_exponent: float = 1.0,
                     dt: float = 1.0) -> np.ndarray:
    """
    하방 침식 (Vertical/Downcutting Erosion)
    Stream Power Law: E = K * A^m * S^n
    
    Parameters:
    -----------
    terrain : Terrain
        지형 객체
    water : Water
        수문 객체
    k_erosion : float
        침식 계수 (암석 경도의 역수)
    m_exponent : float
        유량 지수 (보통 0.4-0.6)
    n_exponent : float
        경사 지수 (보통 1.0)
    dt : float
        시간 단위 (년)
    
    Returns:
    --------
    erosion_amount : np.ndarray
        각 셀의 침식량 (m)
    """
    # 경사 계산
    slope = terrain.get_slope()
    
    # Stream Power Law
    # E = K * Q^m * S^n
    # 암석 경도로 K 조절 (경도가 높으면 침식이 적음)
    effective_k = k_erosion * (1 - terrain.rock_hardness * 0.9)
    
    erosion_rate = effective_k * np.power(water.discharge + 0.1, m_exponent) * np.power(slope + 0.001, n_exponent)
    
    erosion_amount = erosion_rate * dt
    
    # 침식량 제한 (너무 급격한 변화 방지)
    max_erosion = 10.0  # 최대 10m/yr
    erosion_amount = np.clip(erosion_amount, 0, max_erosion)
    
    return erosion_amount


def lateral_erosion(terrain: 'Terrain', water: 'Water',
                    k_lateral: float = 0.00005,
                    curvature_factor: float = 1.0,
                    dt: float = 1.0) -> np.ndarray:
    """
    측방 침식 (Lateral Erosion)
    곡류 하천에서 바깥쪽(공격사면)을 깎음
    
    Parameters:
    -----------
    terrain : Terrain
        지형 객체
    water : Water
        수문 객체
    k_lateral : float
        측방 침식 계수
    curvature_factor : float
        곡률 강조 계수
    dt : float
        시간 단위 (년)
    
    Returns:
    --------
    erosion_amount : np.ndarray
        각 셀의 침식량 (m)
    """
    h, w = terrain.height, terrain.width
    erosion = np.zeros((h, w))
    
    # 유로 곡률 계산 (흐름 방향의 2차 미분)
    flow_x, flow_y = water.flow_x, water.flow_y
    
    # 곡률 근사: 흐름 방향의 변화율
    curvature_x = np.gradient(flow_x, axis=1)
    curvature_y = np.gradient(flow_y, axis=0)
    curvature = np.sqrt(curvature_x**2 + curvature_y**2)
    
    # 측방 침식 = 유량 * 유속 * 곡률
    # 곡률이 큰 곳(급커브) = 바깥쪽 침식 강함
    erosion = k_lateral * water.discharge * water.velocity * curvature * curvature_factor * dt
    
    # 하천이 있는 곳에서만 침식 (유량 임계값)
    channel_mask = water.discharge > 0.1
    erosion = erosion * channel_mask
    
    return np.clip(erosion, 0, 5.0)


def headward_erosion(terrain: 'Terrain', water: 'Water',
                     k_headward: float = 0.0002,
                     dt: float = 1.0) -> np.ndarray:
    """
    두부 침식 (Headward Erosion)
    하천의 상류 끝이 점점 뒤로 물러남
    폭포, 협곡 형성의 핵심 메커니즘
    
    Returns:
    --------
    erosion_amount : np.ndarray
        각 셀의 침식량 (m)
    """
    h, w = terrain.height, terrain.width
    erosion = np.zeros((h, w))
    
    # 급경사 지점(Knickpoint) 찾기
    slope = terrain.get_slope()
    steep_mask = slope > np.percentile(slope[slope > 0], 90)  # 상위 10% 급경사
    
    # 급경사 + 유량이 있는 곳에서 두부 침식 발생
    channel_mask = water.discharge > 0.5
    knickpoint_mask = steep_mask & channel_mask
    
    # 상류 방향으로 침식 확장
    erosion[knickpoint_mask] = k_headward * water.discharge[knickpoint_mask] * dt
    
    return np.clip(erosion, 0, 2.0)


def apply_erosion(terrain: 'Terrain', erosion_amount: np.ndarray,
                  min_elevation: float = 0.0):
    """
    지형에 침식 적용
    
    Parameters:
    -----------
    terrain : Terrain
        수정할 지형 객체
    erosion_amount : np.ndarray
        침식량 배열
    min_elevation : float
        최소 고도 (해수면)
    """
    terrain.elevation -= erosion_amount
    terrain.elevation = np.maximum(terrain.elevation, min_elevation)


def mass_wasting(terrain: 'Terrain', 
                 critical_slope: float = 0.7,  # ~35도
                 transfer_rate: float = 0.3) -> np.ndarray:
    """
    사면 붕괴 (Mass Wasting)
    V자곡 형성 시 양옆 사면이 무너지는 과정
    
    Returns:
    --------
    elevation_change : np.ndarray
        고도 변화량 (높은 곳 -, 낮은 곳 +)
    """
    h, w = terrain.height, terrain.width
    change = np.zeros((h, w))
    
    slope = terrain.get_slope()
    
    # 임계 경사 초과 지점에서 물질 이동
    unstable = slope > critical_slope
    
    for y in range(1, h-1):
        for x in range(1, w-1):
            if unstable[y, x]:
                # 주변으로 물질 분배
                elev = terrain.elevation[y, x]
                neighbors = [
                    (y-1, x), (y+1, x), (y, x-1), (y, x+1)
                ]
                
                for ny, nx in neighbors:
                    if terrain.elevation[ny, nx] < elev:
                        transfer = (elev - terrain.elevation[ny, nx]) * transfer_rate * 0.25
                        change[y, x] -= transfer
                        change[ny, nx] += transfer
    
    return change
