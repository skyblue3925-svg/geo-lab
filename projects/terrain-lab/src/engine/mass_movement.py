"""
Mass Movement Kernel (매스무브먼트)

중력에 의한 사면 이동 프로세스
- 산사태 (Landslide)
- 슬럼프 (Slump)
- 낙석 (Rockfall)

핵심 원리:
경사(Slope) > 임계 경사(Critical Angle) → 물질 이동
"""

import numpy as np
from .grid import WorldGrid


class MassMovementKernel:
    """
    매스무브먼트 커널
    
    경사 안정성을 검사하고, 불안정한 곳에서 물질 이동을 시뮬레이션.
    """
    
    def __init__(self, grid: WorldGrid, 
                 friction_angle: float = 35.0,  # 내부 마찰각 (도)
                 cohesion: float = 0.0):        # 점착력 (Pa, 간소화)
        self.grid = grid
        self.friction_angle = friction_angle
        self.cohesion = cohesion
        
        # 임계 경사 (탄젠트 값)
        self.critical_slope = np.tan(np.radians(friction_angle))
        
    def check_stability(self) -> np.ndarray:
        """
        경사 안정성 검사
        
        Returns:
            unstable_mask: 불안정한 셀 마스크 (True = 불안정)
        """
        slope, _ = self.grid.get_gradient()
        
        # 경사 > 임계 경사 → 불안정
        unstable = slope > self.critical_slope
        
        return unstable
        
    def trigger_landslide(self, unstable_mask: np.ndarray, 
                          efficiency: float = 0.5) -> np.ndarray:
        """
        산사태 발생
        
        불안정한 셀에서 물질을 낮은 곳으로 이동.
        
        Args:
            unstable_mask: 불안정 마스크
            efficiency: 이동 효율 (0.0~1.0, 1.0이면 완전 이동)
            
        Returns:
            change: 지형 변화량
        """
        h, w = self.grid.height, self.grid.width
        change = np.zeros((h, w), dtype=np.float64)
        
        if not np.any(unstable_mask):
            return change
            
        # D8 방향
        dr = np.array([-1, -1, -1,  0,  0,  1,  1,  1])
        dc = np.array([-1,  0,  1, -1,  1, -1,  0,  1])
        
        elev = self.grid.elevation
        slope, _ = self.grid.get_gradient()
        
        # 불안정 셀 좌표
        unstable_coords = np.argwhere(unstable_mask)
        
        for r, c in unstable_coords:
            # 현재 경사 초과분 계산
            excess_slope = slope[r, c] - self.critical_slope
            if excess_slope <= 0:
                continue
                
            # 이동량 = 초과 경사에 비례
            # 퇴적층 먼저 이동, 부족하면 기반암
            available = self.grid.sediment[r, c] + self.grid.bedrock[r, c] * 0.1
            move_amount = min(excess_slope * efficiency * 5.0, available)
            
            if move_amount <= 0:
                continue
                
            # 가장 낮은 이웃 찾기
            min_z = elev[r, c]
            target = None
            
            for k in range(8):
                nr, nc = r + dr[k], c + dc[k]
                if 0 <= nr < h and 0 <= nc < w:
                    if elev[nr, nc] < min_z:
                        min_z = elev[nr, nc]
                        target = (nr, nc)
                        
            if target is None:
                continue
                
            tr, tc = target
            
            # 물질 이동
            change[r, c] -= move_amount
            change[tr, tc] += move_amount * 0.9  # 일부 손실 (분산)
            
        # 지형 업데이트
        # 손실분: sediment에서 제거
        loss_mask = change < 0
        loss = -change[loss_mask]
        
        sed_loss = np.minimum(loss, self.grid.sediment[loss_mask])
        rock_loss = loss - sed_loss
        
        self.grid.sediment[loss_mask] -= sed_loss
        self.grid.bedrock[loss_mask] -= rock_loss
        
        # 퇴적분: sediment에 추가
        self.grid.sediment += np.maximum(change, 0)
        
        self.grid.update_elevation()
        
        return change
        
    def step(self, dt: float = 1.0) -> np.ndarray:
        """
        1단계 매스무브먼트 실행
        
        Args:
            dt: 시간 간격 (사용하지 않지만 인터페이스 일관성)
            
        Returns:
            change: 지형 변화량
        """
        # 1. 안정성 검사
        unstable = self.check_stability()
        
        # 2. 불안정 지점에서 산사태 발생
        change = self.trigger_landslide(unstable)
        
        return change
