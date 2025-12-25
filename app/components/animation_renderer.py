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
    landform_type: str = "river",
    detailed_type: str = None
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
    
    # 재생/정지 버튼 (오른쪽 배치)
    updatemenus = [{
        'type': 'buttons',
        'showactive': False,
        'y': 1.0,
        'x': 0.85,
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
    # 지형 유형별 최적 카메라 각도 (세부 지형 타입 포함)
    camera_settings = _get_optimal_camera(landform_type, detailed_type)
    
    # 지형 유형별 Z축 스케일 (aspect ratio)
    # 지형 유형별 Z축 스케일 (aspect ratio)
    z_scales = {
        # General Categories
        'arid': 0.25,      # Default Dune
        'coastal': 0.35,
        'river': 0.4,
        'glacial': 0.5,
        'volcanic': 0.6,
        'karst': 0.35,
        
        # Specific Overrides
        'mesa_butte': 0.5,
        'pedestal_rock': 0.7,
        'tower_karst': 0.7,
        'shield_volcano': 0.3,
        'stratovolcano': 0.7,
        'horn': 0.7,
        'fjord': 0.5,
        'wadi': 0.5,
        'pediment': 0.4,
        'canyon': 0.6
    }
    
    z_aspect = z_scales.get(detailed_type)
    if z_aspect is None:
        z_aspect = z_scales.get(landform_type, 0.4)
    
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
            aspectratio=dict(x=1, y=1, z=z_aspect)
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


def _get_optimal_camera(landform_type: str, detailed_type: str = None) -> dict:
    """지형 유형별 최적 카메라 각도 반환
    
    각 지형 유형의 형성 과정이 잘 보이는 각도로 설정
    
    Args:
        landform_type: 대분류 ('river', 'glacial', 'volcanic', 등)
        detailed_type: 세부 지형 ('alluvial_fan', 'delta', 'meander', 등)
    """
    # 1. 세부 지형별 카메라 (우선 적용)
    detailed_cameras = {
        # === 하천 지형 ===
        'alluvial_fan': dict(
            # 선상지: 산지에서 평지로 내려다보는 각도 (부채꼴 전체가 보이게)
            eye=dict(x=0.0, y=-2.0, z=1.6),
            center=dict(x=0, y=0.3, z=-0.15),
            up=dict(x=0, y=0, z=1)
        ),
        'delta': dict(
            # 삼각주: 위에서 분기 수로 패턴이 보이게
            eye=dict(x=0.0, y=-1.8, z=1.8),
            center=dict(x=0, y=0.2, z=-0.2),
            up=dict(x=0, y=0, z=1)
        ),
        'bird_foot_delta': dict(
            # 조족상 삼각주: 뻗어나가는 수로가 보이게
            eye=dict(x=0.0, y=-2.0, z=1.5),
            center=dict(x=0, y=0.3, z=-0.2),
            up=dict(x=0, y=0, z=1)
        ),
        'free_meander': dict(
            # 자유곡류: 측면에서 S자 곡선이 보이게
            eye=dict(x=1.8, y=-0.8, z=1.0),
            center=dict(x=0, y=0, z=-0.1),
            up=dict(x=0, y=0, z=1)
        ),
        'incised_meander': dict(
            # 감입곡류: 하안단구가 보이도록 약간 높이
            eye=dict(x=1.5, y=-1.2, z=1.2),
            center=dict(x=0, y=0, z=-0.15),
            up=dict(x=0, y=0, z=1)
        ),
        'v_valley': dict(
            # V자곡: 계곡 깊이가 보이게 측면에서
            eye=dict(x=2.0, y=-0.5, z=0.8),
            center=dict(x=0, y=0, z=-0.1),
            up=dict(x=0, y=0, z=1)
        ),
        'braided_river': dict(
            # 망상하천: 위에서 패턴 보이게
            eye=dict(x=0.3, y=-1.8, z=1.6),
            center=dict(x=0, y=0.1, z=-0.1),
            up=dict(x=0, y=0, z=1)
        ),
        'waterfall': dict(
            # 폭포: 낙차가 보이게 측면에서
            eye=dict(x=2.0, y=-0.3, z=0.6),
            center=dict(x=0, y=0, z=-0.1),
            up=dict(x=0, y=0, z=1)
        ),
        'perched_river': dict(
            # 천정천: 자연제방 높이가 보이게
            eye=dict(x=1.8, y=-1.0, z=0.8),
            center=dict(x=0, y=0, z=0),
            up=dict(x=0, y=0, z=1)
        ),
        
        # === 빙하 지형 ===
        'u_valley': dict(
            # U자곡: 측면에서 U자 단면 보이게
            eye=dict(x=2.0, y=-0.3, z=0.6),
            center=dict(x=0, y=0, z=-0.1),
            up=dict(x=0, y=0, z=1)
        ),
        'cirque': dict(
            # 권곡: 내부가 보이게 약간 위에서
            eye=dict(x=1.2, y=-1.5, z=1.3),
            center=dict(x=0, y=0, z=-0.2),
            up=dict(x=0, y=0, z=1)
        ),
        'horn': dict(
            # 호른: 뾰족한 봉우리가 보이게 측면에서 낮게
            eye=dict(x=1.8, y=-1.5, z=0.7),
            center=dict(x=0, y=0, z=0.1),
            up=dict(x=0, y=0, z=1)
        ),
        'fjord': dict(
            # 피오르드: 길이가 보이게 상류에서
            eye=dict(x=0.3, y=-2.2, z=1.0),
            center=dict(x=0, y=0.2, z=-0.15),
            up=dict(x=0, y=0, z=1)
        ),
        'drumlin': dict(
            # 드럼린: 유선형 보이게 측면 낮은 각도
            eye=dict(x=2.0, y=-0.8, z=0.5),
            center=dict(x=0, y=0, z=0),
            up=dict(x=0, y=0, z=1)
        ),
        'moraine': dict(
            # 빙퇴석: 호형 퇴적 보이게 위에서
            eye=dict(x=0.8, y=-1.8, z=1.5),
            center=dict(x=0, y=0.1, z=-0.2),
            up=dict(x=0, y=0, z=1)
        ),
        'arete': dict(
            # 아레트: 날카로운 능선 보이게
            eye=dict(x=1.5, y=-1.5, z=0.8),
            center=dict(x=0, y=0, z=0),
            up=dict(x=0, y=0, z=1)
        ),
        
        # === 화산 지형 ===
        'shield_volcano': dict(
            # 순상화산: 완만한 경사 보이게 낮은 각도
            eye=dict(x=2.2, y=-1.0, z=0.5),
            center=dict(x=0, y=0, z=0),
            up=dict(x=0, y=0, z=1)
        ),
        'stratovolcano': dict(
            # 성층화산: 급경사 보이게 측면
            eye=dict(x=2.0, y=-1.2, z=0.7),
            center=dict(x=0, y=0, z=0.1),
            up=dict(x=0, y=0, z=1)
        ),
        'caldera': dict(
            # 칼데라: 분화구 내부 보이게 위에서
            eye=dict(x=0.8, y=-1.5, z=1.5),
            center=dict(x=0, y=0, z=-0.1),
            up=dict(x=0, y=0, z=1)
        ),
        'crater_lake': dict(
            # 화구호: 호수 보이게 위에서
            eye=dict(x=0.6, y=-1.6, z=1.6),
            center=dict(x=0, y=0, z=-0.1),
            up=dict(x=0, y=0, z=1)
        ),
        'lava_plateau': dict(
            # 용암대지: 평탄면 보이게 낮은 각도
            eye=dict(x=1.8, y=-1.5, z=0.6),
            center=dict(x=0, y=0, z=0),
            up=dict(x=0, y=0, z=1)
        ),
        
        # === 해안 지형 ===
        'coastal_cliff': dict(
            # 해안절벽: 절벽면 보이게 바다에서
            eye=dict(x=0.3, y=2.2, z=0.7),
            center=dict(x=0, y=-0.1, z=-0.1),
            up=dict(x=0, y=0, z=1)
        ),
        'spit_lagoon': dict(
            # 사취+석호: 위에서 형태 보이게
            eye=dict(x=0.5, y=-1.8, z=1.6),
            center=dict(x=0, y=0.1, z=-0.1),
            up=dict(x=0, y=0, z=1)
        ),
        'tombolo': dict(
            # 육계사주: 연결부 보이게
            eye=dict(x=1.5, y=-1.5, z=1.2),
            center=dict(x=0, y=0, z=-0.1),
            up=dict(x=0, y=0, z=1)
        ),
        'ria_coast': dict(
            # 리아스: 톱니 해안선 보이게 위에서
            eye=dict(x=0.3, y=-1.8, z=1.8),
            center=dict(x=0, y=0.1, z=-0.2),
            up=dict(x=0, y=0, z=1)
        ),
        'sea_arch': dict(
            # 해식아치: 아치 형태 보이게 측면
            eye=dict(x=1.8, y=0.8, z=0.6),
            center=dict(x=0, y=0, z=0),
            up=dict(x=0, y=0, z=1)
        ),
        
        # === 건조 지형 ===
        'barchan': dict(
            # 바르한: 초승달 형태 보이게 낮은 각도
            eye=dict(x=2.0, y=-0.8, z=0.5),
            center=dict(x=0, y=0, z=0),
            up=dict(x=0, y=0, z=1)
        ),
        'transverse_dune': dict(
            # 횡사구: 능선 보이게 측면
            eye=dict(x=2.2, y=-0.5, z=0.5),
            center=dict(x=0, y=0, z=0),
            up=dict(x=0, y=0, z=1)
        ),
        'star_dune': dict(
            # 성사구: 방사형 보이게 위에서
            eye=dict(x=1.0, y=-1.5, z=1.4),
            center=dict(x=0, y=0, z=-0.1),
            up=dict(x=0, y=0, z=1)
        ),
        'mesa_butte': dict(
            # 메사/뷰트: 단애 보이게 측면
            eye=dict(x=2.0, y=-1.2, z=0.7),
            center=dict(x=0, y=0, z=0),
            up=dict(x=0, y=0, z=1)
        ),
        'pedestal_rock': dict(
            # 버섯바위: 줄기 보이게 측면 낮게
            eye=dict(x=2.2, y=-0.5, z=0.4),
            center=dict(x=0, y=0, z=0.1),
            up=dict(x=0, y=0, z=1)
        ),
        
        # === 카르스트 지형 ===
        'karst_doline': dict(
            # 돌리네: 함몰 보이게 위에서
            eye=dict(x=0.8, y=-1.5, z=1.6),
            center=dict(x=0, y=0, z=-0.2),
            up=dict(x=0, y=0, z=1)
        ),
        'uvala': dict(
            # 우발라: 복합 함몰 보이게 위에서
            eye=dict(x=0.6, y=-1.6, z=1.7),
            center=dict(x=0, y=0, z=-0.2),
            up=dict(x=0, y=0, z=1)
        ),
        'tower_karst': dict(
            # 탑카르스트: 탑 형태 보이게 낮은 각도
            eye=dict(x=2.0, y=-1.0, z=0.6),
            center=dict(x=0, y=0, z=0.1),
            up=dict(x=0, y=0, z=1)
        ),
    }
    
    # 세부 지형 카메라가 있으면 사용
    if detailed_type and detailed_type in detailed_cameras:
        return detailed_cameras[detailed_type]
    
    # 2. 대분류 카메라 (fallback)
    category_cameras = {
        'river': dict(
            eye=dict(x=0.0, y=-2.0, z=1.5),
            center=dict(x=0, y=0.2, z=-0.15),
            up=dict(x=0, y=0, z=1)
        ),
        'glacial': dict(
            eye=dict(x=1.0, y=-1.5, z=1.3),
            center=dict(x=0, y=0, z=-0.15),
            up=dict(x=0, y=0, z=1)
        ),
        'volcanic': dict(
            eye=dict(x=1.8, y=-1.2, z=0.8),
            center=dict(x=0, y=0, z=0),
            up=dict(x=0, y=0, z=1)
        ),
        'coastal': dict(
            eye=dict(x=0.5, y=1.8, z=0.9),
            center=dict(x=0, y=0, z=-0.1),
            up=dict(x=0, y=0, z=1)
        ),
        'arid': dict(
            eye=dict(x=2.0, y=-0.8, z=0.5),
            center=dict(x=0, y=0, z=0),
            up=dict(x=0, y=0, z=1)
        ),
        'karst': dict(
            eye=dict(x=0.8, y=-1.5, z=1.6),
            center=dict(x=0, y=0, z=-0.2),
            up=dict(x=0, y=0, z=1)
        ),
    }
    
    if landform_type in category_cameras:
        return category_cameras[landform_type]
    
    # 3. 기본값
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
