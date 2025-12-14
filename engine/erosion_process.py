import numpy as np
from .grid import WorldGrid

class ErosionProcess:
    """
    지형 변경 커널 (Erosion/Deposition Kernel)
    
    물리 공식을 적용하여 지형(고도)을 변경합니다.
    1. Stream Power Law: 하천 침식 (E = K * A^m * S^n)
    2. Hillslope Diffusion: 사면 붕괴/확산 (dz/dt = D * del^2 z)
    """
    
    def __init__(self, grid: WorldGrid, K: float = 1e-4, m: float = 0.5, n: float = 1.0, D: float = 0.01):
        self.grid = grid
        self.K = K  # 침식 계수
        self.m = m  # 유량 지수
        self.n = n  # 경사 지수
        self.D = D  # 확산 계수 (사면)
        
    def stream_power_erosion(self, discharge: np.ndarray, dt: float = 1.0) -> np.ndarray:
        """Stream Power Law 기반 하천 침식"""
        slope, _ = self.grid.get_gradient()
        
        # E = K * Q^m * S^n
        # (유량 Q를 유역면적 A 대신 사용)
        erosion_rate = self.K * np.power(discharge, self.m) * np.power(slope, self.n)
        
        # 실제 침식량 = rate * time
        erosion_amount = erosion_rate * dt
        
        # 기반암 이하로는 침식 불가 (available sediment first, then bedrock)
        # 여기서는 단순화를 위해 Topography(elevation)을 바로 깎음.
        # 단, 해수면 아래는 침식 작용 감소 (물 속에서는 Stream Power가 아님)
        underwater = self.grid.is_underwater()
        erosion_amount[underwater] *= 0.1
        
        # 지형 업데이트
        self.grid.elevation -= erosion_amount
        
        # 단순화: 깎인 만큼 퇴적물로 변환되어 어딘가로 가야 하지만,
        # Stream Power Model(SPL)은 보통 Detachment-limited 모델이라 퇴적을 명시적으로 다루지 않음.
        # 통합 모델을 위해, 침식된 양을 퇴적물 플럭스에 더해줄 수 있음 (구현 예정)
        
        return erosion_amount

    def hillslope_diffusion(self, dt: float = 1.0) -> np.ndarray:
        """사면 확산 프로세스 (Linear Diffusion)"""
        elev = self.grid.elevation
        
        # Laplacian calculation (이산화)
        # del^2 z = (z_up + z_down + z_left + z_right - 4*z) / dx^2
        
        # Numpy roll을 이용한 빠른 계산
        up = np.roll(elev, -1, axis=0)
        down = np.roll(elev, 1, axis=0)
        left = np.roll(elev, -1, axis=1)
        right = np.roll(elev, 1, axis=1)
        
        dx2 = self.grid.cell_size ** 2
        laplacian = (up + down + left + right - 4 * elev) / dx2
        
        # 경계 조건 처리 (가장자리는 계산 제외 or 0)
        laplacian[0, :] = 0
        laplacian[-1, :] = 0
        laplacian[:, 0] = 0
        laplacian[:, -1] = 0
        
        # dz/dt = D * del^2 z
        change = self.D * laplacian * dt
        
        self.grid.elevation += change
        return change

    def overbank_deposition(self, discharge: np.ndarray, 
                            bankfull_capacity: float = 100.0,
                            decay_rate: float = 0.1,
                            dt: float = 1.0) -> np.ndarray:
        """
        범람원 퇴적 (Overbank Deposition)
        
        하천 용량 초과 시 범람하여 주변에 세립질 퇴적.
        하도에서 멀어질수록 퇴적량 감소 (자연제방 형성).
        
        Args:
            discharge: 유량 배열
            bankfull_capacity: 하도 용량 (초과 시 범람)
            decay_rate: 거리에 따른 퇴적 감쇠율
            dt: 시간 간격
            
        Returns:
            deposition: 퇴적량 배열
        """
        from scipy.ndimage import distance_transform_edt
        
        h, w = self.grid.height, self.grid.width
        
        # 1. 범람 지점 식별 (용량 초과)
        overflow = np.maximum(0, discharge - bankfull_capacity)
        flood_mask = overflow > 0
        
        if not np.any(flood_mask):
            return np.zeros((h, w))
        
        # 2. 하도로부터의 거리 계산
        # flood_mask가 있는 곳이 하도
        channel_mask = discharge > bankfull_capacity * 0.5
        
        if not np.any(channel_mask):
            return np.zeros((h, w))
            
        # Distance Transform (하도로부터의 거리)
        distance = distance_transform_edt(~channel_mask) * self.grid.cell_size
        
        # 3. 퇴적량 계산 (지수 감쇠)
        # Deposition = overflow * exp(-k * distance)
        # 하도 근처(자연제방)에 많이, 멀수록(배후습지) 적게
        max_overflow = overflow.max()
        if max_overflow <= 0:
            return np.zeros((h, w))
            
        normalized_overflow = overflow / max_overflow
        
        # 범람 영향 범위 (최대 50 셀)
        max_distance = 50 * self.grid.cell_size
        influence = np.exp(-decay_rate * distance / self.grid.cell_size)
        influence[distance > max_distance] = 0
        
        # 퇴적량
        deposition = normalized_overflow.max() * influence * 0.1 * dt
        
        # 해수면 아래는 제외
        underwater = self.grid.is_underwater()
        deposition[underwater] = 0
        
        # 하도 자체는 제외 (하도는 침식이 우세)
        deposition[channel_mask] = 0
        
        # 4. 퇴적층에 추가
        self.grid.add_sediment(deposition)
        
        return deposition

    def transport_and_deposit(self, discharge: np.ndarray, dt: float = 1.0, Kf: float = 0.01) -> np.ndarray:
        """
        퇴적물 운반 및 퇴적 (Sediment Transport & Deposition)
        
        Transport Capacity Law:
        Q_cap = Kf * Q^m * S^n
        
        - Q_cap > Q_sed: 침식 (Erosion) -> 퇴적물 증가
        - Q_cap < Q_sed: 퇴적 (Deposition) -> 퇴적물 감소, 지형 상승
        
        Args:
            discharge: 유량
            dt: 시간 간격
            Kf: 운반 효율 계수 (Transport Efficiency)
        """
        slope, _ = self.grid.get_gradient()
        # 경사가 0이면 무한 퇴적 방지를 위해 최소값 설정
        slope = np.maximum(slope, 0.001)
        
        # 1. 운반 능력 (Transport Capacity) 계산
        # 침식 계수 K 대신 운반 계수 Kf 사용 (일반적으로 K보다 큼)
        capacity = Kf * np.power(discharge, self.m) * np.power(slope, self.n)
        
        # 2. 현재 부유사(Suspended Sediment) 가정
        # 상류에서 들어오는 유사량은 이전 단계의 침식량이나 기유입량에 의존
        # 여기서는 단순화를 위해 'Local Equilibrium'을 가정하지 않고,
        # 유량에 비례하는 초기 유사량을 가정하거나, 
        # 이전 스텝의 침식 결과를 이용해야 함.
        # 통합 모델을 위해: "Erosion" 함수가 깎아낸 흙을 반환하도록 하고, 
        # 이를 capacity와 비교하여 재퇴적시키거나 하류로 보냄.
        
        # 하지만 D8 알고리즘 상 하류로의 '전달(Routing)'이 필요함.
        # 여기서는 Simplified Landform Evolution Model (SLEM) 방식 적용:
        # dZs/dt = U - E + D
        # D = (Q_cap - Q_sed) / Length_scale (if Q_sed > Q_cap)
        # E = Stream Power (detachment limited)
        
        # Delta 시뮬레이션을 위한 접근:
        # 퇴적물 플럭스(Flux)를 하류로 밀어내는 로직 추가.
        
        h, w = self.grid.height, self.grid.width
        sediment_flux = np.zeros((h, w))
        
        # 유량 순서대로 처리 (Upstream -> Downstream)
        # discharge가 낮은 곳(상류)에서 높은 곳(하류)으로? 
        # D8 흐름 방향을 다시 추적해야 정확함.
        # 여기서는 간단히 'Capacity 초과분 퇴적'만 구현하고, 
        # Flux Routing은 HydroKernel과 연동되어야 함.
        
        # 임시: Capacity based deposition only (Local)
        # 퇴적량 = (현재 유사량 - 용량) * 비율
        # 현재 유사량이 없으므로, 침식된 흙(Stream Power 결과)이 
        # 해당 셀의 Capacity를 넘으면 즉시 퇴적된다고 가정.
        
        pass 
        # TODO: Flux Routing 구현 필요. 현재 구조에서는 어려움.
        # ErosionProcess를 수정하여 'simulate_transport' 메서드로 통합.
        
        return capacity

    def simulate_transport(self, discharge: np.ndarray, dt: float = 1.0, 
                          sediment_influx_map: np.ndarray = None) -> np.ndarray:
        """
        통합 퇴적물 이송 시뮬레이션 (Flux-based)
        1. 상류에서 퇴적물 유입 (Flux In)
        2. 로컬 침식/퇴적 (Erosion/Deposition)
        3. 하류로 배출 (Flux Out)
        """
        h, w = self.grid.height, self.grid.width
        elev = self.grid.elevation
        
        # 1. 정렬 (높은 곳 -> 낮은 곳)
        indices = np.argsort(elev.ravel())[::-1]
        
        # 퇴적물 플럭스 초기화 (유입원 반영)
        flux = np.zeros((h, w))
        if sediment_influx_map is not None:
            flux += sediment_influx_map
            
        slope, _ = self.grid.get_gradient()
        slope = np.maximum(slope, 0.001)
        
        change = np.zeros((h, w))
        
        # D8 Neighbors (Lookup for flow_dir)
        d8_dr = [-1, -1, -1,  0,  0,  1,  1,  1]
        d8_dc = [-1,  0,  1, -1,  1, -1,  0,  1]
        
        # Check if flow_dir is available
        use_flow_dir = (self.grid.flow_dir is not None)
        
        for idx in indices:
            r, c = idx // w, idx % w
            


            # 해수면 아래 깊은 곳은 퇴적 위주
            underwater = self.grid.is_underwater()[r, c]
            
            # A. 운반 능력 (Capacity)
            # 물 속에서는 유속이 급감한다고 가정 -> Capacity 감소
            # eff_slope calculation fix: slope can be very small on flat land
            eff_slope = slope[r, c] if not underwater else slope[r, c] * 0.01
            
            # Kf (Transportation efficiency) should be high enough
            # Use 'self.K * 100' or similar
            qs_cap = self.K * 500 * np.power(discharge[r, c], self.m) * np.power(eff_slope, self.n)
            
            # B. 현재 플럭스 (상류에서 들어온 것 + 로컬 침식 잠재량)
            qs_in = flux[r, c]
            
            # C. 침식 vs 퇴적 결정
            # 기계적 침식 (Stream Power)
            potential_erosion = self.K * np.power(discharge[r, c], self.m) * np.power(slope[r, c], self.n) * dt
            
            # 만약 들어온 흙(qs_in)이 용량(qs_cap)보다 많으면 -> 퇴적
            if qs_in > qs_cap:
                # 퇴적량 = 초과분 * 1.0 (일단 100% 퇴적 가정하여 효과 확인)
                deposition_amount = (qs_in - qs_cap) * 1.0 
                change[r, c] += deposition_amount
                qs_out = qs_cap # 나머지는 하류로? 아니, 퇴적 후 남은건 qs_cap임 (Transport-limited)
            else:
                # 용량이 남으면 -> 침식하여 흙을 더 싣고감
                # 실제 침식 = 잠재 침식 (기반암도 침식 가능)
                erosion_amount = potential_erosion
                
                change[r, c] -= erosion_amount
                qs_out = qs_in + erosion_amount

            # D. 하류로 전달 (Qs Out Routing)
            # Use pre-calculated flow direction if available
            target_r, target_c = -1, -1
            
            if use_flow_dir:
                k = self.grid.flow_dir[r, c]
                # k could be default 0 even if no flow?
                # Usually sink nodes have special value (e.g. -1 or point to self)
                # But here we initialized to 0.
                # Need to check constraints.
                # If discharge[r,c] > 0, flow_dir should be valid.
                if discharge[r, c] > 0:
                     nr = r + d8_dr[k]
                     nc = c + d8_dc[k]
                     if 0 <= nr < h and 0 <= nc < w:
                         target_r, target_c = nr, nc
            else:
                # Fallback: Local Seek (Slow)
                min_z = elev[r, c]
                for k in range(8):
                    nr = r + d8_dr[k]
                    nc = c + d8_dc[k]
                    if 0 <= nr < h and 0 <= nc < w:
                        if elev[nr, nc] < min_z:
                            min_z = elev[nr, nc]
                            target_r, target_c = nr, nc
            
            if target_r != -1:
                flux[target_r, target_c] += qs_out
            else:
                # 갇힌 곳(Sink) -> 그 자리에 퇴적
                # 침식이 발생했다면 되돌려놓고 퇴적
                change[r, c] += qs_out
        
        # 지형 업데이트
        # 침식은 elevation 감소, 퇴적은 sediment 증가이지만
        # 여기서는 통합하여 elevation/sediment 조정
        
        # 퇴적분: sediment 층에 추가
        self.grid.add_sediment(np.maximum(change, 0))
        
        # 침식분: elevation 감소 (grid.add_sediment가 음수도 처리하나? 아님)
        # 침식은 bedrock이나 sediment를 깎아야 함.
        # erosion_process.py의 역할상 직접 grid 수정을 해도 됨.
        erosion_mask = change < 0
        loss = -change[erosion_mask]
        
        # 퇴적층 먼저 깎고 기반암 깎기
        sed_thickness = self.grid.sediment[erosion_mask]
        sed_loss = np.minimum(loss, sed_thickness)
        rock_loss = loss - sed_loss
        
        self.grid.sediment[erosion_mask] -= sed_loss
        self.grid.bedrock[erosion_mask] -= rock_loss
        self.grid.update_elevation()
        
        return change
