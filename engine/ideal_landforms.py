"""
Ideal Landform Geometry Models (이상적 지형 기하학 모델)

교과서적인 지형 형태를 기하학적으로 생성.
물리 시뮬레이션이 아닌, 직접 수학적으로 "이상적 형태"를 그림.

- 삼각주: 부채꼴 (Sector)
- 선상지: 원뿔 (Cone)
- 곡류: S자 곡선 (Kinoshita Curve)
- U자곡: 포물선 단면
- V자곡: 삼각형 단면
- 해안 절벽: 계단형 후퇴
- 사구: 바르한 (Crescent)
"""

import numpy as np
from typing import Tuple


def create_delta(grid_size: int = 100, 
                 apex_row: float = 0.2,
                 spread_angle: float = 120.0,
                 num_channels: int = 7) -> np.ndarray:
    """
    삼각주 (Delta) - 조족상/부채꼴
    
    Args:
        grid_size: 그리드 크기
        apex_row: 정점(Apex) 위치 (0~1, 상단 기준)
        spread_angle: 퍼짐 각도 (도)
        num_channels: 분배 수로 개수
        
    Returns:
        elevation: 고도 배열
    """
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    apex_y = int(h * apex_row)
    center_x = w // 2
    
    # 배경: 바다 (음수)
    elevation[:, :] = -5.0
    
    # 육지 배경 (삼각주 전체)
    half_angle = np.radians(spread_angle / 2)
    
    for r in range(apex_y, h):
        dist = r - apex_y
        if dist == 0:
            continue
            
        # 각도 범위 내 육지
        for c in range(w):
            dx = c - center_x
            angle = np.arctan2(dx, dist)  # 정점 기준 각도
            
            if abs(angle) < half_angle:
                # 삼각주 육지
                # 중심에서 멀수록 낮아짐
                radial_dist = np.sqrt(dx**2 + dist**2)
                max_dist = h - apex_y
                elevation[r, c] = 10.0 * (1 - radial_dist / max_dist)
                
    # 분배 수로 (Distributary Channels)
    for i in range(num_channels):
        channel_angle = -half_angle + (2 * half_angle) * (i / (num_channels - 1))
        
        for r in range(apex_y, h):
            dist = r - apex_y
            c = int(center_x + dist * np.tan(channel_angle))
            
            if 0 <= c < w:
                # 수로 파기 (음각)
                for dc in range(-2, 3):
                    if 0 <= c + dc < w:
                        depth = 2.0 * (1 - abs(dc) / 3)
                        elevation[r, c + dc] -= depth
                        
    return elevation


def create_alluvial_fan(grid_size: int = 100,
                         apex_row: float = 0.15,
                         cone_angle: float = 90.0,
                         max_height: float = 50.0) -> np.ndarray:
    """
    선상지 (Alluvial Fan) - 원뿔형
    
    Args:
        grid_size: 그리드 크기
        apex_row: 정점 위치
        cone_angle: 부채꼴 각도
        max_height: 최대 고도
        
    Returns:
        elevation: 고도 배열
    """
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    apex_y = int(h * apex_row)
    center_x = w // 2
    half_angle = np.radians(cone_angle / 2)
    
    # 배경 산지 (상단)
    for r in range(apex_y):
        elevation[r, :] = max_height + (apex_y - r) * 2.0
        
    # 선상지 본체 (원뿔)
    for r in range(apex_y, h):
        dist = r - apex_y
        max_dist = h - apex_y
        
        for c in range(w):
            dx = c - center_x
            angle = np.arctan2(abs(dx), dist) if dist > 0 else 0
            
            if abs(np.arctan2(dx, dist)) < half_angle:
                # 원뿔 형태: 중심이 높고, 가장자리가 낮음
                radial = np.sqrt(dx**2 + dist**2)
                # 정점에서 멀어질수록 낮아짐
                z = max_height * (1 - radial / (max_dist * 1.5))
                # 가장자리로 갈수록 더 급격히 낮아짐
                lateral_decay = 1 - abs(dx) / (w // 2)
                elevation[r, c] = max(0, z * lateral_decay)
            else:
                elevation[r, c] = 0  # 평지
                
    # 협곡 (Apex에서 시작)
    for r in range(0, apex_y + 5):
        for dc in range(-3, 4):
            c = center_x + dc
            if 0 <= c < w:
                depth = 10.0 * (1 - abs(dc) / 4)
                elevation[r, c] -= depth
                
    return elevation


def create_meander(grid_size: int = 100,
                   amplitude: float = 0.3,
                   wavelength: float = 0.25,
                   num_bends: int = 3) -> np.ndarray:
    """
    곡류 (Meander) - S자 사행 하천
    
    Args:
        grid_size: 그리드 크기
        amplitude: 사행 진폭 (그리드 비율)
        wavelength: 파장 (그리드 비율)
        num_bends: 굽이 개수
        
    Returns:
        elevation: 고도 배열
    """
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    # 배경: 범람원 평탄면
    elevation[:, :] = 10.0
    
    center_x = w // 2
    amp = w * amplitude
    wl = h / num_bends
    channel_width = max(3, w // 20)
    
    # 사행 하천 경로
    for r in range(h):
        # Kinoshita curve (이상화된 곡류)
        theta = 2 * np.pi * r / wl
        meander_x = center_x + amp * np.sin(theta)
        
        for c in range(w):
            dist = abs(c - meander_x)
            
            if dist < channel_width:
                # 하도 (낮게)
                elevation[r, c] = 5.0 - (channel_width - dist) * 0.3
            elif dist < channel_width * 3:
                # 자연제방 (약간 높게)
                elevation[r, c] = 10.5
                
    # 우각호 (Oxbow Lake) 추가
    # 중간쯤에 절단된 곡류 흔적
    oxbow_y = h // 2
    oxbow_amp = amp * 1.5
    
    for dy in range(-int(wl/4), int(wl/4)):
        r = oxbow_y + dy
        if 0 <= r < h:
            theta = 2 * np.pi * dy / (wl/2)
            ox_x = center_x + oxbow_amp * np.sin(theta)
            
            for dc in range(-channel_width, channel_width + 1):
                c = int(ox_x + dc)
                if 0 <= c < w:
                    elevation[r, c] = 4.0  # 호수 수면
                    
    return elevation


def create_u_valley(grid_size: int = 100,
                    valley_depth: float = 100.0,
                    valley_width: float = 0.4) -> np.ndarray:
    """
    U자곡 (U-shaped Valley) - 빙하 침식 지형
    
    Args:
        grid_size: 그리드 크기
        valley_depth: 곡저 깊이
        valley_width: 곡저 너비 (비율)
        
    Returns:
        elevation: 고도 배열
    """
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    center = w // 2
    half_width = int(w * valley_width / 2)
    
    for r in range(h):
        for c in range(w):
            dx = abs(c - center)
            
            if dx < half_width:
                # U자 바닥 (평탄)
                elevation[r, c] = 0
            else:
                # U자 측벽 (급경사 후 완만)
                # y = (x/a)^4 형태
                normalized_x = (dx - half_width) / (w // 2 - half_width)
                elevation[r, c] = valley_depth * (normalized_x ** 2)
                
        # 상류로 갈수록 높아짐
        elevation[r, :] += (h - r) / h * 30.0
        
    return elevation


def create_v_valley(grid_size: int = 100,
                    valley_depth: float = 80.0) -> np.ndarray:
    """
    V자곡 (V-shaped Valley) - 하천 침식 지형
    
    Args:
        grid_size: 그리드 크기
        valley_depth: 곡저 깊이
        
    Returns:
        elevation: 고도 배열
    """
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    center = w // 2
    
    for r in range(h):
        for c in range(w):
            dx = abs(c - center)
            
            # V자 형태: |x| 에 비례
            elevation[r, c] = valley_depth * (dx / (w // 2))
            
        # 상류로 갈수록 높아짐
        elevation[r, :] += (h - r) / h * 50.0
        
    # 하천 (V자 바닥)
    for r in range(h):
        for dc in range(-2, 3):
            c = center + dc
            if 0 <= c < w:
                elevation[r, c] = max(0, elevation[r, c] - 5)
                
    return elevation


def create_barchan_dune(grid_size: int = 100,
                         num_dunes: int = 3) -> np.ndarray:
    """
    바르한 사구 (Barchan Dune) - 초승달 모양
    
    Args:
        grid_size: 그리드 크기
        num_dunes: 사구 개수
        
    Returns:
        elevation: 고도 배열
    """
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    # 사막 기반면
    elevation[:, :] = 5.0
    
    for i in range(num_dunes):
        # 사구 중심
        cy = h // 4 + i * (h // (num_dunes + 1))
        cx = w // 2 + (i - num_dunes // 2) * (w // 5)
        
        dune_height = 15.0 + np.random.rand() * 10.0
        dune_length = w // 5
        dune_width = w // 8
        
        for r in range(h):
            for c in range(w):
                dy = r - cy
                dx = c - cx
                
                # 바르한: 바람받이(앞)는 완만, 바람그늘(뒤)는 급경사
                # 초승달 형태
                
                # 거리
                dist = np.sqrt((dy / dune_length) ** 2 + (dx / dune_width) ** 2)
                
                if dist < 1.0:
                    # 사구 본체
                    # 앞쪽(바람받이): 완만한 경사
                    # 뒤쪽: 급경사 (Slip Face)
                    
                    if dy < 0:  # 바람받이
                        z = dune_height * (1 - dist) * (1 - abs(dy) / dune_length)
                    else:  # 바람그늘
                        z = dune_height * (1 - dist) * max(0, 1 - dy / (dune_length * 0.5))
                        
                    # 초승달 뿔 (Horns)
                    horn_factor = 1 + 0.5 * abs(dx / dune_width)
                    
                    elevation[r, c] = max(elevation[r, c], 5.0 + z * horn_factor)
                    
    return elevation


def create_coastal_cliff(grid_size: int = 100,
                          cliff_height: float = 30.0,
                          num_stacks: int = 2) -> np.ndarray:
    """
    해안 절벽 (Coastal Cliff) + 시스택
    
    Args:
        grid_size: 그리드 크기
        cliff_height: 절벽 높이
        num_stacks: 시스택 개수
        
    Returns:
        elevation: 고도 배열
    """
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    # 바다 (하단)
    sea_line = int(h * 0.6)
    elevation[sea_line:, :] = -5.0
    
    # 육지 + 절벽
    for r in range(sea_line):
        cliff_dist = sea_line - r
        if cliff_dist < 5:
            # 절벽면
            elevation[r, :] = cliff_height * (cliff_dist / 5)
        else:
            # 평탄한 육지
            elevation[r, :] = cliff_height
            
    # 파식대 (Wave-cut Platform)
    for r in range(sea_line, sea_line + 10):
        if r < h:
            elevation[r, :] = -2.0 + (r - sea_line) * 0.2
            
    # 시스택 (Sea Stacks)
    for i in range(num_stacks):
        sx = w // 3 + i * (w // 3)
        sy = sea_line + 5 + i * 3
        
        stack_height = cliff_height * 0.7
        
        for dr in range(-3, 4):
            for dc in range(-3, 4):
                r, c = sy + dr, sx + dc
                if 0 <= r < h and 0 <= c < w:
                    dist = np.sqrt(dr**2 + dc**2)
                    if dist < 3:
                        elevation[r, c] = stack_height * (1 - dist / 4)
                        
    return elevation


# ============================================
# 애니메이션용 형성과정 함수 (Stage-based)
# stage: 0.0 (시작) ~ 1.0 (완성)
# ============================================

def create_delta_animated(grid_size: int, stage: float, 
                           spread_angle: float = 120.0, num_channels: int = 7) -> np.ndarray:
    """삼각주 형성과정 애니메이션"""
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    apex_y = int(h * 0.2)
    center_x = w // 2
    
    # 배경: 바다
    elevation[:, :] = -5.0
    
    # 하천 (항상 존재)
    for r in range(apex_y):
        for dc in range(-3, 4):
            c = center_x + dc
            if 0 <= c < w:
                elevation[r, c] = 5.0
                
    # Stage에 따라 삼각주 성장
    max_reach = int((h - apex_y) * stage)
    half_angle = np.radians(spread_angle / 2) * stage  # 각도도 점진적 확대
    
    for r in range(apex_y, apex_y + max_reach):
        dist = r - apex_y
        if dist == 0:
            continue
            
        for c in range(w):
            dx = c - center_x
            angle = np.arctan2(dx, dist)
            
            if abs(angle) < half_angle:
                radial_dist = np.sqrt(dx**2 + dist**2)
                max_dist = max_reach if max_reach > 0 else 1
                z = 10.0 * (1 - radial_dist / max_dist) * stage
                elevation[r, c] = max(elevation[r, c], z)
                
    # 분배 수로 (stage 0.3 이후)
    if stage > 0.3:
        active_channels = int(num_channels * min(1.0, (stage - 0.3) / 0.7))
        for i in range(active_channels):
            channel_angle = -half_angle + (2 * half_angle) * (i / max(active_channels - 1, 1))
            for r in range(apex_y, apex_y + max_reach):
                dist = r - apex_y
                c = int(center_x + dist * np.tan(channel_angle))
                if 0 <= c < w:
                    for dc in range(-2, 3):
                        if 0 <= c + dc < w:
                            elevation[r, c + dc] -= 1.5
                            
    return elevation


def create_alluvial_fan_animated(grid_size: int, stage: float,
                                  cone_angle: float = 90.0, max_height: float = 50.0) -> np.ndarray:
    """선상지 형성과정 애니메이션"""
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    apex_y = int(h * 0.15)
    center_x = w // 2
    
    # 배경 산지 (항상 존재)
    for r in range(apex_y):
        elevation[r, :] = max_height + (apex_y - r) * 2.0
        
    # 협곡
    for r in range(apex_y + 5):
        for dc in range(-3, 4):
            c = center_x + dc
            if 0 <= c < w:
                elevation[r, c] -= 10.0 * (1 - abs(dc) / 4)
                
    # Stage에 따라 선상지 성장
    max_reach = int((h - apex_y) * stage)
    half_angle = np.radians(cone_angle / 2) * (0.5 + 0.5 * stage)
    
    for r in range(apex_y, apex_y + max_reach):
        dist = r - apex_y
        for c in range(w):
            dx = c - center_x
            if abs(np.arctan2(dx, max(dist, 1))) < half_angle:
                radial = np.sqrt(dx**2 + dist**2)
                z = max_height * (1 - radial / (max_reach * 1.5)) * stage
                lateral_decay = 1 - abs(dx) / (w // 2)
                elevation[r, c] = max(0, z * lateral_decay)
                
    return elevation


def create_meander_animated(grid_size: int, stage: float,
                            amplitude: float = 0.3, num_bends: int = 3) -> np.ndarray:
    """곡류 형성과정 애니메이션 (직선 -> 사행 -> 우각호)"""
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    elevation[:, :] = 10.0  # 범람원
    
    center_x = w // 2
    channel_width = max(3, w // 20)
    
    # Stage에 따른 사행 진폭 변화 (직선 -> 굽음)
    current_amp = w * amplitude * stage
    wl = h / num_bends
    
    for r in range(h):
        theta = 2 * np.pi * r / wl
        meander_x = center_x + current_amp * np.sin(theta)
        
        for c in range(w):
            dist = abs(c - meander_x)
            if dist < channel_width:
                elevation[r, c] = 5.0 - (channel_width - dist) * 0.3
            elif dist < channel_width * 3:
                elevation[r, c] = 10.5
                
    # 우각호 (stage > 0.8)
    if stage > 0.8:
        oxbow_intensity = (stage - 0.8) / 0.2
        oxbow_y = h // 2
        oxbow_amp = current_amp * 1.5
        
        for dy in range(-int(wl/4), int(wl/4)):
            r = oxbow_y + dy
            if 0 <= r < h:
                theta = 2 * np.pi * dy / (wl/2)
                ox_x = center_x + oxbow_amp * np.sin(theta)
                for dc in range(-channel_width, channel_width + 1):
                    c = int(ox_x + dc)
                    if 0 <= c < w:
                        elevation[r, c] = 4.0 * oxbow_intensity + elevation[r, c] * (1 - oxbow_intensity)
                        
    return elevation


def create_u_valley_animated(grid_size: int, stage: float,
                              valley_depth: float = 100.0, valley_width: float = 0.4) -> np.ndarray:
    """U자곡 형성과정 (V자 -> U자 변환)"""
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    center = w // 2
    
    # V자에서 U자로 변환
    # stage 0: 완전 V, stage 1: 완전 U
    half_width = int(w * valley_width / 2) * stage  # U 바닥 너비
    
    for r in range(h):
        for c in range(w):
            dx = abs(c - center)
            
            if dx < half_width:
                # U자 바닥
                elevation[r, c] = 0
            else:
                # V에서 U로 전환
                # V: linear, U: parabolic
                normalized_x = (dx - half_width) / max(1, w // 2 - half_width)
                v_height = valley_depth * normalized_x  # V shape
                u_height = valley_depth * (normalized_x ** 2)  # U shape
                elevation[r, c] = v_height * (1 - stage) + u_height * stage
                
        elevation[r, :] += (h - r) / h * 30.0
        
    return elevation


def create_coastal_cliff_animated(grid_size: int, stage: float,
                                   cliff_height: float = 30.0, num_stacks: int = 2) -> np.ndarray:
    """해안 절벽 후퇴 과정"""
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    # Stage에 따른 해안선 후퇴
    initial_sea_line = int(h * 0.8)
    final_sea_line = int(h * 0.5)
    sea_line = int(initial_sea_line - (initial_sea_line - final_sea_line) * stage)
    
    # 바다
    elevation[sea_line:, :] = -5.0
    
    # 육지 + 절벽
    for r in range(sea_line):
        cliff_dist = sea_line - r
        if cliff_dist < 5:
            elevation[r, :] = cliff_height * (cliff_dist / 5)
        else:
            elevation[r, :] = cliff_height
            
    # 파식대 (stage > 0.3)
    if stage > 0.3:
        platform_width = int(10 * (stage - 0.3) / 0.7)
        for r in range(sea_line, min(h, sea_line + platform_width)):
            elevation[r, :] = -2.0 + (r - sea_line) * 0.2
            
    # 시스택 (stage > 0.6)
    if stage > 0.6:
        stack_stage = (stage - 0.6) / 0.4
        for i in range(num_stacks):
            sx = w // 3 + i * (w // 3)
            sy = sea_line + 5 + i * 3
            stack_height = cliff_height * 0.7 * stack_stage
            
            for dr in range(-3, 4):
                for dc in range(-3, 4):
                    r, c = sy + dr, sx + dc
                    if 0 <= r < h and 0 <= c < w:
                        dist = np.sqrt(dr**2 + dc**2)
                        if dist < 3:
                            elevation[r, c] = stack_height * (1 - dist / 4)
                            
    return elevation


def create_v_valley_animated(grid_size: int, stage: float,
                              valley_depth: float = 80.0) -> np.ndarray:
    """V자곡 형성과정 (평탄면 -> 침식 -> 깊은 V자)"""
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    center = w // 2
    
    # Stage에 따른 침식 깊이 증가
    current_depth = valley_depth * stage
    
    for r in range(h):
        for c in range(w):
            dx = abs(c - center)
            
            # 초기 고원 상태에서 점진적으로 V자 형성
            base_height = 50.0  # 초기 고원 높이
            v_shape = current_depth * (dx / (w // 2))
            
            # 침식 진행에 따라 V자 깊어짐
            elevation[r, c] = base_height - current_depth + v_shape
            
        # 상류 경사
        elevation[r, :] += (h - r) / h * 30.0
        
    # 하천 (단계적으로 형성)
    if stage > 0.2:
        channel_intensity = min(1.0, (stage - 0.2) / 0.8)
        for r in range(h):
            for dc in range(-2, 3):
                c = center + dc
                if 0 <= c < w:
                    elevation[r, c] -= 5 * channel_intensity
                    
    return elevation


def create_barchan_animated(grid_size: int, stage: float,
                             num_dunes: int = 3) -> np.ndarray:
    """바르한 사구 형성과정 (평탄 사막 -> 모래 축적 -> 초승달 형성)"""
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    # 사막 기반면
    elevation[:, :] = 5.0
    
    # Stage에 따른 사구 성장
    np.random.seed(42)  # 일관된 위치
    
    for i in range(num_dunes):
        cy = h // 4 + i * (h // (num_dunes + 1))
        cx = w // 2 + (i - num_dunes // 2) * (w // 5)
        
        # 최종 높이 * stage
        final_height = 15.0 + (i * 5.0)
        dune_height = final_height * stage
        
        # 사구 크기도 stage에 비례
        dune_length = int((w // 5) * (0.3 + 0.7 * stage))
        dune_width = int((w // 8) * (0.3 + 0.7 * stage))
        
        if dune_length < 1 or dune_width < 1:
            continue
        
        for r in range(h):
            for c in range(w):
                dy = r - cy
                dx = c - cx
                
                dist = np.sqrt((dy / max(dune_length, 1)) ** 2 + (dx / max(dune_width, 1)) ** 2)
                
                if dist < 1.0:
                    if dy < 0:  # 바람받이
                        z = dune_height * (1 - dist) * (1 - abs(dy) / max(dune_length, 1))
                    else:  # 바람그늘
                        z = dune_height * (1 - dist) * max(0, 1 - dy / (dune_length * 0.5))
                        
                    horn_factor = 1 + 0.5 * abs(dx / max(dune_width, 1))
                    elevation[r, c] = max(elevation[r, c], 5.0 + z * horn_factor)
                    
    return elevation
# ============================================
# 확장 지형 (Extended Landforms)
# ============================================

def create_incised_meander(grid_size: int = 100, stage: float = 1.0,
                           valley_depth: float = 80.0, num_terraces: int = 3) -> np.ndarray:
    """
    감입곡류 (Incised Meander) + 하안단구 (River Terraces)
    
    융기 환경에서 곡류가 암반을 파고 들어가면서 형성
    """
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    center_x = w // 2
    amplitude = w * 0.25 * stage
    wl = h / 3  # 3 bends
    channel_width = max(3, w // 25)
    
    # 기반 고원
    elevation[:, :] = valley_depth
    
    # 감입 곡류 파기
    for r in range(h):
        theta = 2 * np.pi * r / wl
        meander_x = center_x + amplitude * np.sin(theta)
        
        for c in range(w):
            dist = abs(c - meander_x)
            
            if dist < channel_width:
                # 하도 (가장 깊음)
                elevation[r, c] = 5.0
            elif dist < channel_width * 2:
                # 급경사 측벽
                t = (dist - channel_width) / channel_width
                elevation[r, c] = 5.0 + (valley_depth - 5.0) * t
                
    # 하안단구 (계단)
    terrace_heights = [valley_depth * (0.3 + 0.2 * i) for i in range(num_terraces)]
    
    for terrace_h in terrace_heights:
        for r in range(h):
            theta = 2 * np.pi * r / wl
            meander_x = center_x + amplitude * np.sin(theta) * 0.8
            
            for c in range(w):
                dist = abs(c - meander_x)
                if channel_width * 3 < dist < channel_width * 4:
                    if elevation[r, c] > terrace_h:
                        elevation[r, c] = terrace_h
                        
    return elevation


def create_free_meander(grid_size: int = 100, stage: float = 1.0,
                        num_bends: int = 4) -> np.ndarray:
    """
    자유곡류 (Free Meander) + 범람원 (Floodplain) + 자연제방 (Natural Levee)
    
    충적 평야 위를 자유롭게 사행
    """
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    # 범람원 기반
    elevation[:, :] = 10.0
    
    center_x = w // 2
    amplitude = w * 0.3 * stage
    wl = h / num_bends
    channel_width = max(3, w // 20)
    
    for r in range(h):
        theta = 2 * np.pi * r / wl
        meander_x = center_x + amplitude * np.sin(theta)
        
        for c in range(w):
            dist = abs(c - meander_x)
            
            if dist < channel_width:
                # 하도
                elevation[r, c] = 5.0 - (channel_width - dist) * 0.2
            elif dist < channel_width * 2:
                # 자연제방 (Levee) - 하도보다 약간 높음
                elevation[r, c] = 11.0
            elif dist < channel_width * 4:
                # 배후습지 (Backswamp) - 약간 낮음
                elevation[r, c] = 9.5
                
    # 우각호 (Oxbow Lake)
    if stage > 0.7:
        oxbow_y = h // 2
        for dy in range(-int(wl/4), int(wl/4)):
            r = oxbow_y + dy
            if 0 <= r < h:
                theta = 2 * np.pi * dy / (wl/2)
                ox_x = center_x + amplitude * 1.3 * np.sin(theta)
                for dc in range(-channel_width, channel_width + 1):
                    c = int(ox_x + dc)
                    if 0 <= c < w:
                        elevation[r, c] = 4.5
                        
    return elevation


def create_bird_foot_delta(grid_size: int = 100, stage: float = 1.0) -> np.ndarray:
    """조족상 삼각주 (Bird-foot Delta) - 미시시피강형"""
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    elevation[:, :] = -5.0  # 바다
    
    apex_y = int(h * 0.15)
    center_x = w // 2
    
    # 가늘고 긴 분배수로들
    num_fingers = 5
    max_length = int((h - apex_y) * stage)
    
    for i in range(num_fingers):
        angle = np.radians(-30 + 15 * i)  # -30 to +30 degrees
        
        for d in range(max_length):
            r = apex_y + int(d * np.cos(angle))
            c = center_x + int(d * np.sin(angle))
            
            if 0 <= r < h and 0 <= c < w:
                # 좁은 finger 형태
                for dc in range(-3, 4):
                    for dr in range(-2, 3):
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < h and 0 <= nc < w:
                            dist = np.sqrt(dr**2 + dc**2)
                            z = 8.0 * (1 - d / max_length) * (1 - dist / 4) * stage
                            elevation[nr, nc] = max(elevation[nr, nc], z)
                            
    # 하천
    for r in range(apex_y):
        for dc in range(-3, 4):
            if 0 <= center_x + dc < w:
                elevation[r, center_x + dc] = 6.0
                
    return elevation


def create_arcuate_delta(grid_size: int = 100, stage: float = 1.0) -> np.ndarray:
    """호상 삼각주 (Arcuate Delta) - 나일강형"""
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    elevation[:, :] = -5.0
    
    apex_y = int(h * 0.2)
    center_x = w // 2
    
    # 부드러운 호 형태
    max_reach = int((h - apex_y) * stage)
    
    for r in range(apex_y, apex_y + max_reach):
        dist = r - apex_y
        # Arc width increases with distance
        arc_width = int(dist * 0.8)
        
        for c in range(max(0, center_x - arc_width), min(w, center_x + arc_width)):
            dx = abs(c - center_x)
            radial = np.sqrt(dx**2 + dist**2)
            
            # Smooth arc edge
            edge_dist = arc_width - dx
            if edge_dist > 0:
                z = 10.0 * (1 - radial / (max_reach * 1.2)) * min(1, edge_dist / 10)
                elevation[r, c] = max(elevation[r, c], z * stage)
                
    # 하천
    for r in range(apex_y):
        for dc in range(-4, 5):
            if 0 <= center_x + dc < w:
                elevation[r, center_x + dc] = 6.0
                
    return elevation


def create_cuspate_delta(grid_size: int = 100, stage: float = 1.0) -> np.ndarray:
    """첨두상 삼각주 (Cuspate Delta) - 티베르강형"""
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    elevation[:, :] = -5.0
    
    apex_y = int(h * 0.2)
    center_x = w // 2
    point_y = int(apex_y + (h - apex_y) * 0.8 * stage)
    
    # 뾰족한 삼각형 형태
    for r in range(apex_y, point_y):
        dist = r - apex_y
        total_dist = point_y - apex_y
        
        # Width narrows toward point
        width = int((w // 3) * (1 - dist / total_dist))
        
        for c in range(max(0, center_x - width), min(w, center_x + width)):
            dx = abs(c - center_x)
            z = 10.0 * (1 - dist / total_dist) * (1 - dx / max(width, 1))
            elevation[r, c] = max(elevation[r, c], z * stage)
            
    # 하천
    for r in range(apex_y):
        for dc in range(-3, 4):
            if 0 <= center_x + dc < w:
                elevation[r, center_x + dc] = 6.0
                
    return elevation


def create_cirque(grid_size: int = 100, stage: float = 1.0,
                  depth: float = 50.0) -> np.ndarray:
    """권곡 (Cirque) - 빙하 시작점"""
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    # 산악 배경
    elevation[:, :] = depth + 30.0
    
    # 권곡 위치 (상단 중앙)
    cirque_y = int(h * 0.3)
    cirque_x = w // 2
    cirque_radius = int(w * 0.25 * (0.5 + 0.5 * stage))
    
    for r in range(h):
        for c in range(w):
            dy = r - cirque_y
            dx = c - cirque_x
            dist = np.sqrt(dy**2 + dx**2)
            
            if dist < cirque_radius:
                # 반원형 움푹한 형태
                # 바닥은 평탄, 후벽(headwall)은 급경사
                if dy < 0:  # 후벽
                    z = depth * (1 - dist / cirque_radius) * 0.3
                else:  # 바닥
                    z = depth * 0.1
                elevation[r, c] = z
                
    return elevation


def create_horn(grid_size: int = 100, stage: float = 1.0) -> np.ndarray:
    """호른 (Horn) - 피라미드형 봉우리"""
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    center = (h // 2, w // 2)
    peak_height = 100.0 * stage
    
    # 4방향 권곡에 의한 호른 형성
    num_cirques = 4
    cirque_radius = int(w * 0.3)
    
    for r in range(h):
        for c in range(w):
            dy = r - center[0]
            dx = c - center[1]
            dist = np.sqrt(dy**2 + dx**2)
            
            # 기본 피라미드 형태
            elevation[r, c] = peak_height * max(0, 1 - dist / (w // 2))
            
            # 4방향 권곡 파기
            for i in range(num_cirques):
                angle = i * np.pi / 2
                cx = center[1] + int(cirque_radius * 0.8 * np.cos(angle))
                cy = center[0] + int(cirque_radius * 0.8 * np.sin(angle))
                
                cdist = np.sqrt((r - cy)**2 + (c - cx)**2)
                if cdist < cirque_radius * 0.6:
                    # 권곡 파기
                    elevation[r, c] = min(elevation[r, c], 
                                         20.0 + 30.0 * (cdist / (cirque_radius * 0.6)))
                    
    return elevation


def create_shield_volcano(grid_size: int = 100, stage: float = 1.0,
                          max_height: float = 40.0) -> np.ndarray:
    """순상화산 (Shield Volcano) - 완만한 경사"""
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    center = (h // 2, w // 2)
    radius = w // 2
    
    for r in range(h):
        for c in range(w):
            dist = np.sqrt((r - center[0])**2 + (c - center[1])**2)
            
            if dist < radius:
                # 완만한 포물선 형태 (경사 5-10도)
                elevation[r, c] = max_height * (1 - (dist / radius)**2) * stage
                
    # 정상부 화구
    crater_radius = int(radius * 0.1)
    for r in range(h):
        for c in range(w):
            dist = np.sqrt((r - center[0])**2 + (c - center[1])**2)
            if dist < crater_radius:
                elevation[r, c] = max_height * 0.9 * stage
                
    return elevation


def create_stratovolcano(grid_size: int = 100, stage: float = 1.0,
                         max_height: float = 80.0) -> np.ndarray:
    """성층화산 (Stratovolcano) - 급한 원뿔형"""
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    center = (h // 2, w // 2)
    radius = int(w * 0.4)
    
    for r in range(h):
        for c in range(w):
            dist = np.sqrt((r - center[0])**2 + (c - center[1])**2)
            
            if dist < radius:
                # 급한 원뿔 (경사 25-35도)
                elevation[r, c] = max_height * (1 - dist / radius) * stage
                
    # 정상부 화구
    crater_radius = int(radius * 0.08)
    crater_depth = 10.0
    for r in range(h):
        for c in range(w):
            dist = np.sqrt((r - center[0])**2 + (c - center[1])**2)
            if dist < crater_radius:
                elevation[r, c] = max_height * stage - crater_depth
                
    return elevation


def create_caldera(grid_size: int = 100, stage: float = 1.0,
                   rim_height: float = 50.0) -> np.ndarray:
    """칼데라 (Caldera) - 화구 함몰"""
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    center = (h // 2, w // 2)
    outer_radius = int(w * 0.45)
    caldera_radius = int(w * 0.3)
    
    for r in range(h):
        for c in range(w):
            dist = np.sqrt((r - center[0])**2 + (c - center[1])**2)
            
            if dist < outer_radius:
                if dist < caldera_radius:
                    # 칼데라 바닥 (평탄, 호수 가능)
                    elevation[r, c] = 5.0
                else:
                    # 칼데라 벽 (급경사)
                    t = (dist - caldera_radius) / (outer_radius - caldera_radius)
                    elevation[r, c] = 5.0 + rim_height * (1 - t) * stage
                    
    return elevation


def create_mesa_butte(grid_size: int = 100, stage: float = 1.0,
                      num_mesas: int = 2) -> np.ndarray:
    """메사/뷰트 (Mesa/Butte) - 탁상지"""
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    # 사막 기반
    elevation[:, :] = 5.0
    
    mesa_height = 40.0 * stage
    
    # 메사 배치
    positions = [(h//3, w//3), (h//2, 2*w//3)]
    sizes = [(w//4, w//5), (w//6, w//6)]  # 메사, 뷰트
    
    for i, ((my, mx), (sw, sh)) in enumerate(zip(positions[:num_mesas], sizes[:num_mesas])):
        for r in range(h):
            for c in range(w):
                if abs(r - my) < sh and abs(c - mx) < sw:
                    # 평탄한 정상부
                    elevation[r, c] = mesa_height
                elif abs(r - my) < sh + 3 and abs(c - mx) < sw + 3:
                    # 급경사 측벽
                    edge_dist = min(abs(abs(r - my) - sh), abs(abs(c - mx) - sw))
                    elevation[r, c] = mesa_height * (1 - edge_dist / 3)
                    
    return elevation


def create_spit_lagoon(grid_size: int = 100, stage: float = 1.0) -> np.ndarray:
    """사취 (Spit) + 석호 (Lagoon)"""
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    # 바다 (오른쪽)
    sea_line = int(w * 0.6)
    elevation[:, sea_line:] = -5.0
    
    # 육지 (왼쪽)
    elevation[:, :sea_line] = 10.0
    
    # 사취 (연안류 방향으로 길게)
    spit_start = int(h * 0.3)
    spit_length = int(h * 0.5 * stage)
    spit_width = 5
    
    for r in range(spit_start, min(h, spit_start + spit_length)):
        # 사취가 바다 쪽으로 휘어짐
        curve = int((r - spit_start) / spit_length * (w * 0.15))
        spit_x = sea_line + curve
        
        for dc in range(-spit_width, spit_width + 1):
            c = spit_x + dc
            if 0 <= c < w:
                elevation[r, c] = 3.0 * (1 - abs(dc) / spit_width)
                
    # 석호 (사취 안쪽)
    if stage > 0.5:
        for r in range(spit_start, spit_start + int(spit_length * 0.8)):
            curve = int((r - spit_start) / spit_length * (w * 0.1))
            for c in range(sea_line - 5, sea_line + curve):
                if 0 <= c < w:
                    if elevation[r, c] < 3.0:
                        elevation[r, c] = -2.0  # 얕은 석호
                        
    return elevation


# ============================================
# 추가 지형 (Additional Landforms)
# ============================================

def create_fjord(grid_size: int = 100, stage: float = 1.0) -> np.ndarray:
    """피오르드 (Fjord) - 빙하가 파낸 U자곡에 바다 유입"""
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    # 산악 지형
    elevation[:, :] = 80.0
    
    center = w // 2
    valley_width = int(w * 0.2)
    
    # U자곡 + 바다 유입
    sea_line = int(h * 0.7)
    
    for r in range(h):
        for c in range(w):
            dx = abs(c - center)
            
            if dx < valley_width:
                # U자 바닥
                if r < sea_line:
                    elevation[r, c] = 10.0  # 육지 바닥
                else:
                    elevation[r, c] = -30.0 * stage  # 바다
            elif dx < valley_width + 10:
                # U자 측벽
                t = (dx - valley_width) / 10
                base = -30.0 if r >= sea_line else 10.0
                elevation[r, c] = base + 70.0 * t
                
    return elevation


def create_drumlin(grid_size: int = 100, stage: float = 1.0,
                   num_drumlins: int = 5) -> np.ndarray:
    """드럼린 (Drumlin) - 빙하 방향 타원형 언덕"""
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    elevation[:, :] = 5.0  # 빙하 퇴적 평원
    
    for i in range(num_drumlins):
        # 드럼린 위치 (빙하 흐름 방향으로 정렬)
        cy = int(h * 0.2 + (i % 3) * h * 0.25)
        cx = int(w * 0.2 + (i // 3) * w * 0.3)
        
        # 타원형 (빙하 방향으로 길쭉)
        length = int(w * 0.15 * stage)
        width = int(w * 0.06 * stage)
        height = 15.0 * stage
        
        for r in range(h):
            for c in range(w):
                dy = (r - cy) / max(length, 1)
                dx = (c - cx) / max(width, 1)
                dist = np.sqrt(dy**2 + dx**2)
                
                if dist < 1.0:
                    # 뾰족한 빙하 상류, 완만한 하류
                    asymmetry = 1.0 if dy < 0 else 0.7
                    z = height * (1 - dist) * asymmetry
                    elevation[r, c] = max(elevation[r, c], 5.0 + z)
                    
    return elevation


def create_moraine(grid_size: int = 100, stage: float = 1.0) -> np.ndarray:
    """빙퇴석 (Moraine) - 측퇴석, 종퇴석"""
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    # 빙하 계곡 배경
    elevation[:, :] = 20.0
    center = w // 2
    
    # 빙하 본체 (과거)
    glacier_width = int(w * 0.3)
    for r in range(h):
        for c in range(w):
            if abs(c - center) < glacier_width:
                elevation[r, c] = 5.0  # 빙하 바닥
                
    # 측퇴석 (Lateral Moraine)
    moraine_height = 15.0 * stage
    for r in range(h):
        for side in [-1, 1]:
            moraine_c = center + side * glacier_width
            for dc in range(-5, 6):
                c = moraine_c + dc
                if 0 <= c < w:
                    z = moraine_height * (1 - abs(dc) / 6)
                    elevation[r, c] = max(elevation[r, c], z)
                    
    # 종퇴석 (Terminal Moraine)
    terminal_r = int(h * 0.8)
    for r in range(terminal_r - 5, min(h, terminal_r + 5)):
        for c in range(center - glacier_width, center + glacier_width):
            if 0 <= c < w:
                dr = abs(r - terminal_r)
                z = moraine_height * 1.2 * (1 - dr / 6)
                elevation[r, c] = max(elevation[r, c], z)
                
    return elevation


def create_braided_river(grid_size: int = 100, stage: float = 1.0) -> np.ndarray:
    """망상하천 (Braided River) - 여러 수로"""
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    # 넓은 하상
    elevation[:, :] = 10.0
    
    center = w // 2
    river_width = int(w * 0.5)
    
    # 넓고 얕은 하상
    for c in range(center - river_width // 2, center + river_width // 2):
        if 0 <= c < w:
            elevation[:, c] = 5.0
            
    # 여러 수로와 사주 (모래섬)
    num_channels = int(3 + 4 * stage)
    np.random.seed(42)
    
    for r in range(h):
        # 현재 행의 수로 위치
        for i in range(num_channels):
            channel_x = center - river_width // 3 + int((i / num_channels) * river_width * 0.7)
            channel_x += int(10 * np.sin(r / 10 + i))  # 약간 사행
            
            for dc in range(-2, 3):
                c = channel_x + dc
                if 0 <= c < w:
                    elevation[r, c] = 3.0
                    
    # 사주 (모래섬)
    for i in range(int(5 * stage)):
        bar_r = int(h * 0.2 + i * h * 0.15)
        bar_c = center + int((i - 2) * w * 0.1)
        
        for dr in range(-5, 6):
            for dc in range(-8, 9):
                r, c = bar_r + dr, bar_c + dc
                if 0 <= r < h and 0 <= c < w:
                    dist = np.sqrt((dr/5)**2 + (dc/8)**2)
                    if dist < 1.0:
                        elevation[r, c] = max(elevation[r, c], 6.0 * (1 - dist))
                        
    return elevation


def create_waterfall(grid_size: int = 100, stage: float = 1.0,
                     drop_height: float = 50.0) -> np.ndarray:
    """폭포 (Waterfall) - 차별침식"""
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    center = w // 2
    fall_r = int(h * 0.4)
    
    # 상류 (높은 경암층)
    for r in range(fall_r):
        for c in range(w):
            elevation[r, c] = drop_height + 20.0 + (fall_r - r) * 0.5
            
    # 폭포 (급경사)
    for r in range(fall_r, fall_r + 5):
        for c in range(w):
            t = (r - fall_r) / 5
            elevation[r, c] = drop_height * (1 - t) + 20.0
            
    # 하류
    for r in range(fall_r + 5, h):
        for c in range(w):
            elevation[r, c] = 20.0 - (r - fall_r - 5) * 0.2
            
    # 하천 수로
    for r in range(h):
        for dc in range(-4, 5):
            c = center + dc
            if 0 <= c < w:
                elevation[r, c] -= 5.0
                
    # 플런지풀 (폭호)
    pool_r = fall_r + 5
    for dr in range(-5, 6):
        for dc in range(-6, 7):
            r, c = pool_r + dr, center + dc
            if 0 <= r < h and 0 <= c < w:
                dist = np.sqrt(dr**2 + dc**2)
                if dist < 6:
                    elevation[r, c] = min(elevation[r, c], 10.0)
                    
    return elevation


def create_karst_doline(grid_size: int = 100, stage: float = 1.0,
                        num_dolines: int = 5) -> np.ndarray:
    """돌리네 (Doline/Sinkhole) - 카르스트 지형"""
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    # 석회암 대지
    elevation[:, :] = 30.0
    
    np.random.seed(42)
    for i in range(num_dolines):
        dy = int(h * 0.2 + np.random.rand() * h * 0.6)
        dx = int(w * 0.2 + np.random.rand() * w * 0.6)
        radius = int(w * 0.08 * (0.5 + np.random.rand() * 0.5))
        depth = 20.0 * stage * (0.5 + np.random.rand() * 0.5)
        
        for r in range(h):
            for c in range(w):
                dist = np.sqrt((r - dy)**2 + (c - dx)**2)
                if dist < radius:
                    z = depth * (1 - (dist / radius) ** 2)
                    elevation[r, c] = max(0, elevation[r, c] - z)
                    
    return elevation


def create_ria_coast(grid_size: int = 100, stage: float = 1.0) -> np.ndarray:
    """리아스식 해안 (Ria Coast) - 침수된 하곡"""
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    # 산지 배경
    elevation[:, :] = 40.0
    
    # 여러 개의 V자곡 (침수됨)
    num_valleys = 4
    sea_level = int(h * 0.6)
    
    for i in range(num_valleys):
        valley_x = int(w * 0.15 + i * w * 0.2)
        
        for r in range(h):
            for c in range(w):
                dx = abs(c - valley_x)
                
                if dx < 8:
                    # V자곡
                    depth = 30.0 * (1 - dx / 8)
                    elevation[r, c] -= depth
                    
    # 해수면 이하 = 바다
    for r in range(sea_level, h):
        for c in range(w):
            if elevation[r, c] < 10:
                elevation[r, c] = -5.0 * stage  # 침수
                
    return elevation


def create_tombolo(grid_size: int = 100, stage: float = 1.0) -> np.ndarray:
    """육계사주 (Tombolo) - 육지와 섬을 연결"""
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    # 바다
    elevation[:, :] = -5.0
    
    # 본토 (왼쪽)
    for c in range(int(w * 0.3)):
        elevation[:, c] = 15.0
        
    # 섬 (오른쪽)
    island_cy = h // 2
    island_cx = int(w * 0.75)
    island_radius = int(w * 0.12)
    
    for r in range(h):
        for c in range(w):
            dist = np.sqrt((r - island_cy)**2 + (c - island_cx)**2)
            if dist < island_radius:
                elevation[r, c] = 20.0 * (1 - dist / island_radius / 1.5)
                
    # 육계사주 (연결)
    tombolo_start = int(w * 0.3)
    tombolo_end = island_cx - island_radius
    
    for c in range(tombolo_start, tombolo_end):
        t = (c - tombolo_start) / (tombolo_end - tombolo_start)
        width = int(5 * (1 - abs(t - 0.5) * 2) * stage)
        
        for dr in range(-width, width + 1):
            r = island_cy + dr
            if 0 <= r < h:
                elevation[r, c] = 3.0 * (1 - abs(dr) / max(width, 1))
                
    return elevation


def create_sea_arch(grid_size: int = 100, stage: float = 1.0) -> np.ndarray:
    """해식아치 (Sea Arch) - 동굴이 관통"""
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    # 바다 (아래)
    sea_line = int(h * 0.5)
    elevation[sea_line:, :] = -5.0
    
    # 육지 절벽
    cliff_height = 30.0
    for r in range(sea_line):
        elevation[r, :] = cliff_height
        
    # 돌출부 (곶)
    headland_width = int(w * 0.3)
    headland_cx = w // 2
    headland_length = int(h * 0.3)
    
    for r in range(sea_line, sea_line + headland_length):
        for c in range(headland_cx - headland_width // 2, headland_cx + headland_width // 2):
            if 0 <= c < w:
                elevation[r, c] = cliff_height * (1 - (r - sea_line) / headland_length * 0.3)
                
    # 아치 (관통)
    arch_r = sea_line + int(headland_length * 0.5)
    arch_width = int(headland_width * 0.4 * stage)
    
    for dr in range(-5, 6):
        for dc in range(-arch_width // 2, arch_width // 2 + 1):
            r, c = arch_r + dr, headland_cx + dc
            if 0 <= r < h and 0 <= c < w:
                if abs(dr) < 3:  # 아치 높이
                    elevation[r, c] = -5.0  # 관통
                    
    return elevation


def create_crater_lake(grid_size: int = 100, stage: float = 1.0,
                       rim_height: float = 50.0) -> np.ndarray:
    """화구호 (Crater Lake) - 화구에 물이 고임"""
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    center = (h // 2, w // 2)
    outer_radius = int(w * 0.4)
    crater_radius = int(w * 0.25)
    
    for r in range(h):
        for c in range(w):
            dist = np.sqrt((r - center[0])**2 + (c - center[1])**2)
            
            if dist > outer_radius:
                elevation[r, c] = 0
            elif dist > crater_radius:
                # 외륜산
                t = (dist - crater_radius) / (outer_radius - crater_radius)
                elevation[r, c] = rim_height * (1 - t) * stage
            else:
                # 호수 (물)
                elevation[r, c] = -10.0 * stage
                
    return elevation


def create_lava_plateau(grid_size: int = 100, stage: float = 1.0) -> np.ndarray:
    """용암대지 (Lava Plateau) - 평탄한 용암"""
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    # 기반
    elevation[:, :] = 5.0
    
    # 용암대지 영역
    plateau_height = 30.0 * stage
    margin = int(w * 0.15)
    
    for r in range(margin, h - margin):
        for c in range(margin, w - margin):
            # 거의 평탄하지만 약간의 굴곡
            noise = np.sin(r * 0.2) * np.cos(c * 0.2) * 2.0
            elevation[r, c] = plateau_height + noise
            
    # 가장자리 절벽
    for r in range(h):
        for c in range(w):
            edge_dist = min(r, h - r - 1, c, w - c - 1)
            if edge_dist < margin:
                t = edge_dist / margin
                elevation[r, c] = 5.0 + (elevation[r, c] - 5.0) * t
                
    return elevation


def create_coastal_dune(grid_size: int = 100, stage: float = 1.0,
                        num_dunes: int = 3) -> np.ndarray:
    """해안사구 (Coastal Dune) - 해안가 모래 언덕"""
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    # 바다 (아래)
    beach_line = int(h * 0.7)
    elevation[beach_line:, :] = -3.0
    
    # 해빈 (해변)
    for r in range(beach_line - 5, beach_line):
        elevation[r, :] = 2.0
        
    # 해안사구 (해변 뒤)
    dune_zone_start = int(h * 0.3)
    dune_zone_end = beach_line - 5
    
    for i in range(num_dunes):
        dune_r = dune_zone_start + i * (dune_zone_end - dune_zone_start) // (num_dunes + 1)
        dune_height = 15.0 * stage * (1 - i * 0.2)
        
        for r in range(h):
            for c in range(w):
                dr = abs(r - dune_r)
                if dr < 10:
                    # 사구 형태 (바람받이 완만, 바람그늘 급)
                    if r < dune_r:
                        z = dune_height * (1 - dr / 12)
                    else:
                        z = dune_height * (1 - dr / 8)
                    elevation[r, c] = max(elevation[r, c], z)
                    
    return elevation


# 애니메이션 생성기 매핑
ANIMATED_LANDFORM_GENERATORS = {
    'delta': create_delta_animated,
    'alluvial_fan': create_alluvial_fan_animated,
    'meander': create_meander_animated,
    'u_valley': create_u_valley_animated,
    'v_valley': create_v_valley_animated,
    'barchan': create_barchan_animated,
    'coastal_cliff': create_coastal_cliff_animated,
    # 확장
    'incised_meander': create_incised_meander,
    'free_meander': create_free_meander,
    'bird_foot_delta': create_bird_foot_delta,
    'arcuate_delta': create_arcuate_delta,
    'cuspate_delta': create_cuspate_delta,
    'cirque': create_cirque,
    'horn': create_horn,
    'shield_volcano': create_shield_volcano,
    'stratovolcano': create_stratovolcano,
    'caldera': create_caldera,
    'mesa_butte': create_mesa_butte,
    'spit_lagoon': create_spit_lagoon,
    # 추가 지형
    'fjord': create_fjord,
    'drumlin': create_drumlin,
    'moraine': create_moraine,
    'braided_river': create_braided_river,
    'waterfall': create_waterfall,
    'karst_doline': create_karst_doline,
    'ria_coast': create_ria_coast,
    'tombolo': create_tombolo,
    'sea_arch': create_sea_arch,
    'crater_lake': create_crater_lake,
    'lava_plateau': create_lava_plateau,
    'coastal_dune': create_coastal_dune,
}

# 지형 생성 함수 매핑
IDEAL_LANDFORM_GENERATORS = {
    'delta': create_delta,
    'alluvial_fan': create_alluvial_fan,
    'meander': create_meander,
    'u_valley': create_u_valley,
    'v_valley': create_v_valley,
    'barchan': create_barchan_dune,
    'coastal_cliff': create_coastal_cliff,
    # 확장 지형
    'incised_meander': lambda gs: create_incised_meander(gs, 1.0),
    'free_meander': lambda gs: create_free_meander(gs, 1.0),
    'bird_foot_delta': lambda gs: create_bird_foot_delta(gs, 1.0),
    'arcuate_delta': lambda gs: create_arcuate_delta(gs, 1.0),
    'cuspate_delta': lambda gs: create_cuspate_delta(gs, 1.0),
    'cirque': lambda gs: create_cirque(gs, 1.0),
    'horn': lambda gs: create_horn(gs, 1.0),
    'shield_volcano': lambda gs: create_shield_volcano(gs, 1.0),
    'stratovolcano': lambda gs: create_stratovolcano(gs, 1.0),
    'caldera': lambda gs: create_caldera(gs, 1.0),
    'mesa_butte': lambda gs: create_mesa_butte(gs, 1.0),
    'spit_lagoon': lambda gs: create_spit_lagoon(gs, 1.0),
    # 추가 지형
    'fjord': lambda gs: create_fjord(gs, 1.0),
    'drumlin': lambda gs: create_drumlin(gs, 1.0),
    'moraine': lambda gs: create_moraine(gs, 1.0),
    'braided_river': lambda gs: create_braided_river(gs, 1.0),
    'waterfall': lambda gs: create_waterfall(gs, 1.0),
    'karst_doline': lambda gs: create_karst_doline(gs, 1.0),
    'ria_coast': lambda gs: create_ria_coast(gs, 1.0),
    'tombolo': lambda gs: create_tombolo(gs, 1.0),
    'sea_arch': lambda gs: create_sea_arch(gs, 1.0),
    'crater_lake': lambda gs: create_crater_lake(gs, 1.0),
    'lava_plateau': lambda gs: create_lava_plateau(gs, 1.0),
    'coastal_dune': lambda gs: create_coastal_dune(gs, 1.0),
}

