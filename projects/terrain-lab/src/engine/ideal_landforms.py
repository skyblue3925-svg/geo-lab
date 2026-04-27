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
                           spread_angle: float = 120.0, num_channels: int = 7,
                           return_metadata: bool = False) -> np.ndarray:
    """삼각주 (River Delta) 형성과정 - 학술 자료 기반 (Gilbert-type Delta)
    
    Stage 0.0~0.25: 초기 퇴적 (Initial Deposition)
      - 하천이 정수역(바다/호수)에 유입
      - 유속 감소로 운반력 저하
      - Bottomset beds 형성 시작 (미립 점토/실트)
    
    Stage 0.25~0.50: Foreset Beds 발달
      - 굵은 퇴적물(모래, 자갈)이 델타 전면 경사면에 퇴적
      - 안식각(angle of repose) 약 25-35°로 경사
      - 델타 전진(progradation) 시작
    
    Stage 0.50~0.75: Topset Beds 형성
      - 분배수로(distributary) 발달
      - 상부 평탄면에 하천 퇴적물 축적
      - 자연제방(natural levee) 형성
    
    Stage 0.75~1.0: 성숙 삼각주
      - 다수의 분배수로가 부채꼴로 분기
      - Topset-Foreset-Bottomset 완전한 층서 형성
      - 지속적인 전진(progradation)
    
    퇴적 구조 (Gilbert, 1885):
    - Topset beds: 수평~완만 경사, 하천 퇴적물, 상부 평원
    - Foreset beds: 급경사(15-35°), 굵은 입자, 델타 전면
    - Bottomset beds: 수평, 미립 입자(점토/실트), 심해 퇴적
    
    Reference:
    - Gilbert (1885) Lake Bonneville
    - Galloway (1975) Delta classification
    - Bhattacharya (2006) Deltas in Sedimentary Geology
    """
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    apex_y = int(h * 0.2)
    center_x = w // 2
    
    # 배경: 바다/호수 (수심에 따른 경사)
    for r in range(h):
        base_depth = -5.0 - (r - apex_y) * 0.05  # 하류로 갈수록 깊어짐
        elevation[r, :] = base_depth
    
    # === Bottomset beds (stage 0.0부터 시작) ===
    bottomset_reach = int((h - apex_y) * min(1.0, stage * 1.5))  # 가장 멀리까지
    bottomset_zone = []
    
    for r in range(apex_y + int(bottomset_reach * 0.7), min(h, apex_y + bottomset_reach)):
        dist = r - apex_y
        width = int(dist * 0.6 * stage)
        for c in range(max(0, center_x - width), min(w, center_x + width)):
            # 미립 퇴적물 - 얇은 층
            bottomset_thickness = 0.5 * stage * (1 - abs(c - center_x) / max(width, 1))
            elevation[r, c] += bottomset_thickness
            bottomset_zone.append((r, c))
    
    # === Foreset beds (stage 0.2부터) ===
    foreset_zone = []
    if stage > 0.2:
        foreset_intensity = min(1.0, (stage - 0.2) / 0.4)
        foreset_angle = 25 + 10 * foreset_intensity  # 25-35° 경사
        
        foreset_start = int(apex_y + bottomset_reach * 0.3)
        foreset_end = int(apex_y + bottomset_reach * 0.7)
        
        for r in range(foreset_start, foreset_end):
            dist = r - apex_y
            half_angle = np.radians(spread_angle / 2) * min(1.0, stage * 1.2)
            
            for c in range(w):
                dx = c - center_x
                angle = np.arctan2(dx, dist) if dist > 0 else 0
                
                if abs(angle) < half_angle:
                    radial_dist = np.sqrt(dx**2 + dist**2)
                    relative_pos = (r - foreset_start) / max(foreset_end - foreset_start, 1)
                    
                    # Foreset 경사면 (급경사)
                    foreset_height = 8.0 * foreset_intensity * (1 - relative_pos) * (1 - abs(dx) / max(w // 3, 1))
                    elevation[r, c] = max(elevation[r, c], foreset_height)
                    foreset_zone.append((r, c))
    
    # === Topset beds (stage 0.4부터) ===
    topset_zone = []
    if stage > 0.4:
        topset_intensity = min(1.0, (stage - 0.4) / 0.4)
        
        for r in range(apex_y, int(apex_y + bottomset_reach * 0.4)):
            dist = r - apex_y
            half_angle = np.radians(spread_angle / 2) * topset_intensity
            
            for c in range(w):
                dx = c - center_x
                angle = np.arctan2(dx, dist) if dist > 0 else 0
                
                if abs(angle) < half_angle or dist < 5:
                    # Topset - 거의 수평, 두꺼운 퇴적
                    topset_height = 10.0 * topset_intensity * (1 - dist / max(bottomset_reach * 0.4, 1))
                    elevation[r, c] = max(elevation[r, c], topset_height)
                    topset_zone.append((r, c))
    
    # 상류 하천 (항상 존재)
    for r in range(apex_y):
        for dc in range(-3, 4):
            c = center_x + dc
            if 0 <= c < w:
                elevation[r, c] = 8.0 - abs(dc) * 0.5
                
    # 분배 수로 (stage 0.5 이후)
    distributary_count = 0
    if stage > 0.5:
        half_angle = np.radians(spread_angle / 2) * stage
        active_channels = int(num_channels * min(1.0, (stage - 0.5) / 0.5))
        distributary_count = active_channels
        
        for i in range(active_channels):
            channel_angle = -half_angle + (2 * half_angle) * (i / max(active_channels - 1, 1))
            for r in range(apex_y, apex_y + int(bottomset_reach * 0.6)):
                dist = r - apex_y
                c = int(center_x + dist * np.tan(channel_angle))
                if 0 <= c < w:
                    for dc in range(-2, 3):
                        if 0 <= c + dc < w:
                            # 수로 파기
                            channel_depth = 2.0 * (1 - abs(dc) / 3)
                            elevation[r, c + dc] -= channel_depth
    
    if return_metadata:
        # 전진(progradation) 거리 계산
        progradation_distance = bottomset_reach * 10  # 미터 단위 (가정)
        
        # 층서 정보
        bed_structure = {
            'topset': {
                'description': '상부 평탄층 - 분배수로와 자연제방',
                'slope': '<2°',
                'sediment': '사질(Sand), 실트',
                'thickness': f'{10 * stage:.1f}m'
            },
            'foreset': {
                'description': '전면 경사층 - 델타 전면 급경사면',
                'slope': '25-35° (안식각)',
                'sediment': '자갈(Gravel), 조사(Coarse Sand)',
                'thickness': f'{8 * stage:.1f}m'
            },
            'bottomset': {
                'description': '저부 수평층 - 심해 미립 퇴적물',
                'slope': '<1°',
                'sediment': '점토(Clay), 실트(Silt)',
                'thickness': f'{2 * stage:.1f}m'
            }
        }
        
        return elevation, {
            'stage_description': _get_delta_stage_desc(stage),
            'bed_structure': bed_structure,
            'progradation_distance': progradation_distance,
            'distributary_count': distributary_count,
            'delta_area': len(topset_zone) + len(foreset_zone),  # 상대적 면적
            'spread_angle': spread_angle * stage,
        }
                            
    return elevation


def _get_delta_stage_desc(stage: float) -> str:
    """삼각주 형성 단계별 설명"""
    if stage < 0.25:
        return "초기 퇴적: 하천이 정수역 진입, 유속 감소로 미립 퇴적물(Bottomset beds) 형성 시작"
    elif stage < 0.50:
        return "Foreset 발달: 굵은 퇴적물이 델타 전면에 경사층(25-35°) 형성, 전진(progradation) 시작"
    elif stage < 0.75:
        return "Topset 형성: 분배수로 발달, 상부 평탄면에 하천 퇴적물 축적, 자연제방 형성"
    else:
        return "성숙 삼각주: Topset-Foreset-Bottomset 완전한 Gilbert 구조, 지속적 전진"


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
                              valley_depth: float = 80.0,
                              return_metadata: bool = False) -> np.ndarray:
    """V자곡 (V-shaped Valley) 형성과정 - 학술 자료 기반
    
    Stage 0.0~0.2: 초기 침식 (Initial Incision)
      - 하천이 초기 고원면을 하방침식 시작
      - Hydraulic action (수력작용): 물의 힘으로 암반 파쇄
      - 하도가 아직 얕고 넓음
    
    Stage 0.2~0.5: 활발한 하방침식 (Active Downcutting)
      - Abrasion/Corrasion (마식): 하상하중(bedload)이 기반암을 마모
      - Solution/Corrosion (용식): 화학적 용해
      - V자 형태 발달 시작
      - Interlocking spurs (맞물림 돌출부) 형성
    
    Stage 0.5~0.8: 계곡 심화 (Valley Deepening)
      - 풍화작용: 노출된 계곡 사면 약화
      - Mass wasting (사면붕괴): 중력에 의한 물질 이동
      - Soil creep, rockfall, landslides
      - 하천이 붕괴 물질 운반 → 하상 유지
    
    Stage 0.8~1.0: 성숙 V자곡 (Mature V-Valley)
      - 급경사 사면 + 좁은 하곡저
      - 경암: 급경사 유지, 연암: 완만한 경사
      - 상류에서 침식기준면(base level)까지 하방침식 지속
    
    핵심 개념:
    - Stream Power Law: E = K * A^m * S^n
    - V형 단면은 하방침식 > 측방침식일 때 형성
    - 침식기준면으로부터의 거리가 클수록 침식 활발
    
    Reference: 
    - Summerfield (1991) Global Geomorphology
    - Charlton (2008) Fundamentals of Fluvial Geomorphology
    """
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    center = w // 2
    
    # 단계별 침식 깊이 계산 (비선형적 - 초기에 빠르고 후기에 느림)
    # Stream Power Law 기반 침식률
    erosion_rate = 1.0 - np.exp(-3.0 * stage)  # 지수 감쇠
    current_depth = valley_depth * erosion_rate
    
    # 단계별 사면 경사각 변화 (도 단위)
    # 초기: 급경사, 후기: 풍화/mass wasting으로 완만해짐
    if stage < 0.5:
        slope_angle = 35 + stage * 20  # 35° → 45°
    else:
        slope_angle = 55 - (stage - 0.5) * 10  # 45° → 50° (약간 감소)
    
    # V자 형태 계산
    slope_rad = np.radians(slope_angle)
    
    for r in range(h):
        # 상류-하류 경사 (종단면 경사)
        upstream_gradient = (h - r) / h * 30.0
        
        for c in range(w):
            dx = abs(c - center)
            
            # 초기 고원 상태
            base_height = 50.0
            
            # V자 형태 (경사각에 따른 사면 높이)
            if dx > 0:
                v_shape = dx * np.tan(slope_rad) * (current_depth / valley_depth)
            else:
                v_shape = 0
            
            # 최종 고도
            elevation[r, c] = base_height - current_depth + min(v_shape, current_depth) + upstream_gradient
            
    # Interlocking spurs (맞물림 돌출부) - stage 0.3 이후
    if stage > 0.3:
        spur_intensity = min(1.0, (stage - 0.3) / 0.4)
        num_spurs = 3
        for i in range(num_spurs):
            spur_y = int(h * (0.3 + i * 0.25))
            spur_side = (-1) ** i  # 교대로 좌우 배치
            
            for dy in range(-5, 6):
                r = spur_y + dy
                if 0 <= r < h:
                    spur_width = max(0, 5 - abs(dy))
                    for dc in range(spur_width):
                        c = center + spur_side * (w // 4 - dc * 2)
                        if 0 <= c < w:
                            elevation[r, c] += 8 * spur_intensity * (1 - abs(dy) / 5)
    
    # 하천 수로 (단계적으로 형성)
    if stage > 0.2:
        channel_intensity = min(1.0, (stage - 0.2) / 0.8)
        channel_width = 2 + int(stage * 2)  # 하류로 갈수록 넓어짐
        
        for r in range(h):
            # 하류로 갈수록 하폭 증가
            local_width = channel_width + r // 20
            for dc in range(-local_width, local_width + 1):
                c = center + dc
                if 0 <= c < w:
                    channel_depth = 5 * channel_intensity * (1 - abs(dc) / (local_width + 1))
                    elevation[r, c] -= channel_depth
    
    if return_metadata:
        # 침식 프로세스 정보
        erosion_processes = {}
        if stage < 0.3:
            erosion_processes = {
                'hydraulic_action': '수력작용 - 물의 충격력으로 암반 파쇄',
                'dominant': True
            }
        elif stage < 0.6:
            erosion_processes = {
                'abrasion': '마식 - 하상하중(bedload)이 기반암을 마모',
                'solution': '용식 - 가용성 암석의 화학적 용해',
                'dominant': True
            }
        else:
            erosion_processes = {
                'mass_wasting': '사면붕괴 - 풍화된 물질의 중력 이동',
                'weathering': '풍화 - 노출 사면의 기계적/화학적 분해',
                'dominant': True
            }
        
        return elevation, {
            'stage_description': _get_v_valley_stage_desc(stage),
            'erosion_processes': erosion_processes,
            'valley_depth': current_depth,
            'slope_angle': slope_angle,
            'v_angle': 2 * (90 - slope_angle),  # 협저각 (V의 각도)
            'interlocking_spurs': stage > 0.3,
            'erosion_rate': erosion_rate,
            'base_level_distance': (1 - stage) * 100,  # 침식기준면까지 남은 거리(m)
        }
    
    return elevation


def _get_v_valley_stage_desc(stage: float) -> str:
    """V자곡 형성 단계별 설명"""
    if stage < 0.2:
        return "초기 침식: 하천이 고원면을 수력작용(hydraulic action)으로 하방침식 시작"
    elif stage < 0.5:
        return "활발한 하방침식: 마식(abrasion)과 용식(solution)으로 V자 형태 발달, 맞물림 돌출부(interlocking spurs) 형성"
    elif stage < 0.8:
        return "계곡 심화: 사면 풍화 + 사면붕괴(mass wasting)로 물질 공급, 하천이 운반하여 V자 유지"
    else:
        return "성숙 V자곡: 급경사 사면 + 좁은 하곡저, 침식기준면 접근으로 하방침식 감소"


def create_barchan_animated(grid_size: int, stage: float,
                             num_dunes: int = 3, return_metadata: bool = False) -> np.ndarray:
    """바르한 사구 형성 과정 애니메이션 (학술 자료 기반)
    
    실제 바르한 사구 스케일:
    - 높이: 9-30m (일반), 최대 45m
    - 바람받이 경사: ~15°
    - 낙사면(slip face): 30-35° (안식각)
    - 폭: 최대 350-370m
    
    Stage 0~0.25: 모래 축적 (작은 원형 언덕 형성)
    Stage 0.25~0.5: 비대칭 발달 (바람받이 완경사, 바람그늘 급경사)
    Stage 0.5~0.75: 초승달 형태 발달 (오목면 형성)
    Stage 0.75~1.0: 뿔(horn) 완성 (바람 방향으로 연장)
    
    형성 원리 (바람 방향: 왼쪽→오른쪽):
    - 바람이 모래를 바람받이(왼쪽) 사면으로 운반
    - 정상 넘어 바람그늘(오른쪽)에 퇴적 (낙사면, slip face)
    - 가장자리 모래가 더 빨리 이동 → 뿔이 바람 하류로 뻗음
    """
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    # 사막 기반면: 0으로 설정 (사구 상대 높이가 잘 보이도록)
    elevation[:, :] = 0.0
    
    np.random.seed(42)
    current_radius = max(2, int(w * 0.12))
    
    for i in range(num_dunes):
        # 사구 위치 (고정)
        cy = int(h * 0.25) + (i % 2) * int(h * 0.3)
        cx = int(w * 0.30) + i * int(w * 0.20)
        
        if cx >= w - 15:
            continue
        
        # Stage에 따른 크기 발달
        # 학술 자료: 일반 바르한 높이 9-30m
        max_height = 15.0 + i * 5.0  # 15m, 20m, 25m (학술 범위 내)
        max_radius = max(2, int(w * 0.12))  # 폭 비율 약간 증가
        current_radius = max_radius
        
        # Stage 0~0.25: 작은 원형 언덕
        if stage < 0.25:
            progress = stage / 0.25
            current_height = max_height * 0.3 * progress
            current_radius = max(2, int(max_radius * 0.4 * progress))
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
            horn_length = int(max_radius * 0.5 * progress)
            
        # Stage 0.75~1.0: 뿔 완성
        else:
            progress = (stage - 0.75) / 0.25
            current_height = max_height * (0.9 + 0.1 * progress)
            current_radius = max_radius
            asymmetry = 1.0
            horn_length = int(max_radius * (0.5 + 0.4 * progress))
        
        if current_radius < 2:
            continue
            
        # 초승달 파라미터 (오목면이 바람 하류 쪽)
        inner_ratio = 0.5 + 0.2 * asymmetry
        inner_offset = current_radius * 0.4 * asymmetry  # X방향 오프셋 (바람 하류)
        
        for r in range(h):
            for c in range(w):
                dy = r - cy  # Y축
                dx = c - cx  # X축 (바람 방향)
                
                dist = np.sqrt(dx**2 + dy**2)
                
                # 바깥 원 영역
                if dist < current_radius:
                    # 안쪽 원 (오목면) - 바람 하류(오른쪽)에 위치
                    dist_inner = np.sqrt((dx - inner_offset)**2 + dy**2)
                    inner_r = current_radius * inner_ratio
                    
                    if asymmetry > 0.5 and dist_inner < inner_r:
                        # 오목면 안쪽은 낮게
                        continue
                    
                    # 높이 계산
                    radial_factor = 1 - (dist / current_radius) ** 1.5
                    
                    # 바람받이(왼쪽, ~15°) vs 바람그늘(오른쪽, 30-35° 안식각)
                    if dx < 0:
                        # 바람받이: 완만 (~15° 경사)
                        slope_factor = 0.5 + 0.3 * (1 - asymmetry)
                    else:
                        # 바람그늘: 급경사 (30-35° 안식각)
                        slope_factor = 0.9 + 0.3 * asymmetry
                    
                    z = current_height * radial_factor * slope_factor
                    if z > 0.3:
                        elevation[r, c] = max(elevation[r, c], z)
                
                # 뿔 (horns) - stage 0.5 이후, 바람 하류(오른쪽)로 뻗음
                if horn_length > 2:
                    for side in [-1, 1]:
                        horn_cy = cy + side * int(current_radius * 0.7)
                        horn_cx = cx + inner_offset
                        
                        dx_h = c - horn_cx
                        dy_h = r - horn_cy
                        
                        # 뿔 영역: 바람 방향(X방향)으로 길쭉
                        horn_width = max(2, current_radius * 0.22)
                        if abs(dy_h) < horn_width and 0 < dx_h < horn_length:
                            horn_factor = (1 - dx_h / horn_length) ** 0.7
                            width_factor = 1 - (abs(dy_h) / horn_width) ** 2
                            z = current_height * 0.4 * horn_factor * width_factor
                            if z > 0.2:
                                elevation[r, c] = max(elevation[r, c], z)
    
    if return_metadata:
        # 학술 자료 기반 메타데이터
        current_height_actual = 15.0 * stage  # 9-30m 범위 내
        dune_width = current_radius * 2 * 10  # 미터 단위 (가정: 1셀=5m)
        
        # 이동 속도 (작은 사구가 더 빠름, 1-100m/년)
        migration_rate = max(1, int(100 / (current_height_actual + 1)))  # m/년
        
        return elevation, {
            'stage_description': _get_barchan_stage_desc(stage),
            'windward_angle': 15,  # 고정: 학술 자료 기준
            'slip_face_angle': 32 + 3 * stage,  # 30-35° 안식각
            'horn_length': horn_length * 5,  # 미터 단위
            'dune_height': current_height_actual,  # m
            'dune_width': dune_width,  # m
            'migration_rate': migration_rate,  # m/년
            'wind_direction': '왼쪽 → 오른쪽 (서풍)',
            'crescent_shape': stage > 0.5,  # 초승달 형태 여부
            'processes': {
                'saltation': '도약 이동 - 모래알이 바람에 튀어오르며 이동',
                'creep': '표면 포행 - 모래알이 구르며 이동',
                'avalanche': '사태 - 낙사면(slip face)에서 안식각 초과 시 붕괴'
            }
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


def create_arcuate_delta(grid_size: int = 100, stage: float = 1.0,
                         return_metadata: bool = False) -> np.ndarray:
    """호상 삼각주 (Arcuate Delta) - 나일강형 - 학술 자료 기반
    
    파랑 우세형 삼각주 (Wave-dominated Delta)
    - 파랑 에너지가 하천 에너지보다 우세
    - 부드러운 호(arc) 형태의 해안선
    - 퇴적물이 연안류로 재분배
    
    Stage 0~0.3: 초기 퇴적 → 작은 돌출부
    Stage 0.3~0.6: 파랑 재분배 → 호형 해안 발달
    Stage 0.6~1.0: 성숙 호상 삼각주 완성
    
    Reference: Galloway (1975) Delta Classification
    """
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    elevation[:, :] = -5.0
    
    apex_y = int(h * 0.2)
    center_x = w // 2
    
    # 부드러운 호 형태
    max_reach = int((h - apex_y) * stage)
    arc_area = 0
    
    for r in range(apex_y, apex_y + max_reach):
        dist = r - apex_y
        arc_width = int(dist * 0.8)
        
        for c in range(max(0, center_x - arc_width), min(w, center_x + arc_width)):
            dx = abs(c - center_x)
            radial = np.sqrt(dx**2 + dist**2)
            
            edge_dist = arc_width - dx
            if edge_dist > 0:
                z = 10.0 * (1 - radial / (max_reach * 1.2)) * min(1, edge_dist / 10)
                elevation[r, c] = max(elevation[r, c], z * stage)
                arc_area += 1
                
    # 하천
    for r in range(apex_y):
        for dc in range(-4, 5):
            if 0 <= center_x + dc < w:
                elevation[r, center_x + dc] = 6.0
    
    if return_metadata:
        return elevation, {
            'stage_description': _get_arcuate_stage_desc(stage),
            'delta_type': 'Arcuate (호상형)',
            'dominant_process': 'Wave-dominated (파랑 우세)',
            'arc_width': max_reach * 0.8 * 10,  # 미터 단위
            'arc_area': arc_area * 25,  # m²
            'energy_ratio': {
                'river': '30-40%',
                'wave': '50-60%',
                'tidal': '<10%'
            },
            'characteristics': {
                'coastline': '부드러운 호(arc) 형태',
                'sediment_redistribution': '연안류에 의한 재분배',
                'beach_ridges': '해안 능선(beach ridge) 발달',
                'example': '나일강 삼각주 (이집트)'
            }
        }
                
    return elevation


def _get_arcuate_stage_desc(stage: float) -> str:
    """호상삼각주 단계별 설명"""
    if stage < 0.3:
        return "초기 퇴적: 하구에 작은 돌출부 형성, 파랑이 퇴적물 재분배"
    elif stage < 0.6:
        return "호형 발달: 파랑 에너지로 부채꼴 해안선 형성, 해안 능선 발달"
    else:
        return "성숙 호상 삼각주: 부드러운 호 형태 완성, 연안류 재분배 안정화"


def create_cuspate_delta(grid_size: int = 100, stage: float = 1.0,
                         return_metadata: bool = False) -> np.ndarray:
    """첨두상 삼각주 (Cuspate Delta) - 티베르강형 - 학술 자료 기반
    
    조류 우세형 삼각주 (Tide-dominated Delta)
    - 조류(tidal) 에너지가 우세하거나 하천-파랑 균형
    - 뾰족한 삼각형(cusp) 형태
    - 퇴적물이 조류에 의해 세장하게 연장
    
    Stage 0~0.3: 초기 돌출부
    Stage 0.3~0.6: 첨두형 발달
    Stage 0.6~1.0: 성숙 첨두상 삼각주
    
    Reference: Galloway (1975), Wright & Coleman (1973)
    """
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    elevation[:, :] = -5.0
    
    apex_y = int(h * 0.2)
    center_x = w // 2
    point_y = int(apex_y + (h - apex_y) * 0.8 * stage)
    
    # 뾰족한 삼각형 형태
    cusp_area = 0
    for r in range(apex_y, point_y):
        dist = r - apex_y
        total_dist = point_y - apex_y
        
        width = int((w // 3) * (1 - dist / max(total_dist, 1)))
        
        for c in range(max(0, center_x - width), min(w, center_x + width)):
            dx = abs(c - center_x)
            z = 10.0 * (1 - dist / max(total_dist, 1)) * (1 - dx / max(width, 1))
            elevation[r, c] = max(elevation[r, c], z * stage)
            cusp_area += 1
            
    # 하천
    for r in range(apex_y):
        for dc in range(-3, 4):
            if 0 <= center_x + dc < w:
                elevation[r, center_x + dc] = 6.0
    
    if return_metadata:
        cusp_length = (point_y - apex_y) * 10  # 미터 단위
        return elevation, {
            'stage_description': _get_cuspate_stage_desc(stage),
            'delta_type': 'Cuspate (첨두상형)',
            'dominant_process': 'Tide-dominated or Balanced (조류 우세/균형형)',
            'cusp_length': cusp_length,
            'cusp_area': cusp_area * 25,  # m²
            'cusp_angle': 45 - 15 * stage,  # 첨두각 (좁아짐)
            'energy_ratio': {
                'river': '35-45%',
                'wave': '25-35%',
                'tidal': '25-35%'
            },
            'characteristics': {
                'shape': '뾰족한 삼각형(cusp/tooth) 형태',
                'protrusion': '해안선에서 돌출',
                'tidal_channels': '조류 수로 발달',
                'example': '티베르강 삼각주 (이탈리아)'
            }
        }
                
    return elevation


def _get_cuspate_stage_desc(stage: float) -> str:
    """첨두삼각주 단계별 설명"""
    if stage < 0.3:
        return "초기 돌출: 하구에 삼각형 퇴적체 형성"
    elif stage < 0.6:
        return "첨두 발달: 하천 에너지로 해안선 돌출, 조류가 측면 정리"
    else:
        return "성숙 첨두상 삼각주: 뾰족한 삼각형 완성, 조류 수로 안정화"


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
            'stage_description': _get_strato_stage_desc(stage),
            'current_height': current_height,
            'current_radius': current_radius * 10,  # 미터 단위 (가정)
            'slope_angle': 30 - 5 * stage,  # 25-30° 범위
            'crater_formed': stage > 0.5,
            'magma_composition': {
                'type': 'Andesitic-Dacitic (안산암질-데이사이트질)',
                'SiO2_content': '55-70%',
                'viscosity': 'High (고점성)',
                'gas_content': 'High (고가스 함량)'
            },
            'layered_structure': {
                'description': '용암류 + 화산쇄설물 교호층 (Alternating Layers)',
                'lava_layers': f'{int(stage * 10)}개 (추정)',
                'pyroclastic_layers': f'{int(stage * 12)}개 (추정)',
                'layer_thickness': '0.5-5m'
            },
            'eruption_types': {
                'strombolian': '스트롬볼리: 소규모 용암/테프라 분출',
                'vulcanian': '불카니안: 폭발적 화산재/가스 분출',
                'plinian': '플리니안: 대규모 분출 (화산재 기둥 10km+)'
            },
            'hazards': {
                'pyroclastic_flow': '화산쇄설류 - 200-700°C, 150km/h+',
                'lahar': '라하르 - 화산이류 (강우 시 발생)',
                'lava_dome': '용암돔 - 고점성 용암의 화구 내 축적'
            }
        }
    
    return elevation


def _get_strato_stage_desc(stage: float) -> str:
    """성층화산 단계별 설명"""
    if stage < 0.25:
        return "초기 분출: 화산쇄설물(테프라) 분출로 넓은 기반 형성"
    elif stage < 0.50:
        return "원뿔 형성: 점성 용암류 + 화쇄류 교대 퇴적, 급경사(25-30°) 발달"
    elif stage < 0.75:
        return "고도 상승: 성층 구조 완성, 정상부 분화구 발달 시작"
    else:
        return "성숙 성층화산: 정상 분화구 + 분연 활동, 플리니안/불카니안 분출 가능"


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
                      num_mesas: int = 2, return_metadata: bool = False) -> np.ndarray:
    """메사/뷰트 (Mesa/Butte) - 탁상지 형성과정 - 학술 자료 기반
    
    Stage 0.0~0.25: 대지(Plateau) 상태
      - 수평 퇴적암층이 넓게 분포
      - 경암층(caprock)이 연암층을 보호
      - 침식 시작 전 상태
    
    Stage 0.25~0.50: 메사(Mesa) 발달
      - 측면 침식으로 대지가 고립되기 시작
      - 폭 > 높이 유지
      - 절벽(cliff) + 완사면(talus)
    
    Stage 0.50~0.75: 뷰트(Butte) 전이
      - 지속적 침식으로 폭 감소
      - 폭 ≈ 높이 또는 폭 < 높이
      - 탑 형태로 변화
    
    Stage 0.75~1.0: 첨탑(Pinnacle/Monument)
      - 극단적 침식으로 좁은 탑 형성
      - 최종 붕괴 직전 단계
    
    지질 구조 (위→아래):
    - Cap Rock (경암층): 사암, 석회암, 현무암 등 저항성 높음
    - Cliff Face (절벽): 경암층 하부, 수직~급경사
    - Talus Slope (애추): 붕괴 암설, 30-35° 경사
    - Pediment (페디먼트): 기반 침식면, 완만
    
    Reference:
    - Howard & Selby (2009) Rock Slopes
    - Schumm & Chorley (1966) Talus & Cliff Retreat
    - Moon & Jayasuriya (2018) Mesa Evolution
    """
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    # 사막 기반 (페디먼트)
    elevation[:, :] = 5.0
    
    # 메사 높이 (학술 자료: 일반 30-100m)
    mesa_height = 100.0 * stage
    
    # 메사/뷰트 배치
    positions = [(h//3, w//3), (h//2, 2*w//3)]
    # 메사는 넓고, 뷰트는 좁음
    base_sizes = [(w//5, w//4), (w//12, w//12)]
    
    # 침식에 따른 크기 감소 (stage가 높을수록 작아짐)
    erosion_factor = 1.0 - stage * 0.3  # 최대 30% 수축
    sizes = [(int(sh * erosion_factor), int(sw * erosion_factor)) for sh, sw in base_sizes]
    
    # 형태 분류
    formation_types = []
    
    for i, ((my, mx), (sh, sw)) in enumerate(zip(positions[:num_mesas], sizes[:num_mesas])):
        # Superellipse shape for natural look
        n = 4.0
        
        # 바운딩 박스
        r_min, r_max = max(0, my - int(sh * 1.5)), min(h, my + int(sh * 1.5))
        c_min, c_max = max(0, mx - int(sw * 1.5)), min(w, mx + int(sw * 1.5))
        
        # 형태 분류 (폭/높이 비율)
        width_height_ratio = max(sh, sw) * 2 / max(mesa_height, 1)
        if width_height_ratio > 2:
            form_type = 'mesa'
        elif width_height_ratio > 0.8:
            form_type = 'butte'
        else:
            form_type = 'pinnacle'
        formation_types.append(form_type)
        
        for r in range(r_min, r_max):
            for c in range(c_min, c_max):
                dy = abs(r - my)
                dx = abs(c - mx)
                
                # Normalize distance
                if sh > 0 and sw > 0:
                    dist_norm = (dy / sh)**n + (dx / sw)**n
                else:
                    dist_norm = 999.0
                
                if dist_norm <= 1.0:
                    # 평탄한 정상부 (Cap Rock)
                    elevation[r, c] = max(elevation[r, c], mesa_height)
                elif dist_norm <= 1.3:
                    # 급경사 측벽 (Cliff Face)
                    wall_pos = (dist_norm - 1.0) / 0.3
                    z = mesa_height * (1 - wall_pos * 0.7)  # 70% 높이까지 급경사
                    elevation[r, c] = max(elevation[r, c], z)
                elif dist_norm <= 1.8:
                    # Talus Slope (애추) - 35° 경사
                    talus_pos = (dist_norm - 1.3) / 0.5
                    z = mesa_height * 0.3 * (1 - talus_pos)
                    elevation[r, c] = max(elevation[r, c], z)

    # 뷰트 침식 표현 (Talus 형성)
    if num_mesas > 1 and stage > 0.5:
        by, bx = positions[1]
        b_sh, b_sw = sizes[1]
        
        erosion_mask = (elevation > 10) & (elevation < mesa_height * 0.9)
        dist_b = np.sqrt(((np.arange(h)[:, None] - by)**2 + (np.arange(w)[None, :] - bx)**2))
        erosion_mask &= (dist_b < max(b_sh, b_sw) * 2)
        
        # Talus 노이즈
        np.random.seed(42)
        noise = np.random.rand(h, w) * 5.0
        elevation[erosion_mask] += noise[erosion_mask]

    if return_metadata:
        # 지질 구조 정보
        geological_structure = {
            'cap_rock': {
                'description': '경암층 (Resistant Cap Rock)',
                'material': '사암(Sandstone), 석회암(Limestone), 현무암(Basalt)',
                'thickness': f'{20 * stage:.0f}m'
            },
            'cliff_face': {
                'description': '절벽 사면 (Cliff Face)',
                'slope': '70-90° (수직~급경사)',
                'process': 'Undercutting & Rockfall'
            },
            'talus_slope': {
                'description': '애추 사면 (Talus Slope)',
                'slope': '30-35° (안식각)',
                'material': '붕괴 암설 (Rock Debris)'
            },
            'pediment': {
                'description': '기반 침식면 (Pediment)',
                'slope': '<5°',
                'process': 'Sheet Wash & Deflation'
            }
        }
        
        # 진화 단계
        if stage < 0.25:
            evolution_stage = 'plateau'
            evolution_desc = '대지 상태 - 침식 시작 전'
        elif stage < 0.50:
            evolution_stage = 'mesa'
            evolution_desc = '메사 발달 - 고립된 탁상지, 폭 > 높이'
        elif stage < 0.75:
            evolution_stage = 'butte'
            evolution_desc = '뷰트 전이 - 폭 ≈ 높이, 탑 형태로 변화'
        else:
            evolution_stage = 'pinnacle'
            evolution_desc = '첨탑 단계 - 극단적 침식, 좁은 탑 형태'
        
        return elevation, {
            'stage_description': f"{evolution_desc}",
            'evolution_stage': evolution_stage,
            'formation_types': formation_types,
            'geological_structure': geological_structure,
            'mesa_height': mesa_height,
            'erosion_rate': f'{stage * 100:.0f}%',
            'cliff_retreat_rate': f'{stage * 0.5:.2f}m/년 (추정)',
            'differential_erosion': {
                'description': '차별침식 (Differential Erosion)',
                'resistant_layer': 'Cap Rock (경암층)',
                'weak_layer': 'Shale/Mudstone (연암층)',
                'process': '경암층이 연암층을 보호, 연암층 침식 시 경암층 붕괴'
            }
        }

    return elevation


def create_spit_lagoon(grid_size: int = 100, stage: float = 1.0,
                       return_metadata: bool = False) -> np.ndarray:
    """사취+석호 (Spit+Lagoon) 형성과정 - 학술 자료 기반
    
    Stage 0.0~0.25: 해안 미지형 형성
      - 연안류(Longshore Drift) 활성화
      - 해안선 굴곡부에서 퇴적 시작
      - 수중 사주(Submarine Bar) 축적
    
    Stage 0.25~0.50: 사취(Spit) 성장
      - 사취가 수면 위로 노출
      - 연안류 방향으로 지속적 성장
      - 끝단에서 파랑 굴절로 곡사취(Recurved Spit) 형성
    
    Stage 0.50~0.75: 석호(Lagoon) 폐쇄
      - 사취가 만(Bay)을 가로지르며 성장
      - 내측에 저에너지 수역 형성
      - 석호 수심 감소, 퇴적 증가
    
    Stage 0.75~1.0: 염습지(Salt Marsh) 발달
      - 석호 내 미세 퇴적물 축적
      - 염생식물 군락 발달
      - 석호 점진적 매립
    
    핵심 프로세스:
    - Longshore Drift: 사(Swash)와 역연(Backwash)의 지그재그 운동
    - Refraction: 사취 끝단에서 파랑 굴절
    - Deposition: 유속 감소 지역에서 퇴적
    
    Reference:
    - Bird (2008) Coastal Geomorphology
    - Davis & FitzGerald (2004) Beaches and Coasts
    """
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    # 바다 (오른쪽)
    sea_line = int(w * 0.6)
    for r in range(h):
        for c in range(sea_line, w):
            # 해저 경사
            elevation[r, c] = -5.0 - (c - sea_line) * 0.1
    
    # 육지 (왼쪽)
    elevation[:, :sea_line] = 10.0
    
    # 사취 파라미터
    spit_start = int(h * 0.3)
    spit_length = int(h * 0.5 * stage)
    spit_width = 5 + int(stage * 3)  # 성장에 따라 폭 증가
    recurve_amount = 0  # 곡사취 정도
    
    # === 사취 형성 ===
    spit_cells = []
    if stage > 0.1:
        for r in range(spit_start, min(h, spit_start + spit_length)):
            # 사취가 바다 쪽으로 휘어짐
            progress = (r - spit_start) / max(spit_length, 1)
            curve = int(progress * (w * 0.15))
            
            # 곡사취 (stage 0.4 이후)
            if stage > 0.4 and progress > 0.7:
                recurve = int((progress - 0.7) / 0.3 * w * 0.08)
                recurve_amount = max(recurve_amount, recurve)
            else:
                recurve = 0
            
            spit_x = sea_line + curve
            
            for dc in range(-spit_width, spit_width + 1):
                c = spit_x + dc + recurve
                if 0 <= c < w:
                    # 사취 높이 (중앙이 높음)
                    spit_height = 3.0 * (1 - abs(dc) / spit_width) * min(1.0, stage * 2)
                    if spit_height > elevation[r, c]:
                        elevation[r, c] = spit_height
                        spit_cells.append((r, c))
    
    # === 석호 형성 (stage 0.5 이후) ===
    lagoon_area = 0
    lagoon_depth = 0
    if stage > 0.5:
        lagoon_intensity = (stage - 0.5) / 0.5
        for r in range(spit_start, spit_start + int(spit_length * 0.8)):
            progress = (r - spit_start) / max(spit_length * 0.8, 1)
            curve = int(progress * (w * 0.1))
            for c in range(sea_line - 5, sea_line + curve):
                if 0 <= c < w:
                    if elevation[r, c] < 3.0:
                        # 석호 수심 (내륙일수록 얕음)
                        depth = -2.0 + (sea_line - c) * 0.1
                        elevation[r, c] = max(depth, -3.0)
                        lagoon_area += 1
                        lagoon_depth = min(lagoon_depth, depth)
        
        # 염습지 (stage 0.8 이후)
        if stage > 0.8:
            marsh_intensity = (stage - 0.8) / 0.2
            for r in range(spit_start, spit_start + int(spit_length * 0.6)):
                for c in range(sea_line - 5, sea_line):
                    if 0 <= c < w and elevation[r, c] < 0:
                        # 염습지로 변환
                        elevation[r, c] = -0.5 * marsh_intensity
    
    if return_metadata:
        # 형성 단계 판정
        if stage < 0.25:
            formation_stage = 'submarine_bar'
            stage_desc = '수중 사주 축적: 연안류에 의해 해저에 사주 형성'
        elif stage < 0.50:
            formation_stage = 'emerging_spit'
            stage_desc = '사취 노출: 사주가 수면 위로 성장, 연안류 방향으로 연장'
        elif stage < 0.75:
            formation_stage = 'lagoon_enclosure'
            stage_desc = '석호 폐쇄: 사취가 만을 가로지르며 내측에 저에너지 수역 형성'
        else:
            formation_stage = 'salt_marsh'
            stage_desc = '염습지 발달: 석호 내 미세 퇴적 + 염생식물 군락 정착'
        
        return elevation, {
            'stage_description': stage_desc,
            'formation_stage': formation_stage,
            'spit_length': spit_length * 10,  # 미터 단위 (가정)
            'spit_width': spit_width * 5,  # 미터 단위
            'recurved': recurve_amount > 0,
            'lagoon_area': lagoon_area * 25,  # m² (가정)
            'lagoon_depth': abs(lagoon_depth),  # m
            'longshore_drift': {
                'description': '연안류 (Longshore Drift)',
                'process': 'Swash(사)가 경사 방향, Backwash(역연)가 수직으로 발생하여 지그재그 이동',
                'direction': '북 → 남 (예시)',
                'sediment': '사질(Sand), 자갈(Shingle)'
            },
            'coastal_processes': {
                'refraction': '파랑 굴절 - 사취 끝단에서 에너지 분산',
                'deposition': '퇴적 - 유속 감소 지역에서 축적',
                'salt_marsh': '염습지 - 석호 매립 최종 단계'
            }
        }
                        
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


def create_moraine(grid_size: int = 100, stage: float = 1.0,
                   return_metadata: bool = False) -> np.ndarray:
    """빙퇴석 (Moraine) 형성과정 - 학술 자료 기반
    
    Stage 0.0~0.25: 빙하 전진기
      - 빙하가 계곡을 따라 전진
      - 측면에 암설 운반 시작
    
    Stage 0.25~0.50: 빙하 최대 확장
      - 종퇴석 형성 위치 도달
      - 빙하 말단에 퇴적물 축적
    
    Stage 0.50~0.75: 빙하 후퇴기
      - 온난화로 빙하 후퇴
      - 측퇴석/종퇴석 노출 시작
    
    Stage 0.75~1.0: 빙퇴석 완전 노출
      - 빙하 소멸
      - 호형 종퇴석 + 능선형 측퇴석
    
    Reference: Benn & Evans (2010) Glaciers and Glaciation
    """
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    glacier_mask = np.zeros((h, w), dtype=bool)  # 빙하 위치 마스크
    
    # 빙하 계곡 배경 (산지)
    for r in range(h):
        for c in range(w):
            # 양쪽 산지
            base = 25.0
            dist_from_center = abs(c - w // 2)
            elevation[r, c] = base + dist_from_center * 0.3
    
    center = w // 2
    glacier_width = int(w * 0.3)
    
    # === 단계별 빙하 상태 ===
    if stage < 0.25:
        # 빙하 전진기
        glacier_front = int(h * 0.3 + stage * 4 * h * 0.5)  # 전진
        glacier_visible = True
        moraine_visible = stage * 4  # 측퇴석 축적 중
        phase = "advance"
    elif stage < 0.50:
        # 빙하 최대 확장
        glacier_front = int(h * 0.8)  # 최대
        glacier_visible = True
        moraine_visible = 0.5 + (stage - 0.25) * 2  # 종퇴석 형성
        phase = "maximum"
    elif stage < 0.75:
        # 빙하 후퇴기
        glacier_front = int(h * 0.8 - (stage - 0.50) * 4 * h * 0.6)  # 후퇴
        glacier_visible = True
        moraine_visible = 1.0
        phase = "retreat"
    else:
        # 빙하 소멸
        glacier_front = int(h * 0.1)
        glacier_visible = False
        moraine_visible = 1.0
        phase = "post_glacial"
    
    # === 빙하 바닥 (U자곡) ===
    for r in range(h):
        for c in range(w):
            if abs(c - center) < glacier_width:
                elevation[r, c] = 5.0  # U자곡 바닥
    
    # === 빙하 본체 시각화 ===
    if glacier_visible and glacier_front > int(h * 0.1):
        glacier_rear = int(h * 0.05)
        glacier_thickness = 30.0 if phase == "maximum" else 20.0
        
        for r in range(glacier_rear, glacier_front):
            for c in range(w):
                if abs(c - center) < glacier_width * 0.8:
                    # 빙하 표면 높이
                    rel_pos = (r - glacier_rear) / max(glacier_front - glacier_rear, 1)
                    # 빙하 혀(tongue) 형태
                    long_profile = 1.0 - abs(rel_pos - 0.5) * 0.5
                    lateral_profile = 1.0 - (abs(c - center) / (glacier_width * 0.8)) ** 0.5
                    
                    ice_height = glacier_thickness * long_profile * lateral_profile
                    if r > glacier_front - int(h * 0.1):
                        # 빙하 말단 경사
                        snout_factor = (glacier_front - r) / (h * 0.1)
                        ice_height *= snout_factor
                    
                    if ice_height > 2.0:  # 빙하 두께가 충분할 때만
                        elevation[r, c] = max(elevation[r, c], 5.0 + ice_height)
                        glacier_mask[r, c] = True  # 빙하 위치 표시
    
    # === 측퇴석 (Lateral Moraine) ===
    moraine_height = 15.0 * moraine_visible
    lateral_length = 0
    for r in range(min(glacier_front, int(h * 0.8))):
        for side in [-1, 1]:
            moraine_c = center + side * glacier_width
            # 상류로 갈수록 높아지는 측퇴석
            height_factor = 1.0 - r / h * 0.3
            for dc in range(-5, 6):
                c = moraine_c + dc
                if 0 <= c < w:
                    z = moraine_height * height_factor * (1 - abs(dc) / 6)
                    elevation[r, c] = max(elevation[r, c], z + 10)
            lateral_length += 1
    
    # === 종퇴석 (Terminal Moraine) - 호형 ===
    terminal_r = int(h * 0.8)
    terminal_area = 0
    if moraine_visible > 0.5:
        arc_intensity = min(1.0, (moraine_visible - 0.5) * 2)
        for r in range(terminal_r - 8, min(h, terminal_r + 8)):
            for c in range(w):
                # 호형(arc) 계산
                dx = c - center
                dy = r - terminal_r
                
                # 포물선 형태
                arc_center = terminal_r + int(abs(dx) ** 1.5 / 20)
                if abs(r - arc_center) < 5 and abs(dx) < glacier_width + 10:
                    dr = abs(r - arc_center)
                    lateral_decay = 1 - abs(dx) / (glacier_width + 10)
                    z = moraine_height * 1.3 * arc_intensity * (1 - dr / 5) * lateral_decay
                    elevation[r, c] = max(elevation[r, c], z + 5)
                    terminal_area += 1
    
    if return_metadata:
        return elevation, {
            'stage_description': _get_moraine_stage_desc(stage),
            'phase': phase,
            'glacier_front': glacier_front,
            'glacier_visible': glacier_visible,
            'glacier_mask': glacier_mask,  # 빙하 위치 마스크 (하얀색 표시용)
            'moraine_height': moraine_height,
            'glacier_width': glacier_width * 10,
            'moraine_types': {
                'lateral': {
                    'name': '측퇴석 (Lateral Moraine)',
                    'location': '빙하 측면/계곡 사면',
                    'length': lateral_length // 2 * 10,
                    'formation': '계곡 사면 낙하 암설 + 빙하 연변 퇴적'
                },
                'terminal': {
                    'name': '종퇴석 (Terminal Moraine)',
                    'location': '빙하 최대 전진 위치',
                    'area': terminal_area * 25,
                    'shape': '호형(arc) - 빙하 곡률 반영',
                    'formation': '빙하 말단에서 밀어올린 퇴적물'
                }
            },
            'till_composition': {
                'description': 'Till (빙력토)',
                'sorting': 'Unsorted (미분급)',
                'material': '점토~표석(boulder)까지 혼재',
                'structure': '무층리, 치밀'
            }
        }
                
    return elevation


def _get_moraine_stage_desc(stage: float) -> str:
    """빙퇴석 단계별 설명"""
    if stage < 0.25:
        return "빙하 전진기: 빙하가 계곡을 따라 전진, 측면에 암설 운반"
    elif stage < 0.50:
        return "빙하 최대 확장: 종퇴석 형성 위치 도달, 말단에 퇴적물 축적"
    elif stage < 0.75:
        return "빙하 후퇴기: 온난화로 빙하 후퇴, 측퇴석/종퇴석 노출 시작"
    else:
        return "빙퇴석 완전 노출: 빙하 소멸, 호형 종퇴석 + 능선형 측퇴석"


def create_braided_river(grid_size: int = 100, stage: float = 1.0,
                         return_metadata: bool = False) -> np.ndarray:
    """망상하천 (Braided River) 형성과정 - 학술 자료 기반
    
    Stage 0.0~0.25: 초기 하도 형성
      - 넓은 하상(river bed)에 단일 수로
      - 하상하중(bedload) 퇴적 시작
    
    Stage 0.25~0.50: 사주(bar) 발달
      - 중앙사주(mid-channel bar) 형성
      - 수로 분기 시작
    
    Stage 0.50~0.75: 망상 패턴 발달
      - 다수의 수로와 사주
      - 빈번한 수로 이동
    
    Stage 0.75~1.0: 성숙 망상하천
      - 복잡한 수로망
      - 안정된 사주 체계
    
    형성 조건:
    - 고유량 변동성, 급경사
    - 조립질 하상하중(자갈, 모래)
    - 약한 제방/식생 부재
    
    Reference:
    - Leopold & Wolman (1957) River Channel Patterns
    - Bridge (2003) Rivers and Floodplains
    """
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
    
    channel_positions = []
    for r in range(h):
        for i in range(num_channels):
            channel_x = center - river_width // 3 + int((i / num_channels) * river_width * 0.7)
            channel_x += int(10 * np.sin(r / 10 + i))
            
            for dc in range(-2, 3):
                c = channel_x + dc
                if 0 <= c < w:
                    elevation[r, c] = 3.0
            channel_positions.append(channel_x)
                    
    # 사주 (모래섬)
    bar_count = int(5 * stage)
    bar_info = []
    for i in range(bar_count):
        bar_r = int(h * 0.2 + i * h * 0.15)
        bar_c = center + int((i - 2) * w * 0.1)
        bar_area = 0
        
        for dr in range(-5, 6):
            for dc in range(-8, 9):
                r, c = bar_r + dr, bar_c + dc
                if 0 <= r < h and 0 <= c < w:
                    dist = np.sqrt((dr/5)**2 + (dc/8)**2)
                    if dist < 1.0:
                        elevation[r, c] = max(elevation[r, c], 6.0 * (1 - dist))
                        bar_area += 1
        
        bar_info.append({'center': (bar_r, bar_c), 'area': bar_area})
    
    if return_metadata:
        return elevation, {
            'stage_description': _get_braided_stage_desc(stage),
            'num_channels': num_channels,
            'num_bars': bar_count,
            'bar_info': bar_info,
            'river_width': river_width * 10,  # 미터 단위
            'channel_pattern': {
                'type': 'Braided (망상형)',
                'sinuosity': '<1.5',
                'gradient': '>0.01',
                'characteristics': '다수 수로, 빈번한 수로 이동'
            },
            'sediment': {
                'type': 'Coarse bedload (조립질 하상하중)',
                'material': '자갈(Gravel), 조사(Coarse Sand)',
                'transport': 'Bedload-dominant (하상하중 우세)'
            },
            'formation_conditions': {
                'discharge': '고유량 변동성 (홍수/갈수 차이 큼)',
                'gradient': '급경사 (>0.01)',
                'bank': '약한 제방 (침식 용이)',
                'vegetation': '식생 부재/희박'
            }
        }
                        
    return elevation


def _get_braided_stage_desc(stage: float) -> str:
    """망상하천 단계별 설명"""
    if stage < 0.25:
        return "초기 형성: 넓은 하상에 단일 수로, 하상하중 퇴적 시작"
    elif stage < 0.50:
        return "사주 발달: 중앙사주(mid-channel bar) 형성, 수로 분기 시작"
    elif stage < 0.75:
        return "망상 패턴: 다수 수로와 사주, 빈번한 수로 이동"
    else:
        return "성숙 망상하천: 복잡한 수로망, 안정된 사주 체계"


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
                        num_dolines: int = 5, return_metadata: bool = False) -> np.ndarray:
    """돌리네 (Doline/Sinkhole) - 카르스트 지형 형성과정 - 학술 자료 기반
    
    Stage 0.0~0.25: 초기 용식 (Initial Dissolution)
      - 석회암 절리/층리면을 따라 용식 시작
      - 카렌(Karren) 형성 - 표면 미세 용식 홈
      - 지하수 유입점 형성
    
    Stage 0.25~0.50: 용식 돌리네 발달 (Solution Doline)
      - 용식으로 부드러운 깔때기형 함몰
      - 점진적 침하 (gradual subsidence)
      - 지하 배수 시스템 발달
    
    Stage 0.50~0.75: 함몰 돌리네 전이 (Collapse Doline)
      - 지하 동굴 천장 붕괴 시작
      - 급경사 절벽형 측벽
      - 복합 형태(Polygenetic) 발달
    
    Stage 0.75~1.0: 우발라/폴레 형성
      - 인접 돌리네 결합→우발라(Uvala)
      - 대형 카르스트 분지
      - 지하 배수망 완성
    
    핵심 프로세스:
    - 탄산화 반응: CO2 + H2O → H2CO3 (탄산)
    - CaCO3 + H2CO3 → Ca(HCO3)2 (용해)
    
    Reference:
    - Ford & Williams (2007) Karst Hydrogeology and Geomorphology
    - Waltham et al. (2005) Sinkholes and Subsidence
    """
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    # 석회암 대지
    elevation[:, :] = 30.0
    
    np.random.seed(42)
    doline_info = []
    total_area = 0
    max_depth = 0
    
    for i in range(num_dolines):
        dy = int(h * 0.2 + np.random.rand() * h * 0.6)
        dx = int(w * 0.2 + np.random.rand() * w * 0.6)
        radius = int(w * 0.08 * (0.5 + np.random.rand() * 0.5))
        depth = 20.0 * stage * (0.5 + np.random.rand() * 0.5)
        
        # 돌리네 유형 결정
        if stage < 0.4:
            doline_type = 'solution'  # 용식 돌리네
            profile_exp = 2.0  # 부드러운 깔때기형
        elif stage < 0.7:
            doline_type = 'collapse'  # 함몰 돌리네
            profile_exp = 1.2  # 급경사
        else:
            doline_type = 'polygenetic'  # 복합형
            profile_exp = 1.5
        
        for r in range(h):
            for c in range(w):
                dist = np.sqrt((r - dy)**2 + (c - dx)**2)
                if dist < radius:
                    z = depth * (1 - (dist / radius) ** profile_exp)
                    elevation[r, c] = max(0, elevation[r, c] - z)
                    total_area += 1
        
        doline_info.append({
            'center': (dy, dx),
            'radius': radius * 5,  # 미터 단위 (가정)
            'depth': depth,
            'type': doline_type
        })
        max_depth = max(max_depth, depth)
    
    # 우발라 형성 (stage 0.8 이후) - 인접 돌리네 결합
    if stage > 0.8 and num_dolines >= 2:
        # 첫 번째와 두 번째 돌리네 연결
        d1, d2 = doline_info[0], doline_info[1]
        cy1, cx1 = d1['center']
        cy2, cx2 = d2['center']
        
        for r in range(h):
            for c in range(w):
                # 두 돌리네 사이의 골짜기
                t = np.clip(((r - cy1) * (cy2 - cy1) + (c - cx1) * (cx2 - cx1)) / 
                           max(1, (cy2 - cy1)**2 + (cx2 - cx1)**2), 0, 1)
                closest_y = cy1 + t * (cy2 - cy1)
                closest_x = cx1 + t * (cx2 - cx1)
                dist_to_line = np.sqrt((r - closest_y)**2 + (c - closest_x)**2)
                
                if dist_to_line < 8:
                    uvala_depth = 5.0 * (1 - dist_to_line / 8) * (stage - 0.8) / 0.2
                    elevation[r, c] = max(0, elevation[r, c] - uvala_depth)
    
    if return_metadata:
        # 형성 단계 판정
        if stage < 0.25:
            formation_stage = 'initial_karren'
            stage_desc = '초기 용식: 석회암 표면에 카렌(Karren) 형성, 절리면 용식 시작'
        elif stage < 0.50:
            formation_stage = 'solution_doline'
            stage_desc = '용식 돌리네: 점진적 용식으로 부드러운 깔때기형 함몰 발달'
        elif stage < 0.75:
            formation_stage = 'collapse_doline'
            stage_desc = '함몰 돌리네: 지하 동굴 천장 붕괴, 급경사 측벽 형성'
        else:
            formation_stage = 'uvala'
            stage_desc = '우발라 형성: 인접 돌리네 결합, 대형 카르스트 분지 발달'
        
        return elevation, {
            'stage_description': stage_desc,
            'formation_stage': formation_stage,
            'num_dolines': num_dolines,
            'max_depth': max_depth,
            'total_area': total_area * 25,  # m² (가정)
            'doline_types': [d['type'] for d in doline_info],
            'dissolution_process': {
                'description': '탄산화 용식 (Carbonation)',
                'reaction': 'CaCO3 + H2CO3 → Ca(HCO3)2',
                'rate': f'{0.1 * stage:.2f}mm/년 (추정)',
                'solvent': '탄산(H2CO3) - 빗물+CO2'
            },
            'doline_classification': {
                'solution': '용식 돌리네 - 점진적 용식, 깔때기형',
                'collapse': '함몰 돌리네 - 동굴 천장 붕괴, 급경사',
                'cover_collapse': '피복층 함몰 - 상부 토양층 붕괴',
                'suffosion': '세굴 돌리네 - 토양 세굴로 침하'
            },
            'karst_features': {
                'karren': '카렌 - 표면 미세 용식 홈',
                'ponor': '폰노르 - 지하수 흡입구',
                'uvala': '우발라 - 돌리네 결합체',
                'polje': '폴리에 - 대형 카르스트 분지'
            }
        }
                    
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


def create_tombolo(grid_size: int = 100, stage: float = 1.0,
                   return_metadata: bool = False) -> np.ndarray:
    """육계사주 (Tombolo) 형성과정 - 학술 자료 기반
    
    파랑 굴절(wave refraction)에 의한 섬-육지 연결 퇴적체
    
    Stage 0~0.3: 섬 후면 퇴적 시작
      - 섬이 파랑 에너지 차단
      - 섬 후면(shadow zone)에 저에너지 영역 형성
    
    Stage 0.3~0.6: 사주 성장
      - 양측에서 굴절된 파랑이 수렴
      - 사주가 연결 방향으로 성장
    
    Stage 0.6~1.0: 육계사주 완성
      - 섬과 육지가 사주로 연결
      - 육계도(tied island) 형성
    
    Reference: Evans (1942) Tombolo Formation
    """
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
    tombolo_length = tombolo_end - tombolo_start
    
    for c in range(tombolo_start, tombolo_end):
        t = (c - tombolo_start) / max(tombolo_length, 1)
        width = int(5 * (1 - abs(t - 0.5) * 2) * stage)
        
        for dr in range(-width, width + 1):
            r = island_cy + dr
            if 0 <= r < h:
                elevation[r, c] = 3.0 * (1 - abs(dr) / max(width, 1))
    
    if return_metadata:
        return elevation, {
            'stage_description': _get_tombolo_stage_desc(stage),
            'tombolo_length': tombolo_length * 10,  # 미터 단위
            'island_radius': island_radius * 10,  # 미터
            'formation_complete': stage > 0.8,
            'wave_processes': {
                'refraction': '파랑 굴절 - 섬 주변에서 파랑 방향 변화',
                'diffraction': '파랑 회절 - 섬 후면으로 에너지 전달',
                'convergence': '파랑 수렴 - 양측 굴절파가 섬 후면에서 만남'
            },
            'formation_conditions': {
                'island_size': '적절한 크기 (너무 크거나 작지 않음)',
                'distance': '육지로부터 적절한 거리',
                'sediment_supply': '충분한 퇴적물 공급',
                'wave_energy': '중간 정도의 파랑 에너지'
            },
            'resulting_features': {
                'tied_island': '육계도 - 연결된 섬',
                'double_tombolo': '이중 육계사주 - 두 개 사주로 연결 (간혹)',
                'lagoon': '폐쇄 석호 형성 가능'
            }
        }
                
    return elevation


def _get_tombolo_stage_desc(stage: float) -> str:
    """육계사주 단계별 설명"""
    if stage < 0.3:
        return "퇴적 시작: 섬 후면(shadow zone)에 저에너지 영역, 사주 축적 시작"
    elif stage < 0.6:
        return "사주 성장: 파랑 굴절로 양측에서 퇴적물 수렴, 사주 연장"
    else:
        return "육계사주 완성: 섬과 육지가 연결, 육계도(tied island) 형성"


def create_sea_arch(grid_size: int = 100, stage: float = 1.0,
                    return_metadata: bool = False) -> np.ndarray:
    """해식아치 (Sea Arch) 형성과정 - 학술 자료 기반
    
    Stage 0.0~0.25: 해식 노치(notch) 형성
      - 파랑 침식으로 절벽 기부에 오목한 홈
      - 곶(headland)의 양측에서 침식 시작
    
    Stage 0.25~0.50: 해식동굴(sea cave) 발달
      - 노치가 깊어져 동굴 형성
      - 양측 동굴이 점점 관통 방향으로
    
    Stage 0.50~0.75: 아치(arch) 형성
      - 양측 동굴이 관통하여 터널 완성
      - 아치 상부에 암괴 잔류
    
    Stage 0.75~1.0: 시스택(stack) 전이
      - 아치 천장 붕괴 임박
      - 붕괴 시 고립된 암주(stack) 형성
    
    Reference: Trenhaile (1987) The Geomorphology of Rock Coasts
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
            dist_from_edge = min(r, c, w - c - 1)
            elevation[r, c] = cliff_height
    
    # 돌출부 (곶 - headland)
    headland_cx = w // 2
    headland_width = int(w * 0.35)
    headland_length = int(h * 0.4)
    
    for r in range(sea_line, sea_line + headland_length):
        taper = 1 - (r - sea_line) / headland_length * 0.5
        current_width = int(headland_width * taper)
        
        for c in range(headland_cx - current_width // 2, headland_cx + current_width // 2):
            if 0 <= c < w:
                height = cliff_height * (1 - (r - sea_line) / headland_length * 0.2)
                elevation[r, c] = height
    
    # 해식아치 (곶 중간에 관통)
    arch_r = sea_line + int(headland_length * 0.5)
    arch_height = int(cliff_height * 0.6 * stage)
    arch_width = int(headland_width * 0.3 * stage)
    arch_area = 0
    
    for dr in range(-8, 9):
        for dc in range(-arch_width, arch_width + 1):
            r = arch_r + dr
            c = headland_cx + dc
            
            if 0 <= r < h and 0 <= c < w:
                arch_profile = arch_height * np.sqrt(max(0, 1 - (dc / max(arch_width, 1))**2))
                
                if abs(dr) < 3 and arch_profile > 5:
                    elevation[r, c] = -5.0
                    arch_area += 1
                elif abs(dr) < 5:
                    if elevation[r, c] > arch_profile:
                        elevation[r, c] = min(elevation[r, c], cliff_height - arch_profile * 0.3)
    
    if return_metadata:
        # 진화 단계 판정
        if stage < 0.25:
            evolution_stage = 'notch'
            stage_desc = '해식 노치: 파랑 침식으로 절벽 기부에 오목한 홈 형성'
        elif stage < 0.50:
            evolution_stage = 'cave'
            stage_desc = '해식동굴: 노치가 깊어져 곶 양측에 동굴 발달'
        elif stage < 0.75:
            evolution_stage = 'arch'
            stage_desc = '해식아치: 양측 동굴이 관통, 터널형 아치 완성'
        else:
            evolution_stage = 'pre_stack'
            stage_desc = '시스택 전이: 아치 천장 붕괴 임박, 암주(stack) 형성 직전'
        
        return elevation, {
            'stage_description': stage_desc,
            'evolution_stage': evolution_stage,
            'arch_width': arch_width * 10,  # 미터 단위
            'arch_height': arch_height,
            'arch_area': arch_area * 25,  # m² (터널 면적)
            'cliff_height': cliff_height,
            'erosion_sequence': {
                1: '노치(Notch) - 파랑 침식으로 오목한 홈',
                2: '동굴(Cave) - 노치가 깊어져 동굴',
                3: '아치(Arch) - 양측 동굴 관통',
                4: '스택(Stack) - 아치 붕괴, 고립 암주',
                5: '스텀프(Stump) - 스택 풍화로 낮은 잔류암'
            },
            'erosion_processes': {
                'hydraulic_action': '수력작용 - 파랑 충격 압력',
                'abrasion': '마식 - 암편이 절벽 연마',
                'solution': '용식 - 해수의 화학적 용해',
                'weathering': '풍화 - 염류 결정, 건습 반복'
            }
        }
    
    return elevation


def create_crater_lake(grid_size: int = 100, stage: float = 1.0,
                       rim_height: float = 50.0, return_metadata: bool = False) -> np.ndarray:
    """칼데라호 (Caldera Lake) 형성과정 - 학술 자료 기반
    
    칼데라(Caldera): 대규모 화산 폭발 후 마그마방 함몰로 형성된 분지
    - 지름 1km 이상 (화구 crater는 1km 미만)
    - 정상부 함몰로 규모가 크고 깊음
    
    Stage 0.0~0.25: 화산체 성장
      - 용암/화산쇄설물 분출
      - 원뿔형 화산체 형성
      - 정상부에 작은 분화구 (crater)
    
    Stage 0.25~0.50: 대분출/함몰
      - 대규모 플리니안 분출
      - 마그마방 비워짐
      - 정상부 함몰 → 칼데라 형성 (crater→caldera)
    
    Stage 0.50~0.75: 분화 진정/안정화
      - 분연 활동 감소
      - 칼데라 벽 안정화
      - 물 유입 시작
    
    Stage 0.75~1.0: 호수 충전
      - 강수/지하수 축적
      - 호수 수면 상승
      - 칼데라호 완성
    
    예시: 백두산 천지, 미국 Crater Lake, 인도네시아 토바호
    
    Reference: Simkin & Siebert (1994) Volcanoes of the World
    """
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    center = (h // 2, w // 2)
    max_outer_radius = int(w * 0.4)
    max_crater_radius = int(w * 0.25)
    
    # === 단계별 화산 형태 ===
    if stage < 0.25:
        # 화산체 성장
        progress = stage / 0.25
        volcano_height = rim_height * progress
        crater_radius = int(max_crater_radius * 0.3)  # 작은 분화구
        crater_depth = 5.0 * progress
        water_level = None
        phase = "growth"
        outer_radius = int(max_outer_radius * (0.5 + 0.5 * progress))
    elif stage < 0.50:
        # 대분출/함몰
        progress = (stage - 0.25) / 0.25
        volcano_height = rim_height * (1.0 - progress * 0.3)  # 정상부 함몰
        crater_radius = int(max_crater_radius * (0.3 + 0.7 * progress))  # 확장
        crater_depth = 5.0 + 30.0 * progress  # 깊어짐
        water_level = None
        phase = "collapse"
        outer_radius = max_outer_radius
    elif stage < 0.75:
        # 분화 진정
        progress = (stage - 0.50) / 0.25
        volcano_height = rim_height * 0.7
        crater_radius = max_crater_radius
        crater_depth = 35.0 + 5.0 * progress
        water_level = crater_depth * 0.3 * progress  # 물 축적 시작
        phase = "stabilizing"
        outer_radius = max_outer_radius
    else:
        # 호수 충전
        progress = (stage - 0.75) / 0.25
        volcano_height = rim_height * 0.7
        crater_radius = max_crater_radius
        crater_depth = 40.0
        water_level = crater_depth * (0.3 + 0.6 * progress)  # 수면 상승
        phase = "filled"
        outer_radius = max_outer_radius
    
    lake_area = 0
    
    for r in range(h):
        for c in range(w):
            dist = np.sqrt((r - center[0])**2 + (c - center[1])**2)
            
            if dist > outer_radius:
                elevation[r, c] = 0
            elif dist > crater_radius:
                # 외륜산/화산 사면
                t = (dist - crater_radius) / max(outer_radius - crater_radius, 1)
                # 화산 사면 프로파일 (오목한 형태)
                profile = (1 - t ** 0.7)
                elevation[r, c] = volcano_height * profile
            else:
                # 화구/칼데라 내부
                if water_level is not None and water_level > 5:
                    # 호수 (물)
                    base_depth = -crater_depth
                    bowl_shape = (dist / max(crater_radius, 1)) ** 2 * crater_depth * 0.3
                    floor_elev = base_depth + bowl_shape
                    
                    if floor_elev < -water_level:
                        # 수면 아래
                        elevation[r, c] = -water_level  # 수면
                        lake_area += 1
                    else:
                        # 노출된 바닥
                        elevation[r, c] = floor_elev
                else:
                    # 건조한 화구
                    bowl_shape = (dist / max(crater_radius, 1)) ** 2 * crater_depth * 0.5
                    elevation[r, c] = -crater_depth + bowl_shape
    
    if return_metadata:
        return elevation, {
            'stage_description': _get_crater_lake_stage_desc(stage),
            'phase': phase,
            'lake_type': 'Caldera Lake (칼데라호)' if crater_radius > 20 else 'Maar (마르)',
            'crater_radius': crater_radius * 10,
            'crater_depth': crater_depth,
            'water_level': water_level if water_level else 0,
            'lake_area': lake_area * 25,
            'rim_height': volcano_height,
            'formation_type': {
                'caldera': {
                    'description': '칼데라 - 대규모 마그마 분출 후 함몰',
                    'process': 'Magma chamber collapse',
                    'size': '>1km 직경'
                },
                'maar': {
                    'description': '마르 - 마그마-지하수 폭발(phreatomagmatic)',
                    'process': 'Steam explosion',
                    'size': '<1km 직경'
                }
            },
            'water_source': {
                'precipitation': '강수(직접 유입)',
                'groundwater': '지하수 용출',
                'snowmelt': '융설수'
            }
        }
                
    return elevation


def _get_crater_lake_stage_desc(stage: float) -> str:
    """화구호 단계별 설명"""
    if stage < 0.25:
        return "화산체 성장: 용암/화산쇄설물 분출, 원뿔형 화산체 형성"
    elif stage < 0.50:
        return "대분출/함몰: 플리니안 분출 후 마그마방 비워짐, 정상부 함몰"
    elif stage < 0.75:
        return "분화 진정: 칼데라 벽 안정화, 물 유입 시작"
    else:
        return "호수 충전: 강수/지하수 축적, 칼데라호 완성"


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
    groove_band = max(1, groove_spacing // 2)
    groove_core = max(1, groove_spacing // 4)
    groove_depth = 3.0 * stage
    
    for c in range(w):
        if c % groove_spacing < groove_band:
            for r in range(h):
                # 길쭉한 홈
                groove_center_offset = abs(c % groove_spacing - groove_core)
                depth = groove_depth * max(0.0, 1 - groove_center_offset / groove_core)
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
                           num_ridges: int = 4, return_metadata: bool = False) -> np.ndarray:
    """횡사구 (Transverse Dune) 형성과정 - 학술 자료 기반
    
    단일 방향 바람 + 풍부한 모래 공급
    - 바람 방향에 수직인 사구 능선
    - 비대칭 단면: 바람받이(15°) / 바람그늘(30-35°)
    
    Stage 0~0.3: 사구 능선 형성 시작
    Stage 0.3~0.7: 능선 성장 및 연속화
    Stage 0.7~1.0: 성숙 횡사구열
    
    Reference: Tsoar (2001) Types of Aeolian Sand Dunes
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
    
    if return_metadata:
        return elevation, {
            'stage_description': _get_transverse_dune_stage_desc(stage),
            'dune_type': 'Transverse (횡사구)',
            'num_ridges': num_ridges,
            'ridge_height': ridge_height,
            'ridge_spacing': ridge_spacing * 10,  # 미터 단위
            'asymmetry': {
                'windward_slope': '~15° (완만, 바람받이)',
                'slip_face': '30-35° (급경사, 바람그늘)',
                'description': 'Saltation on windward, Avalanche on lee'
            },
            'wind_conditions': {
                'direction': '단일방향 (Unidirectional)',
                'constancy': '일정함 (Constant)',
                'sand_supply': '풍부 (Abundant)'
            },
            'migration_rate': f'{int(10 / (stage + 0.1))}m/년 (추정)'
        }
                    
    return elevation


def _get_transverse_dune_stage_desc(stage: float) -> str:
    """횡사구 단계별 설명"""
    if stage < 0.3:
        return "능선 형성: 모래 공급으로 바람 수직 방향 사구 형성 시작"
    elif stage < 0.7:
        return "능선 성장: 사구열 연속화, 평행 능선 발달"
    else:
        return "성숙 횡사구: 규칙적인 평행 사구열, 비대칭 단면 완성"


def create_star_dune(grid_size: int = 100, stage: float = 1.0,
                     num_dunes: int = 2, return_metadata: bool = False) -> np.ndarray:
    """성사구 (Star Dune) 형성과정 - 학술 자료 기반
    
    다방향 바람(Multi-directional wind)으로 형성
    - 중앙에서 방사상으로 뻗은 능선(arms)
    - 높이가 크고 이동이 느림
    - 세계에서 가장 높은 사구 유형
    
    Stage 0~0.3: 중앙 봉우리 형성
    Stage 0.3~0.7: 방사상 팔 발달
    Stage 0.7~1.0: 성숙 성사구
    
    Reference: Lancaster (1989) Star Dunes
    """
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    elevation[:, :] = 5.0  # 사막 기반
    
    dune_info = []
    num_arms = 5  # 별 모양 팔 개수
    
    for d in range(num_dunes):
        cy = h // 3 + d * h // 3
        cx = w // 3 + d * w // 3
        
        dune_height = 20.0 * stage
        arm_length = int(w * 0.2)
        arm_width = max(3, w // 20)
        
        dune_info.append({
            'center': (cy, cx),
            'height': dune_height,
            'arm_count': num_arms
        })
        
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
                    arm_dir = np.array([np.cos(angle), np.sin(angle)])
                    pos = np.array([dx, dy])
                    proj = np.dot(pos, arm_dir)
                    perp = np.abs(np.cross(arm_dir, pos))
                    
                    if proj > 0 and proj < arm_length and perp < arm_width:
                        z = dune_height * 0.6 * (1 - proj / arm_length) * (1 - perp / arm_width)
                        elevation[r, c] = max(elevation[r, c], 5.0 + z)
    
    if return_metadata:
        return elevation, {
            'stage_description': _get_star_dune_stage_desc(stage),
            'dune_type': 'Star (성사구)',
            'num_dunes': num_dunes,
            'num_arms': num_arms,
            'max_height': 20.0 * stage,
            'arm_length': arm_length * 10,  # 미터 단위
            'dune_info': dune_info,
            'wind_conditions': {
                'direction': '다방향 (Multi-directional)',
                'seasonality': '계절풍 전환',
                'sand_supply': '중간 정도'
            },
            'characteristics': {
                'stability': '고정적 (Stationary) - 거의 이동 안 함',
                'height': '세계 최고 높이 사구 유형 (500m+)',
                'age': '수천 년~수만 년',
                'example': '나미브 사막 Namib Sand Sea'
            }
        }
                        
    return elevation


def _get_star_dune_stage_desc(stage: float) -> str:
    """성사구 단계별 설명"""
    if stage < 0.3:
        return "봉우리 형성: 다방향 바람이 모래를 중앙으로 집중"
    elif stage < 0.7:
        return "방사상 발달: 여러 팔(arm)이 바람 방향으로 뻗음"
    else:
        return "성숙 성사구: 별 모양 완성, 높이 극대화, 위치 고정"


# ============================================
# 추가 확장 지형들 (Additional Expansion)
# ============================================

def create_perched_river(grid_size: int = 100, stage: float = 1.0,
                         return_metadata: bool = False):
    """천정천 (Perched River) 형성과정 - 학술 자료 기반
    
    자연제방(Natural Levee) 발달로 하상이 주변보다 높아진 하천
    
    Stage 0.0~0.25: 범람원 형성
      - 반복적 범람으로 평탄한 범람원 형성
      - 하천 사행, 미세한 자연제방 시작
    
    Stage 0.25~0.50: 자연제방 발달
      - 범람 시 하도 가장자리에 조립질 퇴적
      - 제방 높이 증가, 배후습지 형성 시작
    
    Stage 0.50~0.75: 천정천 발달
      - 하상 퇴적으로 하천 바닥 상승
      - 배후습지 물 고임, 습지 확대
    
    Stage 0.75~1.0: 천정천 완성
      - 하상이 주변 범람원보다 확연히 높음
      - 제방 붕괴 시 대규모 범람 위험
    
    Reference: 
    - Blum & Törnqvist (2000) Fluvial responses to climate change
    - Hudson (2005) Natural Levee Formation
    """
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    # 범람원 기본 높이
    base_height = 10.0
    elevation[:] = base_height
    
    # === 단계별 변수 ===
    if stage < 0.25:
        progress = stage / 0.25
        levee_height = 2.0 * progress
        river_lift = 0.5 * progress
        backswamp_depth = 0.5 * progress
        flood_visible = progress > 0.5  # 범람 시각화
        phase = "floodplain"
    elif stage < 0.50:
        progress = (stage - 0.25) / 0.25
        levee_height = 2.0 + 3.0 * progress
        river_lift = 0.5 + 2.0 * progress
        backswamp_depth = 0.5 + 1.5 * progress
        flood_visible = False
        phase = "levee_growth"
    elif stage < 0.75:
        progress = (stage - 0.50) / 0.25
        levee_height = 5.0 + 2.0 * progress
        river_lift = 2.5 + 2.0 * progress
        backswamp_depth = 2.0 + 1.0 * progress
        flood_visible = False
        phase = "perching"
    else:
        progress = (stage - 0.75) / 0.25
        levee_height = 7.0 + 1.5 * progress
        river_lift = 4.5 + 1.0 * progress
        backswamp_depth = 3.0 + 0.5 * progress
        flood_visible = False
        phase = "complete"
    
    levee_width = int(w * 0.15)
    center = w // 2
    
    # 하천 사행 (약간의 곡선)
    np.random.seed(42)
    meander_amp = int(w * 0.05)
    
    for r in range(h):
        # 사행하는 하천 중심선
        meander_offset = int(meander_amp * np.sin(r / h * 4 * np.pi))
        local_center = center + meander_offset
        
        for c in range(w):
            dist_from_center = abs(c - local_center)
            
            if dist_from_center < 5:
                # 하도 (하천 바닥) - 물
                river_bed = base_height + river_lift
                elevation[r, c] = river_bed - 2  # 수면보다 약간 아래 (물)
            elif dist_from_center < levee_width:
                # 자연제방
                decay = 1 - (dist_from_center - 5) / max(levee_width - 5, 1)
                decay = decay ** 0.6  # 지수적 감소
                levee_elev = base_height + levee_height * decay
                elevation[r, c] = levee_elev
            else:
                # 배후습지
                dist_from_levee = dist_from_center - levee_width
                # 제방에서 멀어질수록 더 낮아짐
                extra_depth = min(1.0, dist_from_levee / (w * 0.2)) * 1.0
                elevation[r, c] = base_height - backswamp_depth - extra_depth
    
    # 배후습지에 물 표현 (stage > 0.5)
    if stage > 0.5 and stage < 0.75:
        water_level = base_height - backswamp_depth + 0.5
        for r in range(h):
            for c in range(w):
                if elevation[r, c] < water_level:
                    elevation[r, c] = water_level - 0.1
    
    # 범람 시각화 (초기 단계)
    if flood_visible:
        flood_level = base_height + 0.5
        for r in range(h):
            for c in range(w):
                if elevation[r, c] < flood_level:
                    # 범람수
                    elevation[r, c] = flood_level
    
    river_bed_height = base_height + river_lift
    perched_height = river_bed_height - (base_height - backswamp_depth)
    
    if return_metadata:
        return elevation, {
            'stage_description': _get_perched_river_stage_desc(stage),
            'phase': phase,
            'levee_height': levee_height,
            'river_bed_height': river_bed_height,
            'backswamp_depth': backswamp_depth,
            'perched_height': perched_height,
            'formation_process': {
                'natural_levee': {
                    'description': '자연제방 (Natural Levee)',
                    'mechanism': '범람 시 유속 감소→조립질 퇴적',
                    'material': '모래, 조사 (Coarse sediment)',
                    'slope': '하도에서 멀어질수록 완만히 하강'
                },
                'backswamp': {
                    'description': '배후습지 (Backswamp)',
                    'mechanism': '제방 뒤 배수 불량 지역',
                    'material': '점토, 실트 (Fine sediment)',
                    'features': '습지, 호수 형성'
                }
            },
            'flood_hazard': {
                'risk_level': '높음 (High)' if stage > 0.7 else '중간',
                'mechanism': '제방 붕괴 시 주변으로 급격히 범람',
                'examples': '황하(黃河), 낙동강 하류'
            }
        }
    
    return elevation


def _get_perched_river_stage_desc(stage: float) -> str:
    """천정천 단계별 설명"""
    if stage < 0.25:
        return "범람원 형성: 반복적 범람으로 평탄 지형, 사행하천과 미세한 제방"
    elif stage < 0.50:
        return "자연제방 발달: 범람 시 하도 가장자리에 조립질 퇴적, 제방 성장"
    elif stage < 0.75:
        return "천정천 발달: 하상 퇴적으로 바닥 상승, 배후습지 물 고임"
    else:
        return "천정천 완성: 하상이 주변보다 확연히 높음, 범람 위험 최대"


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


def create_pediment(grid_size: int = 100, stage: float = 1.0):
    """페디먼트 (Pediment) - 산록 완사촌 (침식 평원)
    
    산지 전면의 완만한 경사지. 침식 작용으로 형성된 암석 표면.
    하부에는 선상지 연합(Bajada)이 덮이기도 함.
    """
    h, w = grid_size, grid_size
    elevation = np.zeros((h, w))
    
    # 1. 후면 산지 (급경사, Mountain Front)
    mountain_end = int(h * 0.25)
    mountain_height = 80.0
    
    # 2. 페디먼트 경사 (Pediment Slope)
    # 상부는 암석 노출, 하부는 퇴적물 피복
    
    for r in range(h):
        for c in range(w):
            if r < mountain_end:
                # 산지: 급경사 및 불규칙
                elevation[r, c] = mountain_height * (0.8 + 0.2 * np.random.rand())
            else:
                # 페디먼트: 완만한 경사 (1~7도)
                # 요형 사면 (Concave)
                dist = r - mountain_end
                max_dist = h - mountain_end
                
                # 높이 80m(산기슭) -> 5m(말단)
                slope_start_h = mountain_height
                slope_end_h = 5.0
                
                # 거리에 따른 감쇠 (Concave)
                t = dist / max_dist
                profile_h = slope_end_h + (slope_start_h - slope_end_h) * ((1 - t) ** 1.5)
                
                # 가로방향 약간의 굴곡
                undulation = np.sin(c * 0.05) * 2.0 * (1 - t)
                
                elevation[r, c] = profile_h + undulation
                
                # 바하다 (Bajada) 퇴적 효과 (Stage에 따라 덮임)
                if stage > 0.5:
                    if t > 0.4:
                        sediment = 5.0 * (t - 0.4) / 0.6 * stage
                        elevation[r, c] += sediment

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
        rock_height = np.random.uniform(30, 50)  # 높이 상향 (25-40 -> 30-50)
        
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

def create_esker(
    grid_size: int = 100,
    stage: float = 1.0,
    return_metadata: bool = False,
) -> np.ndarray:
    """에스커(Esker): 빙하 밑 융빙수 하천 퇴적물이 남긴 구불구불한 능선."""

    h, w = grid_size, grid_size
    stage = float(np.clip(stage, 0.0, 1.0))
    y, x = np.mgrid[0:h, 0:w]
    x_norm = x / max(w - 1, 1)
    y_norm = y / max(h - 1, 1)

    base = 12.0 - y_norm * 4.0
    low_relief = 0.6 * np.sin(y_norm * np.pi * 2.0) + 0.35 * np.cos(x_norm * np.pi * 3.0)

    centerline = (w * 0.5) + np.sin(y_norm * np.pi * 3.2 + 0.8) * (w * 0.16)
    centerline += np.sin(y_norm * np.pi * 7.0) * (w * 0.035)
    distance = x - centerline

    ridge_width = max(w * (0.035 + 0.015 * stage), 2.0)
    ridge_height = 18.0 * stage
    ridge = np.exp(-(distance**2) / (2.0 * ridge_width**2)) * ridge_height
    ridge *= 0.82 + 0.18 * np.sin(y_norm * np.pi * 12.0 + 1.4)

    meltwater_trench = -2.5 * np.exp(-(distance**2) / (2.0 * (ridge_width * 2.6) ** 2)) * (1.0 - stage) * 0.7
    ice_cover = np.clip(1.0 - stage * 1.5, 0.0, 1.0) * (18.0 - y_norm * 7.0)
    elevation = base + low_relief + meltwater_trench + ridge + ice_cover * 0.35

    if return_metadata:
        return elevation.astype(float), {
            "landform": "esker",
            "stage": stage,
            "dominant_process": "subglacial meltwater deposition",
            "teaching_focus": "빙하가 물러난 뒤, 빙하 밑 하천의 퇴적물이 긴 능선으로 남는다.",
        }
    return elevation.astype(float)


def create_lava_dome(grid_size: int = 100, stage: float = 1.0, return_metadata: bool = False) -> np.ndarray:
    y, x = np.mgrid[0:grid_size, 0:grid_size]
    xn = (x - (grid_size - 1) / 2) / max(grid_size - 1, 1)
    yn = (y - (grid_size - 1) / 2) / max(grid_size - 1, 1)
    r = np.sqrt(xn * xn + yn * yn)
    stage = float(np.clip(stage, 0.0, 1.0))
    base = 22.0 - 10.0 * yn
    vent_radius = 0.05 + 0.23 * stage
    dome = 135.0 * stage * np.exp(-(r / max(vent_radius, 0.04)) ** 2.3)
    plug = 45.0 * stage * np.exp(-(r / max(vent_radius * 0.42, 0.03)) ** 2.0)
    fracture = np.zeros_like(base)
    for angle in np.linspace(0.0, 2.0 * np.pi, 9, endpoint=False):
        ray = np.abs(np.sin(np.arctan2(yn, xn) - angle))
        fracture += np.exp(-(ray / 0.045) ** 2) * np.exp(-(r / max(vent_radius * 1.15, 0.06)) ** 2)
    collapse = 26.0 * np.clip((stage - 0.72) / 0.28, 0.0, 1.0)
    scar = collapse * np.exp(-(((xn - 0.10) / 0.12) ** 2 + ((yn + 0.08) / 0.20) ** 2))
    elevation = base + dome + plug - 9.0 * fracture * stage - scar
    if return_metadata:
        return elevation, {"type": "lava_dome", "stage": stage}
    return elevation


def create_tidal_flat(grid_size: int = 100, stage: float = 1.0, return_metadata: bool = False) -> np.ndarray:
    y, x = np.mgrid[0:grid_size, 0:grid_size]
    xn = x / max(grid_size - 1, 1)
    yn = y / max(grid_size - 1, 1)
    stage = float(np.clip(stage, 0.0, 1.0))
    slope = 7.0 - 9.0 * yn
    accretion = 7.5 * stage * np.exp(-((yn - 0.42) / 0.32) ** 2)
    channels = np.zeros_like(slope)
    for offset, amp, width in [(0.12, 0.10, 0.025), (0.50, 0.08, 0.020), (0.82, 0.06, 0.018)]:
        center = offset + amp * np.sin(yn * np.pi * (1.2 + stage))
        channels += np.exp(-((xn - center) / width) ** 2) * (1.0 - yn * 0.55)
    elevation = slope + accretion - channels * (3.0 + 5.0 * stage)
    if return_metadata:
        return elevation, {"type": "tidal_flat", "stage": stage}
    return elevation


def create_marine_terrace(grid_size: int = 100, stage: float = 1.0, return_metadata: bool = False) -> np.ndarray:
    y, x = np.mgrid[0:grid_size, 0:grid_size]
    yn = y / max(grid_size - 1, 1)
    xn = x / max(grid_size - 1, 1)
    stage = float(np.clip(stage, 0.0, 1.0))
    coast = 0.62 - 0.18 * stage
    elevation = 70.0 * (1.0 - yn) + 3.0 * np.sin(xn * np.pi * 3)
    for idx, level in enumerate([0.70, 0.56, 0.42]):
        active = np.clip((stage - idx * 0.22) / 0.42, 0.0, 1.0)
        band = np.exp(-((yn - level) / 0.055) ** 8)
        elevation = elevation * (1.0 - band * active) + (46.0 - idx * 13.0) * band * active
    sea = yn > coast
    elevation[sea] = -4.0 - (yn[sea] - coast) * 20.0
    if return_metadata:
        return elevation, {"type": "marine_terrace", "stage": stage}
    return elevation


def create_kettle_lake(grid_size: int = 100, stage: float = 1.0, return_metadata: bool = False) -> np.ndarray:
    y, x = np.mgrid[0:grid_size, 0:grid_size]
    xn = x / max(grid_size - 1, 1)
    yn = y / max(grid_size - 1, 1)
    stage = float(np.clip(stage, 0.0, 1.0))
    elevation = 42.0 - 18.0 * yn + 2.5 * np.sin(xn * np.pi * 5) * np.sin(yn * np.pi * 2)
    for cx, cy, radius in [(0.35, 0.48, 0.12), (0.62, 0.58, 0.09), (0.52, 0.33, 0.07)]:
        melt = np.clip((stage - 0.25) / 0.75, 0.0, 1.0)
        depression = np.exp(-(((xn - cx) ** 2 + (yn - cy) ** 2) / max(radius, 0.01) ** 2))
        rim = np.exp(-(((np.sqrt((xn - cx) ** 2 + (yn - cy) ** 2) - radius) / 0.03) ** 2))
        elevation -= depression * 26.0 * melt
        elevation += rim * 5.0 * melt
    if return_metadata:
        return elevation, {"type": "kettle_lake", "stage": stage}
    return elevation


def create_outwash_plain(grid_size: int = 100, stage: float = 1.0, return_metadata: bool = False) -> np.ndarray:
    y, x = np.mgrid[0:grid_size, 0:grid_size]
    xn = x / max(grid_size - 1, 1)
    yn = y / max(grid_size - 1, 1)
    stage = float(np.clip(stage, 0.0, 1.0))
    slope = 65.0 - 45.0 * yn
    fan = 18.0 * stage * np.exp(-((xn - 0.5) / (0.18 + 0.35 * yn)) ** 2) * (1.0 - yn * 0.65)
    braid = np.zeros_like(slope)
    for phase in [0.0, 1.9, 3.8, 5.2]:
        center = 0.5 + (0.08 + 0.20 * yn) * np.sin(yn * np.pi * 4 + phase)
        braid += np.exp(-((xn - center) / 0.018) ** 2)
    elevation = slope + fan - braid * (4.0 + 5.0 * stage)
    if return_metadata:
        return elevation, {"type": "outwash_plain", "stage": stage}
    return elevation


def create_thermokarst(grid_size: int = 100, stage: float = 1.0, return_metadata: bool = False) -> np.ndarray:
    y, x = np.mgrid[0:grid_size, 0:grid_size]
    xn = x / max(grid_size - 1, 1)
    yn = y / max(grid_size - 1, 1)
    stage = float(np.clip(stage, 0.0, 1.0))
    elevation = 32.0 + 2.0 * np.sin(xn * np.pi * 6) + 1.5 * np.cos(yn * np.pi * 5)
    centers = [(0.28, 0.36, 0.10), (0.62, 0.42, 0.13), (0.45, 0.66, 0.09), (0.78, 0.72, 0.07)]
    for idx, (cx, cy, radius) in enumerate(centers):
        thaw = np.clip((stage - idx * 0.10) / 0.72, 0.0, 1.0)
        basin = np.exp(-(((xn - cx) ** 2 + (yn - cy) ** 2) / radius ** 2))
        elevation -= basin * (12.0 + idx * 2.0) * thaw
    if return_metadata:
        return elevation, {"type": "thermokarst", "stage": stage}
    return elevation


def create_cinder_cone(grid_size: int = 100, stage: float = 1.0, return_metadata: bool = False) -> np.ndarray:
    y, x = np.mgrid[0:grid_size, 0:grid_size]
    xn = (x - (grid_size - 1) / 2) / max(grid_size - 1, 1)
    yn = (y - (grid_size - 1) / 2) / max(grid_size - 1, 1)
    r = np.sqrt(xn * xn + yn * yn)
    stage = float(np.clip(stage, 0.0, 1.0))
    radius = 0.08 + 0.30 * stage
    cone = np.clip(1.0 - r / max(radius, 0.02), 0.0, 1.0) * 105.0 * stage
    crater = np.exp(-(r / max(radius * 0.28, 0.02)) ** 4) * 48.0 * stage
    apron = 18.0 * stage * np.exp(-(r / max(radius * 1.8, 0.08)) ** 2)
    elevation = 18.0 + cone + apron - crater
    if return_metadata:
        return elevation, {"type": "cinder_cone", "stage": stage}
    return elevation


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
    'pediment': create_pediment,  # 추가
    # Additional teaching IDs backed by existing or lightweight procedural generators.
    'oxbow_lake': create_free_meander,
    'floodplain_natural_levee': create_perched_river,
    'river_terrace': create_incised_meander,
    'sea_cave_stack': create_sea_arch,
    'wave_cut_platform': create_coastal_cliff,
    'barrier_island': create_spit_lagoon,
    'esker': create_esker,
    'maar': create_crater_lake,
    'lava_dome': create_lava_dome,
    'tidal_flat': create_tidal_flat,
    'marine_terrace': create_marine_terrace,
    'kettle_lake': create_kettle_lake,
    'outwash_plain': create_outwash_plain,
    'thermokarst': create_thermokarst,
    'cinder_cone': create_cinder_cone,
    'polje': create_uvala,
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
    'pediment': lambda gs: create_pediment(gs, 1.0),  # 추가
    # Additional teaching IDs.
    'oxbow_lake': lambda gs: create_free_meander(gs, 1.0),
    'floodplain_natural_levee': lambda gs: create_perched_river(gs, 1.0),
    'river_terrace': lambda gs: create_incised_meander(gs, 1.0),
    'sea_cave_stack': lambda gs: create_sea_arch(gs, 1.0),
    'wave_cut_platform': lambda gs: create_coastal_cliff(gs, 1.0),
    'barrier_island': lambda gs: create_spit_lagoon(gs, 1.0),
    'esker': lambda gs: create_esker(gs, 1.0),
    'maar': lambda gs: create_crater_lake(gs, 1.0),
    'lava_dome': lambda gs: create_lava_dome(gs, 1.0),
    'tidal_flat': lambda gs: create_tidal_flat(gs, 1.0),
    'marine_terrace': lambda gs: create_marine_terrace(gs, 1.0),
    'kettle_lake': lambda gs: create_kettle_lake(gs, 1.0),
    'outwash_plain': lambda gs: create_outwash_plain(gs, 1.0),
    'thermokarst': lambda gs: create_thermokarst(gs, 1.0),
    'cinder_cone': lambda gs: create_cinder_cone(gs, 1.0),
    'polje': lambda gs: create_uvala(gs, 1.0),
}

