"""
📊 Visualization - LEM 시각화 모듈
실시간 그래프, A/B 비교, 물 파티클 애니메이션
"""
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from app.utils.plotly_compat import go, make_subplots

@dataclass
class SimulationStats:
    """시뮬레이션 통계"""
    time: float = 0.0
    mean_elevation: float = 0.0
    max_elevation: float = 0.0
    total_erosion: float = 0.0
    total_deposition: float = 0.0
    river_length: float = 0.0
    
@dataclass
class SimulationHistory:
    """시뮬레이션 히스토리"""
    times: List[float] = field(default_factory=list)
    mean_elevations: List[float] = field(default_factory=list)
    max_elevations: List[float] = field(default_factory=list)
    erosion_rates: List[float] = field(default_factory=list)
    
class LEMVisualizer:
    """
    LEM 시각화 도구
    
    - 실시간 통계 그래프
    - A/B 시나리오 비교
    - 물 파티클 애니메이션
    """
    
    def __init__(self):
        self.history_a = SimulationHistory()
        self.history_b = SimulationHistory()
        
    # ========== 실시간 그래프 ==========
    def record_stats(self, elevation: np.ndarray, 
                     erosion: np.ndarray, 
                     time: float,
                     scenario: str = 'a'):
        """
        통계 기록
        
        Args:
            elevation: 고도 그리드
            erosion: 침식 그리드
            time: 현재 시간
            scenario: 'a' 또는 'b'
        """
        history = self.history_a if scenario == 'a' else self.history_b
        
        history.times.append(time)
        history.mean_elevations.append(float(np.mean(elevation)))
        history.max_elevations.append(float(np.max(elevation)))
        history.erosion_rates.append(float(np.mean(erosion)))
    
    def create_realtime_graph(self, scenario: str = 'a') -> go.Figure:
        if go is None or make_subplots is None:
            from app.utils.plotly_compat import plotly_error_message
            raise RuntimeError(plotly_error_message())

        """
        실시간 통계 그래프 생성
        
        Args:
            scenario: 'a' 또는 'b'
            
        Returns:
            Plotly Figure
        """
        history = self.history_a if scenario == 'a' else self.history_b
        
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('고도 변화', '침식률')
        )
        
        # 고도 그래프
        fig.add_trace(
            go.Scatter(
                x=history.times,
                y=history.mean_elevations,
                name='평균 고도',
                line=dict(color='#007AFF', width=2)
            ),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(
                x=history.times,
                y=history.max_elevations,
                name='최고 고도',
                line=dict(color='#5AC8FA', width=2, dash='dash')
            ),
            row=1, col=1
        )
        
        # 침식률 그래프
        fig.add_trace(
            go.Scatter(
                x=history.times,
                y=history.erosion_rates,
                name='침식률',
                line=dict(color='#FF3B30', width=2),
                fill='tozeroy',
                fillcolor='rgba(255,59,48,0.2)'
            ),
            row=2, col=1
        )
        
        fig.update_layout(
            height=500,
            template='plotly_dark',
            showlegend=True
        )
        
        return fig
    
    # ========== A/B 시나리오 비교 ==========
    def compare_scenarios(self) -> go.Figure:
        """
        A/B 시나리오 비교 그래프
        
        Returns:
            비교 그래프
        """
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'A: 평균 고도', 'B: 평균 고도',
                'A: 침식률', 'B: 침식률'
            )
        )
        
        # Scenario A
        fig.add_trace(
            go.Scatter(x=self.history_a.times, y=self.history_a.mean_elevations,
                      name='A 고도', line=dict(color='#007AFF')),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=self.history_a.times, y=self.history_a.erosion_rates,
                      name='A 침식', line=dict(color='#FF3B30')),
            row=2, col=1
        )
        
        # Scenario B
        fig.add_trace(
            go.Scatter(x=self.history_b.times, y=self.history_b.mean_elevations,
                      name='B 고도', line=dict(color='#34C759')),
            row=1, col=2
        )
        fig.add_trace(
            go.Scatter(x=self.history_b.times, y=self.history_b.erosion_rates,
                      name='B 침식', line=dict(color='#FF9500')),
            row=2, col=2
        )
        
        fig.update_layout(
            height=600,
            template='plotly_dark',
            title='시나리오 A vs B 비교'
        )
        
        return fig
    
    def compare_elevations(self, elev_a: np.ndarray, 
                           elev_b: np.ndarray) -> go.Figure:
        """
        두 고도 그리드 차이 시각화
        
        Args:
            elev_a: 시나리오 A 고도
            elev_b: 시나리오 B 고도
            
        Returns:
            차이 히트맵
        """
        diff = elev_a - elev_b
        
        fig = go.Figure(data=go.Heatmap(
            z=diff,
            colorscale='RdBu',
            zmid=0,
            colorbar=dict(title='A - B (m)')
        ))
        
        fig.update_layout(
            title='시나리오 차이 (A - B)',
            height=500,
            template='plotly_dark'
        )
        
        return fig
    
    # ========== 물 파티클 ==========
    def create_water_particles(self, drainage_area: np.ndarray,
                               elevation: np.ndarray,
                               num_particles: int = 500) -> Dict:
        """
        물 파티클 위치 생성
        
        Args:
            drainage_area: 배수면적 그리드
            elevation: 고도 그리드
            num_particles: 파티클 수
            
        Returns:
            파티클 위치 딕셔너리
        """
        h, w = drainage_area.shape
        
        # 배수면적 기반 확률로 파티클 배치
        prob = drainage_area.flatten() / (drainage_area.sum() + 1e-10)
        
        indices = np.random.choice(len(prob), size=num_particles, p=prob)
        
        rows = indices // w
        cols = indices % w
        heights = elevation[rows, cols] + 1  # 지형 위에 표시
        
        # 파티클 크기 = 배수면적
        sizes = np.log10(drainage_area[rows, cols] + 1)
        sizes = (sizes / sizes.max()) * 8 + 2
        
        return {
            'x': cols,
            'y': rows,
            'z': heights,
            'sizes': sizes
        }
    
    def clear_history(self, scenario: str = 'both'):
        """히스토리 초기화"""
        if scenario in ['a', 'both']:
            self.history_a = SimulationHistory()
        if scenario in ['b', 'both']:
            self.history_b = SimulationHistory()
