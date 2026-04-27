"""
🌍 Global Climate Engine - 전지구적 기후 시스템 모듈
위도/계절 기반 이론적 기후 계산

- 태양 입사각 및 일사량
- ITCZ 위치 (계절별 이동)
- 기압대 및 바람 패턴
- 쾨펜 기후 구분 (단순화)
"""
import numpy as np
from dataclasses import dataclass
from typing import Tuple, List, Dict

# Earth constants
AXIAL_TILT = 23.44  # 지구 자전축 기울기 (도)
EARTH_RADIUS = 6371  # km


@dataclass
class ClimateData:
    """특정 위치/시간의 기후 데이터"""
    temperature: float  # °C
    pressure: float  # hPa (상대값)
    wind_u: float  # 동서 방향 바람 (m/s, 동쪽 +)
    wind_v: float  # 남북 방향 바람 (m/s, 북쪽 +)
    precipitation: float  # 상대 강수량 (0-100)
    koppen_zone: str  # 쾨펜 기호


class GlobalClimateEngine:
    """
    전지구적 기후 시뮬레이션 엔진
    
    위도와 월(계절)에 따른 이론적 기후 패턴을 계산합니다.
    실제 데이터가 아닌 교육용 이론 모델입니다.
    """
    
    def __init__(self):
        # 위도 그리드 (-90 ~ 90)
        self.lat_resolution = 2  # 2도 간격
        self.lon_resolution = 4  # 4도 간격
        
        self.lats = np.arange(-90, 91, self.lat_resolution)
        self.lons = np.arange(-180, 181, self.lon_resolution)
        
        # 대기 셀 경계 (ITCZ 기준 상대적)
        self.cell_boundaries = {
            'hadley': (0, 30),  # 적도 ~ 아열대
            'ferrel': (30, 60),  # 중위도
            'polar': (60, 90),  # 고위도
        }
    
    # ========== 태양 입사 ==========
    def solar_declination(self, day_of_year: int) -> float:
        """
        태양 적위 계산 (도)
        
        Args:
            day_of_year: 1-365
            
        Returns:
            태양 적위 (북반구 여름 +, 겨울 -)
        """
        # 하지(6/21) ≈ 172일을 기준으로 사인파
        return AXIAL_TILT * np.sin(2 * np.pi * (day_of_year - 81) / 365)
    
    def month_to_day(self, month: int) -> int:
        """월(1-12)을 대표 일자로 변환"""
        # 각 월의 중간일
        days_mid = [15, 45, 74, 105, 135, 166, 196, 227, 258, 288, 319, 349]
        return days_mid[month - 1]
    
    def itcz_latitude(self, month: int) -> float:
        """
        ITCZ(열대수렴대) 위치 계산
        
        북반구 여름: 북상 (~15°N)
        북반구 겨울: 남하 (~5°S)
        """
        day = self.month_to_day(month)
        # ITCZ는 태양 직사점을 따라가지만 지연됨
        declination = self.solar_declination(day)
        # 대륙 분포로 인해 ITCZ는 평균적으로 북쪽에 치우침 (+5°)
        return declination * 0.6 + 5.0
    
    # ========== 지형 마스크 (간소화) ==========
    def get_land_mask(self, lat: float, lon: float) -> float:
        """
        육지/해양 마스크 반환 (1: 육지, 0: 해양)
        대략적인 대륙 분포를 사각형/타원 형태로 근사
        """
        # 아프로-유라시아 (대략적)
        if -35 <= lat <= 75 and -20 <= lon <= 150:
            return 1.0
        # 아메리카
        if -55 <= lat <= 70 and -130 <= lon <= -35:
            return 1.0
        # 호주
        if -40 <= lat <= -10 and 110 <= lon <= 155:
            return 1.0
        # 남극
        if lat <= -60:
            return 1.0
        return 0.0

    # ========== 온도 계산 ==========
    def calculate_temperature(self, lat: float, month: int, mode: str = 'ideal', lon: float = 0) -> float:
        """
        위도와 월에 따른 기온 계산 (Real 모드: 대륙성 기후 반영)
        """
        # 기본 온도 (적도)
        T_base = 27.0
        
        # 위도 효과
        lat_effect = 0.6 * abs(lat)
        
        # 계절 효과
        day = self.month_to_day(month)
        declination = self.solar_declination(day)
        
        if lat >= 0:
            season_factor = declination * (abs(lat) / 90) * 0.8
        else:
            season_factor = -declination * (abs(lat) / 90) * 0.8
            
        temp = T_base - lat_effect + season_factor
        
        # [Real 모드] 대륙성 기후 효과 (비열 차이)
        if mode == 'real':
            is_land = self.get_land_mask(lat, lon)
            if is_land:
                # 육지는 여름에 더 덥고(+), 겨울에 더 춥다(-)
                # 북반구 육지
                if lat > 0:
                    # declination > 0 (여름) -> 더 더움
                    # declination < 0 (겨울) -> 더 추움
                    land_effect = declination * 0.5 
                # 남반구 육지
                else: 
                    # declination < 0 (여름) -> 더 더움 (음수 * 음수 = 양수 필요)
                    land_effect = -declination * 0.5
                
                temp += land_effect
        
        return temp
    
    # ========== 기압 계산 ==========
    def calculate_pressure(self, lat: float, month: int, mode: str = 'ideal', lon: float = 0) -> float:
        itcz = self.itcz_latitude(month)
        
        # [Real 모드] 몬순 효과 (여름철 육지 저기압)
        monsoon_effect = 0
        if mode == 'real':
            day = self.month_to_day(month)
            declination = self.solar_declination(day)
            is_land = self.get_land_mask(lat, lon)
            
            # 여름철 대륙 내부 강한 저기압 발달 (티베트 고기압/인도 저기압)
            if is_land:
                # 북반구 여름 (declination > 0)
                if lat > 20 and declination > 10:
                    monsoon_effect = -0.4  # 강한 저기압
                # 북반구 겨울 (declination < 0) -> 시베리아 고기압
                elif lat > 40 and declination < -10:
                    monsoon_effect = 0.5   # 강한 고기압
        
        rel_lat = lat - itcz
        pressure = np.sin(np.radians(rel_lat * 3))
        
        if abs(rel_lat) < 10:
            pressure = -0.8
            
        return pressure + monsoon_effect
    
    # ========== 바람 계산 ==========
    def calculate_wind(self, lat: float, month: int) -> Tuple[float, float]:
        # 바람은 복잡도를 위해 Real 모드에서도 일단 Ideal 패턴 유지 (또는 몬순 추가 가능)
        return super().calculate_wind(lat, month) if hasattr(super(), 'calculate_wind') else self._ideal_wind(lat, month)

    def _ideal_wind(self, lat: float, month: int) -> Tuple[float, float]:
        # 기존 calculate_wind 로직 이동
        itcz = self.itcz_latitude(month)
        rel_lat = lat - itcz
        
        if abs(rel_lat) < 30:  # Hadley
            v = -5.0 if lat > itcz else 5.0
            u = -3.0 if lat > 0 else 3.0
        elif abs(rel_lat) < 60:  # Ferrel
            v = 2.0 if lat > itcz else -2.0
            u = 5.0
        else:  # Polar
            v = -2.0 if lat > 0 else 2.0
            u = -3.0 if lat > 0 else 3.0
        return (u, v)

    # ========== 강수량 계산 (업데이트) ==========
    def calculate_precipitation(self, lat: float, month: int, mode: str = 'ideal', lon: float = 0) -> float:
        itcz = self.itcz_latitude(month)
        rel_lat = lat - itcz
        
        base_precip = 0
        if abs(rel_lat) < 10: base_precip = 90 - abs(rel_lat) * 5
        elif 20 < abs(rel_lat) < 35: base_precip = 20
        elif 40 < abs(lat) < 60: base_precip = 60
        elif abs(lat) > 70: base_precip = 15
        else: base_precip = 40
        
        # [Real 모드] 몬순 우기
        if mode == 'real':
            is_land = self.get_land_mask(lat, lon)
            day = self.month_to_day(month)
            declination = self.solar_declination(day)
            
            # 아시아 몬순 (대략적 위치: 인도/동남아)
            # 여름철(6-9월) 강수량 폭증
            if is_land and 10 < lat < 40 and 60 < lon < 130:
                if declination > 10:  # 여름
                    base_precip += 100  # 폭우
                elif declination < -10: # 겨울
                    base_precip -= 30   # 건조
            
            # 사하라 사막 (대략적) - ITCZ가 올라와도 비가 안옴
            if is_land and 15 < lat < 30 and -15 < lon < 50:
                base_precip = 5  # 강제 건조
                
        return base_precip
    
    # ========== 쾨펜 기후 구분 ==========
    def get_koppen_zone(self, temp: float, precip: float, lat: float) -> str:
        """
        단순화된 쾨펜 기후 구분
        
        Returns:
            쾨펜 기호 (Af, Am, Aw, BWh, BSh, Cfa, Dfc, ET 등)
        """
        # 연평균 기온과 강수량으로 단순 분류
        
        # E기후 (한대)
        if temp < 0:
            if temp < -10:
                return 'EF'  # 빙설기후
            return 'ET'  # 툰드라
        
        # D기후 (냉대)
        if temp < 10 and abs(lat) > 40:
            if precip > 50:
                return 'Dfc'  # 냉대습윤 (타이가)
            return 'Dwc'  # 냉대동계건조
        
        # A기후 (열대)
        if temp > 18 and abs(lat) < 25:
            if precip > 80:
                return 'Af'  # 열대우림
            elif precip > 40:
                return 'Am'  # 열대몬순
            return 'Aw'  # 열대사바나
        
        # B기후 (건조)
        if precip < 25:
            if temp > 18:
                return 'BWh'  # 고온사막
            return 'BWk'  # 한랭사막
        if precip < 40:
            if temp > 18:
                return 'BSh'  # 고온스텝
            return 'BSk'  # 한랭스텝
        
        # C기후 (온대)
        if temp > 0:
            if precip > 60:
                return 'Cfa'  # 온난습윤
            return 'Cs'  # 지중해성
        
        return 'Cfb'  # 서안해양성 (기본)
    
    # ========== 전체 그리드 계산 ==========
    def compute_global_climate(self, month: int, mode: str = 'ideal') -> Dict[str, np.ndarray]:
        """
        전 지구적 기후 데이터 그리드 계산
        
        Args:
            month: 1-12
            mode: 'ideal' (이론적 모델) 또는 'real' (현실 근사 모델)
            
        Returns:
            Dict with keys: 'temp', 'pressure', 'wind_u', 'wind_v', 'precip', 'koppen'
        """
        n_lat = len(self.lats)
        n_lon = len(self.lons)
        
        temp = np.zeros((n_lat, n_lon))
        pressure = np.zeros((n_lat, n_lon))
        wind_u = np.zeros((n_lat, n_lon))
        wind_v = np.zeros((n_lat, n_lon))
        precip = np.zeros((n_lat, n_lon))
        koppen = np.empty((n_lat, n_lon), dtype=object)
        
        for i, lat in enumerate(self.lats):
            for j, lon in enumerate(self.lons):
                t = self.calculate_temperature(lat, month, mode, lon)
                p = self.calculate_pressure(lat, month, mode, lon)
                u, v = self.calculate_wind(lat, month) # 바람은 로직상 Ideal 유지
                pr = self.calculate_precipitation(lat, month, mode, lon)
                k = self.get_koppen_zone(t, pr, lat)
                
                temp[i, j] = t
                pressure[i, j] = p
                wind_u[i, j] = u
                wind_v[i, j] = v
                precip[i, j] = pr
                koppen[i, j] = k
        
        return {
            'lats': self.lats,
            'lons': self.lons,
            'temp': temp,
            'pressure': pressure,
            'wind_u': wind_u,
            'wind_v': wind_v,
            'precip': precip,
            'koppen': koppen,
            'itcz_lat': self.itcz_latitude(month),
        }
    
    # ========== 대기 순환 셀 좌표 ==========
    def get_circulation_cells(self, month: int) -> List[Dict]:
        """
        대기 순환 셀(해들리/페렐/극) 표시를 위한 좌표 반환
        
        Returns:
            List of cell info dicts
        """
        itcz = self.itcz_latitude(month)
        
        cells = []
        
        # 북반구 해들리
        cells.append({
            'name': 'Hadley (N)',
            'lat_range': (itcz, itcz + 30),
            'direction': 'clockwise',
            'color': '#FF6B6B',
        })
        
        # 남반구 해들리
        cells.append({
            'name': 'Hadley (S)',
            'lat_range': (itcz - 30, itcz),
            'direction': 'counterclockwise',
            'color': '#FF6B6B',
        })
        
        # 북반구 페렐
        cells.append({
            'name': 'Ferrel (N)',
            'lat_range': (itcz + 30, itcz + 60),
            'direction': 'counterclockwise',
            'color': '#4ECDC4',
        })
        
        # 남반구 페렐
        cells.append({
            'name': 'Ferrel (S)',
            'lat_range': (itcz - 60, itcz - 30),
            'direction': 'clockwise',
            'color': '#4ECDC4',
        })
        
        # 북반구 극순환
        cells.append({
            'name': 'Polar (N)',
            'lat_range': (itcz + 60, 90),
            'direction': 'clockwise',
            'color': '#45B7D1',
        })
        
        # 남반구 극순환
        cells.append({
            'name': 'Polar (S)',
            'lat_range': (-90, itcz - 60),
            'direction': 'counterclockwise',
            'color': '#45B7D1',
        })
        
        return cells
