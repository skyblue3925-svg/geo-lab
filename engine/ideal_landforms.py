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
    
    for r in range(apex_y, min(apex_y + max_reach, h)):  # h 범위 체크 추가
        dist = r - apex_y
        for c in range(w):
            dx = c - center_x
            if abs(np.arctan2(dx, max(dist, 1))) < half_angle:
                radial = np.sqrt(dx**2 + dist**2)
                z = max_height * (1 - radial / (max_reach * 1.5 + 0.001)) * stage  # divide by zero 방지
                lateral_decay = 1 - abs(dx) / (w // 2)
                elevation[r, c] = max(0, z * lateral_decay)
                
    return elevation


def create_meander_animated(grid_size: int, stage: float,
                            amplitude: float = 0.3, num_bends: int = 3) -> np.ndarray:
    """곡류 형성과정 애니메이션 (직선 → 사행 → 우각호 → 하중도)
    
    Stage 0.0~0.3: 직선 하천 → 약한 사행 시작
    Stage 0.3~0.6: 사행 발달 + 공격사면 침식 + 활주사면 퇴적
    Stage 0.6~0.8: 곡류 목 절단 → 우각호 형성
    Stage 0.8~1.0: 하중도(river island) 형성 + 구하도 안정화
    """
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    elevation[:, :] = 10.0  # 범람원 기준면
    
    center_x = w // 2
    channel_width = max(3, w // 20)
    
    # Stage에 따른 사행 진폭 변화
    if stage < 0.6:
        current_amp = w * amplitude * (stage / 0.6)
    else:
        current_amp = w * amplitude  # 최대 진폭 유지
    
    wl = h / num_bends  # 파장
    
    # 메인 하천 그리기
    for r in range(h):
        theta = 2 * np.pi * r / wl
        meander_x = center_x + current_amp * np.sin(theta)
        
        # 공격사면 (attack slope) - 바깥쪽, 침식
        # 활주사면 (slip-off slope) - 안쪽, 퇴적
        dtheta = np.cos(theta)  # 곡률 방향
        
        for c in range(w):
            dist = c - meander_x
            
            # 하천 채널
            if abs(dist) < channel_width:
                # 수심 (중앙이 깊음)
                depth_factor = 1 - (abs(dist) / channel_width)
                elevation[r, c] = 5.0 - depth_factor * 3.0  # 2~5m
                
            # 공격사면 (외측) - 절벽
            elif dist * dtheta > 0 and abs(dist) < channel_width * 2:
                # 외측은 침식으로 가파름
                erosion_factor = (abs(dist) - channel_width) / channel_width
                elevation[r, c] = 8.0 + erosion_factor * 3.0
                
            # 활주사면 (내측) - 포인트바
            elif dist * dtheta < 0 and abs(dist) < channel_width * 3:
                # 내측은 퇴적으로 완만
                deposit_factor = (abs(dist) - channel_width) / (channel_width * 2)
                elevation[r, c] = 6.0 + deposit_factor * 4.0
                
            # 자연제방 (levee)
            elif abs(dist) < channel_width * 4:
                levee_height = 11.0 - (abs(dist) - channel_width * 2) * 0.5
                elevation[r, c] = max(levee_height, 10.0)
    
    # 우각호 형성 (stage > 0.6)
    if stage > 0.6:
        oxbow_intensity = min((stage - 0.6) / 0.2, 1.0)
        
        # 곡류 목 직선화 (cutoff)
        cutoff_y = int(h * 0.5)
        cutoff_width = int(wl * 0.3)
        
        for r in range(cutoff_y - cutoff_width // 2, cutoff_y + cutoff_width // 2):
            if 0 <= r < h:
                # 직선 채널
                for dc in range(-channel_width, channel_width + 1):
                    c = center_x + dc
                    if 0 <= c < w:
                        new_elev = 4.0 * oxbow_intensity + elevation[r, c] * (1 - oxbow_intensity)
                        elevation[r, c] = new_elev
        
        # 구하도 (우각호) - 물이 고인 곳
        for r in range(cutoff_y - int(wl * 0.4), cutoff_y + int(wl * 0.4)):
            if 0 <= r < h:
                theta = 2 * np.pi * r / wl
                old_channel_x = center_x + current_amp * np.sin(theta)
                
                # 구하도가 메인 채널과 겹치지 않는 곳만
                if abs(old_channel_x - center_x) > channel_width * 2:
                    for dc in range(-channel_width, channel_width + 1):
                        c = int(old_channel_x + dc)
                        if 0 <= c < w:
                            # 구하도는 물이 고여 낮음
                            elevation[r, c] = 3.0 * oxbow_intensity + elevation[r, c] * (1 - oxbow_intensity)
    
    # 하중도 형성 (stage > 0.8)
    if stage > 0.8:
        island_intensity = (stage - 0.8) / 0.2
        
        # 하류에 하중도 생성
        island_y = int(h * 0.75)
        island_size = max(3, channel_width // 2)
        
        for dy in range(-island_size, island_size + 1):
            for dx in range(-island_size, island_size + 1):
                if dy**2 + dx**2 < island_size**2:
                    r, c = island_y + dy, center_x + dx
                    if 0 <= r < h and 0 <= c < w:
                        elevation[r, c] = 7.0 * island_intensity + elevation[r, c] * (1 - island_intensity)
                        
    return elevation


def create_u_valley_animated(grid_size: int, stage: float,
                              valley_depth: float = 100.0, valley_width: float = 0.4) -> np.ndarray:
    """U자곡 형성과정 (빙하 성장 → 침식 → 빙하 후퇴 → U자곡)
    
    Stage 0.0~0.3: 빙하 성장 (V자곡에 빙하 채워짐)
    Stage 0.3~0.6: 빙하 침식 (U자 형태로 변형)
    Stage 0.6~1.0: 빙하 후퇴 (빙하 녹으면서 U자곡 드러남)
    """
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    center = w // 2
    
    # 1단계: V자곡 → U자곡 변형 (침식)
    if stage < 0.6:
        u_factor = min(stage / 0.6, 1.0)  # 0~1로 정규화
    else:
        u_factor = 1.0  # 완전 U자
    
    half_width = int(w * valley_width / 2) * u_factor  # U 바닥 너비
    
    for r in range(h):
        for c in range(w):
            dx = abs(c - center)
            
            if dx < half_width:
                # U자 바닥
                elevation[r, c] = 0
            else:
                # V에서 U로 전환
                normalized_x = (dx - half_width) / max(1, w // 2 - half_width)
                v_height = valley_depth * normalized_x  # V shape
                u_height = valley_depth * (normalized_x ** 2)  # U shape
                elevation[r, c] = v_height * (1 - u_factor) + u_height * u_factor
                
        # 상류로 갈수록 높아짐
        elevation[r, :] += (h - r) / h * 30.0
    
    # 2단계: 빙하 추가 (stage에 따라 성장/후퇴)
    # stage 0~0.3: 빙하 성장 (하류로 전진)
    # stage 0.3~0.6: 최대 범위
    # stage 0.6~1.0: 빙하 후퇴 (상류로 후퇴)
    
    glacier_grid = np.zeros((h, w))
    
    if stage < 0.3:
        # 빙하 성장: 상류에서 하류로 전진
        glacier_extent = int(h * (stage / 0.3) * 0.8)  # 최대 80%까지 전진
        glacier_start = 0
        glacier_end = glacier_extent
    elif stage < 0.6:
        # 최대 빙하 범위
        glacier_start = 0
        glacier_end = int(h * 0.8)
    else:
        # 빙하 후퇴
        retreat_factor = (stage - 0.6) / 0.4
        glacier_start = int(h * 0.8 * retreat_factor)  # 하류에서 녹음
        glacier_end = int(h * 0.8 * (1 - retreat_factor * 0.5))  # 상류도 줄어듦
    
    # 빙하 표시 (골짜기 채움)
    for r in range(glacier_start, min(glacier_end, h)):
        for c in range(w):
            dx = abs(c - center)
            if dx < half_width + 5:  # U자곡 바닥 + 약간 넓게
                glacier_thickness = 20.0 * (1 - abs(c - center) / (half_width + 5))
                if stage < 0.6:
                    elevation[r, c] += glacier_thickness
                else:
                    # 후퇴 중: 빙하 높이 감소
                    retreat_factor = (stage - 0.6) / 0.4
                    elevation[r, c] += glacier_thickness * (1 - retreat_factor)
    
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
    """바르한 사구 이동 애니메이션
    
    위에서 볼 때 초승달(🌙) 모양:
    - 볼록면(convex): 바람 불어오는 쪽 (상단)
    - 오목면(concave): 바람 가는 쪽 (하단) + 뿔
    - 뿔(horns): 바람 방향으로 뻗음
    
    바람 방향: 위 → 아래
    """
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    # 사막 기반면
    elevation[:, :] = 5.0
    
    np.random.seed(42)
    
    # 사구 이동
    move_distance = int(h * 0.5 * stage)
    
    for i in range(num_dunes):
        # 위치
        initial_y = h // 5 + i * (h // (num_dunes + 1))
        cx = w // 4 + (i % 2) * (w // 2)
        cy = initial_y + move_distance
        
        if cy >= h - 20:
            continue
        
        # 사구 크기
        dune_height = 10.0 + i * 2.0
        outer_r = w // 7  # 바깥 원 반지름
        inner_r = outer_r * 0.6  # 안쪽 원 반지름
        inner_offset = outer_r * 0.5  # 안쪽 원 오프셋 (아래로)
        
        for r in range(h):
            for c in range(w):
                dy = r - cy
                dx = c - cx
                
                # 바깥 원 (볼록면 - 상단)
                dist_outer = np.sqrt(dx**2 + dy**2)
                
                # 안쪽 원 (오목면 - 하단으로 오프셋)
                dist_inner = np.sqrt(dx**2 + (dy - inner_offset)**2)
                
                # 초승달 영역: 바깥 원 안 AND 안쪽 원 밖
                in_crescent = (dist_outer < outer_r) and (dist_inner > inner_r)
                
                if in_crescent:
                    # 높이 계산: 중심에서 멀수록 낮아짐
                    height_factor = 1 - (dist_outer / outer_r)
                    
                    # 바람받이(상단) 완만, 바람그늘(하단) 급
                    if dy < 0:
                        # 바람받이: 완만한 경사
                        slope = height_factor * 0.8
                    else:
                        # 바람그늘: 더 높게 (급경사 효과)
                        slope = height_factor * 1.2
                    
                    z = dune_height * slope
                    elevation[r, c] = max(elevation[r, c], 5.0 + z)
                
                # 뿔 (horn) - 양쪽으로 바람 방향으로 뻗음
                horn_width = outer_r * 0.3
                horn_length = outer_r * 0.8
                
                for side in [-1, 1]:  # 왼쪽, 오른쪽 뿔
                    horn_cx = cx + side * (outer_r - horn_width)
                    horn_cy = cy + inner_offset
                    
                    dx_horn = c - horn_cx
                    dy_horn = r - horn_cy
                    
                    # 뿔 영역 (바람 방향으로 길쭉)
                    if abs(dx_horn) < horn_width and 0 < dy_horn < horn_length:
                        # 뿔 높이: 끝으로 갈수록 낮아짐
                        horn_factor = 1 - dy_horn / horn_length
                        width_factor = 1 - abs(dx_horn) / horn_width
                        z = dune_height * 0.5 * horn_factor * width_factor
                        
                        if z > 0.3:
                            elevation[r, c] = max(elevation[r, c], 5.0 + z)
    
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
    """피오르드 (Fjord) - 빙하 후퇴 후 바다 유입
    
    Stage 0.0~0.4: 빙하가 U자곡을 채움 (빙하기)
    Stage 0.4~0.7: 빙하 후퇴 시작 (바다 유입 시작)
    Stage 0.7~1.0: 빙하 완전 후퇴 (피오르드 완성)
    """
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    # 산악 지형 (높은 산)
    elevation[:, :] = 100.0
    
    center = w // 2
    valley_width = int(w * 0.25)
    valley_depth = 60.0
    
    # U자곡 형성
    for r in range(h):
        for c in range(w):
            dx = abs(c - center)
            
            if dx < valley_width:
                # U자 바닥
                base_height = 10.0
                elevation[r, c] = base_height
            elif dx < valley_width + 15:
                # U자 측벽 (수직에 가까움)
                t = (dx - valley_width) / 15
                elevation[r, c] = 10.0 + 90.0 * (t ** 0.5)  # 급경사
    
    # 빙하 / 바다 상태
    if stage < 0.4:
        # 빙하기: U자곡에 빙하 채움
        glacier_extent = int(h * 0.9)  # 거의 전체 채움
        glacier_thickness = 40.0
        
        for r in range(glacier_extent):
            for c in range(w):
                dx = abs(c - center)
                if dx < valley_width:
                    # 빙하 표면 (볼록)
                    cross_profile = glacier_thickness * (1 - (dx / valley_width) ** 2)
                    elevation[r, c] = 10.0 + cross_profile
                    
    elif stage < 0.7:
        # 빙하 후퇴 중: 일부 빙하 + 바다 유입
        retreat_factor = (stage - 0.4) / 0.3
        
        # 빙하 잔류 (상류에만)
        glacier_end = int(h * (0.9 - 0.6 * retreat_factor))
        glacier_thickness = 40.0 * (1 - retreat_factor * 0.5)
        
        for r in range(glacier_end):
            for c in range(w):
                dx = abs(c - center)
                if dx < valley_width:
                    cross_profile = glacier_thickness * (1 - (dx / valley_width) ** 2)
                    elevation[r, c] = 10.0 + cross_profile
        
        # 바다 유입 (하류부터)
        sea_start = glacier_end
        for r in range(sea_start, h):
            for c in range(w):
                dx = abs(c - center)
                if dx < valley_width:
                    # 깊은 바다
                    elevation[r, c] = -30.0 * retreat_factor
    else:
        # 피오르드 완성: 깊은 바다만
        sea_depth = -50.0  # 깊은 피오르드
        
        for r in range(h):
            for c in range(w):
                dx = abs(c - center)
                if dx < valley_width:
                    # 상류로 갈수록 얕아짐
                    depth_gradient = 1 - (r / h) * 0.3
                    elevation[r, c] = sea_depth * depth_gradient
                    
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
    """폭포 (Waterfall) - 두부침식으로 후퇴
    
    Stage 0.0: 폭포가 하류에 위치
    Stage 1.0: 폭포가 상류로 후퇴 (두부침식)
    - 경암층과 연암층의 차별침식
    - 플런지풀(폭호) 발달
    - 후퇴하면서 협곡 형성
    """
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    center = w // 2
    
    # 폭포 위치 (stage에 따라 상류로 후퇴)
    # stage 0: 하류(h*0.7), stage 1: 상류(h*0.3)
    initial_fall = int(h * 0.7)
    final_fall = int(h * 0.3)
    fall_r = int(initial_fall - (initial_fall - final_fall) * stage)
    
    # 상류 (높은 경암층)
    hard_rock_height = drop_height + 30.0
    for r in range(fall_r):
        for c in range(w):
            # 상류로 갈수록 높아짐
            upstream_rise = (fall_r - r) * 0.3
            elevation[r, c] = hard_rock_height + upstream_rise
    
    # 폭포 절벽 (급경사)
    cliff_width = 5
    for r in range(fall_r, min(fall_r + cliff_width, h)):
        for c in range(w):
            t = (r - fall_r) / cliff_width
            # 수직 낙하
            elevation[r, c] = hard_rock_height * (1 - t) + 10.0 * t
    
    # 하류 (연암층 침식됨)
    for r in range(fall_r + cliff_width, h):
        for c in range(w):
            # 하류로 갈수록 낮아짐
            downstream_drop = (r - fall_r - cliff_width) * 0.2
            elevation[r, c] = 10.0 - downstream_drop
    
    # 협곡 (폭포 후퇴 경로)
    gorge_start = fall_r + cliff_width
    gorge_end = initial_fall + 10  # 원래 폭포 위치까지
    gorge_depth = 8.0
    
    for r in range(gorge_start, min(gorge_end, h)):
        for dc in range(-6, 7):
            c = center + dc
            if 0 <= c < w:
                # V자 협곡 단면
                depth = gorge_depth * (1 - abs(dc) / 6)
                elevation[r, c] -= depth
    
    # 하천 수로
    for r in range(h):
        for dc in range(-4, 5):
            c = center + dc
            if 0 <= c < w:
                elevation[r, c] -= 3.0
    
    # 플런지풀 (폭호) - 폭포 바로 아래
    pool_r = fall_r + cliff_width + 2
    pool_depth = 15.0
    for dr in range(-6, 7):
        for dc in range(-7, 8):
            r, c = pool_r + dr, center + dc
            if 0 <= r < h and 0 <= c < w:
                dist = np.sqrt(dr**2 + dc**2)
                if dist < 7:
                    pool_effect = pool_depth * (1 - dist / 7)
                    elevation[r, c] = min(elevation[r, c], 5.0 - pool_effect)
    
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
    """리아스식 해안 (Ria Coast) - 침수된 하곡
    
    해수면 상승으로 V자곡이 침수되어 형성
    - 톱니 모양 해안선
    - 좁고 깊은 만 (리아)
    """
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    # 산지 배경 (높은 육지)
    elevation[:, :] = 50.0
    
    # 여러 개의 V자 하곡
    num_valleys = 5
    valley_spacing = w // (num_valleys + 1)
    
    for i in range(num_valleys):
        valley_x = valley_spacing * (i + 1)
        valley_width = 12 + (i % 2) * 4  # 약간의 변화
        valley_depth = 40.0 + (i % 3) * 10
        
        for r in range(h):
            for c in range(w):
                dx = abs(c - valley_x)
                
                if dx < valley_width:
                    # V자곡 (상류로 갈수록 좁아짐)
                    upstream_factor = 1 - r / h * 0.5
                    effective_width = valley_width * upstream_factor
                    
                    if dx < effective_width:
                        depth = valley_depth * (1 - dx / effective_width)
                        elevation[r, c] = min(elevation[r, c], 50.0 - depth)
    
    # 해수면 (stage에 따라 상승)
    sea_level = 15.0 * stage  # 높을수록 많이 침수
    
    for r in range(h):
        for c in range(w):
            if elevation[r, c] < sea_level:
                # 해수면 아래 = 바다 (리아)
                elevation[r, c] = -10.0 - (sea_level - elevation[r, c]) * 0.3
                
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
    """해식아치 (Sea Arch) - 해식동굴이 관통
    
    곶의 양쪽에서 파랑 침식 → 해식동굴 → 관통 = 아치
    Stage: 아치 크기 발달
    """
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    # 바다 (하단)
    sea_line = int(h * 0.4)
    elevation[sea_line:, :] = -8.0
    
    # 육지 절벽
    cliff_height = 35.0
    for r in range(sea_line):
        for c in range(w):
            # 거리에 따른 육지 높이
            dist_from_edge = min(r, c, w - c - 1)
            elevation[r, c] = cliff_height
    
    # 돌출부 (곶 - headland)
    headland_cx = w // 2
    headland_width = int(w * 0.35)
    headland_length = int(h * 0.4)
    
    for r in range(sea_line, sea_line + headland_length):
        # 곶 폭이 끝으로 갈수록 좁아짐
        taper = 1 - (r - sea_line) / headland_length * 0.5
        current_width = int(headland_width * taper)
        
        for c in range(headland_cx - current_width // 2, headland_cx + current_width // 2):
            if 0 <= c < w:
                # 곶 높이 (끝으로 갈수록 약간 낮아짐)
                height = cliff_height * (1 - (r - sea_line) / headland_length * 0.2)
                elevation[r, c] = height
    
    # 해식아치 (곶 중간에 관통)
    arch_r = sea_line + int(headland_length * 0.5)
    arch_height = int(cliff_height * 0.6 * stage)  # 아치 높이
    arch_width = int(headland_width * 0.3 * stage)  # 아치 폭
    
    for dr in range(-8, 9):
        for dc in range(-arch_width, arch_width + 1):
            r = arch_r + dr
            c = headland_cx + dc
            
            if 0 <= r < h and 0 <= c < w:
                # 아치 형태 (반원형 터널)
                arch_profile = arch_height * np.sqrt(max(0, 1 - (dc / max(arch_width, 1))**2))
                
                if abs(dr) < 3 and arch_profile > 5:
                    # 터널 관통
                    elevation[r, c] = -5.0
                elif abs(dr) < 5:
                    # 아치 천장
                    if elevation[r, c] > arch_profile:
                        elevation[r, c] = min(elevation[r, c], cliff_height - arch_profile * 0.3)
    
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
    """용암대지 (Lava Plateau) - 한탄강 형성과정
    
    Stage 0.0~0.3: 원래 V자곡 존재
    Stage 0.3~0.6: 열하분출로 V자곡 메워짐 (용암대지 형성)
    Stage 0.6~1.0: 하천 재침식으로 새로운 협곡 형성
    """
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    center = w // 2
    
    # 기반 고원 높이
    plateau_base = 30.0
    
    if stage < 0.3:
        # 원래 V자곡 상태
        v_factor = 1.0
        lava_fill = 0.0
        new_valley = 0.0
    elif stage < 0.6:
        # 열하분출로 V자곡 메워짐
        v_factor = 1.0 - ((stage - 0.3) / 0.3)  # V자곡 점점 사라짐
        lava_fill = (stage - 0.3) / 0.3  # 용암 채워짐
        new_valley = 0.0
    else:
        # 새 협곡 형성
        v_factor = 0.0  # 원래 V자곡 완전히 덮임
        lava_fill = 1.0
        new_valley = (stage - 0.6) / 0.4  # 새 협곡 발달
    
    for r in range(h):
        for c in range(w):
            dx = abs(c - center)
            
            # 기본 고원
            elevation[r, c] = plateau_base
            
            # 원래 V자곡 (열하분출 전)
            if v_factor > 0:
                valley_depth = 25.0 * v_factor
                if dx < 15:
                    v_shape = valley_depth * (1 - dx / 15)
                    elevation[r, c] -= v_shape
            
            # 용암 채움 (평탄화)
            if lava_fill > 0:
                # 용암이 V자곡을 메움
                if dx < 15:
                    fill_amount = 25.0 * lava_fill * (1 - dx / 15)
                    elevation[r, c] += fill_amount * 0.8  # 약간 낮게
                    
            # 새로운 협곡 (하천 재침식)
            if new_valley > 0:
                # 새 하천이 용암대지를 파고듦
                new_valley_width = int(8 * new_valley)
                new_valley_depth = 20.0 * new_valley
                
                if dx < new_valley_width:
                    # 더 좁고 깊은 협곡
                    gorge_shape = new_valley_depth * (1 - dx / max(new_valley_width, 1))
                    elevation[r, c] -= gorge_shape
                    
    # 가장자리 경사
    margin = int(w * 0.1)
    for r in range(h):
        for c in range(w):
            edge_dist = min(r, h - r - 1, c, w - c - 1)
            if edge_dist < margin:
                t = edge_dist / margin
                elevation[r, c] = elevation[r, c] * t + 5.0 * (1 - t)
                
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


# ============================================
# 새로 추가된 지형들
# ============================================

def create_uvala(grid_size: int = 100, stage: float = 1.0,
                 num_dolines: int = 4) -> np.ndarray:
    """우발라 (Uvala) - 복합 돌리네
    
    여러 돌리네가 합쳐져서 형성된 큰 와지
    Stage 0~0.5: 개별 돌리네 형성
    Stage 0.5~1.0: 돌리네들이 합쳐짐
    """
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    elevation[:, :] = 30.0  # 석회암 대지
    
    center = w // 2
    
    # 돌리네 위치들
    doline_positions = [
        (h // 3, center - w // 6),
        (h // 3, center + w // 6),
        (h * 2 // 3, center - w // 6),
        (h * 2 // 3, center + w // 6),
    ]
    
    doline_radius = int(w * 0.15)
    doline_depth = 20.0 * stage
    
    for i, (cy, cx) in enumerate(doline_positions[:num_dolines]):
        for r in range(h):
            for c in range(w):
                dist = np.sqrt((r - cy)**2 + (c - cx)**2)
                if dist < doline_radius:
                    # 돌리네 형태 (가장자리 높고 중앙 낮음)
                    depth = doline_depth * (1 - dist / doline_radius)
                    elevation[r, c] = min(elevation[r, c], 30.0 - depth)
    
    # Stage > 0.5: 돌리네 사이 연결 (합쳐짐)
    if stage > 0.5:
        merge_factor = (stage - 0.5) / 0.5
        merge_depth = 10.0 * merge_factor
        
        # 중앙 연결부
        for r in range(h):
            for c in range(w):
                dist_center = np.sqrt((r - h//2)**2 + (c - center)**2)
                if dist_center < doline_radius * 1.5:
                    elevation[r, c] = min(elevation[r, c], 30.0 - merge_depth)
                    
    return elevation


def create_tower_karst(grid_size: int = 100, stage: float = 1.0,
                       num_towers: int = 6) -> np.ndarray:
    """탑카르스트 (Tower Karst) - 봉우리 형태 카르스트
    
    중국 구이린 같은 탑 모양 석회암 봉우리
    """
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    elevation[:, :] = 5.0  # 저지대
    
    np.random.seed(42)
    
    for i in range(num_towers):
        cy = int(h * 0.2 + (i % 3) * h * 0.3)
        cx = int(w * 0.2 + (i // 3) * w * 0.3 + np.random.randint(-10, 10))
        
        tower_height = (40.0 + np.random.rand() * 30) * stage
        tower_radius = int(w * 0.08 + np.random.rand() * w * 0.04)
        
        for r in range(h):
            for c in range(w):
                dist = np.sqrt((r - cy)**2 + (c - cx)**2)
                if dist < tower_radius:
                    # 수직 절벽 형태 (가파른 측면)
                    edge_factor = 1 - (dist / tower_radius) ** 3
                    z = tower_height * edge_factor
                    elevation[r, c] = max(elevation[r, c], 5.0 + z)
                    
    return elevation


def create_karren(grid_size: int = 100, stage: float = 1.0) -> np.ndarray:
    """카렌 (Karren/Lapies) - 석회암 용식 홈
    
    빗물에 의한 용식으로 형성된 홈과 릿지
    """
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    elevation[:, :] = 20.0  # 석회암 표면
    
    # 용식 홈 (Rillenkarren) - 평행한 홈
    groove_spacing = max(3, w // 20)
    groove_depth = 3.0 * stage
    
    for c in range(w):
        if c % groove_spacing < groove_spacing // 2:
            for r in range(h):
                # 길쭉한 홈
                depth = groove_depth * (1 - abs(c % groove_spacing - groove_spacing // 4) / (groove_spacing // 4))
                elevation[r, c] -= depth
    
    # 클린트/그라이크 (Clint/Grike) - 직각 패턴
    block_size = max(8, w // 8)
    grike_depth = 5.0 * stage
    grike_width = 2
    
    for r in range(h):
        for c in range(w):
            if r % block_size < grike_width or c % block_size < grike_width:
                elevation[r, c] -= grike_depth
                
    return elevation


def create_transverse_dune(grid_size: int = 100, stage: float = 1.0,
                           num_ridges: int = 4) -> np.ndarray:
    """횡사구 (Transverse Dune) - 바람에 직각인 사구열
    
    바람 방향에 수직으로 형성된 긴 사구
    """
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    elevation[:, :] = 5.0  # 사막 기반
    
    # 횡사구 (바람 방향 상→하에 수직 = 좌우로 길게)
    ridge_spacing = h // (num_ridges + 1)
    ridge_height = 12.0 * stage
    ridge_width = max(5, h // 10)
    
    for i in range(num_ridges):
        ridge_r = ridge_spacing * (i + 1)
        
        for r in range(h):
            for c in range(w):
                dr = r - ridge_r
                
                if abs(dr) < ridge_width:
                    # 비대칭: 바람받이 완만, 바람그늘 급
                    if dr < 0:
                        # 바람받이
                        z = ridge_height * (1 - abs(dr) / (ridge_width * 1.5))
                    else:
                        # 바람그늘
                        z = ridge_height * (1 - dr / (ridge_width * 0.6))
                    z = max(0, z)
                    elevation[r, c] = max(elevation[r, c], 5.0 + z)
                    
    return elevation


def create_star_dune(grid_size: int = 100, stage: float = 1.0,
                     num_dunes: int = 2) -> np.ndarray:
    """성사구 (Star Dune) - 별 모양 사구
    
    다방향 바람으로 형성된 방사상 사구
    """
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    elevation[:, :] = 5.0  # 사막 기반
    
    for d in range(num_dunes):
        cy = h // 3 + d * h // 3
        cx = w // 3 + d * w // 3
        
        dune_height = 20.0 * stage
        arm_length = int(w * 0.2)
        arm_width = max(3, w // 20)
        num_arms = 5  # 별 모양 팔 개수
        
        for r in range(h):
            for c in range(w):
                dx = c - cx
                dy = r - cy
                dist = np.sqrt(dx**2 + dy**2)
                
                # 중앙 봉우리
                if dist < arm_width * 2:
                    z = dune_height * (1 - dist / (arm_width * 2))
                    elevation[r, c] = max(elevation[r, c], 5.0 + z)
                
                # 팔 (방사상)
                for arm in range(num_arms):
                    angle = arm * 2 * np.pi / num_arms
                    # 팔 중심선까지의 거리
                    arm_dir = np.array([np.cos(angle), np.sin(angle)])
                    pos = np.array([dx, dy])
                    proj = np.dot(pos, arm_dir)
                    perp = np.abs(np.cross(arm_dir, pos))
                    
                    if proj > 0 and proj < arm_length and perp < arm_width:
                        # 팔 높이: 중앙에서 멀어질수록 낮아짐
                        z = dune_height * 0.6 * (1 - proj / arm_length) * (1 - perp / arm_width)
                        elevation[r, c] = max(elevation[r, c], 5.0 + z)
                        
    return elevation


# ============================================
# 추가 확장 지형들 (Additional Expansion)
# ============================================

def create_perched_river(grid_size: int = 100, stage: float = 1.0):
    """천정천 (Perched River) - 자연제방 발달로 하상이 주변보다 높음
    
    Stage 0~0.5: 범람원 형성 + 자연제방 발달
    Stage 0.5~1.0: 하상 퇴적으로 주변보다 높아짐 (천정천)
    """
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    # 범람원 기본 높이
    base_height = 10.0
    elevation[:] = base_height
    
    # 하천 중심선
    center = w // 2
    
    # 자연제방 발달 (stage에 따라)
    levee_height = 8.0 * stage
    levee_width = int(w * 0.15)
    
    for c in range(w):
        dist_from_center = abs(c - center)
        
        if dist_from_center < levee_width:
            # 하상 (하천 바닥) - 주변보다 높아짐
            if dist_from_center < 5:
                river_bed_height = base_height + levee_height * 0.8 * stage
                elevation[:, c] = river_bed_height
            else:
                # 자연제방 (제방)
                decay = 1 - (dist_from_center - 5) / (levee_width - 5)
                elevation[:, c] = base_height + levee_height * decay * stage
        else:
            # 배후습지 (낮은 곳)
            backswamp_depth = 3.0 * stage
            elevation[:, c] = base_height - backswamp_depth
    
    return elevation


def create_arete(grid_size: int = 100, stage: float = 1.0):
    """아레트 (Arête) - 빙하에 의해 형성된 날카로운 능선
    
    두 권곡 사이의 날카로운 능선
    """
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    # 기본 고산 지형
    base_height = 100.0
    elevation[:] = base_height
    
    center = w // 2
    
    # 양쪽에 권곡 형성
    cirque_depth = 60.0 * stage
    cirque_radius = int(w * 0.35)
    
    for r in range(h):
        for c in range(w):
            # 왼쪽 권곡
            left_cx = center - int(w * 0.25)
            left_cy = int(h * 0.5)
            dist_left = np.sqrt((r - left_cy)**2 + (c - left_cx)**2)
            
            # 오른쪽 권곡
            right_cx = center + int(w * 0.25)
            right_cy = int(h * 0.5)
            dist_right = np.sqrt((r - right_cy)**2 + (c - right_cx)**2)
            
            if dist_left < cirque_radius:
                bowl_depth = cirque_depth * (1 - (dist_left / cirque_radius)**2)
                elevation[r, c] = min(elevation[r, c], base_height - bowl_depth)
            
            if dist_right < cirque_radius:
                bowl_depth = cirque_depth * (1 - (dist_right / cirque_radius)**2)
                elevation[r, c] = min(elevation[r, c], base_height - bowl_depth)
    
    # 중앙 능선 (아레트) 강조
    ridge_width = 5
    for c in range(center - ridge_width, center + ridge_width):
        if 0 <= c < w:
            sharpness = 1 - abs(c - center) / ridge_width
            elevation[:, c] = base_height + 10.0 * sharpness * stage
    
    return elevation


def create_wadi(grid_size: int = 100, stage: float = 1.0):
    """와디 (Wadi) - 건조지역 일시적 하천 계곡
    
    평상시 건조, 우기에만 물이 흐르는 계곡
    """
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    # 건조 고원
    base_height = 50.0
    elevation[:] = base_height
    
    # 와디 계곡 생성 (구불구불)
    center = w // 2
    valley_depth = 25.0 * stage
    valley_width = int(w * 0.2)
    
    for r in range(h):
        # 구불구불한 계곡 중심
        offset = int(15 * np.sin(r * 0.08))
        valley_center = center + offset
        
        for c in range(w):
            dist = abs(c - valley_center)
            if dist < valley_width:
                # V자형 계곡
                depth = valley_depth * (1 - dist / valley_width)
                elevation[r, c] = base_height - depth
    
    # 모래/자갈 바닥 (평탄)
    for r in range(h):
        offset = int(15 * np.sin(r * 0.08))
        valley_center = center + offset
        for c in range(valley_center - 3, valley_center + 3):
            if 0 <= c < w:
                elevation[r, c] = base_height - valley_depth + 2  # 평탄한 바닥
    
    return elevation


def create_playa(grid_size: int = 100, stage: float = 1.0):
    """플라야 (Playa) - 건조 호수 바닥
    
    건조지역에서 물이 증발하고 남은 평탄한 호수 바닥
    """
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    # 분지 지형
    center_r, center_c = h // 2, w // 2
    basin_radius = int(min(h, w) * 0.4)
    
    for r in range(h):
        for c in range(w):
            dist = np.sqrt((r - center_r)**2 + (c - center_c)**2)
            
            if dist < basin_radius:
                # 분지 내부 (플라야)
                # 매우 평탄한 호수 바닥
                elevation[r, c] = 10.0 + np.random.uniform(0, 0.5)  # 거의 평탄
            else:
                # 분지 외부 (산지)
                rim_height = 50.0 * (1 - basin_radius / (dist + 1))
                elevation[r, c] = 30.0 + rim_height * stage
    
    # 소금 결정 패턴 (다각형)
    if stage > 0.7:
        for i in range(10):
            poly_r = center_r + np.random.randint(-basin_radius//2, basin_radius//2)
            poly_c = center_c + np.random.randint(-basin_radius//2, basin_radius//2)
            poly_size = np.random.randint(5, 15)
            for dr in range(-poly_size, poly_size):
                for dc in range(-poly_size, poly_size):
                    if 0 <= poly_r+dr < h and 0 <= poly_c+dc < w:
                        if abs(dr) + abs(dc) == poly_size - 1:  # 테두리
                            elevation[poly_r+dr, poly_c+dc] += 0.3
    
    return elevation


def create_pedestal_rock(grid_size: int = 100, stage: float = 1.0):
    """버섯바위 (Pedestal Rock) - 바람에 의한 차별풍화 지형
    
    Stage 0~0.3: 원래 암석 기둥
    Stage 0.3~0.7: 바람에 의한 하부 침식 (연마작용)
    Stage 0.7~1.0: 버섯 모양 완성 (줄기가 매우 얇아짐)
    
    바람에 실려온 모래가 하부를 깎아냄 (지표 가까울수록 모래 농도 높음)
    """
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    # 사막 평원
    base_height = 5.0
    elevation[:] = base_height
    
    # 버섯바위 여러 개
    num_rocks = 3
    np.random.seed(42)
    
    for i in range(num_rocks):
        # 위치
        rock_r = np.random.randint(h // 4, 3 * h // 4)
        rock_c = np.random.randint(w // 4, 3 * w // 4)
        
        # 원래 바위 크기 (stage 0에서의 크기)
        original_radius = np.random.randint(10, 16)
        rock_height = np.random.uniform(25, 40)
        
        # stage에 따른 침식 정도 (stage 높을수록 하부 더 깎임)
        erosion_factor = stage  # 0~1
        
        for r in range(h):
            for c in range(w):
                dist = np.sqrt((r - rock_r)**2 + (c - rock_c)**2)
                
                if dist < original_radius:
                    # 바위 내부 - 높이에 따라 반경이 다름
                    # 상부: 원래 반경 유지
                    # 하부: stage에 따라 깎임
                    
                    # 각 높이에서의 유효 반경 계산
                    for z_level in range(int(rock_height)):
                        # 지표에서의 높이 비율 (0=바닥, 1=꼭대기)
                        height_ratio = z_level / rock_height
                        
                        # 하부일수록 바람 침식 심함 (지표 가까울수록)
                        if height_ratio < 0.5:
                            # 하부: 침식으로 반경 감소
                            erosion_at_height = erosion_factor * (1 - height_ratio * 2)  # 바닥에서 최대
                            current_radius = original_radius * (1 - erosion_at_height * 0.7)
                        else:
                            # 상부: 원래 반경 유지 (모자 부분)
                            current_radius = original_radius
                        
                        if dist < current_radius:
                            elevation[r, c] = max(elevation[r, c], base_height + z_level)
    
    return elevation


def create_estuary(grid_size: int = 100, stage: float = 1.0):
    """에스추어리 (Estuary) - 삼각강, 조석 영향
    
    조석의 영향을 받는 넓은 하구
    """
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    # 육지 기본
    land_height = 20.0
    elevation[:] = land_height
    
    # 에스추어리 (깔때기 모양)
    apex_row = int(h * 0.1)
    center = w // 2
    
    for r in range(h):
        # 하류로 갈수록 넓어짐
        progress = (r - apex_row) / (h - apex_row) if r > apex_row else 0
        estuary_width = int(5 + 40 * progress * stage)
        
        for c in range(w):
            dist = abs(c - center)
            
            if r < apex_row:
                # 상류 하천 (좁음)
                if dist < 5:
                    elevation[r, c] = -5.0
            elif dist < estuary_width:
                # 에스추어리 영역
                depth = 10.0 * (1 - dist / estuary_width) * (0.5 + 0.5 * progress)
                elevation[r, c] = -depth
            
            # 조간대 (tide flat)
            if dist >= estuary_width - 10 and dist < estuary_width and r > apex_row:
                elevation[r, c] = max(elevation[r, c], -1.0)  # 조간대 (얕음)
    
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
    # 새로 추가된 지형
    'uvala': create_uvala,
    'tower_karst': create_tower_karst,
    'karren': create_karren,
    'transverse_dune': create_transverse_dune,
    'star_dune': create_star_dune,
    # 추가 확장 지형
    'perched_river': create_perched_river,
    'arete': create_arete,
    'wadi': create_wadi,
    'playa': create_playa,
    'pedestal_rock': create_pedestal_rock,
    'estuary': create_estuary,
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
    # 새로 추가된 지형
    'uvala': lambda gs: create_uvala(gs, 1.0),
    'tower_karst': lambda gs: create_tower_karst(gs, 1.0),
    'karren': lambda gs: create_karren(gs, 1.0),
    'transverse_dune': lambda gs: create_transverse_dune(gs, 1.0),
    'star_dune': lambda gs: create_star_dune(gs, 1.0),
    # 추가 확장 지형
    'perched_river': lambda gs: create_perched_river(gs, 1.0),
    'arete': lambda gs: create_arete(gs, 1.0),
    'wadi': lambda gs: create_wadi(gs, 1.0),
    'playa': lambda gs: create_playa(gs, 1.0),
    'pedestal_rock': lambda gs: create_pedestal_rock(gs, 1.0),
    'estuary': lambda gs: create_estuary(gs, 1.0),
}

