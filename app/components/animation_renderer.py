"""
🎬 Plotly Animation Renderer
부드러운 3D 지형 애니메이션 (카메라 유지)
"""
import numpy as np
import plotly.graph_objects as go
from typing import Callable


def create_animated_terrain_figure(
    landform_func: Callable,
    grid_size: int = 50,
    num_frames: int = 40,  # 더 많은 프레임 (천천히 부드럽게)
    title: str = "지형 형성 과정",
    landform_type: str = "river"
) -> go.Figure:
    """Plotly 네이티브 애니메이션으로 부드러운 3D 지형 애니메이션 생성
    
    Args:
        landform_func: 지형 생성 함수 (grid_size, stage) -> elevation
        grid_size: 그리드 크기
        num_frames: 애니메이션 프레임 수 (많을수록 부드러움)
        title: 그래프 제목
        landform_type: 지형 유형 (colorscale 결정)
    
    Returns:
        go.Figure: 애니메이션이 포함된 Plotly Figure
    """
    h, w = grid_size, grid_size
    x = np.arange(w)
    y = np.arange(h)
    
    # 컬러스케일 설정
    colorscale = _get_colorscale(landform_type)
    
    # 모든 프레임 미리 생성
    frames = []
    all_elevations = []
    
    stage_descriptions = []
    
    for i in range(num_frames):
        stage = i / (num_frames - 1)
        
        # 지형 생성 + 단계 설명 추출
        stage_desc = ""
        try:
            result = landform_func(grid_size, stage, return_metadata=True)
            if isinstance(result, tuple):
                elevation = result[0]
                metadata = result[1] if len(result) > 1 else {}
                stage_desc = metadata.get('stage_description', '')
            else:
                elevation = result
        except:
            try:
                elevation = landform_func(grid_size, stage)
            except:
                elevation = np.zeros((grid_size, grid_size))
        
        all_elevations.append(elevation)
        stage_descriptions.append(stage_desc)
        
        # Biome 계산 (간소화)
        dy, dx = np.gradient(elevation)
        slope = np.sqrt(dx**2 + dy**2)
        biome = np.ones_like(elevation)  # 기본: 풀
        biome[slope > 1.2] = 2  # 암석
        biome[elevation < 5] = 0  # 물/모래
        
        # 프레임 라벨
        frame_label = f"{int(stage * 100)}%"
        
        # 단계 설명이 있으면 제목에 포함
        frame_layout = None
        if stage_desc:
            frame_layout = go.Layout(
                title=dict(
                    text=f"{title}<br><span style='font-size:13px;color:#88ccff;'>{stage_desc}</span>",
                    font=dict(color='white', size=16)
                )
            )
        
        frames.append(go.Frame(
            data=[go.Surface(
                z=elevation,
                x=x, y=y,
                surfacecolor=biome,
                colorscale=colorscale,
                cmin=0, cmax=3,
                showscale=False,
                lighting=dict(ambient=0.4, diffuse=0.5, roughness=0.9, specular=0.1)
            )],
            name=frame_label,
            layout=frame_layout
        ))
    
    # 초기 프레임 (stage=0)
    initial_elevation = all_elevations[0]
    dy, dx = np.gradient(initial_elevation)
    slope = np.sqrt(dx**2 + dy**2)
    initial_biome = np.ones_like(initial_elevation)
    initial_biome[slope > 1.2] = 2
    initial_biome[initial_elevation < 5] = 0
    
    fig = go.Figure(
        data=[go.Surface(
            z=initial_elevation,
            x=x, y=y,
            surfacecolor=initial_biome,
            colorscale=colorscale,
            cmin=0, cmax=3,
            showscale=False,
            lighting=dict(ambient=0.4, diffuse=0.5, roughness=0.9, specular=0.1)
        )],
        frames=frames
    )
    
    # 슬라이더 (프레임 이동용)
    sliders = [{
        'active': 0,
        'yanchor': 'top',
        'xanchor': 'left',
        'currentvalue': {
            'font': {'size': 14, 'color': 'white'},
            'prefix': '형성 단계: ',
            'suffix': '',
            'visible': True,
            'xanchor': 'center'
        },
        'transition': {'duration': 50, 'easing': 'cubic-in-out'},
        'pad': {'b': 10, 't': 50},
        'len': 0.9,
        'x': 0.05,
        'y': 0,
        'steps': [
            {
                'args': [[f.name], {'frame': {'duration': 50, 'redraw': True}, 'mode': 'immediate', 'transition': {'duration': 50}}],
                'label': f.name,
                'method': 'animate'
            }
            for f in frames
        ]
    }]
    
    # 재생/정지 버튼
    updatemenus = [{
        'type': 'buttons',
        'showactive': False,
        'y': 1.15,
        'x': 0.05,
        'xanchor': 'left',
        'yanchor': 'top',
        'pad': {'t': 0, 'r': 10},
        'buttons': [
            {
                'label': '▶️ 재생',
                'method': 'animate',
                'args': [
                    None,
                    {
                        'frame': {'duration': 350, 'redraw': True},
                        'fromcurrent': True,
                        'transition': {'duration': 200, 'easing': 'quadratic-in-out'}
                    }
                ]
            },
            {
                'label': '⏸️ 정지',
                'method': 'animate',
                'args': [
                    [None],
                    {
                        'frame': {'duration': 0, 'redraw': False},
                        'mode': 'immediate',
                        'transition': {'duration': 0}
                    }
                ]
            },
            {
                'label': '⏮️ 처음',
                'method': 'animate',
                'args': [
                    ['0%'],
                    {
                        'frame': {'duration': 0, 'redraw': True},
                        'mode': 'immediate',
                        'transition': {'duration': 0}
                    }
                ]
            }
        ]
    }]
    # 지형 유형별 최적 카메라 각도
    camera_settings = _get_optimal_camera(landform_type)
    
    # 레이아웃
    fig.update_layout(
        title=dict(text=title, font=dict(color='white', size=16)),
        scene=dict(
            xaxis=dict(title='X (m)', backgroundcolor='#1a1a2e', gridcolor='#444', color='#cccccc'),
            yaxis=dict(title='Y (m)', backgroundcolor='#1a1a2e', gridcolor='#444', color='#cccccc'),
            zaxis=dict(title='Elevation', backgroundcolor='#1a1a2e', gridcolor='#444', color='#cccccc'),
            bgcolor='#0e1117',
            camera=camera_settings,
            aspectmode='manual',
            aspectratio=dict(x=1, y=1, z=0.4)
        ),
        paper_bgcolor='#0e1117',
        plot_bgcolor='#0e1117',
        height=700,
        margin=dict(l=10, r=10, t=80, b=80),
        updatemenus=updatemenus,
        sliders=sliders
    )
    
    return fig


def _get_colorscale(landform_type: str):
    """지형 유형에 따른 컬러스케일 반환"""
    if landform_type == 'glacial':
        return [
            [0.0, '#4682B4'], [0.33, '#4682B4'],
            [0.33, '#556B2F'], [0.66, '#556B2F'],
            [0.66, '#808080'], [1.0, '#E0FFFF']
        ]
    elif landform_type in ['river', 'coastal']:
        return [
            [0.0, '#4682B4'], [0.33, '#4682B4'],
            [0.33, '#556B2F'], [0.66, '#556B2F'],
            [0.66, '#808080'], [1.0, '#D2B48C']
        ]
    elif landform_type == 'arid':
        return [
            [0.0, '#EDC9AF'], [0.33, '#EDC9AF'],
            [0.33, '#CD853F'], [0.66, '#CD853F'],
            [0.66, '#808080'], [1.0, '#DAA520']
        ]
    else:
        return [
            [0.0, '#E6C288'], [0.33, '#E6C288'],
            [0.33, '#556B2F'], [0.66, '#556B2F'],
            [0.66, '#808080'], [1.0, '#A0522D']
        ]


def _get_optimal_camera(landform_type: str) -> dict:
    """지형 유형별 최적 카메라 각도 반환
    
    각 지형 유형의 형성 과정이 잘 보이는 각도로 설정
    """
    if landform_type == 'river':
        # 하천/선상지: 산쪽(상류)에서 평지(하류) 방향으로 내려다봄
        # 선상지가 부채꼴로 펼쳐지는 모습이 잘 보이는 각도
        return dict(
            eye=dict(x=-0.3, y=-2.2, z=1.8),
            center=dict(x=0, y=0.2, z=-0.2),
            up=dict(x=0, y=0, z=1)
        )
    elif landform_type == 'glacial':
        # 빙하: 위에서 내려다보는 각도로 U자곡/권곡 잘 보이게
        return dict(
            eye=dict(x=0.8, y=-1.5, z=1.5),
            center=dict(x=0, y=0, z=-0.2),
            up=dict(x=0, y=0, z=1)
        )
    elif landform_type == 'volcanic':
        # 화산: 측면에서 봐서 산체 형태 잘 보이게
        return dict(
            eye=dict(x=1.8, y=-1.2, z=0.8),
            center=dict(x=0, y=0, z=0),
            up=dict(x=0, y=0, z=1)
        )
    elif landform_type == 'coastal':
        # 해안: 바다→육지 방향으로 절벽 잘 보이게
        return dict(
            eye=dict(x=0.5, y=2.0, z=0.8),
            center=dict(x=0, y=0, z=-0.1),
            up=dict(x=0, y=0, z=1)
        )
    elif landform_type == 'arid':
        # 건조: 사구 형태 잘 보이게 낮은 각도
        return dict(
            eye=dict(x=2.0, y=-1.0, z=0.6),
            center=dict(x=0, y=0, z=-0.1),
            up=dict(x=0, y=0, z=1)
        )
    elif landform_type == 'karst':
        # 카르스트: 위에서 돌리네/우발라 잘 보이게
        return dict(
            eye=dict(x=1.0, y=-1.0, z=1.8),
            center=dict(x=0, y=0, z=-0.2),
            up=dict(x=0, y=0, z=1)
        )
    else:
        # 기본값: 대각선 방향
        return dict(
            eye=dict(x=1.5, y=-1.5, z=1.0),
            center=dict(x=0, y=0, z=-0.1),
            up=dict(x=0, y=0, z=1)
        )


def get_multi_angle_cameras() -> dict:
    """다중 시점 카메라 프리셋
    
    X축(정면), Y축(측면), Z축(평면도), 등각투영 4가지 시점
    """
    return {
        "🎯 등각 (기본)": dict(
            eye=dict(x=1.5, y=-1.5, z=1.2),
            center=dict(x=0, y=0, z=-0.1),
            up=dict(x=0, y=0, z=1)
        ),
        "➡️ X축 (좌측면)": dict(
            eye=dict(x=2.5, y=0, z=0.3),
            center=dict(x=0, y=0, z=0),
            up=dict(x=0, y=0, z=1)
        ),
        "⬅️ X축 (우측면)": dict(
            eye=dict(x=-2.5, y=0, z=0.3),
            center=dict(x=0, y=0, z=0),
            up=dict(x=0, y=0, z=1)
        ),
        "⬆️ Y축 (정면)": dict(
            eye=dict(x=0, y=-2.5, z=0.3),
            center=dict(x=0, y=0, z=0),
            up=dict(x=0, y=0, z=1)
        ),
        "⬇️ Y축 (후면)": dict(
            eye=dict(x=0, y=2.5, z=0.3),
            center=dict(x=0, y=0, z=0),
            up=dict(x=0, y=0, z=1)
        ),
        "🔽 Z축 (평면도)": dict(
            eye=dict(x=0, y=0, z=2.5),
            center=dict(x=0, y=0, z=0),
            up=dict(x=0, y=1, z=0)
        ),
        "🔄 대각선 낮음": dict(
            eye=dict(x=2.0, y=-2.0, z=0.5),
            center=dict(x=0, y=0, z=-0.1),
            up=dict(x=0, y=0, z=1)
        ),
        "🌄 상류→하류": dict(
            eye=dict(x=-0.3, y=-2.5, z=1.5),
            center=dict(x=0, y=0.2, z=-0.2),
            up=dict(x=0, y=0, z=1)
        )
    }
