"""
지형 분석 엔진 (Terrain Analysis Engine)

대학 연구용 지형 분석 도구 모음
- 종/횡단면 프로파일
- Hypsometric Curve
- 사면 경사 분석
- 배수 네트워크 분석
"""
import numpy as np
from typing import Tuple, Dict, List, Optional
from dataclasses import dataclass


@dataclass
class ProfileResult:
    """프로파일 분석 결과"""
    distance: np.ndarray  # 거리 (m)
    elevation: np.ndarray  # 고도 (m)
    slope: np.ndarray  # 경사도 (degrees)
    points: List[Tuple[int, int]]  # 샘플 포인트 좌표


@dataclass
class HypsometricResult:
    """Hypsometric 분석 결과"""
    relative_area: np.ndarray  # a/A (0~1)
    relative_elevation: np.ndarray  # h/H (0~1)
    hypsometric_integral: float  # HI 값 (0~1)
    stage: str  # "Young", "Mature", "Old"


def extract_profile(
    elevation: np.ndarray,
    start: Tuple[int, int],
    end: Tuple[int, int],
    num_samples: int = 100,
    cell_size: float = 1.0
) -> ProfileResult:
    """
    두 점 사이의 고도 프로파일 추출
    
    Args:
        elevation: 고도 배열
        start: 시작점 (row, col)
        end: 끝점 (row, col)
        num_samples: 샘플 개수
        cell_size: 셀 크기 (m)
    
    Returns:
        ProfileResult: 프로파일 분석 결과
    """
    # 샘플 포인트 생성 (선형 보간)
    rows = np.linspace(start[0], end[0], num_samples).astype(int)
    cols = np.linspace(start[1], end[1], num_samples).astype(int)
    
    # 경계 체크
    h, w = elevation.shape
    rows = np.clip(rows, 0, h - 1)
    cols = np.clip(cols, 0, w - 1)
    
    # 고도 추출
    elevations = elevation[rows, cols]
    
    # 거리 계산
    total_dist = np.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2) * cell_size
    distances = np.linspace(0, total_dist, num_samples)
    
    # 경사도 계산 (중앙 차분)
    slopes = np.zeros(num_samples)
    for i in range(1, num_samples - 1):
        dz = elevations[i + 1] - elevations[i - 1]
        dx = distances[i + 1] - distances[i - 1]
        if dx > 0:
            slopes[i] = np.degrees(np.arctan(dz / dx))
    slopes[0] = slopes[1]
    slopes[-1] = slopes[-2]
    
    points = [(int(r), int(c)) for r, c in zip(rows, cols)]
    
    return ProfileResult(
        distance=distances,
        elevation=elevations,
        slope=slopes,
        points=points
    )


def extract_cross_section(
    elevation: np.ndarray,
    row: int,
    cell_size: float = 1.0
) -> ProfileResult:
    """횡단면 추출 (특정 row의 전체 너비)"""
    h, w = elevation.shape
    row = np.clip(row, 0, h - 1)
    
    return extract_profile(
        elevation,
        start=(row, 0),
        end=(row, w - 1),
        num_samples=w,
        cell_size=cell_size
    )


def extract_longitudinal(
    elevation: np.ndarray,
    col: int,
    cell_size: float = 1.0
) -> ProfileResult:
    """종단면 추출 (특정 col의 전체 길이)"""
    h, w = elevation.shape
    col = np.clip(col, 0, w - 1)
    
    return extract_profile(
        elevation,
        start=(0, col),
        end=(h - 1, col),
        num_samples=h,
        cell_size=cell_size
    )


def calculate_hypsometric_curve(
    elevation: np.ndarray,
    num_bins: int = 50
) -> HypsometricResult:
    """
    Hypsometric Curve 계산
    
    침식 단계 판단:
    - HI > 0.6: Young (유년기) - 침식 초기
    - 0.35 < HI < 0.6: Mature (장년기) - 평형 상태
    - HI < 0.35: Old (노년기) - 침식 후기
    
    Args:
        elevation: 고도 배열
        num_bins: 고도 구간 개수
    
    Returns:
        HypsometricResult: Hypsometric 분석 결과
    """
    # 유효 데이터만 사용
    valid_elev = elevation[~np.isnan(elevation)]
    
    if len(valid_elev) == 0:
        return HypsometricResult(
            relative_area=np.array([0, 1]),
            relative_elevation=np.array([1, 0]),
            hypsometric_integral=0.5,
            stage="Unknown"
        )
    
    z_min = np.min(valid_elev)
    z_max = np.max(valid_elev)
    z_range = z_max - z_min
    
    if z_range == 0:
        return HypsometricResult(
            relative_area=np.array([0, 1]),
            relative_elevation=np.array([0.5, 0.5]),
            hypsometric_integral=0.5,
            stage="Flat"
        )
    
    # 고도 구간별 누적 면적 계산
    thresholds = np.linspace(z_min, z_max, num_bins + 1)
    total_area = len(valid_elev)
    
    relative_areas = []
    relative_elevations = []
    
    for threshold in thresholds:
        # 이 고도 이상인 면적 비율
        area_above = np.sum(valid_elev >= threshold) / total_area
        relative_areas.append(area_above)
        
        # 상대 고도
        rel_elev = (threshold - z_min) / z_range
        relative_elevations.append(rel_elev)
    
    relative_areas = np.array(relative_areas)
    relative_elevations = np.array(relative_elevations)
    
    # Hypsometric Integral (곡선 아래 면적)
    hi = np.trapz(relative_elevations, relative_areas)
    hi = abs(hi)  # 적분 방향에 따라 부호 정규화
    
    # 침식 단계 판단
    if hi > 0.6:
        stage = "Young (유년기)"
    elif hi > 0.35:
        stage = "Mature (장년기)"
    else:
        stage = "Old (노년기)"
    
    return HypsometricResult(
        relative_area=relative_areas,
        relative_elevation=relative_elevations,
        hypsometric_integral=hi,
        stage=stage
    )


def calculate_slope_distribution(
    elevation: np.ndarray,
    cell_size: float = 1.0,
    num_bins: int = 36
) -> Dict:
    """
    사면 경사 분포 계산
    
    Args:
        elevation: 고도 배열
        cell_size: 셀 크기 (m)
        num_bins: 히스토그램 구간 수
    
    Returns:
        dict: 경사도 통계 및 히스토그램 데이터
    """
    # 경사도 계산 (Sobel 연산자 사용)
    dy, dx = np.gradient(elevation, cell_size)
    slope_rad = np.arctan(np.sqrt(dx**2 + dy**2))
    slope_deg = np.degrees(slope_rad)
    
    # 유효 데이터
    valid_slope = slope_deg[~np.isnan(slope_deg)]
    
    # 히스토그램
    hist, bin_edges = np.histogram(valid_slope, bins=num_bins, range=(0, 90))
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    
    return {
        'slope_grid': slope_deg,
        'histogram': {
            'counts': hist,
            'bin_centers': bin_centers,
            'bin_edges': bin_edges
        },
        'statistics': {
            'mean': float(np.mean(valid_slope)),
            'std': float(np.std(valid_slope)),
            'min': float(np.min(valid_slope)),
            'max': float(np.max(valid_slope)),
            'median': float(np.median(valid_slope))
        }
    }


def calculate_relief_ratio(elevation: np.ndarray) -> float:
    """
    기복비 (Relief Ratio) 계산
    
    RR = H / L
    H: 최대 기복량 (max - min)
    L: 유역 최대 길이
    """
    h, w = elevation.shape
    max_length = np.sqrt(h**2 + w**2)
    relief = np.nanmax(elevation) - np.nanmin(elevation)
    
    return relief / max_length if max_length > 0 else 0


def calculate_curvature(
    elevation: np.ndarray,
    cell_size: float = 1.0
) -> Dict[str, np.ndarray]:
    """
    곡률 (Curvature) 계산
    
    - Profile Curvature: 경사 방향 곡률 (흐름 가속/감속)
    - Plan Curvature: 등고선 방향 곡률 (흐름 수렴/발산)
    
    양수: 볼록 (Convex)
    음수: 오목 (Concave)
    """
    # 1차 도함수
    fy, fx = np.gradient(elevation, cell_size)
    
    # 2차 도함수
    fyy, fyx = np.gradient(fy, cell_size)
    fxy, fxx = np.gradient(fx, cell_size)
    
    # 경사 크기
    p = fx
    q = fy
    p2 = p * p
    q2 = q * q
    pq = p * q
    denom = p2 + q2
    
    # Profile Curvature (경사 방향)
    with np.errstate(divide='ignore', invalid='ignore'):
        profile_curv = -(fxx * p2 + 2 * fxy * pq + fyy * q2) / (denom * np.sqrt(denom + 1))
        profile_curv = np.nan_to_num(profile_curv, nan=0.0, posinf=0.0, neginf=0.0)
    
    # Plan Curvature (등고선 방향)
    with np.errstate(divide='ignore', invalid='ignore'):
        plan_curv = -(fxx * q2 - 2 * fxy * pq + fyy * p2) / (denom ** 1.5)
        plan_curv = np.nan_to_num(plan_curv, nan=0.0, posinf=0.0, neginf=0.0)
    
    return {
        'profile': profile_curv,
        'plan': plan_curv,
        'total': profile_curv + plan_curv
    }


def compare_elevations(
    elev1: np.ndarray,
    elev2: np.ndarray,
    label1: str = "DEM 1",
    label2: str = "DEM 2"
) -> Dict:
    """
    두 고도 배열 비교
    
    Args:
        elev1: 첫 번째 고도 배열 (예: 시뮬레이션)
        elev2: 두 번째 고도 배열 (예: 실측 DEM)
    
    Returns:
        dict: 차이 분석 결과
    """
    # 크기가 다르면 리샘플링
    if elev1.shape != elev2.shape:
        from scipy.ndimage import zoom
        zoom_factors = (elev1.shape[0] / elev2.shape[0],
                       elev1.shape[1] / elev2.shape[1])
        elev2 = zoom(elev2, zoom_factors, order=1)
    
    diff = elev1 - elev2
    
    return {
        'difference_grid': diff,
        'statistics': {
            'mean_diff': float(np.nanmean(diff)),
            'std_diff': float(np.nanstd(diff)),
            'rmse': float(np.sqrt(np.nanmean(diff**2))),
            'mae': float(np.nanmean(np.abs(diff))),
            'max_diff': float(np.nanmax(diff)),
            'min_diff': float(np.nanmin(diff)),
            'correlation': float(np.corrcoef(elev1.flatten(), elev2.flatten())[0, 1])
        },
        'labels': (label1, label2)
    }
