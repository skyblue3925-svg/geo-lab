"""
PyVista 기반 고품질 3D 지형 렌더링
- 진짜 3D 렌더링
- 텍스처 매핑
- 조명, 그림자 효과
"""
import numpy as np

try:
    import pyvista as pv
    PYVISTA_AVAILABLE = True
except ImportError:
    PYVISTA_AVAILABLE = False


def create_terrain_mesh(elevation: np.ndarray, x_scale: float = 1.0, y_scale: float = 1.0, z_scale: float = 1.0):
    """고도 배열을 PyVista 메시로 변환"""
    if not PYVISTA_AVAILABLE:
        raise ImportError("PyVista is not installed")
    
    h, w = elevation.shape
    x = np.arange(w) * x_scale
    y = np.arange(h) * y_scale
    X, Y = np.meshgrid(x, y)
    Z = elevation * z_scale
    
    grid = pv.StructuredGrid(X, Y, Z)
    grid["elevation"] = Z.flatten(order="F")
    
    return grid


def create_interactive_plotter(elevation: np.ndarray, title: str = "지형",
                               x_scale: float = 1.0, y_scale: float = 1.0, z_scale: float = 1.0):
    """인터랙티브 회전 가능한 PyVista 플로터 생성 (stpyvista용)"""
    if not PYVISTA_AVAILABLE:
        return None
    
    mesh = create_terrain_mesh(elevation, x_scale, y_scale, z_scale)
    
    plotter = pv.Plotter(window_size=[800, 600])
    plotter.set_background("#1a1a2e")
    
    # 단일 색상 (copper)
    plotter.add_mesh(
        mesh,
        scalars="elevation",
        cmap="copper",
        lighting=True,
        smooth_shading=True,
        show_scalar_bar=True,
        scalar_bar_args={
            "title": "고도 (m)",
            "color": "white"
        },
        specular=0.3,
        specular_power=15
    )
    
    # 조명
    plotter.remove_all_lights()
    plotter.add_light(pv.Light(position=(1000, 1000, 2000), intensity=1.2))
    plotter.add_light(pv.Light(position=(-500, -500, 1000), intensity=0.5))
    
    plotter.add_text(title, font_size=14, position="upper_left", color="white")
    
    return plotter


def render_v_valley_pyvista(elevation: np.ndarray, depth: float):
    """V자곡 PyVista 렌더링 - 단일 색상 명도 변화"""
    if not PYVISTA_AVAILABLE:
        return None
    
    # 메시 생성 (수직 과장 2배)
    mesh = create_terrain_mesh(elevation, x_scale=12.5, y_scale=12.5, z_scale=2.0)
    
    # 플로터 설정
    plotter = pv.Plotter(off_screen=True, window_size=[1200, 900])
    plotter.set_background("#1a1a2e")  # 어두운 배경
    
    # 단일 색상 (갈색 계열 - copper) 명도 변화
    plotter.add_mesh(
        mesh,
        scalars="elevation",
        cmap="copper",  # 갈색 단일 색상 명도 변화
        lighting=True,
        smooth_shading=True,
        show_scalar_bar=True,
        scalar_bar_args={
            "title": "고도 (m)", 
            "vertical": True,
            "title_font_size": 14,
            "label_font_size": 12
        },
        specular=0.3,
        specular_power=15
    )
    
    # 하천 (더 진한 색상)
    water_level = elevation.min() + 3
    h, w = elevation.shape
    x_water = np.arange(w) * 12.5
    y_water = np.arange(h) * 12.5
    X_w, Y_w = np.meshgrid(x_water, y_water)
    Z_w = np.full_like(elevation, water_level, dtype=float)
    water_mask = elevation < water_level
    Z_w[~water_mask] = np.nan
    
    if np.any(water_mask):
        water_grid = pv.StructuredGrid(X_w, Y_w, Z_w)
        plotter.add_mesh(water_grid, color="#2C3E50", opacity=0.9)  # 어두운 물
    
    # 드라마틱한 카메라 각도
    plotter.camera_position = [
        (w * 12.5 * 1.5, h * 12.5 * 0.2, elevation.max() * 3),
        (w * 12.5 * 0.5, h * 12.5 * 0.5, elevation.min()),
        (0, 0, 1)
    ]
    
    # 강한 조명 (그림자 효과)
    plotter.remove_all_lights()
    key_light = pv.Light(position=(w*12.5*3, 0, elevation.max()*5), intensity=1.2)
    fill_light = pv.Light(position=(-w*12.5, h*12.5*2, elevation.max()*2), intensity=0.4)
    plotter.add_light(key_light)
    plotter.add_light(fill_light)
    
    plotter.add_text(f"V자곡 | 깊이: {depth:.0f}m", font_size=16, 
                     position="upper_left", color="white")
    
    img = plotter.screenshot(return_img=True)
    plotter.close()
    
    return img


def render_delta_pyvista(elevation: np.ndarray, delta_type: str, area: float):
    """삼각주 PyVista 렌더링 - 단일 색상"""
    if not PYVISTA_AVAILABLE:
        return None
    
    # 메시 생성 (수직 과장)
    mesh = create_terrain_mesh(elevation, x_scale=50, y_scale=50, z_scale=10.0)
    
    plotter = pv.Plotter(off_screen=True, window_size=[1200, 900])
    plotter.set_background("#0f0f23")  # 어두운 배경
    
    # 단일 색상 (bone - 베이지/갈색 명도 변화)
    plotter.add_mesh(
        mesh,
        scalars="elevation",
        cmap="bone",  # 베이지 단일 색상 명도 변화
        lighting=True,
        smooth_shading=True,
        clim=[elevation.min(), elevation.max()],
        show_scalar_bar=True,
        scalar_bar_args={
            "title": "고도 (m)",
            "title_font_size": 14,
            "label_font_size": 12
        },
        specular=0.2,
        specular_power=10
    )
    
    # 해수면 (진한 색상)
    h, w = elevation.shape
    x = np.arange(w) * 50
    y = np.arange(h) * 50
    X, Y = np.meshgrid(x, y)
    Z_sea = np.zeros_like(elevation, dtype=float)
    sea_mask = elevation < 0
    Z_sea[~sea_mask] = np.nan
    
    if np.any(sea_mask):
        sea_grid = pv.StructuredGrid(X, Y, Z_sea)
        plotter.add_mesh(sea_grid, color="#1a3a5f", opacity=0.85)
    
    # 카메라
    plotter.camera_position = [
        (w * 50 * 0.5, -h * 50 * 0.5, elevation.max() * 50),
        (w * 50 * 0.5, h * 50 * 0.5, 0),
        (0, 0, 1)
    ]
    
    # 조명
    plotter.remove_all_lights()
    plotter.add_light(pv.Light(position=(w*50*2, -h*50, 1000), intensity=1.3))
    plotter.add_light(pv.Light(position=(-w*50, h*50*2, 500), intensity=0.5))
    
    plotter.add_text(f"{delta_type} | 면적: {area:.2f} km²", font_size=16, 
                     position="upper_left", color="white")
    
    img = plotter.screenshot(return_img=True)
    plotter.close()
    
    return img


def render_meander_pyvista(x: np.ndarray, y: np.ndarray, sinuosity: float, oxbow_lakes: list):
    """곡류 하천 PyVista 렌더링 (2.5D)"""
    if not PYVISTA_AVAILABLE:
        return None
    
    plotter = pv.Plotter(off_screen=True, window_size=[1400, 600])
    
    # 범람원 (평면)
    floodplain = pv.Plane(
        center=(x.mean(), y.mean(), -1),
        direction=(0, 0, 1),
        i_size=x.max() - x.min() + 200,
        j_size=max(200, (y.max() - y.min()) * 3)
    )
    plotter.add_mesh(floodplain, color="#8FBC8F", opacity=0.8)
    
    # 하천 (튜브)
    points = np.column_stack([x, y, np.zeros_like(x)])
    spline = pv.Spline(points, 500)
    tube = spline.tube(radius=8)
    plotter.add_mesh(tube, color="#4169E1", smooth_shading=True)
    
    # 우각호
    for lake_x, lake_y in oxbow_lakes:
        if len(lake_x) > 3:
            lake_points = np.column_stack([lake_x, lake_y, np.full_like(lake_x, -0.5)])
            lake_spline = pv.Spline(lake_points, 100)
            lake_tube = lake_spline.tube(radius=6)
            plotter.add_mesh(lake_tube, color="#87CEEB", opacity=0.8)
    
    # 카메라 (위에서 약간 기울어진 시점)
    plotter.camera_position = [
        (x.mean(), y.mean() - 300, 400),
        (x.mean(), y.mean(), 0),
        (0, 0, 1)
    ]
    
    # 조명
    plotter.add_light(pv.Light(position=(x.mean(), y.mean(), 500), intensity=1.0))
    
    plotter.add_text(f"곡류 하천 (굴곡도: {sinuosity:.2f})", font_size=14, position="upper_left")
    
    img = plotter.screenshot(return_img=True)
    plotter.close()
    
    return img


def save_pyvista_image(img: np.ndarray, filepath: str):
    """PyVista 렌더링 이미지 저장"""
    from PIL import Image
    if img is not None:
        Image.fromarray(img).save(filepath)
        return True
    return False
