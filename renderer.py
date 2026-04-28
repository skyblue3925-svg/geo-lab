"""
🎨 Terrain Renderer - Plotly 3D 시각화
분리된 모듈로 HuggingFace Spaces 호환성 향상
"""
import numpy as np
from app.utils.plotly_compat import go, plotly_error_message
import os
try:
    from PIL import Image
except ImportError:
    Image = None


def render_terrain_plotly(elevation, title, add_water=True, water_level=0, 
                          texture_path=None, force_camera=True, 
                          water_depth_grid=None, sediment_grid=None, 
                          landform_type=None):
    if go is None:
        return None
    """Plotly 인터랙티브 3D Surface - 사실적 텍스처(Biome) 적용
    
    Args:
        elevation: 2D numpy array - 고도 데이터
        title: 그래프 제목
        add_water: 물 표면 추가 여부
        water_level: 해수면 높이
        texture_path: 텍스처 이미지 경로
        force_camera: 카메라 위치 고정 여부
        water_depth_grid: 물 깊이 그리드
        sediment_grid: 퇴적물 그리드
        landform_type: 'river', 'coastal', 'glacial', 'volcanic', 'karst', 'arid'
    """
    h, w = elevation.shape
    x = np.arange(w)
    y = np.arange(h)
    
    # 경사도 계산
    dy, dx = np.gradient(elevation)
    slope = np.sqrt(dx**2 + dy**2)
    
    # Biome Index (0: 물/모래, 1: 풀, 2: 암석, 3: 눈)
    biome = np.zeros_like(elevation)
    biome[:] = 1  # 기본: 풀
    
    # 퇴적지 판별
    sand_level = water_level + 5 if add_water else elevation.min() + 10
    is_deposit = np.zeros_like(elevation, dtype=bool)
    
    if sediment_grid is not None:
        is_deposit = (sediment_grid > 0.5)
    else:
        is_deposit = (elevation < sand_level) & (slope < 0.5)
    biome[is_deposit] = 0
    
    # 암석 (경사가 급한 곳)
    biome[slope > 1.2] = 2
    
    # 지형 유형별 처리
    if landform_type == 'glacial':
        biome[elevation > 50] = 3
        biome[slope > 1.5] = 2
    elif landform_type in ['river', 'coastal']:
        if water_depth_grid is not None:
            is_water = water_depth_grid > 0.5
            biome[is_water] = 0
        biome[elevation < 0] = 0
    elif landform_type == 'arid':
        biome[slope < 0.8] = 0
    
    # 노이즈 추가
    noise = np.random.normal(0, 0.2, elevation.shape)
    biome_noisy = np.clip(biome + noise, 0, 3).round(2)
    
    # 컬러스케일 설정
    if landform_type == 'glacial':
        realistic_colorscale = [
            [0.0, '#E6C288'], [0.25, '#E6C288'],
            [0.25, '#556B2F'], [0.5, '#556B2F'],
            [0.5, '#808080'], [0.75, '#808080'],
            [0.75, '#E0FFFF'], [1.0, '#FFFFFF']
        ]
        colorbar_labels = ["퇴적(土)", "식생(草)", "암석(岩)", "빙하(氷)"]
    elif landform_type in ['river', 'coastal']:
        realistic_colorscale = [
            [0.0, '#4682B4'], [0.25, '#4682B4'],
            [0.25, '#556B2F'], [0.5, '#556B2F'],
            [0.5, '#808080'], [0.75, '#808080'],
            [0.75, '#D2B48C'], [1.0, '#D2B48C']
        ]
        colorbar_labels = ["수역(水)", "식생(草)", "암석(岩)", "사질(砂)"]
    elif landform_type == 'arid':
        realistic_colorscale = [
            [0.0, '#EDC9AF'], [0.25, '#EDC9AF'],
            [0.25, '#CD853F'], [0.5, '#CD853F'],
            [0.5, '#808080'], [0.75, '#808080'],
            [0.75, '#DAA520'], [1.0, '#DAA520']
        ]
        colorbar_labels = ["사막(砂)", "암질(巖)", "암석(岩)", "모래(沙)"]
    else:
        realistic_colorscale = [
            [0.0, '#E6C288'], [0.25, '#E6C288'],
            [0.25, '#556B2F'], [0.5, '#556B2F'],
            [0.5, '#808080'], [0.75, '#808080'],
            [0.75, '#A0522D'], [1.0, '#A0522D']
        ]
        colorbar_labels = ["퇴적(土)", "식생(草)", "암석(岩)", "표토(土)"]
    
    # 시각적 노이즈
    visual_z = (elevation + np.random.normal(0, 0.2, elevation.shape)).round(2)
    
    final_surface_color = biome_noisy
    final_colorscale = realistic_colorscale
    final_cmin = 0
    final_cmax = 3
    final_colorbar = dict(
        title=dict(text="지표 상태", font=dict(color='white')), 
        tickvals=[0.37, 1.12, 1.87, 2.62], 
        ticktext=colorbar_labels,
        tickfont=dict(color='white')
    )

    # 텍스처 이미지 처리
    if texture_path and os.path.exists(texture_path) and Image:
        try:
            img = Image.open(texture_path).convert('L')
            img = img.resize((w, h))
            img_array = np.array(img) / 255.0
            final_surface_color = img_array
            final_colorscale = 'Gray'
            final_cmin = 0
            final_cmax = 1
            final_colorbar = dict(title="텍스처 명암")
        except Exception as e:
            print(f"Texture error: {e}")

    # 3D Plot
    lighting_effects = dict(ambient=0.4, diffuse=0.5, roughness=0.9, specular=0.1, fresnel=0.2)
    
    trace_terrain = go.Surface(
        z=visual_z, x=x, y=y,
        surfacecolor=final_surface_color,
        colorscale=final_colorscale,
        cmin=final_cmin, cmax=final_cmax,
        colorbar=final_colorbar,
        lighting=lighting_effects,
        hoverinfo='z'
    )
    
    data = [trace_terrain]
    
    # Water Surface
    if water_depth_grid is not None:
        water_mask = water_depth_grid > 0.1
        if np.any(water_mask):
            water_z = elevation + water_depth_grid
            water_z[~water_mask] = np.nan
            trace_water = go.Surface(
                z=water_z, x=x, y=y,
                colorscale=[[0, 'rgba(30,144,255,0.7)'], [1, 'rgba(30,144,255,0.7)']],
                showscale=False,
                lighting=dict(ambient=0.6, diffuse=0.5, specular=0.8, roughness=0.1),
                hoverinfo='skip'
            )
            data.append(trace_water)
    elif add_water:
        water_z = np.ones_like(elevation) * water_level
        trace_water = go.Surface(
            z=water_z, x=x, y=y,
            hoverinfo='none',
            lighting=dict(ambient=0.6, diffuse=0.6, specular=0.5)
        )
        data.append(trace_water)
    
    # Layout
    fig = go.Figure(data=data)
    fig.update_layout(
        title=dict(text=title, font=dict(color='white', size=16)),
        uirevision='terrain_viz',
        scene=dict(
            xaxis=dict(title='X (m)', backgroundcolor='#1a1a2e', gridcolor='#444', color='#cccccc'),
            yaxis=dict(title='Y (m)', backgroundcolor='#1a1a2e', gridcolor='#444', color='#cccccc'),
            zaxis=dict(title='Elevation', backgroundcolor='#1a1a2e', gridcolor='#444', color='#cccccc'),
            bgcolor='#0e1117',
            camera=dict(
                eye=dict(x=1.6, y=-1.6, z=0.8),
                center=dict(x=0, y=0, z=-0.2),
                up=dict(x=0, y=0, z=1)
            ) if force_camera else None,
            aspectmode='manual',
            aspectratio=dict(x=1, y=1, z=0.35)
        ),
        paper_bgcolor='#0e1117',
        plot_bgcolor='#0e1117',
        height=700,
        margin=dict(l=10, r=10, t=50, b=10),
    )
    
    return fig
