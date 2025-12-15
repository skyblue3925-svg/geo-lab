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


def create_coastal_cliff(grid_size: int = 100, stage: float = 1.0,
                          cliff_height: float = 30.0,
                          num_stacks: int = 2,
                          return_metadata: bool = False) -> np.ndarray:
    """
    해안 절벽 (Coastal Cliff) + 파식대 + 시스택
    
    Stage 0~0.3: 초기 해안 (절벽 형성 시작)
      - 파랑의 수압작용(hydraulic action)
      - 노치(notch) 형성 시작
    
    Stage 0.3~0.6: 절벽 발달
      - 연마작용(abrasion)으로 노치 확대
      - 오버행(overhang) 형성
      - 절벽 붕괴 시작
    
    Stage 0.6~0.8: 절벽 후퇴
      - 반복적 붕괴로 절벽이 육지쪽으로 후퇴
      - 파식대(wave-cut platform) 확장
    
    Stage 0.8~1.0: 시스택/해식동 형성
      - 연약부 차별침식
      - 해식아치 → 시스택 형성
    
    핵심 과정:
    - 수압작용: 파랑 충격 → 암석 틈새 압축공기
    - 연마작용: 해빈 자갈/모래가 절벽 깎음
    - 용식작용: 해수의 화학적 용해 (석회암)
    """
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    # 해안선 위치 (stage에 따라 육지쪽으로 후퇴)
    initial_sea_line = int(h * 0.7)
    retreat_amount = int(h * 0.2 * stage)
    sea_line = initial_sea_line - retreat_amount
    
    # 바다 (하단)
    for r in range(sea_line, h):
        elevation[r, :] = -5.0
    
    # 절벽 높이 (stage에 따라 발달)
    current_cliff_height = cliff_height * (0.5 + 0.5 * stage)
    
    # 육지 + 절벽
    cliff_width = max(3, int(5 * stage))
    for r in range(sea_line):
        cliff_dist = sea_line - r
        if cliff_dist < cliff_width:
            # 절벽면 (수직에 가까움)
            t = cliff_dist / cliff_width
            elevation[r, :] = current_cliff_height * (t ** 0.7)  # 오목한 프로파일
        else:
            # 평탄한 육지
            elevation[r, :] = current_cliff_height
    
    # 노치 (Notch) - stage > 0.3에서 형성
    if stage > 0.3:
        notch_depth = int(3 * (stage - 0.3) / 0.7)
        notch_height = 2  # 파랑대 높이
        
        for r in range(sea_line - notch_height, sea_line):
            for c in range(w):
                if 0 <= r < h:
                    # 노치 깊이만큼 파임
                    elevation[r, c] = min(elevation[r, c], 
                                         elevation[r, c] - notch_depth * (1 - abs(r - (sea_line - 1)) / notch_height))
    
    # 파식대 (Wave-cut Platform) - stage > 0.4에서 확장
    platform_width = int(10 + 15 * max(0, (stage - 0.4) / 0.6))
    for r in range(sea_line, min(sea_line + platform_width, h)):
        platform_depth = -1.0 - (r - sea_line) * 0.3
        elevation[r, :] = max(platform_depth, -5.0)
    
    # 시스택 (Sea Stacks) - stage > 0.7에서 형성
    stacks_formed = []
    if stage > 0.7:
        stack_progress = (stage - 0.7) / 0.3
        visible_stacks = int(num_stacks * stack_progress) + 1
        
        for i in range(min(visible_stacks, num_stacks)):
            sx = w // 4 + i * (w // 2)
            sy = sea_line + 8 + i * 4
            
            stack_height = current_cliff_height * 0.6 * stack_progress
            stack_radius = 4
            
            for dr in range(-stack_radius, stack_radius + 1):
                for dc in range(-stack_radius, stack_radius + 1):
                    r_pos, c_pos = sy + dr, sx + dc
                    if 0 <= r_pos < h and 0 <= c_pos < w:
                        dist = np.sqrt(dr**2 + dc**2)
                        if dist < stack_radius:
                            z = stack_height * (1 - (dist / stack_radius) ** 2)
                            elevation[r_pos, c_pos] = max(elevation[r_pos, c_pos], z)
            
            stacks_formed.append((sy, sx))
    
    if return_metadata:
        return elevation, {
            'sea_line': sea_line,
            'cliff_height': current_cliff_height,
            'retreat_amount': retreat_amount,
            'platform_width': platform_width,
            'stacks_formed': stacks_formed,
            'erosion_processes': {
                'hydraulic_action': '파랑 충격 → 암석 틈새 압축공기',
                'abrasion': '해빈 자갈/모래가 절벽 연마',
                'corrosion': '해수의 화학적 용해 (석회암)'
            },
            'stage_description': _get_cliff_stage_desc(stage)
        }
    
    return elevation


def _get_cliff_stage_desc(stage: float) -> str:
    """해안절벽 단계별 설명"""
    if stage < 0.2:
        return "🌊 초기 해안: 파랑 침식 시작"
    elif stage < 0.4:
        return "⛏️ 노치 형성: 수압작용으로 파랑대 침식"
    elif stage < 0.6:
        return "🏔️ 절벽 발달: 오버행 형성 → 붕괴"
    elif stage < 0.8:
        return "📉 절벽 후퇴: 파식대 노출"
    else:
        return "🪨 시스택 형성: 차별침식으로 고립 암석"


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
                                  cone_angle: float = 90.0, max_height: float = 50.0,
                                  return_metadata: bool = False) -> np.ndarray:
    """선상지 형성과정 애니메이션
    
    Stage 0~0.3: 선정(Apex) 형성 - 협곡 출구, 역 퇴적
    Stage 0.3~0.7: 선앙(Mid-fan) 확장 - 분기 수로, 사질 퇴적
    Stage 0.7~1.0: 선단(Toe) 완성 - 말단부, 니질 퇴적
    
    세부 구조:
    - 선정: 경사 5-15°, 역(Gravel) 퇴적, 단일 주수로
    - 선앙: 경사 2-5°, 사(Sand) 퇴적, 분기 수로
    - 선단: 경사 <2°, 니(Silt) 퇴적, 망상/시상 수로
    """
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    zone_mask = np.zeros((h, w), dtype=int)  # 0: 없음, 1: 선정, 2: 선앙, 3: 선단
    
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
    
    # 존 경계 계산
    apex_end = apex_y + max(1, int(max_reach * 0.2))      # 선정: 0~20%
    mid_end = apex_y + max(1, int(max_reach * 0.6))       # 선앙: 20~60%
    # 선단: 60~100%
    
    for r in range(apex_y, min(apex_y + max_reach, h)):
        dist = r - apex_y
        
        # 존 결정
        if r < apex_end:
            current_zone = 1  # 선정
        elif r < mid_end:
            current_zone = 2  # 선앙
        else:
            current_zone = 3  # 선단
        
        for c in range(w):
            dx = c - center_x
            if abs(np.arctan2(dx, max(dist, 1))) < half_angle:
                radial = np.sqrt(dx**2 + dist**2)
                z = max_height * (1 - radial / (max_reach * 1.5 + 0.001)) * stage
                lateral_decay = 1 - abs(dx) / (w // 2)
                new_elevation = max(0, z * lateral_decay)
                
                if new_elevation > 0:
                    elevation[r, c] = new_elevation
                    zone_mask[r, c] = current_zone
    
    if return_metadata:
        return elevation, {
            'zone_mask': zone_mask,
            'apex_boundary': apex_end,
            'mid_boundary': mid_end,
            'stage_description': _get_fan_stage_desc(stage),
            'zone_info': {
                1: {'name': '선정 (Apex)', 'slope': '5-15°', 'sediment': '역 (Gravel)'},
                2: {'name': '선앙 (Mid-fan)', 'slope': '2-5°', 'sediment': '사 (Sand)'},
                3: {'name': '선단 (Toe)', 'slope': '<2°', 'sediment': '니 (Silt)'}
            }
        }
    
    return elevation


def _get_fan_stage_desc(stage: float) -> str:
    """선상지 단계별 설명"""
    if stage < 0.3:
        return "🏔️ 선정 형성: 협곡 출구에서 유속 급감, 역 퇴적 시작"
    elif stage < 0.6:
        return "📊 선앙 확장: 수로 분기, 사질 퇴적물 확산"
    elif stage < 0.8:
        return "🌊 선단 발달: 세립질 퇴적, 말단부 완만해짐"
    else:
        return "✅ 선상지 완성: 선정-선앙-선단 분화 완료"


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
                              valley_depth: float = 100.0, valley_width: float = 0.4,
                              return_metadata: bool = False) -> np.ndarray:
    """U자곡 (Glacial Trough) 형성과정 - 학술 자료 기반
    
    Stage 0~0.15: V자곡 (하천 침식 지형) - 빙하 없음
    Stage 0.15~0.35: 빙기 - 계곡빙하 전진 (상류→하류)
    Stage 0.35~0.55: 빙기 절정 - 마식+플러킹 활발, V→U 변환
    Stage 0.55~0.75: 간빙기 - 빙하 후퇴 (하류→상류)
    Stage 0.75~0.90: U자곡 + 현수곡 노출
    Stage 0.90~1.0: 빙하호 형성, 종퇴석 명확
    
    핵심 과정:
    - 마식(Abrasion): 빙하 바닥 암석이 기반암 연마
    - 플러킹(Plucking): 빙하가 기반암 조각 뜯어냄
    - U자형: 마찰 최소화 형태 + 동시 측면/바닥 침식
    """
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    center = w // 2
    
    # === 빙하 전진/후퇴 계산 ===
    if stage < 0.15:
        # V자곡 상태 (빙하 없음)
        glacier_front = 0
        glacier_rear = 0
        erosion_progress = 0.0
        phase = "pre_glacial"
    elif stage < 0.35:
        # 빙기: 빙하 전진 (상류에서 시작, 하류로 진행)
        advance = (stage - 0.15) / 0.2
        glacier_rear = int(h * 0.05)  # 상류 끝 (빙하 시작점)
        glacier_front = int(h * 0.05 + h * 0.75 * advance)  # 하류로 전진
        erosion_progress = advance * 0.3  # 30%까지 침식
        phase = "glacial_advance"
    elif stage < 0.55:
        # 빙기 절정: 최대 확장 + 활발한 침식
        glacier_rear = int(h * 0.05)
        glacier_front = int(h * 0.85)  # 최대 전진
        erosion_progress = 0.3 + (stage - 0.35) / 0.2 * 0.6  # 30%→90%
        phase = "glacial_max"
    elif stage < 0.75:
        # 간빙기: 빙하 후퇴 (하류에서 상류로)
        retreat = (stage - 0.55) / 0.2
        glacier_front = int(h * 0.85 - h * 0.6 * retreat)  # 상류로 후퇴
        glacier_rear = int(h * 0.05 + h * 0.15 * retreat)  # 상류도 녹음
        erosion_progress = 0.9 + retreat * 0.08  # 90%→98%
        phase = "glacial_retreat"
    else:
        # 빙하 완전 소멸
        glacier_front = 0
        glacier_rear = 0
        erosion_progress = 1.0
        phase = "post_glacial"
    
    # === 지형 생성 ===
    for r in range(h):
        # 상류로 갈수록 기반 높아짐 (경사)
        base_height = (h - r) / h * 60.0
        
        # 이 행까지 빙하가 도달했는가?
        was_glaciated = (r >= glacier_rear and r <= glacier_front) or phase == "post_glacial"
        
        # 빙하가 지나간 구간의 침식 정도
        if was_glaciated or phase == "post_glacial":
            local_erosion = erosion_progress
        elif phase == "glacial_advance" and r < glacier_front:
            # 아직 빙하가 안 도달한 하류
            local_erosion = 0
        else:
            local_erosion = 0
        
        # U자 바닥 너비 (침식에 따라 넓어짐)
        floor_width = int(w * valley_width * 0.08) + int(w * valley_width * 0.35 * local_erosion)
        
        for c in range(w):
            dx = abs(c - center)
            
            if dx < floor_width:
                # U자 바닥 (평탄) - 마식으로 연마됨
                elev = 0
            else:
                # 측벽
                wall_dist = (dx - floor_width) / max(1, w // 2 - floor_width)
                wall_dist = min(1, wall_dist)
                
                # V자형 단면 (포물선 아님, 삼각형)
                v_profile = valley_depth * wall_dist
                
                # U자형 단면 (측벽이 급해지고 바닥이 편평)
                u_profile = valley_depth * (wall_dist ** 0.35)  # 급한 측벽
                
                # V→U 변환
                elev = v_profile * (1 - local_erosion) + u_profile * local_erosion
            
            elevation[r, c] = base_height + elev
    
    # === 빙하 시각화 ===
    if glacier_front > glacier_rear and phase not in ["pre_glacial", "post_glacial"]:
        glacier_thickness = 40.0 if phase == "glacial_max" else 30.0
        
        for r in range(glacier_rear, glacier_front):
            # 빙하 두께: 중앙 두껍고 위/아래로 갈수록 얇아짐
            relative_pos = (r - glacier_rear) / max(1, glacier_front - glacier_rear)
            
            # 빙하 혀(tongue) 형태: 중앙 두껍고 앞/뒤 얇음
            long_profile = 1.0 - abs(relative_pos - 0.5) * 0.6
            
            # 빙하 앞부분(snout) 경사
            if r > glacier_front - int(h * 0.08):
                snout_factor = (glacier_front - r) / (h * 0.08)
                long_profile *= snout_factor
            
            for c in range(w):
                dx = abs(c - center)
                floor_w = int(w * valley_width * 0.3)
                
                if dx < floor_w + 12:
                    # 빙하 표면 (볼록, 중앙 두꺼움)
                    cross_profile = 1 - (dx / (floor_w + 12)) ** 2
                    ice_surface = glacier_thickness * cross_profile * long_profile
                    elevation[r, c] += ice_surface
    
    # === 현수곡 (Hanging Valley) ===
    if stage > 0.65:
        hang_progress = min(1, (stage - 0.65) / 0.25)
        
        # 지류 빙하가 덜 침식 → 높은 위치에 매달림
        hanging_valleys = [
            (int(h * 0.25), -1, 30 * hang_progress),  # 좌측 상류
            (int(h * 0.50), 1, 25 * hang_progress),   # 우측 중류
        ]
        
        for hy, side, height in hanging_valleys:
            hx = center + side * int(w * 0.42)
            
            for dy in range(-15, 16):
                for dx in range(-12, 13):
                    r, c = hy + dy, hx + dx
                    if 0 <= r < h and 0 <= c < w:
                        dist = np.sqrt(dy**2 + dx**2)
                        if dist < 14:
                            # 현수곡 입구 (높게 매달림)
                            notch = height * (1 - dist / 14) ** 0.7
                            elevation[r, c] = max(elevation[r, c], height + notch)
    
    # === 종퇴석 (Terminal Moraine) ===
    if stage > 0.55:
        moraine_progress = min(1, (stage - 0.55) / 0.25)
        moraine_row = int(h * 0.85)  # 빙하 최대 전진선
        moraine_height = 12 * moraine_progress
        
        for c in range(w):
            dx = abs(c - center)
            floor_w = int(w * valley_width * 0.35)
            if dx < floor_w + 25:
                ridge = moraine_height * (1 - (dx / (floor_w + 25)) ** 2)
                # 불규칙한 퇴적
                ridge *= 0.7 + 0.3 * np.sin(c * 0.3)
                elevation[moraine_row, c] += ridge
                elevation[moraine_row + 1, c] += ridge * 0.6
    
    # === 빙하호 (Tarn/Lake) ===
    if stage > 0.85:
        lake_progress = (stage - 0.85) / 0.15
        lake_center_y = int(h * 0.15)
        lake_radius = int(w * 0.12 * lake_progress)
        lake_depth = 10 * lake_progress
        
        for dy in range(-lake_radius - 3, lake_radius + 4):
            for dx in range(-lake_radius - 3, lake_radius + 4):
                r, c = lake_center_y + dy, center + dx
                if 0 <= r < h and 0 <= c < w:
                    dist = np.sqrt(dy**2 + dx**2)
                    if dist < lake_radius:
                        # 호수 바닥 (오목)
                        depth = lake_depth * (1 - (dist / lake_radius) ** 2)
                        elevation[r, c] = min(elevation[r, c], -depth)
    
    if return_metadata:
        return elevation, {
            'glacier_front': glacier_front,
            'glacier_rear': glacier_rear,
            'erosion_progress': erosion_progress,
            'phase': phase,
            'stage_description': _get_u_valley_stage_desc(stage)
        }
    
    return elevation


def _get_u_valley_stage_desc(stage: float) -> str:
    """U자곡 단계별 설명 (학술 기반)"""
    if stage < 0.15:
        return "🏞️ V자곡: 하천 침식으로 형성된 계곡 (빙하 없음)"
    elif stage < 0.35:
        return "❄️ 빙기/빙하 전진: 계곡빙하가 상류→하류로 진출"
    elif stage < 0.55:
        return "🧊 빙기 절정: 마식(abrasion)+플러킹(plucking) 활발"
    elif stage < 0.75:
        return "🌡️ 간빙기/빙하 후퇴: 하류→상류로 융해 후퇴"
    elif stage < 0.90:
        return "🗻 U자곡 노출: 현수곡(Hanging Valley) 드러남"
    else:
        return "💧 빙하호+종퇴석: 과굴착 바닥에 물 고임"


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
                             num_dunes: int = 3, return_metadata: bool = False) -> np.ndarray:
    """바르한 사구 형성 과정 애니메이션
    
    Stage 0~0.25: 모래 축적 (작은 원형 언덕 형성)
    Stage 0.25~0.5: 비대칭 발달 (바람받이 완경사, 바람그늘 급경사)
    Stage 0.5~0.75: 초승달 형태 발달 (오목면 형성)
    Stage 0.75~1.0: 뿔(horn) 완성 (바람 방향으로 연장)
    
    형성 원리:
    - 바람이 모래를 바람받이 사면으로 운반
    - 정상 넘어 바람그늘에 퇴적 (낙사면, slip face)
    - 가장자리 모래가 더 빨리 이동 → 뿔 형성
    """
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    # 사막 기반면
    elevation[:, :] = 5.0
    
    np.random.seed(42)
    
    for i in range(num_dunes):
        # 사구 위치 (고정)
        cx = w // 4 + (i % 2) * (w // 2)
        cy = int(h * 0.3) + i * (h // (num_dunes + 1))
        
        if cy >= h - 15:
            continue
        
        # Stage에 따른 크기 발달
        max_height = 12.0 + i * 3.0
        max_radius = int(w * 0.12)
        
        # Stage 0~0.25: 작은 원형 언덕
        if stage < 0.25:
            progress = stage / 0.25
            current_height = max_height * 0.3 * progress
            current_radius = int(max_radius * 0.4 * progress)
            asymmetry = 0  # 대칭
            horn_length = 0
            
        # Stage 0.25~0.5: 비대칭 발달
        elif stage < 0.5:
            progress = (stage - 0.25) / 0.25
            current_height = max_height * (0.3 + 0.4 * progress)
            current_radius = int(max_radius * (0.4 + 0.3 * progress))
            asymmetry = progress  # 점차 비대칭
            horn_length = 0
            
        # Stage 0.5~0.75: 초승달 형태
        elif stage < 0.75:
            progress = (stage - 0.5) / 0.25
            current_height = max_height * (0.7 + 0.2 * progress)
            current_radius = int(max_radius * (0.7 + 0.2 * progress))
            asymmetry = 1.0
            horn_length = int(max_radius * 0.4 * progress)
            
        # Stage 0.75~1.0: 뿔 완성
        else:
            progress = (stage - 0.75) / 0.25
            current_height = max_height * (0.9 + 0.1 * progress)
            current_radius = max_radius
            asymmetry = 1.0
            horn_length = int(max_radius * (0.4 + 0.4 * progress))
        
        if current_radius < 2:
            continue
            
        # 초승달 파라미터
        inner_ratio = 0.5 + 0.2 * asymmetry  # 안쪽 원 비율
        inner_offset = current_radius * 0.4 * asymmetry  # 오프셋
        
        for r in range(h):
            for c in range(w):
                dy = r - cy
                dx = c - cx
                
                dist = np.sqrt(dx**2 + dy**2)
                
                # 바깥 원 영역
                if dist < current_radius:
                    # 안쪽 원 (오목면) - 비대칭일 때만
                    dist_inner = np.sqrt(dx**2 + (dy - inner_offset)**2)
                    inner_r = current_radius * inner_ratio
                    
                    if asymmetry > 0.5 and dist_inner < inner_r:
                        # 오목면 안쪽은 낮게
                        continue
                    
                    # 높이 계산
                    radial_factor = 1 - (dist / current_radius) ** 1.5
                    
                    # 바람받이(상단) vs 바람그늘(하단) 비대칭
                    if dy < 0:
                        # 바람받이: 완만 (5-12° 경사)
                        slope_factor = 0.6 + 0.4 * (1 - asymmetry)
                    else:
                        # 바람그늘: 급경사 (30-34° 안식각)
                        slope_factor = 0.8 + 0.5 * asymmetry
                    
                    z = current_height * radial_factor * slope_factor
                    if z > 0.5:
                        elevation[r, c] = max(elevation[r, c], 5.0 + z)
                
                # 뿔 (horns) - stage 0.5 이후
                if horn_length > 2:
                    for side in [-1, 1]:
                        horn_cx = cx + side * (current_radius * 0.7)
                        horn_cy = cy + inner_offset
                        
                        dx_h = c - horn_cx
                        dy_h = r - horn_cy
                        
                        # 뿔 영역: 바람 방향으로 길쭉
                        horn_width = max(2, current_radius * 0.25)
                        if abs(dx_h) < horn_width and 0 < dy_h < horn_length:
                            horn_factor = (1 - dy_h / horn_length) ** 0.7
                            width_factor = 1 - (abs(dx_h) / horn_width) ** 2
                            z = current_height * 0.4 * horn_factor * width_factor
                            if z > 0.3:
                                elevation[r, c] = max(elevation[r, c], 5.0 + z)
    
    if return_metadata:
        return elevation, {
            'stage_description': _get_barchan_stage_desc(stage)
        }
    
    return elevation


def _get_barchan_stage_desc(stage: float) -> str:
    """바르한 단계별 설명"""
    if stage < 0.2:
        return "🏜️ 모래 축적: 장애물 주변 모래 쌓임 시작"
    elif stage < 0.4:
        return "⬆️ 언덕 성장: 원형 모래언덕 형성"
    elif stage < 0.6:
        return "↗️ 비대칭 발달: 바람받이 완경사, 바람그늘 급경사"
    elif stage < 0.8:
        return "🌙 초승달 형태: 오목면 형성, 뿔 발달 시작"
    else:
        return "🏜️ 바르한 완성: 뿔이 바람 방향으로 연장"
# ============================================
# 확장 지형 (Extended Landforms)
# ============================================

def create_incised_meander(grid_size: int = 100, stage: float = 1.0,
                           valley_depth: float = 80.0, num_terraces: int = 3,
                           return_metadata: bool = False) -> np.ndarray:
    """
    감입곡류 (Incised Meander) + 하안단구 (River Terraces)
    
    Stage 0~0.3: 자유곡류 (범람원 위, 침식기준면 높음)
    Stage 0.3~0.7: 융기 시작 → 하방침식 강화
    Stage 0.7~1.0: 깊은 협곡 + 하안단구 노출
    
    융기 환경에서 곡류가 암반을 파고 들어가면서 형성
    """
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    center_x = w // 2
    wl = h / 3  # 3개 굽이
    channel_width = max(3, w // 25)
    
    # 침식기준면 (stage에 따라 하강)
    # Stage 0: 기준면 높음 (자유곡류)
    # Stage 1: 기준면 낮음 (감입)
    base_level = valley_depth * (1 - stage * 0.9)  # 90% 하강
    
    # 곡류 진폭 (stage에 따라 고정화)
    if stage < 0.3:
        amplitude = w * 0.25 * (stage / 0.3)  # 사행 발달
    else:
        amplitude = w * 0.25  # 곡류 패턴 고정
    
    # 기반 고원 높이
    plateau_height = valley_depth
    elevation[:, :] = plateau_height
    
    # 현재 침식 깊이 (stage에 따라 증가)
    current_depth = (plateau_height - base_level) * min(1.0, (stage - 0.2) / 0.8) if stage > 0.2 else 0
    
    # 감입 곡류 파기
    for r in range(h):
        theta = 2 * np.pi * r / wl
        meander_x = center_x + amplitude * np.sin(theta)
        
        for c in range(w):
            dist = abs(c - meander_x)
            
            # 하도 바닥 (침식기준면까지)
            river_bottom = plateau_height - current_depth
            
            if dist < channel_width:
                # 하도 (가장 깊음)
                elevation[r, c] = max(base_level, river_bottom)
            elif dist < channel_width * 3:
                # 협곡 측벽 (V자형)
                t = (dist - channel_width) / (channel_width * 2)
                elevation[r, c] = river_bottom + current_depth * t
    
    # 하안단구 (stage > 0.5에서 형성)
    if stage > 0.5:
        terrace_progress = (stage - 0.5) / 0.5
        num_visible_terraces = int(num_terraces * terrace_progress) + 1
        
        for t_idx in range(min(num_visible_terraces, num_terraces)):
            terrace_height = plateau_height - current_depth * (0.3 + 0.25 * t_idx)
            terrace_width_start = channel_width * (3 + t_idx)
            terrace_width_end = channel_width * (4 + t_idx)
            
            for r in range(h):
                theta = 2 * np.pi * r / wl
                meander_x = center_x + amplitude * np.sin(theta) * (0.9 - 0.1 * t_idx)
                
                for c in range(w):
                    dist = abs(c - meander_x)
                    if terrace_width_start < dist < terrace_width_end:
                        if elevation[r, c] > terrace_height:
                            elevation[r, c] = terrace_height
    
    if return_metadata:
        return elevation, {
            'base_level': base_level,
            'current_depth': current_depth,
            'stage_description': _get_incised_stage_desc(stage)
        }
    
    return elevation


def _get_incised_stage_desc(stage: float) -> str:
    """감입곡류 단계별 설명"""
    if stage < 0.3:
        return "🌊 자유곡류 단계: 범람원 위를 자유롭게 사행"
    elif stage < 0.5:
        return "⬆️ 융기 시작: 침식기준면 하강, 하방침식 시작"
    elif stage < 0.7:
        return "⛏️ 감입 진행: 곡류 패턴 고정, 협곡 깊어짐"
    else:
        return "🏔️ 감입곡류 완성: 하안단구 형성, 과거 하상 노출"


def create_free_meander(grid_size: int = 100, stage: float = 1.0,
                        num_bends: int = 4, return_metadata: bool = False) -> np.ndarray:
    """
    자유곡류 (Free Meander) + 범람원 (Floodplain) + 자연제방 (Natural Levee)
    
    Stage 0~0.2: 직선 하천 (초기 하도)
    Stage 0.2~0.5: 사행 발달 (헬리컬 흐름에 의한 공격사면 침식)
    Stage 0.5~0.7: 곡류 진폭 증가 (사행도 > 1.5)
    Stage 0.7~0.9: 곡류 목 절단 (Neck Cutoff) → 우각호 형성
    Stage 0.9~1.0: 자연제방 완성 + 배후습지 분화
    
    헬리컬 흐름 (Helical Flow):
    - 곡류부 외측: 원심력 → 수면 상승 → 바닥에서 내측으로 횡류
    - 공격사면(Cut Bank): 침식
    - 활주사면(Point Bar): 퇴적
    """
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    # 범람원 기반
    base_height = 10.0
    elevation[:, :] = base_height
    
    center_x = w // 2
    channel_width = max(3, w // 20)
    wl = h / num_bends
    
    # Stage에 따른 사행 진폭
    if stage < 0.2:
        amplitude = w * 0.05  # 거의 직선
    else:
        amplitude = w * 0.3 * min(1.0, (stage - 0.1) / 0.4)
    
    # 사행도 계산
    sinuosity = 1.0 + amplitude / (h / num_bends) * 2
    
    # 공격사면/활주사면 위치 저장
    cutbank_positions = []
    pointbar_positions = []
    
    for r in range(h):
        theta = 2 * np.pi * r / wl
        meander_x = center_x + amplitude * np.sin(theta)
        
        # 곡률 방향 (공격사면 결정용)
        curvature = np.cos(theta)  # +: 오른쪽 공격사면, -: 왼쪽 공격사면
        
        for c in range(w):
            dist = c - meander_x
            abs_dist = abs(dist)
            
            if abs_dist < channel_width:
                # 하도 (비대칭 단면 - stage 후반에)
                if stage > 0.3:
                    # 공격사면 쪽은 더 깊음
                    if (curvature > 0 and dist > 0) or (curvature < 0 and dist < 0):
                        depth_factor = 1.2  # 공격사면
                        if r % 20 == 0:
                            cutbank_positions.append((r, c))
                    else:
                        depth_factor = 0.7  # 활주사면
                        if r % 20 == 0:
                            pointbar_positions.append((r, c))
                else:
                    depth_factor = 1.0
                elevation[r, c] = 5.0 - (channel_width - abs_dist) * 0.2 * depth_factor
                
            elif abs_dist < channel_width * 2 and stage > 0.5:
                # 자연제방 (Levee) - stage 후반에 발달
                levee_height = base_height + 1.5 * ((stage - 0.5) / 0.5)
                elevation[r, c] = levee_height
                
            elif abs_dist < channel_width * 5 and stage > 0.7:
                # 배후습지 (Backswamp) - 자연제방보다 낮음
                elevation[r, c] = base_height - 0.5
    
    # 우각호 (Oxbow Lake) - Stage 0.7 이후
    oxbow_formed = False
    if stage > 0.7:
        oxbow_progress = (stage - 0.7) / 0.3
        oxbow_y = h // 2
        oxbow_amplitude = amplitude * 1.4
        
        for dy in range(-int(wl/4), int(wl/4)):
            r = oxbow_y + dy
            if 0 <= r < h:
                theta = 2 * np.pi * dy / (wl/2)
                ox_x = center_x + oxbow_amplitude * np.sin(theta)
                
                for dc in range(-channel_width-2, channel_width + 3):
                    c = int(ox_x + dc)
                    if 0 <= c < w:
                        # 우각호 (고립된 호수)
                        elevation[r, c] = 4.0
                        oxbow_formed = True
    
    if return_metadata:
        return elevation, {
            'sinuosity': sinuosity,
            'amplitude': amplitude,
            'cutbank_positions': cutbank_positions[:5],  # 상위 5개
            'pointbar_positions': pointbar_positions[:5],
            'oxbow_formed': oxbow_formed,
            'stage_description': _get_meander_stage_desc(stage)
        }
    
    return elevation


def _get_meander_stage_desc(stage: float) -> str:
    """자유곡류 단계별 설명"""
    if stage < 0.2:
        return "📏 초기 하도: 거의 직선 흐름"
    elif stage < 0.4:
        return "🌀 사행 시작: 헬리컬 흐름으로 공격사면 침식 시작"
    elif stage < 0.6:
        return "🔄 곡류 발달: 사행도 증가, 활주사면 퇴적"
    elif stage < 0.8:
        return "✂️ 목 절단: 곡류 목 근접, 우각호 형성 시작"
    else:
        return "🏞️ 성숙 곡류: 자연제방 + 배후습지 + 우각호 완성"


def create_bird_foot_delta(grid_size: int = 100, stage: float = 1.0,
                           return_metadata: bool = False) -> np.ndarray:
    """조족상 삼각주 (Bird-foot Delta) - 미시시피강형
    
    Stage 0~0.3: 주 수로 형성
      - 단일 하도가 바다로 진입
      - 초기 퇴적 시작
    
    Stage 0.3~0.6: 분배수로 발달
      - 수로 분기 시작
      - 각 수로 양옆에 자연제방 형성
    
    Stage 0.6~1.0: 조족상 완성
      - 다수의 분배수로가 새발 모양으로 돌출
      - 각 finger 끝에서 퇴적 활발
    
    형성 조건:
    - 파랑 에너지 약함 (만 또는 내해)
    - 조석 영향 적음
    - 퇴적물 공급 풍부
    
    대표 사례: 미시시피강 삼각주
    """
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    elevation[:, :] = -5.0  # 바다
    
    apex_y = int(h * 0.12)
    center_x = w // 2
    
    # Stage에 따른 분배수로 개수
    if stage < 0.3:
        num_fingers = 1
    elif stage < 0.5:
        num_fingers = 3
    else:
        num_fingers = min(7, 3 + int(4 * (stage - 0.5) / 0.5))
    
    max_length = int((h - apex_y) * stage * 0.9)
    finger_width = max(3, int(4 * (1 - stage * 0.3)))  # 시간이 갈수록 좁아짐
    
    distributary_info = []
    
    for i in range(num_fingers):
        # 각도 분포 (중앙에서 양쪽으로)
        if num_fingers == 1:
            angle = 0
        else:
            angle = np.radians(-35 + 70 * i / (num_fingers - 1))
        
        finger_length = 0
        
        for d in range(max_length):
            r = apex_y + int(d * np.cos(angle))
            c = center_x + int(d * np.sin(angle))
            
            if 0 <= r < h and 0 <= c < w:
                finger_length = d
                
                # 분배수로 + 자연제방
                for dc in range(-finger_width, finger_width + 1):
                    for dr in range(-2, 3):
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < h and 0 <= nc < w:
                            dist = np.sqrt(dr**2 + dc**2)
                            
                            # 중앙: 수로 (낮음), 양쪽: 자연제방 (높음)
                            if abs(dc) < 2:
                                # 수로
                                z = 2.0 * (1 - d / max_length) * stage
                            else:
                                # 자연제방
                                z = 6.0 * (1 - d / max_length) * (1 - (abs(dc) - 2) / finger_width) * stage
                            
                            elevation[nr, nc] = max(elevation[nr, nc], z)
        
        distributary_info.append({
            'angle_deg': np.degrees(angle),
            'length': finger_length
        })
    
    # 상류 하천
    for r in range(apex_y):
        for dc in range(-4, 5):
            if 0 <= center_x + dc < w:
                channel_depth = 3.0 * (1 - abs(dc) / 5)
                elevation[r, center_x + dc] = 5.0 + channel_depth
    
    if return_metadata:
        return elevation, {
            'num_distributaries': num_fingers,
            'max_length': max_length,
            'distributary_info': distributary_info,
            'stage_description': _get_bird_foot_stage_desc(stage)
        }
    
    return elevation


def _get_bird_foot_stage_desc(stage: float) -> str:
    """조족상 삼각주 단계별 설명"""
    if stage < 0.2:
        return "🏞️ 초기: 단일 하도가 바다로 진입"
    elif stage < 0.4:
        return "🌊 퇴적 시작: 하구에서 퇴적물 축적"
    elif stage < 0.6:
        return "🔀 분기 발생: 수로가 여러 갈래로 나뉨"
    elif stage < 0.8:
        return "🦶 조족상 발달: 각 finger에 자연제방 형성"
    else:
        return "🦆 조족상 완성: 새발 모양 삼각주"


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
                  depth: float = 50.0, return_metadata: bool = False) -> np.ndarray:
    """권곡 (Cirque) 형성과정 - 학술 자료 기반
    
    Stage 0~0.15: 산악 지형 (빙하 없음)
    Stage 0.15~0.30: 니발 침식 (Nivation) - 만년설로 얕은 함지 형성
    Stage 0.30~0.45: 빙기/빙하 생성 - 피른화 → 빙하 얼음
    Stage 0.45~0.60: 빙기 절정 - 회전류(rotational flow) 침식
    Stage 0.60~0.75: 간빙기/빙하 후퇴 - 가장자리부터 융해
    Stage 0.75~1.0: 빙하 소멸 - 턴(Tarn) 호수 형성
    
    핵심 과정:
    - 니발 침식: 동결풍화로 암석 파쇄
    - 회전류: 빙하가 반원형으로 회전하며 바닥 연마
    - 베르그슈런트: 빙하/후벽 사이 크레바스 → 급경사 후벽
    - 과굴착(overdeepening): 바닥이 빙하 혀보다 깊어짐
    """
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    # 산악 배경
    mountain_height = depth + 60.0
    elevation[:, :] = mountain_height
    
    # 권곡 위치 (상단 중앙)
    cirque_y = int(h * 0.32)
    cirque_x = w // 2
    
    # === 단계별 상태 계산 ===
    if stage < 0.15:
        # 산악 지형 (빙하 없음)
        erosion = 0.0
        glacier_fill = 0.0
        phase = "pre_glacial"
    elif stage < 0.30:
        # 니발 침식: 만년설 아래 동결풍화
        erosion = (stage - 0.15) / 0.15 * 0.15
        glacier_fill = 0.0
        phase = "nivation"
    elif stage < 0.45:
        # 빙기: 피른 → 빙하 생성
        erosion = 0.15 + (stage - 0.30) / 0.15 * 0.25
        glacier_fill = (stage - 0.30) / 0.15
        phase = "glacial_advance"
    elif stage < 0.60:
        # 빙기 절정: 회전류 침식 활발
        erosion = 0.40 + (stage - 0.45) / 0.15 * 0.45
        glacier_fill = 1.0
        phase = "glacial_max"
    elif stage < 0.75:
        # 간빙기: 빙하 후퇴
        erosion = 0.85 + (stage - 0.60) / 0.15 * 0.1
        glacier_fill = 1.0 - (stage - 0.60) / 0.15
        phase = "glacial_retreat"
    else:
        # 빙하 소멸
        erosion = 0.95 + (stage - 0.75) / 0.25 * 0.05
        glacier_fill = 0.0
        phase = "post_glacial"
    
    # === 권곡 형태 계산 ===
    base_radius = int(w * 0.10)
    cirque_radius = base_radius + int(w * 0.18 * erosion)
    bowl_depth = depth * (0.1 + 0.9 * erosion)
    
    # 후벽 경사도 (베르그슈런트 동결풍화 → 급해짐)
    headwall_steepness = 0.2 + 0.8 * erosion
    
    # === 지형 생성 ===
    for r in range(h):
        for c in range(w):
            dy = r - cirque_y
            dx = c - cirque_x
            dist = np.sqrt(dy**2 + dx**2)
            
            if dist < cirque_radius:
                # 방향에 따른 형태
                angle = np.arctan2(dy, dx)
                
                if dy < 0:
                    # 후벽 (Headwall) - 베르그슈런트 동결풍화로 급경사
                    wall_factor = (1 - dist / cirque_radius) * headwall_steepness
                    base_elev = mountain_height - bowl_depth + bowl_depth * wall_factor
                else:
                    # 바닥 - 회전류 침식으로 오목 (과굴착)
                    # 중앙이 가장 깊고 가장자리로 갈수록 얕아짐
                    floor_profile = 1 - (dist / cirque_radius) ** 1.5
                    scour_depth = bowl_depth * 0.85 * floor_profile
                    base_elev = mountain_height - scour_depth
                
                elevation[r, c] = base_elev
            
            # 빙하 유출 곡(outlet)
            if cirque_y < r < cirque_y + cirque_radius * 0.7:
                if abs(c - cirque_x) < cirque_radius * 0.20:
                    outlet_dist = (r - cirque_y) / (cirque_radius * 0.7)
                    outlet_depth = bowl_depth * 0.35 * (1 - outlet_dist)
                    elevation[r, c] = min(elevation[r, c], mountain_height - outlet_depth)
    
    # === 빙하 시각화 ===
    if glacier_fill > 0 and phase != "post_glacial":
        ice_radius = int(cirque_radius * 0.80 * glacier_fill)
        ice_thickness = 25.0 * glacier_fill
        
        for r in range(cirque_y - ice_radius, cirque_y + int(ice_radius * 0.6)):
            for c in range(cirque_x - ice_radius, cirque_x + ice_radius):
                if 0 <= r < h and 0 <= c < w:
                    dist = np.sqrt((r - cirque_y)**2 + (c - cirque_x)**2)
                    if dist < ice_radius:
                        # 빙하 표면 - 볼록 (중앙 두꺼움)
                        ice_profile = 1 - (dist / ice_radius) ** 2
                        
                        # 후퇴 중이면 가장자리부터 녹음
                        if phase == "glacial_retreat":
                            melt_edge = ice_radius * 0.4
                            if dist > ice_radius - melt_edge:
                                ice_profile *= (ice_radius - dist) / melt_edge
                        
                        elevation[r, c] = max(elevation[r, c], 
                                             elevation[r, c] + ice_thickness * ice_profile)
    
    # === 턴(Tarn) 호수 ===
    if stage > 0.70:
        tarn_progress = min(1, (stage - 0.70) / 0.30)
        tarn_radius = int(cirque_radius * 0.35 * tarn_progress)
        tarn_depth = bowl_depth * 0.20 * tarn_progress
        
        for r in range(cirque_y - tarn_radius, cirque_y + int(tarn_radius * 0.4)):
            for c in range(cirque_x - tarn_radius, cirque_x + tarn_radius):
                if 0 <= r < h and 0 <= c < w:
                    dist = np.sqrt((r - cirque_y)**2 + (c - cirque_x)**2)
                    if dist < tarn_radius:
                        # 호수 바닥 (과굴착된 바닥에 물 고임)
                        water_depth = tarn_depth * (1 - (dist / tarn_radius) ** 2)
                        elevation[r, c] = min(elevation[r, c], 
                                             mountain_height - bowl_depth - water_depth)
    
    if return_metadata:
        return elevation, {
            'cirque_radius': cirque_radius,
            'bowl_depth': bowl_depth,
            'glacier_fill': glacier_fill,
            'erosion': erosion,
            'phase': phase,
            'stage_description': _get_cirque_stage_desc(stage)
        }
    
    return elevation


def _get_cirque_stage_desc(stage: float) -> str:
    """권곡 단계별 설명 (학술 기반)"""
    if stage < 0.15:
        return "🏔️ 산악 지형: 빙하 형성 이전"
    elif stage < 0.30:
        return "❄️ 니발 침식: 만년설 아래 동결풍화 시작"
    elif stage < 0.45:
        return "🧊 빙기/빙하 생성: 피른→빙하 얼음 압밀"
    elif stage < 0.60:
        return "⛏️ 빙기 절정: 회전류(rotational flow) 침식"
    elif stage < 0.75:
        return "🌡️ 간빙기/빙하 후퇴: 가장자리부터 융해"
    else:
        return "💧 턴(Tarn) 형성: 과굴착 바닥에 빙하호"


def create_horn(grid_size: int = 100, stage: float = 1.0,
                num_cirques: int = 4, return_metadata: bool = False) -> np.ndarray:
    """호른 (Horn) - 피라미드형 봉우리
    
    Stage 0~0.3: 초기 권곡 형성
      - 여러 방향에서 권곡 발달 시작
      - 능선 형태 유지
    
    Stage 0.3~0.6: 권곡 확장
      - 두부침식으로 권곡 깊어짐
      - 아레트(arête) 발달
    
    Stage 0.6~0.9: 호른 형성
      - 권곡들의 만남
      - 피라미드형 봉우리 돌출
    
    Stage 0.9~1.0: 성숙 호른
      - 날카로운 정상
      - 마터호른 형태
    
    대표 사례: 마터호른 (스위스), K2
    """
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    center = (h // 2, w // 2)
    max_peak_height = 120.0
    
    # Stage에 따른 봉우리 높이와 권곡 깊이
    if stage < 0.3:
        peak_height = max_peak_height * 0.6
        cirque_depth = 30.0 * (stage / 0.3)
    else:
        peak_height = max_peak_height * (0.6 + 0.4 * ((stage - 0.3) / 0.7))
        cirque_depth = 30.0 + 40.0 * ((stage - 0.3) / 0.7)
    
    cirque_radius = int(w * 0.28 * (0.6 + 0.4 * stage))
    
    # 기본 원뿔형 산체
    for r in range(h):
        for c in range(w):
            dy = r - center[0]
            dx = c - center[1]
            dist = np.sqrt(dy**2 + dx**2)
            
            # 원뿔형 기본 형태
            elevation[r, c] = peak_height * max(0, 1 - dist / (w * 0.45))
    
    # 다방향 권곡 파기
    cirque_centers = []
    arete_count = 0
    
    for i in range(num_cirques):
        angle = i * 2 * np.pi / num_cirques + np.pi / num_cirques  # 약간 회전
        cx = center[1] + int(cirque_radius * 0.7 * np.cos(angle))
        cy = center[0] + int(cirque_radius * 0.7 * np.sin(angle))
        cirque_centers.append((cy, cx))
        
        for r in range(h):
            for c in range(w):
                cdist = np.sqrt((r - cy)**2 + (c - cx)**2)
                
                if cdist < cirque_radius * 0.6:
                    # 권곡 파기 (반그릇 형태)
                    floor_height = 20.0 + cirque_depth * (cdist / (cirque_radius * 0.6)) ** 0.5
                    
                    # 후벽 방향 (중심쪽)으로 더 급경사
                    dir_to_center = np.sqrt((r - center[0])**2 + (c - center[1])**2)
                    if dir_to_center < cirque_radius * 0.5:
                        floor_height += 20.0 * (1 - dir_to_center / (cirque_radius * 0.5))
                    
                    elevation[r, c] = min(elevation[r, c], floor_height)
    
    # 아레트 강화 (인접 권곡 사이 능선)
    for i in range(num_cirques):
        next_i = (i + 1) % num_cirques
        cy1, cx1 = cirque_centers[i]
        cy2, cx2 = cirque_centers[next_i]
        
        # 두 권곡 중간점
        mid_y, mid_x = (cy1 + cy2) // 2, (cx1 + cx2) // 2
        
        for r in range(h):
            for c in range(w):
                # 능선 방향에 가까운 픽셀은 높이 유지
                dist_to_mid = np.sqrt((r - mid_y)**2 + (c - mid_x)**2)
                if dist_to_mid < cirque_radius * 0.3:
                    dist_to_center = np.sqrt((r - center[0])**2 + (c - center[1])**2)
                    if dist_to_center < cirque_radius * 0.5:
                        ridge_boost = 15.0 * stage * (1 - dist_to_mid / (cirque_radius * 0.3))
                        elevation[r, c] = min(elevation[r, c] + ridge_boost, peak_height)
    
    if return_metadata:
        return elevation, {
            'peak_height': peak_height,
            'num_cirques': num_cirques,
            'cirque_depth': cirque_depth,
            'cirque_radius': cirque_radius,
            'cirque_centers': cirque_centers,
            'stage_description': _get_horn_stage_desc(stage)
        }
    
    return elevation


def _get_horn_stage_desc(stage: float) -> str:
    """호른 단계별 설명"""
    if stage < 0.2:
        return "🏔️ 초기 산체: 원뿔형 산, 니발 영역 형성"
    elif stage < 0.4:
        return "🧊 빙기/빙하 전진: 여러 방향에서 권곡 발달"
    elif stage < 0.6:
        return "❄️ 빙기 절정: 권곡 확장, 아레트 형성"
    elif stage < 0.8:
        return "🌡️ 간빙기/빙하 후퇴: 피라미드 봉우리 노출"
    else:
        return "⛰️ 성숙 호른: 날카로운 정상 (마터호른형)"


def create_shield_volcano(grid_size: int = 100, stage: float = 1.0,
                          max_height: float = 40.0, return_metadata: bool = False) -> np.ndarray:
    """순상화산 (Shield Volcano) - 하와이형
    
    Stage 0~0.3: 해저 분출 → 해수면 도달
    Stage 0.3~0.6: 용암류 반복 → 완만한 순상 형성
    Stage 0.6~0.8: 정상부 확장 + 중앙 화구 형성
    Stage 0.8~1.0: 정상 칼데라 + 용암 흐름 흔적
    
    특징:
    - 현무암질 용암 (유동성 높음)
    - 경사 5-10°
    - 용암류가 넓게 퍼짐
    """
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    center = (h // 2, w // 2)
    max_radius = int(w * 0.45)
    
    # Stage에 따른 반경 성장
    current_radius = int(max_radius * min(1.0, stage * 1.3))
    current_height = max_height * stage
    
    for r in range(h):
        for c in range(w):
            dist = np.sqrt((r - center[0])**2 + (c - center[1])**2)
            
            if dist < current_radius and current_radius > 0:
                # 완만한 포물선 형태 (경사 5-10도)  
                radial_factor = 1 - (dist / current_radius) ** 1.8
                elevation[r, c] = current_height * radial_factor
    
    # 용암류 흔적 (방사상) - stage 0.4 이후
    if stage > 0.4:
        np.random.seed(42)
        num_flows = 6
        for i in range(num_flows):
            angle = 2 * np.pi * i / num_flows + np.random.random() * 0.3
            flow_length = int(current_radius * (0.6 + 0.4 * stage))
            flow_width = 3 + int(2 * stage)
            
            for d in range(10, flow_length):
                fx = int(center[1] + d * np.cos(angle))
                fy = int(center[0] + d * np.sin(angle))
                
                for dw in range(-flow_width, flow_width + 1):
                    tx = int(fx + dw * np.sin(angle))
                    ty = int(fy - dw * np.cos(angle))
                    
                    if 0 <= ty < h and 0 <= tx < w:
                        # 용암류 융기
                        flow_height = 2.0 * (1 - abs(dw) / flow_width) * (1 - d / flow_length)
                        elevation[ty, tx] += flow_height
    
    # 정상부 화구/칼데라 - stage 0.6 이후
    if stage > 0.6:
        caldera_progress = (stage - 0.6) / 0.4
        crater_radius = int(max_radius * 0.08 * (1 + caldera_progress))
        crater_depth = 5.0 * caldera_progress
        
        for r in range(h):
            for c in range(w):
                dist = np.sqrt((r - center[0])**2 + (c - center[1])**2)
                if dist < crater_radius:
                    # 함몰 칼데라
                    depression = crater_depth * (1 - (dist / crater_radius) ** 2)
                    elevation[r, c] = max(elevation[r, c] - depression, current_height * 0.85)
    
    if return_metadata:
        return elevation, {
            'current_radius': current_radius,
            'current_height': current_height,
            'stage_description': _get_shield_stage_desc(stage)
        }
    
    return elevation


def _get_shield_stage_desc(stage: float) -> str:
    """순상화산 단계별 설명"""
    if stage < 0.2:
        return "🌋 해저 분출: 현무암 용암 분출 시작"
    elif stage < 0.4:
        return "🏝️ 해수면 도달: 화산섬 형성"
    elif stage < 0.6:
        return "🔥 용암류 확장: 파호이호이 용암 흐름"
    elif stage < 0.8:
        return "⛰️ 순상 형성: 완만한 경사 (5-10°)"
    else:
        return "🕳️ 정상 칼데라: 마그마 빠짐 → 함몰"


def create_stratovolcano(grid_size: int = 100, stage: float = 1.0,
                         max_height: float = 80.0, return_metadata: bool = False) -> np.ndarray:
    """성층화산 (Stratovolcano) - 복합화산
    
    Stage 0~0.25: 초기 분출 → 원뿔 형성 시작
    Stage 0.25~0.5: 용암+화쇄물 교대 → 급경사 원뿔
    Stage 0.5~0.75: 고도 상승 + 분화구 발달
    Stage 0.75~1.0: 정상 분화구 + 화산쇄설물 사면
    
    특징:
    - 안산암질/유문암질 마그마
    - 경사 25-35°
    - 용암류 + 화쇄류 교대층
    """
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    center = (h // 2, w // 2)
    max_radius = int(w * 0.4)
    
    # Stage에 따른 성장
    current_radius = int(max_radius * min(1.0, stage * 1.2))
    current_height = max_height * stage
    
    for r in range(h):
        for c in range(w):
            dist = np.sqrt((r - center[0])**2 + (c - center[1])**2)
            
            if dist < current_radius and current_radius > 0:
                # 급한 원뿔 (경사 25-35도)
                radial_factor = 1 - (dist / current_radius) ** 0.8
                elevation[r, c] = current_height * radial_factor
    
    # 층리 표현 (작은 요철) - stage 0.3 이후
    if stage > 0.3:
        np.random.seed(42)
        num_layers = int(5 * stage)
        for layer in range(num_layers):
            layer_radius = current_radius * (0.3 + 0.7 * layer / max(1, num_layers))
            layer_height = current_height * (0.2 + 0.6 * layer / max(1, num_layers))
            
            for r in range(h):
                for c in range(w):
                    dist = np.sqrt((r - center[0])**2 + (c - center[1])**2)
                    if abs(dist - layer_radius) < 3:
                        # 층리 경계에 약간의 요철
                        bump = 1.5 * np.sin(np.arctan2(r - center[0], c - center[1]) * 8)
                        elevation[r, c] += bump
    
    # 정상부 분화구 - stage 0.5 이후
    if stage > 0.5:
        crater_progress = (stage - 0.5) / 0.5
        crater_radius = int(max_radius * 0.06 * (1 + crater_progress * 0.5))
        crater_depth = 12.0 * crater_progress
        
        for r in range(h):
            for c in range(w):
                dist = np.sqrt((r - center[0])**2 + (c - center[1])**2)
                if dist < crater_radius:
                    # 분화구
                    if dist < crater_radius * 0.7:
                        elevation[r, c] = current_height - crater_depth
                    else:
                        # 분화구 테두리
                        rim_factor = (dist - crater_radius * 0.7) / (crater_radius * 0.3)
                        elevation[r, c] = current_height - crater_depth + crater_depth * rim_factor
    
    if return_metadata:
        return elevation, {
            'current_height': current_height,
            'stage_description': _get_strato_stage_desc(stage)
        }
    
    return elevation


def _get_strato_stage_desc(stage: float) -> str:
    """성층화산 단계별 설명"""
    if stage < 0.2:
        return "🌋 초기 분출: 화산쇄설물 분출"
    elif stage < 0.4:
        return "🔥 원뿔 형성: 용암 + 화쇄류 교대"
    elif stage < 0.6:
        return "⛰️ 급경사 발달: 성층 구조 형성"
    elif stage < 0.8:
        return "🗻 고도 상승: 분화구 발달"
    else:
        return "💨 정상 분화구: 분연 활동 가능"


def create_caldera(grid_size: int = 100, stage: float = 1.0,
                   rim_height: float = 50.0, return_metadata: bool = False) -> np.ndarray:
    """칼데라 (Caldera) - 화산 정상부 함몰
    
    Stage 0~0.3: 성층화산 성장 (분화 활동)
    Stage 0.3~0.5: 대분화 → 마그마방 공동화
    Stage 0.5~0.8: 정상부 함몰 (칼데라 형성)
    Stage 0.8~1.0: 칼데라 확장 + 호수 형성 (백두산 천지)
    
    핵심 과정:
    - 마그마방 비워짐 → 지지력 상실
    - 정상부 함몰 → 넓은 원형 분지
    - 칼데라 직경 수 km ~ 수십 km
    """
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    center = (h // 2, w // 2)
    max_outer = int(w * 0.45)
    
    if stage < 0.3:
        # Stage 0~0.3: 성층화산 성장
        progress = stage / 0.3
        volcano_height = rim_height * 1.5 * progress
        volcano_radius = int(max_outer * 0.8 * progress)
        
        for r in range(h):
            for c in range(w):
                dist = np.sqrt((r - center[0])**2 + (c - center[1])**2)
                if dist < volcano_radius and volcano_radius > 0:
                    # 성층화산 형태
                    elevation[r, c] = volcano_height * (1 - (dist / volcano_radius) ** 0.9)
        
        # 작은 분화구
        crater_r = max(2, int(volcano_radius * 0.08))
        for r in range(h):
            for c in range(w):
                dist = np.sqrt((r - center[0])**2 + (c - center[1])**2)
                if dist < crater_r:
                    elevation[r, c] = volcano_height * 0.85
                    
    elif stage < 0.5:
        # Stage 0.3~0.5: 대분화 시작, 함몰 시작
        progress = (stage - 0.3) / 0.2
        volcano_height = rim_height * 1.5
        collapse_depth = rim_height * 0.5 * progress
        collapse_radius = int(max_outer * 0.15 * (1 + progress))
        
        for r in range(h):
            for c in range(w):
                dist = np.sqrt((r - center[0])**2 + (c - center[1])**2)
                if dist < max_outer * 0.8:
                    # 화산체
                    base = volcano_height * (1 - (dist / (max_outer * 0.8)) ** 0.9)
                    
                    if dist < collapse_radius:
                        # 함몰 시작
                        elevation[r, c] = base - collapse_depth * (1 - (dist / collapse_radius) ** 2)
                    else:
                        elevation[r, c] = base
                        
    elif stage < 0.8:
        # Stage 0.5~0.8: 칼데라 확장
        progress = (stage - 0.5) / 0.3
        caldera_radius = int(max_outer * (0.2 + 0.25 * progress))  # 점점 넓어짐
        collapse_depth = rim_height * (0.5 + 0.4 * progress)
        
        for r in range(h):
            for c in range(w):
                dist = np.sqrt((r - center[0])**2 + (c - center[1])**2)
                
                if dist < max_outer:
                    if dist < caldera_radius:
                        # 칼데라 바닥 (평탄)
                        elevation[r, c] = rim_height * 1.5 - collapse_depth
                    else:
                        # 칼데라 벽 + 외륜산
                        wall_progress = (dist - caldera_radius) / (max_outer - caldera_radius)
                        if wall_progress < 0.3:
                            # 급경사 벽
                            elevation[r, c] = (rim_height * 1.5 - collapse_depth) + rim_height * 0.8 * (wall_progress / 0.3)
                        else:
                            # 외륜산 사면
                            elevation[r, c] = rim_height * (1 - (wall_progress - 0.3) / 0.7) * 1.2
                            
    else:
        # Stage 0.8~1.0: 칼데라 완성 + 호수
        progress = (stage - 0.8) / 0.2
        caldera_radius = int(max_outer * 0.45)  # 최종 크기
        
        for r in range(h):
            for c in range(w):
                dist = np.sqrt((r - center[0])**2 + (c - center[1])**2)
                
                if dist < max_outer:
                    if dist < caldera_radius:
                        # 칼데라 바닥 (호수)
                        water_level = 5.0
                        elevation[r, c] = water_level - 3.0 * (1 - (dist / caldera_radius) ** 2)
                    elif dist < caldera_radius + 8:
                        # 급경사 벽
                        wall_t = (dist - caldera_radius) / 8
                        elevation[r, c] = 5.0 + rim_height * 0.9 * wall_t
                    else:
                        # 외륜산
                        outer_t = (dist - caldera_radius - 8) / (max_outer - caldera_radius - 8)
                        elevation[r, c] = rim_height * (1 - outer_t ** 0.8) * 0.9
    
    if return_metadata:
        return elevation, {
            'stage_description': _get_caldera_stage_desc(stage)
        }
    
    return elevation


def _get_caldera_stage_desc(stage: float) -> str:
    """칼데라 단계별 설명"""
    if stage < 0.2:
        return "🌋 성층화산 성장: 분화 활동으로 산체 형성"
    elif stage < 0.4:
        return "💥 대분화: 마그마 대량 분출"
    elif stage < 0.6:
        return "🕳️ 함몰 시작: 마그마방 비워짐 → 지지력 상실"
    elif stage < 0.8:
        return "⬇️ 칼데라 확장: 정상부 함몰 확대"
    else:
        return "💧 칼데라 호수: 융해수 고임 (백두산 천지)"


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

def create_fjord(grid_size: int = 100, stage: float = 1.0,
                 return_metadata: bool = False) -> np.ndarray:
    """피오르드 (Fjord) 형성과정 - 학술 자료 기반
    
    Stage 0.0~0.15: V자곡 (하천 침식 지형, 해안까지 연결)
    Stage 0.15~0.30: 빙기 - 빙하 전진 (산지→해안)
    Stage 0.30~0.50: 빙기 절정 - 해수면 이하 과굴착(overdeepening)
    Stage 0.50~0.70: 간빙기 - 빙하 후퇴 + 해침(sea invasion)
    Stage 0.70~0.85: 해침 진행 - 바닷물 협곡 채움
    Stage 0.85~1.0: 피오르드 완성 - 문턱(sill) 가시화
    
    핵심 과정:
    - 과굴착: 빙하 무게로 해수면 이하까지 침식 (내륙이 더 깊음)
    - 문턱(sill): 빙하 말단 퇴적물로 입구가 얕아짐
    - 해침: 빙하 후퇴 시 바닷물이 빙하 뒤따라 유입
    """
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    # 산악 지형
    elevation[:, :] = 100.0
    
    center = w // 2
    valley_width = int(w * 0.22)
    
    # === 단계별 상태 계산 ===
    if stage < 0.15:
        # V자곡 상태 (빙하 없음)
        glacier_front = 0
        glacier_rear = 0
        erosion = 0.0
        sea_level = h  # 바다 없음
        phase = "pre_glacial"
    elif stage < 0.30:
        # 빙기: 빙하 전진 (산지→해안)
        advance = (stage - 0.15) / 0.15
        glacier_rear = int(h * 0.05)
        glacier_front = int(h * 0.05 + h * 0.85 * advance)
        erosion = advance * 0.3
        sea_level = h
        phase = "glacial_advance"
    elif stage < 0.50:
        # 빙기 절정: 해안 도달 + 과굴착
        glacier_rear = int(h * 0.05)
        glacier_front = int(h * 0.95)  # 해안까지
        erosion = 0.3 + (stage - 0.30) / 0.20 * 0.6
        sea_level = h
        phase = "glacial_max"
    elif stage < 0.70:
        # 간빙기: 빙하 후퇴 + 해침
        retreat = (stage - 0.50) / 0.20
        glacier_front = int(h * 0.95 - h * 0.6 * retreat)
        glacier_rear = int(h * 0.05 + h * 0.20 * retreat)
        erosion = 0.9 + retreat * 0.08
        sea_level = int(h * (1 - 0.3 * retreat))  # 바닷물 상류로
        phase = "glacial_retreat"
    elif stage < 0.85:
        # 해침 진행
        sea_progress = (stage - 0.70) / 0.15
        glacier_front = int(h * 0.35 * (1 - sea_progress))
        glacier_rear = int(h * 0.25 + h * 0.1 * sea_progress)
        erosion = 0.98
        sea_level = int(h * 0.7 - h * 0.5 * sea_progress)
        phase = "sea_invasion"
    else:
        # 피오르드 완성
        glacier_front = 0
        glacier_rear = 0
        erosion = 1.0
        sea_level = int(h * 0.1)  # 바다가 상류까지
        phase = "post_glacial"
    
    # === 지형 생성 ===
    max_depth = -55.0  # 과굴착 최대 깊이 (해수면 이하)
    
    for r in range(h):
        # 종단 경사: 상류 높음, 하류는 해수면
        base_height = (h - r) / h * 80.0
        
        # 과굴착: 내륙(상류)이 더 깊음
        overdeepen_factor = 1.0 - (r / h) * 0.4  # 상류 깊고 하류 얕음
        
        for c in range(w):
            dx = abs(c - center)
            
            if dx < valley_width:
                # U자곡 바닥
                # V→U 변환 + 과굴착
                if erosion > 0:
                    depth = max_depth * erosion * overdeepen_factor
                else:
                    depth = 10.0  # V자곡 바닥
                elevation[r, c] = depth
                
            elif dx < valley_width + 15:
                # U자 측벽 (급경사)
                t = (dx - valley_width) / 15
                floor = max_depth * erosion * overdeepen_factor if erosion > 0 else 10.0
                elevation[r, c] = floor + (100.0 - floor) * (t ** 0.4)
    
    # === 문턱 (Sill) - 빙하 최대 전진선 ===
    if stage > 0.55:
        sill_progress = min(1, (stage - 0.55) / 0.30)
        sill_row = int(h * 0.90)  # 피오르드 입구
        sill_height = 35.0 * sill_progress  # 문턱 높이 (바닥에서 솟아오름)
        
        for r in range(sill_row - 3, min(h, sill_row + 5)):
            for c in range(w):
                dx = abs(c - center)
                if dx < valley_width:
                    # 문턱 형태 (종퇴석 퇴적)
                    row_factor = 1 - abs(r - sill_row) / 4
                    if row_factor > 0:
                        ridge = sill_height * row_factor * (1 - (dx / valley_width) ** 2)
                        elevation[r, c] += ridge
    
    # === 빙하 시각화 ===
    if glacier_front > glacier_rear and phase not in ["pre_glacial", "post_glacial"]:
        glacier_thickness = 50.0 if phase == "glacial_max" else 40.0
        
        for r in range(glacier_rear, glacier_front):
            # 빙하 두께 프로파일
            relative_pos = (r - glacier_rear) / max(1, glacier_front - glacier_rear)
            long_profile = 1.0 - abs(relative_pos - 0.4) * 0.5
            
            # 빙하 말단(snout)
            if r > glacier_front - int(h * 0.10):
                snout = (glacier_front - r) / (h * 0.10)
                long_profile *= snout
            
            for c in range(w):
                dx = abs(c - center)
                if dx < valley_width:
                    cross_profile = 1 - (dx / valley_width) ** 2
                    ice_surface = glacier_thickness * cross_profile * long_profile
                    elevation[r, c] += ice_surface
    
    # === 바닷물 시각화 ===
    # 바다는 elevation < 0 인 구간에만 (실제로는 renderer에서 처리)
    
    if return_metadata:
        return elevation, {
            'glacier_front': glacier_front,
            'glacier_rear': glacier_rear,
            'erosion': erosion,
            'sea_level_row': sea_level,
            'phase': phase,
            'stage_description': _get_fjord_stage_desc(stage)
        }
    
    return elevation


def _get_fjord_stage_desc(stage: float) -> str:
    """피오르드 단계별 설명 (학술 기반)"""
    if stage < 0.15:
        return "🏞️ V자곡: 하천 침식 계곡이 해안까지 연결"
    elif stage < 0.30:
        return "🧊 빙기/빙하 전진: 계곡빙하가 산지→해안 진출"
    elif stage < 0.50:
        return "❄️ 빙기 절정: 해수면 이하 과굴착(overdeepening)"
    elif stage < 0.70:
        return "🌡️ 간빙기/빙하 후퇴: 해침(sea invasion) 시작"
    elif stage < 0.85:
        return "🌊 해침 진행: 바닷물이 협곡 채움"
    else:
        return "🌅 피오르드 완성: 문턱(sill) + 깊은 협만"


def create_drumlin(grid_size: int = 100, stage: float = 1.0,
                   num_drumlins: int = 5, return_metadata: bool = False) -> np.ndarray:
    """드럼린 (Drumlin) 형성과정 - 학술 자료 기반
    
    Stage 0~0.15: 빙하 이전 평원
    Stage 0.15~0.35: 빙기 - 대륙빙하 전진 (덮음)
    Stage 0.35~0.60: 빙기 절정 - 빙하 바닥에서 til 성형
    Stage 0.60~0.80: 간빙기 - 빙하 후퇴
    Stage 0.80~1.0: 드럼린 노출 (유선형 언덕군)
    
    핵심 과정:
    - 빙하 바닥의 til이 빙하 흐름 방향으로 성형
    - Stoss (상류/둥근) + Lee (하류/뾰족) 비대칭
    - 빙하 이동 방향 지시자
    """
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    # 빙하 퇴적 평원
    elevation[:, :] = 5.0
    
    # === 단계별 상태 계산 ===
    if stage < 0.15:
        glacier_cover = 0.0
        drumlin_visible = 0.0
        phase = "pre_glacial"
    elif stage < 0.35:
        # 빙기: 빙하 전진 (대륙빙하가 덮음)
        glacier_cover = (stage - 0.15) / 0.20
        drumlin_visible = 0.0
        phase = "glacial_advance"
    elif stage < 0.60:
        # 빙기 절정: 빙하 아래에서 드럼린 형성
        glacier_cover = 1.0
        drumlin_visible = (stage - 0.35) / 0.25  # 형성 중
        phase = "glacial_max"
    elif stage < 0.80:
        # 간빙기: 빙하 후퇴
        glacier_cover = 1.0 - (stage - 0.60) / 0.20
        drumlin_visible = 1.0
        phase = "glacial_retreat"
    else:
        # 드럼린 노출
        glacier_cover = 0.0
        drumlin_visible = 1.0
        phase = "post_glacial"
    
    # === 드럼린 생성 ===
    drumlin_positions = []
    np.random.seed(42)  # 재현성
    
    for i in range(num_drumlins):
        # 드럼린 위치 (빙하 흐름 방향: 왼쪽→오른쪽)
        cy = int(h * 0.20 + (i % 3) * h * 0.25)
        cx = int(w * 0.25 + (i // 3) * w * 0.25)
        drumlin_positions.append((cy, cx))
        
        # 드럼린 크기 - 가로로 길쭉 (눕혀진 숟가락)
        length = int(w * 0.22 * drumlin_visible)  # X방향 (빙하 흐름 방향) 길이
        width_val = int(h * 0.08 * drumlin_visible)  # Y방향 너비
        height_val = 15.0 * drumlin_visible
        
        if length > 0 and width_val > 0:
            for r in range(max(0, cy - width_val - 3), min(h, cy + width_val + 3)):
                for c in range(max(0, cx - length), min(w, cx + length)):
                    dy = (r - cy) / max(width_val, 1)  # Y축: 너비
                    dx = (c - cx) / max(length, 1)  # X축: 길이 (빙하 방향)
                    
                    # 유선형 (stoss-lee 비대칭) - X방향
                    if dx < 0:
                        # Stoss (상류/왼쪽) - 둥글고 완만
                        dist = np.sqrt(dy**2 + dx**2)
                    else:
                        # Lee (하류/오른쪽) - 뾰족하게 캐리
                        dist = np.sqrt(dy**2 + (dx * 1.8)**2)
                    
                    if dist < 1.0:
                        # 언덕 형태 - 부드러운 곡선
                        z = height_val * (1 - dist ** 1.5) * (1 - abs(dy) * 0.3)
                        elevation[r, c] = max(elevation[r, c], 5.0 + z)
    
    # === 빙하 덮음 시각화 ===
    if glacier_cover > 0 and phase != "post_glacial":
        ice_thickness = 25.0 * glacier_cover
        
        # 빙하 전진 위치
        ice_front = int(h * glacier_cover * 0.95)
        
        for r in range(ice_front):
            for c in range(w):
                # 빙하 표면 (약간 볼록)
                ice_surface = ice_thickness * (1 - (r / max(1, ice_front)) * 0.2)
                elevation[r, c] = max(elevation[r, c], 5.0 + ice_surface)
    
    if return_metadata:
        return elevation, {
            'glacier_cover': glacier_cover,
            'drumlin_visible': drumlin_visible,
            'num_drumlins': num_drumlins,
            'phase': phase,
            'stage_description': _get_drumlin_stage_desc(stage)
        }
    
    return elevation


def _get_drumlin_stage_desc(stage: float) -> str:
    """드럼린 단계별 설명"""
    if stage < 0.15:
        return "🏜️ 빙하 이전: 퇴적 평원"
    elif stage < 0.35:
        return "🧊 빙기/빙하 전진: 대륙빙하가 평원 덮음"
    elif stage < 0.60:
        return "❄️ 빙기 절정: 빙하 바닥에서 til 유선형 성형"
    elif stage < 0.80:
        return "🌡️ 간빙기/빙하 후퇴: 드럼린 노출 시작"
    else:
        return "🏔️ 드럼린 완성: 빙하 이동 방향 지시 언덕군"


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
                     drop_height: float = 50.0, return_metadata: bool = False) -> np.ndarray:
    """폭포 (Waterfall) - 두부침식으로 후퇴
    
    Stage 0.0~0.3: 폭포 형성 (하류에서 시작)
    Stage 0.3~0.7: 두부침식 진행 (상류로 후퇴)
    Stage 0.7~1.0: 협곡 발달 (깊은 곡저)
    
    차별침식 (Differential Erosion):
    - 경암층(hard rock): 침식에 강함 → 폭포 절벽 형성
    - 연암층(soft rock): 침식에 약함 → 언더컷팅 → 붕괴
    
    플런지풀(Plunge Pool):
    - 낙하수의 충격으로 바닥 침식
    - 와류(vortex)에 의한 포트홀 형성
    """
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    center = w // 2
    
    # 폭포 위치 (stage에 따라 상류로 후퇴)
    initial_fall = int(h * 0.75)
    final_fall = int(h * 0.25)
    retreat_distance = (initial_fall - final_fall) * stage
    fall_r = int(initial_fall - retreat_distance)
    
    # 상류 (높은 고원 - 경암층)
    hard_rock_height = drop_height + 30.0
    
    for r in range(fall_r):
        for c in range(w):
            # 상류로 갈수록 높아짐
            upstream_rise = (fall_r - r) * 0.3
            elevation[r, c] = hard_rock_height + upstream_rise
    
    # 폭포 절벽 (거의 수직)
    cliff_width = max(3, int(5 * stage))
    for r in range(fall_r, min(fall_r + cliff_width, h)):
        for c in range(w):
            t = (r - fall_r) / cliff_width
            # 수직에 가까운 낙하
            elevation[r, c] = hard_rock_height * (1 - t**0.5) + 10.0 * t**0.5
    
    # 하류 (연암층 - 침식됨)
    for r in range(fall_r + cliff_width, h):
        for c in range(w):
            downstream_drop = (r - fall_r - cliff_width) * 0.15
            elevation[r, c] = 10.0 - downstream_drop
    
    # 협곡 (폭포 후퇴 경로) - stage에 따라 발달
    gorge_start = fall_r + cliff_width
    gorge_end = initial_fall + 10
    gorge_depth = 10.0 * stage
    gorge_width = int(6 + 4 * stage)
    
    for r in range(gorge_start, min(gorge_end, h)):
        for dc in range(-gorge_width, gorge_width + 1):
            c = center + dc
            if 0 <= c < w:
                # V자 협곡 단면
                depth = gorge_depth * (1 - abs(dc) / gorge_width)
                elevation[r, c] -= depth
    
    # 하천 수로
    channel_width = 4
    for r in range(h):
        for dc in range(-channel_width, channel_width + 1):
            c = center + dc
            if 0 <= c < w:
                channel_depth = 3.0 * (1 - abs(dc) / channel_width)
                elevation[r, c] -= channel_depth
    
    # 플런지풀 (폭호)
    pool_r = fall_r + cliff_width + 3
    pool_depth = 12.0 + 5.0 * stage
    pool_radius = 8
    
    for dr in range(-pool_radius, pool_radius + 1):
        for dc in range(-pool_radius, pool_radius + 1):
            r_pos, c_pos = pool_r + dr, center + dc
            if 0 <= r_pos < h and 0 <= c_pos < w:
                dist = np.sqrt(dr**2 + dc**2)
                if dist < pool_radius:
                    pool_effect = pool_depth * (1 - (dist / pool_radius)**2)
                    elevation[r_pos, c_pos] = min(elevation[r_pos, c_pos], 5.0 - pool_effect)
    
    if return_metadata:
        return elevation, {
            'waterfall_position': fall_r,
            'retreat_distance': retreat_distance,
            'gorge_length': gorge_end - gorge_start if stage > 0.3 else 0,
            'plunge_pool_depth': pool_depth,
            'layer_info': {
                'hard_rock': {'height': hard_rock_height, 'description': '경암층 (저항성 높음)'},
                'soft_rock': {'height': 20, 'description': '연암층 (침식에 약함)'}
            },
            'stage_description': _get_waterfall_stage_desc(stage)
        }
    
    return elevation


def _get_waterfall_stage_desc(stage: float) -> str:
    """폭포 단계별 설명"""
    if stage < 0.2:
        return "🏞️ 폭포 형성: 경암-연암 경계에서 차별침식 시작"
    elif stage < 0.4:
        return "💧 플런지풀 발달: 낙하수 충격으로 폭호 형성"
    elif stage < 0.6:
        return "⛏️ 두부침식 진행: 연암 언더컷팅 → 경암 붕괴"
    elif stage < 0.8:
        return "🏔️ 폭포 후퇴: 상류로 이동, 협곡 연장"
    else:
        return "🗻 성숙 폭포: 깊은 협곡 + 넓은 플런지풀"


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


def create_lava_plateau(grid_size: int = 100, stage: float = 1.0,
                        return_metadata: bool = False) -> np.ndarray:
    """용암대지 (Lava Plateau) - 한탄강/제주도형
    
    Stage 0~0.25: 원래 V자곡 존재 (하천 흐름)
    Stage 0.25~0.5: 열하분출 → 용암이 V자곡 메움 (용암류)
    Stage 0.5~0.75: 용암대지 형성 (평탄화)
    Stage 0.75~1.0: 하천 재침식 → 새로운 협곡 형성
    
    핵심 과정:
    - 열하분출(fissure eruption): 선상으로 용암 분출
    - 홍수현무암(flood basalt): 넓은 지역 뒤덮음
    - 재침식(rejuvenation): 새 하천이 협곡 형성
    """
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    lava_mask = np.zeros((h, w), dtype=bool)  # 용암 위치 표시
    center = w // 2
    
    # 기반 고원 높이
    plateau_base = 30.0
    
    if stage < 0.25:
        # Stage 0~0.25: 원래 V자곡 (하천 흐름)
        v_depth = 30.0
        for r in range(h):
            for c in range(w):
                dx = abs(c - center)
                elevation[r, c] = plateau_base
                
                # V자곡
                if dx < 18:
                    v_shape = v_depth * (1 - dx / 18) ** 1.2
                    elevation[r, c] -= v_shape
                    
    elif stage < 0.5:
        # Stage 0.25~0.5: 용암 분출 → 골짜기 메움
        progress = (stage - 0.25) / 0.25
        v_depth = 30.0 * (1 - progress * 0.9)  # V자곡 점점 메워짐
        lava_thickness = 25.0 * progress
        
        for r in range(h):
            # 용암 흐름 범위 (상류에서 하류로 진행)
            flow_reach = int(h * progress)
            
            for c in range(w):
                dx = abs(c - center)
                elevation[r, c] = plateau_base
                
                # 잔여 V자곡
                if dx < 18:
                    v_shape = v_depth * (1 - dx / 18) ** 1.2
                    elevation[r, c] -= v_shape
                
                # 용암 채움
                if r < flow_reach and dx < 20:
                    lava_fill = lava_thickness * (1 - dx / 20) ** 0.8
                    elevation[r, c] += lava_fill
                    lava_mask[r, c] = True
                    
    elif stage < 0.75:
        # Stage 0.5~0.75: 용암대지 평탄화
        progress = (stage - 0.5) / 0.25
        
        for r in range(h):
            for c in range(w):
                dx = abs(c - center)
                
                # 평탄한 용암대지
                if dx < 25:
                    elevation[r, c] = plateau_base + 5.0
                    lava_mask[r, c] = True
                else:
                    # 가장자리 경사
                    edge_t = (dx - 25) / (w // 2 - 25)
                    elevation[r, c] = (plateau_base + 5.0) * (1 - edge_t ** 0.7)
                    
    else:
        # Stage 0.75~1.0: 새 협곡 형성
        progress = (stage - 0.75) / 0.25
        gorge_width = int(6 + 6 * progress)
        gorge_depth = 35.0 * progress
        
        for r in range(h):
            for c in range(w):
                dx = abs(c - center)
                
                # 용암대지 기반
                if dx < 25:
                    elevation[r, c] = plateau_base + 5.0
                    lava_mask[r, c] = True
                else:
                    edge_t = (dx - 25) / (w // 2 - 25)
                    elevation[r, c] = (plateau_base + 5.0) * (1 - edge_t ** 0.7)
                
                # 새로운 협곡 (하천 재침식)
                if dx < gorge_width:
                    gorge_shape = gorge_depth * (1 - (dx / gorge_width) ** 2)
                    elevation[r, c] -= gorge_shape
                    
                    # 수직 절벽 형성 (주상절리 효과)
                    if dx > gorge_width * 0.7:
                        elevation[r, c] -= 3.0  # 급경사
    
    if return_metadata:
        return elevation, {
            'lava_mask': lava_mask,
            'stage_description': _get_lava_plateau_stage_desc(stage)
        }
    
    return elevation


def _get_lava_plateau_stage_desc(stage: float) -> str:
    """용암대지 단계별 설명"""
    if stage < 0.2:
        return "🏞️ 원래 V자곡: 하천 침식에 의한 계곡"
    elif stage < 0.4:
        return "🌋 열하분출: 용암이 계곡을 따라 흐름"
    elif stage < 0.6:
        return "🔥 용암 홍수: 계곡을 완전히 메움"
    elif stage < 0.8:
        return "⬛ 용암대지 형성: 평탄한 현무암 대지"
    else:
        return "🏞️ 재침식: 새로운 하천이 협곡 형성 (주상절리)"


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

