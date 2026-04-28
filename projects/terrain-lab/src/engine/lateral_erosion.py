"""
Lateral Erosion Module (측방 침식)

하천의 곡류(Meander) 형성을 위한 측방 침식 프로세스
- 곡률 외측: 침식 (Cutbank)
- 곡률 내측: 퇴적 (Point Bar)

핵심 공식:
E_lateral = k * τ * (1/R)
- k: 침식 계수
- τ: 전단응력 (유량 함수)
- R: 곡률 반경 (작을수록 급회전 → 침식 증가)
"""

import numpy as np
from .grid import WorldGrid


def compute_flow_curvature(flow_dir: np.ndarray, elevation: np.ndarray) -> np.ndarray:
    """
    유향(Flow Direction)으로부터 곡률(Curvature) 계산
    
    Args:
        flow_dir: D8 유향 배열 (0-7, -1 = sink)
        elevation: 고도 배열
        
    Returns:
        curvature: 곡률 배열 (양수: 좌회전, 음수: 우회전)
    """
    h, w = flow_dir.shape
    curvature = np.zeros((h, w), dtype=np.float64)
    
    # D8 방향 벡터 (index 0-7)
    # 0: NW, 1: N, 2: NE, 3: W, 4: E, 5: SW, 6: S, 7: SE
    dir_dy = np.array([-1, -1, -1,  0,  0,  1,  1,  1])
    dir_dx = np.array([-1,  0,  1, -1,  1, -1,  0,  1])
    
    # 방향을 각도로 변환 (라디안)
    # atan2(dy, dx)
    dir_angles = np.arctan2(dir_dy, dir_dx)
    
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            current_dir = int(flow_dir[r, c])
            if current_dir < 0 or current_dir > 7:
                continue
                
            # 상류 방향 찾기 (나를 향해 흐르는 셀)
            upstream_dirs = []
            for k in range(8):
                nr = r + dir_dy[k]
                nc = c + dir_dx[k]
                if 0 <= nr < h and 0 <= nc < w:
                    neighbor_dir = int(flow_dir[nr, nc])
                    if neighbor_dir >= 0 and neighbor_dir < 8:
                        # 이웃이 나를 향해 흐르는가?
                        target_r = nr + dir_dy[neighbor_dir]
                        target_c = nc + dir_dx[neighbor_dir]
                        if target_r == r and target_c == c:
                            upstream_dirs.append(neighbor_dir)
            
            if not upstream_dirs:
                continue
                
            # 상류 방향의 평균 각도
            upstream_angle = np.mean([dir_angles[d] for d in upstream_dirs])
            current_angle = dir_angles[current_dir]
            
            # 각도 변화 = 곡률 (정규화된 값)
            angle_diff = current_angle - upstream_angle
            
            # -π ~ π 범위로 정규화
            while angle_diff > np.pi:
                angle_diff -= 2 * np.pi
            while angle_diff < -np.pi:
                angle_diff += 2 * np.pi
                
            curvature[r, c] = angle_diff
            
    return curvature


def apply_lateral_erosion(grid: WorldGrid, 
                          curvature: np.ndarray, 
                          discharge: np.ndarray,
                          k: float = 0.01,
                          dt: float = 1.0) -> np.ndarray:
    """
    측방 침식 적용
    
    Args:
        grid: WorldGrid 객체
        curvature: 곡률 배열 (양수: 좌회전, 음수: 우회전)
        discharge: 유량 배열
        k: 침식 계수
        dt: 시간 간격
        
    Returns:
        change: 지형 변화량 배열
    """
    h, w = grid.height, grid.width
    change = np.zeros((h, w), dtype=np.float64)
    
    # D8 방향 벡터
    dir_dy = np.array([-1, -1, -1,  0,  0,  1,  1,  1])
    dir_dx = np.array([-1,  0,  1, -1,  1, -1,  0,  1])
    
    # 좌/우측 방향 (상대적)
    # 현재 방향이 k일 때, 좌측은 (k-2)%8, 우측은 (k+2)%8 (대략적 근사)
    
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            curv = curvature[r, c]
            Q = discharge[r, c]
            
            if abs(curv) < 0.01 or Q < 1.0:
                continue
                
            # 침식량 = k * sqrt(Q) * |curvature| * dt
            erosion_amount = k * np.sqrt(Q) * abs(curv) * dt
            
            # 현재 유향
            flow_k = int(grid.flow_dir[r, c])
            if flow_k < 0 or flow_k > 7:
                continue
                
            # 좌/우측 셀 결정
            if curv > 0:  # 좌회전 → 우측(외측) 침식, 좌측(내측) 퇴적
                erode_k = (flow_k + 2) % 8  # 우측
                deposit_k = (flow_k - 2 + 8) % 8  # 좌측
            else:  # 우회전 → 좌측(외측) 침식, 우측(내측) 퇴적
                erode_k = (flow_k - 2 + 8) % 8  # 좌측
                deposit_k = (flow_k + 2) % 8  # 우측
                
            # 침식 셀
            er = r + dir_dy[erode_k]
            ec = c + dir_dx[erode_k]
            
            # 퇴적 셀
            dr = r + dir_dy[deposit_k]
            dc = c + dir_dx[deposit_k]
            
            # 경계 체크
            if 0 <= er < h and 0 <= ec < w:
                change[er, ec] -= erosion_amount
                
            if 0 <= dr < h and 0 <= dc < w:
                change[dr, dc] += erosion_amount * 0.8  # 일부 손실
                
    return change


class LateralErosionKernel:
    """
    측방 침식 커널
    
    EarthSystem에 통합하여 사용
    """
    
    def __init__(self, grid: WorldGrid, k: float = 0.01):
        self.grid = grid
        self.k = k
        
    def step(self, discharge: np.ndarray, dt: float = 1.0) -> np.ndarray:
        """
        1단계 측방 침식 실행
        
        Args:
            discharge: 유량 배열
            dt: 시간 간격
            
        Returns:
            change: 지형 변화량
        """
        # 1. 곡률 계산
        curvature = compute_flow_curvature(self.grid.flow_dir, self.grid.elevation)
        
        # 2. 측방 침식 적용
        change = apply_lateral_erosion(self.grid, curvature, discharge, self.k, dt)
        
        # 3. 지형 업데이트
        # 침식분: bedrock/sediment에서 제거
        erosion_mask = change < 0
        erosion_amount = -change[erosion_mask]
        
        # 퇴적층 먼저, 부족하면 기반암
        sed_loss = np.minimum(erosion_amount, self.grid.sediment[erosion_mask])
        rock_loss = erosion_amount - sed_loss
        
        self.grid.sediment[erosion_mask] -= sed_loss
        self.grid.bedrock[erosion_mask] -= rock_loss
        
        # 퇴적분: sediment에 추가
        self.grid.sediment += np.maximum(change, 0)
        
        # 고도 동기화
        self.grid.update_elevation()
        
        return change
