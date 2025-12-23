"""
🎨 Terrain Renderer - Plotly 3D 시각화
분리된 모듈로 HuggingFace Spaces 호환성 향상
"""
import numpy as np
import plotly.graph_objects as go
import os
try:
    from PIL import Image
except ImportError:
    Image = None


def render_terrain_plotly(elevation, title, add_water=True, water_level=0, 
                          texture_path=None, force_camera=True, 
                          water_depth_grid=None, sediment_grid=None, 
                          landform_type=None, detailed_type=None,
                          drainage_area=None, river_threshold_percentile=95):
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
    
    # ========== 하천 네트워크 (River Network) ==========
    if drainage_area is not None:
        # 임계값 이상인 셀을 하천으로 표시
        threshold = np.percentile(drainage_area, river_threshold_percentile)
        river_mask = drainage_area >= threshold
        
        if np.any(river_mask):
            # 하천 포인트 추출
            river_y, river_x = np.where(river_mask)
            river_z = elevation[river_mask] + 0.5  # 약간 위에 표시
            
            # 배수면적에 따른 하천 크기 (로그 스케일)
            river_sizes = np.log10(drainage_area[river_mask] + 1)
            river_sizes = (river_sizes / river_sizes.max()) * 8 + 2  # 2~10 범위
            
            # 배수면적에 따른 색상 (옅은 파랑 -> 진한 파랑)
            river_colors = drainage_area[river_mask]
            
            trace_river = go.Scatter3d(
                x=river_x,
                y=river_y,
                z=river_z,
                mode='markers',
                marker=dict(
                    size=river_sizes,
                    color=river_colors,
                    colorscale='Blues',
                    opacity=0.8,
                    symbol='circle',
                    line=dict(width=0)
                ),
                name='🌊 하천',
                hovertemplate='<b>하천</b><br>배수면적: %{marker.color:.0f}<extra></extra>'
            )
            data.append(trace_river)
    
    # 지형 유형별 Z축 스케일 (aspect ratio) 설정
    z_scales = {
        # General Categories
        'arid': 0.25,      # 사구(Dune) 등 기본값 (납작함)
        'coastal': 0.35,   # 해안
        'river': 0.4,      # 하천
        'glacial': 0.5,    # 빙하
        'volcanic': 0.6,   # 화산
        'karst': 0.35,     # 카르스트
        
        # Specific Types Overrides (상세 지형별 맞춤 비율)
        'mesa_butte': 0.5,        # 메사/뷰트는 높고 웅장해야 함
        'pedestal_rock': 0.7,     # 버섯바위는 수직적임
        'tower_karst': 0.7,       # 탑카르스트는 가파른 기둥
        'shield_volcano': 0.3,    # 순상화산은 완만한 경사
        'stratovolcano': 0.7,     # 성층화산은 급경사 원뿔
        'horn': 0.7,              # 호른은 날카로운 봉우리
        'fjord': 0.5,             # 피오르드는 깊은 계곡
        'canyon': 0.6,            # 협곡
        'wadi': 0.5,              # 와디(건천), 깊이감 필요
        'pediment': 0.4,          # 페디먼트, 경사 강조
    }
    
    # Priority: detailed_type -> landform_type -> Default
    z_aspect = z_scales.get(detailed_type)
    if z_aspect is None:
        z_aspect = z_scales.get(landform_type, 0.35)

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
            aspectratio=dict(x=1, y=1, z=z_aspect)
        ),
        paper_bgcolor='#0e1117',
        plot_bgcolor='#0e1117',
        height=700,
        margin=dict(l=10, r=10, t=50, b=10),
    )
    
    return fig
