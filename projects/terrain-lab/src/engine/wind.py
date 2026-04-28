"""
Wind Kernel (바람 커널)

풍성 지형 형성 프로세스
- 풍식 (Deflation): 미세 입자 제거
- 마식 (Abrasion): 모래 충돌에 의한 침식
- 풍적 (Aeolian Deposition): 사구 형성

핵심:
- 바람 속도에 비례한 운반력
- 입자 크기에 따른 선택적 운반
"""

import numpy as np
from .grid import WorldGrid


class WindKernel:
    """
    바람 커널
    
    건조 지역에서의 풍식과 풍적을 시뮬레이션.
    """
    
    def __init__(self, grid: WorldGrid,
                 wind_speed: float = 10.0,        # m/s
                 wind_direction: float = 45.0,    # degrees from N
                 K_erosion: float = 0.0001,
                 sand_threshold: float = 0.1):    # 사구 형성 임계 퇴적량
        self.grid = grid
        self.wind_speed = wind_speed
        self.wind_direction = np.radians(wind_direction)
        self.K = K_erosion
        self.sand_threshold = sand_threshold
        
    def get_wind_vector(self) -> tuple:
        """
        바람 방향 벡터 반환
        
        Returns:
            (dy, dx): 바람 방향 단위 벡터
        """
        dx = np.sin(self.wind_direction)
        dy = -np.cos(self.wind_direction)  # Y축 반전 (화면 좌표계)
        return dy, dx
        
    def calculate_transport_capacity(self, 
                                      vegetation_cover: np.ndarray = None) -> np.ndarray:
        """
        모래 운반력 계산
        
        Args:
            vegetation_cover: 식생 피복률 (0~1, 높으면 운반력 감소)
            
        Returns:
            capacity: 운반력 배열
        """
        h, w = self.grid.height, self.grid.width
        
        # 기본 운반력 = 풍속^3 (경험식)
        base_capacity = (self.wind_speed ** 3) * self.K
        
        capacity = np.ones((h, w)) * base_capacity
        
        # 식생 효과 (있으면 운반력 감소)
        if vegetation_cover is not None:
            capacity *= (1 - vegetation_cover)
            
        # 경사 효과 (바람받이 vs 바람그늘)
        slope, aspect = self.grid.get_gradient()
        
        # 바람받이 = 풍향과 반대 경사면 → 감속 → 퇴적
        # 바람그늘 = 풍향과 같은 경사면 → 가속 → 침식
        dy, dx = self.get_wind_vector()
        
        # 경사면의 노출도 (바람과 경사 방향의 내적)
        exposure = dx * np.gradient(self.grid.elevation, axis=1) + \
                   dy * np.gradient(self.grid.elevation, axis=0)
        
        # 노출도에 따른 운반력 조정
        capacity *= (1 + 0.5 * np.clip(exposure, -1, 1))
        
        # 해수면 아래는 0
        capacity[self.grid.is_underwater()] = 0
        
        return np.maximum(capacity, 0)
        
    def deflation(self, capacity: np.ndarray, dt: float = 1.0) -> np.ndarray:
        """
        풍식 (Deflation) - 미세 입자 제거
        
        Args:
            capacity: 운반력 배열
            dt: 시간 간격
            
        Returns:
            erosion: 침식량 배열
        """
        h, w = self.grid.height, self.grid.width
        
        # 침식량 = 운반력 * dt (퇴적층에서만)
        available = self.grid.sediment
        erosion = np.minimum(capacity * dt, available)
        
        # 퇴적층 감소
        self.grid.sediment -= erosion
        
        return erosion
        
    def transport_and_deposit(self, 
                              eroded_material: np.ndarray,
                              capacity: np.ndarray,
                              dt: float = 1.0) -> np.ndarray:
        """
        풍적 (Aeolian Deposition) - 사구 형성
        
        Args:
            eroded_material: 침식된 물질량
            capacity: 운반력 배열
            dt: 시간 간격
            
        Returns:
            deposition: 퇴적량 배열
        """
        h, w = self.grid.height, self.grid.width
        
        dy, dx = self.get_wind_vector()
        
        # 물질 이동
        deposition = np.zeros((h, w), dtype=np.float64)
        
        for r in range(h):
            for c in range(w):
                if eroded_material[r, c] <= 0:
                    continue
                    
                # 바람 방향으로 이동
                tr = int(r + dy * 2)  # 2셀 이동
                tc = int(c + dx * 2)
                
                if not (0 <= tr < h and 0 <= tc < w):
                    continue
                    
                # 목표 지점의 운반력 확인
                if capacity[tr, tc] < capacity[r, c]:
                    # 운반력 감소 → 퇴적
                    deposit_amount = eroded_material[r, c] * (1 - capacity[tr, tc] / capacity[r, c])
                    deposition[tr, tc] += deposit_amount
                else:
                    # 계속 운반 (다음 셀로)
                    # 간단히 위해 일부만 퇴적
                    deposition[tr, tc] += eroded_material[r, c] * 0.1
                    
        # 퇴적 적용
        self.grid.add_sediment(deposition)
        
        return deposition
        
    def form_barchan(self, iteration: int = 5):
        """
        바르한 사구 형성 (반복 시뮬레이션)
        
        바람받이: 완경사, 바람그늘: 급경사 (Slip Face)
        
        Args:
            iteration: 형태 다듬기 반복 횟수
        """
        h, w = self.grid.height, self.grid.width
        dy, dx = self.get_wind_vector()
        
        # 사구 후보 (퇴적물 많은 곳)
        dune_mask = self.grid.sediment > self.sand_threshold
        
        for _ in range(iteration):
            # 바람받이 쪽 완만하게
            for r in range(1, h - 1):
                for c in range(1, w - 1):
                    if not dune_mask[r, c]:
                        continue
                        
                    # 바람받이 이웃
                    wr, wc = int(r - dy), int(c - dx)
                    if 0 <= wr < h and 0 <= wc < w:
                        # 경사 완화
                        avg = (self.grid.sediment[r, c] + self.grid.sediment[wr, wc]) / 2
                        self.grid.sediment[r, c] = self.grid.sediment[r, c] * 0.9 + avg * 0.1
                        
        self.grid.update_elevation()
        
    def step(self, vegetation_cover: np.ndarray = None,
             dt: float = 1.0) -> dict:
        """
        1단계 바람 작용 실행
        
        Args:
            vegetation_cover: 식생 피복률
            dt: 시간 간격
            
        Returns:
            result: 침식/퇴적 결과
        """
        # 1. 운반력 계산
        capacity = self.calculate_transport_capacity(vegetation_cover)
        
        # 2. 풍식
        erosion = self.deflation(capacity, dt)
        
        # 3. 이동 및 퇴적
        deposition = self.transport_and_deposit(erosion, capacity, dt)
        
        return {
            'erosion': erosion,
            'deposition': deposition,
            'capacity': capacity
        }
