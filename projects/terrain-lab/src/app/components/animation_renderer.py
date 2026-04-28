"""
?렗 Plotly Animation Renderer
遺?쒕윭??3D 吏???좊땲硫붿씠??(移대찓???좎?)
"""
import json
import uuid
import numpy as np
from app.utils.plotly_compat import go, plotly_error_message
from typing import Any, Callable, Optional, Sequence
import tempfile
from pathlib import Path
try:
    from PIL import Image
except ImportError:
    Image = None


def _plotly_json_array(values: Any) -> list:
    """Return plain JSON arrays so Streamlit renders 3D animation surfaces."""

    return np.asarray(values).tolist()


def create_animated_terrain_figure(
    landform_func: Callable,
    grid_size: int = 50,
    num_frames: int = 40,  # ??留롮? ?꾨젅??(泥쒖쿇??遺?쒕읇寃?
    title: str = "지형 형성 과정",
    landform_type: str = "river",
    detailed_type: str = None,
    start_stage: float = 0.0,
    render_style: str = "terrain",
    camera_motion: str = "fixed",
    base_camera: Optional[dict] = None,
    cinematic_zoom: float = 1.0,
    texture_map: Optional[np.ndarray] = None,
) -> go.Figure:
    if go is None:
        try:
            import streamlit as st
            st.error(plotly_error_message())
        except Exception:
            pass
        return None

    """Plotly ?ㅼ씠?곕툕 ?좊땲硫붿씠?섏쑝濡?遺?쒕윭??3D 吏???좊땲硫붿씠???앹꽦
    
    Args:
        landform_func: 吏???앹꽦 ?⑥닔 (grid_size, stage) -> elevation
        grid_size: 洹몃━???ш린
        num_frames: ?좊땲硫붿씠???꾨젅????(留롮쓣?섎줉 遺?쒕윭?)
        title: 洹몃옒???쒕ぉ
        landform_type: 吏???좏삎 (colorscale 寃곗젙)
    
    Returns:
        go.Figure: ?좊땲硫붿씠?섏씠 ?ы븿??Plotly Figure
    """
    h, w = grid_size, grid_size
    x = np.arange(w)
    y = np.arange(h)
    x_plot = _plotly_json_array(x)
    y_plot = _plotly_json_array(y)
    
    # Normalize invalid inputs
    render_style = render_style if render_style in {"terrain", "satellite"} else "terrain"
    camera_motion = camera_motion if camera_motion in {"fixed", "orbit", "sweep"} else "fixed"
    cinematic_zoom = float(np.clip(cinematic_zoom, 0.6, 2.5))

    # Camera baseline
    camera_settings = base_camera if isinstance(base_camera, dict) else _get_optimal_camera(landform_type, detailed_type)
    texture_payload = _prepare_texture_payload(texture_map, grid_size)

    # Build elevation list first, then generate consistent per-frame colors.
    frames = []
    frame_ids = []
    frame_labels = []
    all_elevations = []
    
    stage_descriptions = []
    
    for i in range(num_frames):
        stage = i / (num_frames - 1)

        # 吏???앹꽦 + ?④퀎 ?ㅻ챸 異붿텧
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
        
        all_elevations.append(np.array(elevation, dtype=float))
        stage_descriptions.append(stage_desc)

        # Use a stable frame id so "fromcurrent" playback does not drift.
        frame_id = f"f{i:03d}"
        frame_label = f"{int(stage * 100)}%"
        frame_ids.append(frame_id)
        frame_labels.append(frame_label)

    elev_min = float(min(np.min(e) for e in all_elevations))
    elev_max = float(max(np.max(e) for e in all_elevations))

    for i, elevation in enumerate(all_elevations):
        surfacecolor, colorscale, lighting = _compute_surface_style(
            elevation,
            landform_type=landform_type,
            render_style=render_style,
            elev_min=elev_min,
            elev_max=elev_max,
            texture_payload=texture_payload,
        )

        frame_layout = None
        if camera_motion != "fixed":
            frame_layout = go.Layout(
                scene=dict(
                    camera=_get_motion_camera(
                        camera_settings,
                        motion_mode=camera_motion,
                        frame_idx=i,
                        total_frames=num_frames,
                        cinematic_zoom=cinematic_zoom,
                    )
                )
            )

        frames.append(
            go.Frame(
                data=[
                    go.Surface(
                        z=_plotly_json_array(elevation),
                        x=x_plot,
                        y=y_plot,
                        surfacecolor=_plotly_json_array(surfacecolor),
                        colorscale=colorscale,
                        cmin=0,
                        cmax=1,
                        showscale=False,
                        lighting=lighting,
                    )
                ],
                name=frame_ids[i],
                layout=frame_layout,
            )
        )
    
    # 珥덇린 ?꾨젅??(stage=0)
    # Use selected start stage as initial frame so Play begins from user context.
    start_stage = float(np.clip(start_stage, 0.0, 1.0))
    start_frame_idx = int(round(start_stage * (num_frames - 1)))

    initial_elevation = all_elevations[start_frame_idx]
    start_frame_id = frame_ids[start_frame_idx]

    initial_surfacecolor, initial_colorscale, initial_lighting = _compute_surface_style(
        initial_elevation,
        landform_type=landform_type,
        render_style=render_style,
        elev_min=elev_min,
        elev_max=elev_max,
        texture_payload=texture_payload,
    )
    
    fig = go.Figure(
        data=[go.Surface(
            z=_plotly_json_array(initial_elevation),
            x=x_plot,
            y=y_plot,
            surfacecolor=_plotly_json_array(initial_surfacecolor),
            colorscale=initial_colorscale,
            cmin=0, cmax=1,
            showscale=False,
            lighting=initial_lighting,
        )],
        frames=frames
    )
    
    # ?щ씪?대뜑 (?꾨젅???대룞??
    sliders = [{
        'active': start_frame_idx,
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
                'args': [[f.name], {'frame': {'duration': 70, 'redraw': True}, 'mode': 'immediate', 'transition': {'duration': 70}}],
                'label': frame_labels[idx],
                'method': 'animate'
            }
            for idx, f in enumerate(frames)
        ]
    }]
    
    # ?ъ깮/?뺤? 踰꾪듉 (?ㅻⅨ履?諛곗튂)
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
                'label': '재생',
                'method': 'animate',
                'args': [
                    None,
                    {
                        'frame': {'duration': 280, 'redraw': True},
                        'fromcurrent': True,
                        'mode': 'immediate',
                        'transition': {'duration': 140, 'easing': 'linear'}
                    }
                ]
            },
            {
                'label': '정지',
                'method': 'animate',
                'args': [
                    [None],
                    {
                        'frame': {'duration': 0, 'redraw': True},
                        'mode': 'immediate',
                        'transition': {'duration': 0}
                    }
                ]
            },
            {
                'label': '시작 지점',
                'method': 'animate',
                'args': [
                    [start_frame_id],
                    {
                        'frame': {'duration': 0, 'redraw': True},
                        'mode': 'immediate',
                        'transition': {'duration': 0}
                    }
                ]
            }
        ]
    }]
    # 吏???좏삎蹂?Z異??ㅼ???(aspect ratio)
    # 吏???좏삎蹂?Z異??ㅼ???(aspect ratio)
    z_scales = {
        # General Categories
        'arid': 0.25,      # Default Dune
        'coastal': 0.35,
        'river': 0.4,
        'glacial': 0.5,
        'tectonic': 0.55,
        'volcanic': 0.6,
        'karst': 0.35,
        
        # Specific Overrides
        'mesa_butte': 0.5,
        'pedestal_rock': 0.7,
        'tower_karst': 0.7,
        'shield_volcano': 0.3,
        'stratovolcano': 0.7,
        'folded_range': 0.55,
        'horn': 0.7,
        'fjord': 0.5,
        'wadi': 0.5,
        'pediment': 0.4,
        'canyon': 0.6
    }
    
    z_aspect = z_scales.get(detailed_type)
    if z_aspect is None:
        z_aspect = z_scales.get(landform_type, 0.4)

    initial_camera = camera_settings
    if camera_motion != "fixed":
        initial_camera = _get_motion_camera(
            camera_settings,
            motion_mode=camera_motion,
            frame_idx=start_frame_idx,
            total_frames=num_frames,
            cinematic_zoom=cinematic_zoom,
        )
    
    # ?덉씠?꾩썐
    fig.update_layout(
        title=dict(text=title, font=dict(color='white', size=16)),
        uirevision='terrain_anim',
        font=dict(
            family='Malgun Gothic, Apple SD Gothic Neo, NanumGothic, sans-serif',
            color='#ffffff',
        ),
        scene=dict(
            xaxis=dict(title='X (m)', backgroundcolor='#1a1a2e', gridcolor='#444', color='#cccccc'),
            yaxis=dict(title='Y (m)', backgroundcolor='#1a1a2e', gridcolor='#444', color='#cccccc'),
            zaxis=dict(title='Elevation', backgroundcolor='#1a1a2e', gridcolor='#444', color='#cccccc'),
            bgcolor='#0e1117',
            camera=initial_camera,
            uirevision='terrain_anim_scene',
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


def _format_year_label(value: float) -> str:
    if abs(value) >= 10000:
        return f"{value:,.0f}년"
    return f"{value:.0f}년"


def get_next_history_frame(current_frame: int, frame_count: int) -> int:
    if frame_count <= 0:
        return 0
    return (max(int(current_frame), 0) + 1) % frame_count


def _normalize_overlay_field(field: np.ndarray) -> np.ndarray:
    values = np.abs(np.array(field, dtype=float))
    if values.size == 0:
        return values
    scale = float(np.percentile(values, 95))
    if scale <= 1e-12:
        return np.zeros_like(values)
    return np.clip(values / scale, 0.0, 1.0)


def _overlay_colorscale(overlay_type: str | None) -> list[list[Any]]:
    palettes = {
        "tectonic": [[0.0, "#fff4cc"], [0.45, "#f6b73c"], [1.0, "#c4451c"]],
        "erosion": [[0.0, "#d9f1ff"], [0.45, "#5aa9e6"], [1.0, "#0b5ea8"]],
        "deposition": [[0.0, "#e4f7df"], [0.45, "#7bc96f"], [1.0, "#2d7a2d"]],
        "transport": [[0.0, "#fff4d6"], [0.45, "#ffb347"], [1.0, "#d96b1f"]],
        "change": [[0.0, "#f2f2f2"], [0.45, "#b2b2b2"], [1.0, "#4f4f4f"]],
    }
    return palettes.get(overlay_type or "change", palettes["change"])


def _extract_overlay_field(process_fields: dict[str, Any] | None, overlay_type: str | None, shape: tuple[int, int]) -> np.ndarray:
    zeros = np.zeros(shape, dtype=float)
    if not process_fields or not overlay_type:
        return zeros

    def field(name: str) -> np.ndarray:
        value = process_fields.get(name)
        if value is None:
            return zeros
        arr = np.array(value, dtype=float)
        return arr if arr.shape == shape else zeros

    if overlay_type == "tectonic":
        return field("tectonic")
    if overlay_type == "erosion":
        return field("total_erosion")
    if overlay_type == "deposition":
        return field("deposition") + field("moraine")
    if overlay_type == "transport":
        return (
            field("erosion")
            + field("lateral")
            + field("diffusion")
            + field("glacial")
            + field("marine")
            + field("aeolian")
            + field("groundwater")
        )
    if overlay_type == "change":
        return field("tectonic") + field("total_erosion") + field("deposition")
    return zeros


def _build_history_surface_traces(
    *,
    elevation: np.ndarray,
    x: np.ndarray,
    y: np.ndarray,
    surfacecolor: np.ndarray,
    colorscale: list[list[Any]],
    lighting: dict[str, Any],
    overlay_field: np.ndarray | None = None,
    overlay_type: str | None = None,
    overlay_offset: float = 0.05,
) -> list[Any]:
    traces = [
        go.Surface(
            z=elevation,
            x=x,
            y=y,
            surfacecolor=surfacecolor,
            colorscale=colorscale,
            cmin=0,
            cmax=1,
            showscale=False,
            lighting=lighting,
        )
    ]

    if overlay_field is None:
        return traces

    overlay_norm = _normalize_overlay_field(overlay_field)
    if float(np.max(overlay_norm)) <= 1e-12:
        overlay_norm = np.zeros_like(overlay_norm)

    traces.append(
        go.Surface(
            z=elevation + overlay_offset,
            x=x,
            y=y,
            surfacecolor=overlay_norm,
            colorscale=_overlay_colorscale(overlay_type),
            cmin=0,
            cmax=1,
            showscale=False,
            opacity=0.48,
            hoverinfo="skip",
            lighting={"ambient": 1.0, "diffuse": 0.0, "specular": 0.0, "roughness": 1.0, "fresnel": 0.0},
        )
    )
    return traces


def _overlay_mpl_cmap(overlay_type: str | None):
    from matplotlib.colors import LinearSegmentedColormap

    palette = _overlay_colorscale(overlay_type)
    return LinearSegmentedColormap.from_list(
        f"{overlay_type or 'change'}_overlay",
        [color for _, color in palette],
    )


def _blend_overlay_facecolors(
    terrain_rgba: np.ndarray,
    process_fields: dict[str, Any] | None,
    overlay_type: str | None,
) -> np.ndarray:
    blended = np.array(terrain_rgba, copy=True)
    if process_fields is None or not overlay_type:
        return blended

    overlay_field = _extract_overlay_field(process_fields, overlay_type, blended.shape[:2])
    if overlay_field is None:
        return blended

    overlay_norm = _normalize_overlay_field(overlay_field)
    peak = float(np.nanmax(overlay_norm)) if overlay_norm.size else 0.0
    if peak <= 1e-12:
        return blended

    overlay_rgba = _overlay_mpl_cmap(overlay_type)(overlay_norm)
    alpha = np.clip(overlay_norm, 0.0, 1.0)[..., None] * 0.58
    blended[..., :3] = (blended[..., :3] * (1.0 - alpha)) + (overlay_rgba[..., :3] * alpha)
    return blended


def _camera_to_matplotlib_view(camera: dict[str, Any] | None) -> tuple[float, float]:
    eye = (camera or {}).get("eye", {})
    x = float(eye.get("x", 1.6))
    y = float(eye.get("y", -1.6))
    z = float(eye.get("z", 0.8))
    radius_xy = max(np.hypot(x, y), 1e-6)
    elev = float(np.degrees(np.arctan2(z, radius_xy)))
    azim = float(np.degrees(np.arctan2(y, x)))
    return elev, azim


def create_history_gif_bytes(
    history: Sequence[np.ndarray],
    times: Sequence[float],
    process_history: Sequence[dict[str, Any]] | None = None,
    stage_history: Sequence[dict[str, Any]] | None = None,
    overlay_type: str | None = None,
    fps: int = 5,
    view_elev: float | None = None,
    view_azim: float | None = None,
    landform_type: str = "general",
    detailed_type: str | None = None,
) -> bytes:
    if not history:
        return b""

    import matplotlib.pyplot as plt
    from matplotlib import animation, cm

    frames = [np.array(frame, dtype=float) for frame in history]
    labels = list(times) if times else list(range(len(frames)))
    if len(labels) < len(frames):
        labels.extend(range(len(labels), len(frames)))

    rows, cols = frames[0].shape
    x = np.arange(cols)
    y = np.arange(rows)
    X, Y = np.meshgrid(x, y)
    z_min = float(min(np.min(frame) for frame in frames))
    z_max = float(max(np.max(frame) for frame in frames))
    z_range = max(z_max - z_min, 1e-6)
    runtime_tmp_dir = Path(__file__).resolve().parents[2] / "tmp"
    runtime_tmp_dir.mkdir(parents=True, exist_ok=True)
    if view_elev is None or view_azim is None:
        camera = _get_optimal_camera(landform_type, detailed_type)
        auto_elev, auto_azim = _camera_to_matplotlib_view(camera)
        view_elev = auto_elev if view_elev is None else view_elev
        view_azim = auto_azim if view_azim is None else view_azim

    overlay_types = []
    stage_titles = []
    for idx in range(len(frames)):
        stage = stage_history[idx] if stage_history and idx < len(stage_history) and isinstance(stage_history[idx], dict) else {}
        overlay_types.append(stage.get("overlay_type", overlay_type) if stage else overlay_type)
        stage_titles.append(stage.get("title", "") if stage else "")

    figure = None
    tmp_path = None
    try:
        figure = plt.figure(figsize=(7.2, 5.4), facecolor="#1a1a2e")
        axis = figure.add_subplot(111, projection="3d", facecolor="#1a1a2e")
        axis.set_axis_off()

        def update(frame_idx: int):
            axis.clear()
            axis.set_axis_off()
            elevation = frames[frame_idx]
            elev_norm = np.clip((elevation - z_min) / z_range, 0.0, 1.0)
            facecolors = _blend_overlay_facecolors(
                cm.terrain(elev_norm),
                process_history[frame_idx] if process_history and frame_idx < len(process_history) else None,
                overlay_types[frame_idx],
            )
            axis.plot_surface(
                X,
                Y,
                elevation,
                facecolors=facecolors,
                linewidth=0,
                antialiased=True,
                shade=False,
                rstride=1,
                cstride=1,
            )
            axis.view_init(elev=view_elev, azim=view_azim)
            axis.set_zlim(z_min, z_max)
            axis.set_box_aspect((cols, rows, max(z_range * 0.35, 1.0)))
            overlay_label = overlay_types[frame_idx]
            title_parts = [f"{float(labels[frame_idx]):,.0f} yr"]
            if overlay_label:
                title_parts.append(f"{overlay_label} overlay")
            if stage_titles[frame_idx]:
                title_parts.append(stage_titles[frame_idx])
            axis.set_title(" | ".join(title_parts), color="white", pad=14)

        anim = animation.FuncAnimation(figure, update, frames=len(frames), interval=200)
        with tempfile.NamedTemporaryFile(dir=runtime_tmp_dir, suffix=".gif", delete=False) as handle:
            tmp_path = Path(handle.name)
        anim.save(str(tmp_path), writer="pillow", fps=fps)
        return tmp_path.read_bytes()
    finally:
        if figure is not None:
            plt.close(figure)
        if tmp_path is not None and tmp_path.exists():
            tmp_path.unlink()


# Smooth history playback for education mode.
def create_history_animation_figure(
    history: Sequence[np.ndarray],
    times: Sequence[float],
    process_history: Sequence[dict[str, Any]] | None = None,
    stage_history: Sequence[dict[str, Any]] | None = None,
    overlay_type: str | None = None,
    title: str = "지형 변화 애니메이션",
    landform_type: str = "general",
    detailed_type: str = None,
    render_style: str = "terrain",
    base_camera: Optional[dict] = None,
    cinematic_zoom: float = 1.0,
    interpolation_steps: int = 6,
    camera_motion: str = "fixed",
    frame_duration_ms: int = 90,
    transition_duration_ms: int = 80,
    show_slider: bool = True,
    show_controls: bool = True,
) -> go.Figure:
    if go is None:
        try:
            import streamlit as st
            st.error(plotly_error_message())
        except Exception:
            pass
        return None

    if not history:
        return None

    render_style = render_style if render_style in {"terrain", "satellite"} else "terrain"
    cinematic_zoom = float(np.clip(cinematic_zoom, 0.6, 2.5))
    interpolation_steps = max(int(interpolation_steps), 1)
    frame_duration_ms = max(int(frame_duration_ms), 0)
    transition_duration_ms = max(int(transition_duration_ms), 0)
    camera_motion = camera_motion if camera_motion in {"fixed", "orbit", "sweep", "auto"} else "fixed"
    if camera_motion == "auto":
        camera_motion = _get_recommended_camera_motion(landform_type, detailed_type)

    source_history = [np.array(frame, dtype=float) for frame in history]
    source_times = list(times) if times else list(range(len(source_history)))
    if len(source_times) < len(source_history):
        source_times.extend(range(len(source_times), len(source_history)))

    dense_history = []
    dense_times = []
    source_process_history = None
    if process_history:
        source_process_history = []
        for idx in range(len(source_history)):
            raw = process_history[idx] if idx < len(process_history) else {}
            source_process_history.append({key: np.array(value, dtype=float) for key, value in dict(raw).items()})

    source_overlay_types = None
    if stage_history:
        source_overlay_types = []
        for idx in range(len(source_history)):
            stage = stage_history[idx] if idx < len(stage_history) else {}
            source_overlay_types.append(stage.get("overlay_type", overlay_type) if isinstance(stage, dict) else overlay_type)
    elif overlay_type:
        source_overlay_types = [overlay_type for _ in source_history]

    dense_process_history = [] if source_process_history is not None else None
    dense_overlay_types = [] if source_overlay_types is not None else None
    for idx, current in enumerate(source_history[:-1]):
        nxt = source_history[idx + 1]
        t0 = float(source_times[idx])
        t1 = float(source_times[idx + 1])
        for step in range(interpolation_steps):
            blend = step / interpolation_steps
            dense_history.append(((1.0 - blend) * current) + (blend * nxt))
            dense_times.append(t0 + ((t1 - t0) * blend))
            if dense_process_history is not None:
                current_process = source_process_history[idx]
                next_process = source_process_history[idx + 1]
                keys = set(current_process) | set(next_process)
                dense_process_history.append(
                    {
                        key: ((1.0 - blend) * np.array(current_process.get(key, 0.0), dtype=float))
                        + (blend * np.array(next_process.get(key, 0.0), dtype=float))
                        for key in keys
                    }
                )
            if dense_overlay_types is not None:
                dense_overlay_types.append(source_overlay_types[idx])

    dense_history.append(source_history[-1])
    dense_times.append(float(source_times[len(source_history) - 1]))
    if dense_process_history is not None:
        dense_process_history.append({key: np.array(value, dtype=float) for key, value in source_process_history[-1].items()})
    if dense_overlay_types is not None:
        dense_overlay_types.append(source_overlay_types[-1])

    x = np.arange(dense_history[0].shape[1])
    y = np.arange(dense_history[0].shape[0])
    camera_settings = base_camera if isinstance(base_camera, dict) else _get_optimal_camera(landform_type, detailed_type)

    elev_min = float(min(np.min(frame) for frame in dense_history))
    elev_max = float(max(np.max(frame) for frame in dense_history))
    overlay_offset = max((elev_max - elev_min) * 0.0025, 0.02)
    total_frames = len(dense_history)

    frame_ids = []
    frame_labels = []
    frames = []
    for idx, elevation in enumerate(dense_history):
        frame_ids.append(f"hist_{idx:03d}")
        frame_labels.append(_format_year_label(dense_times[idx]))
        surfacecolor, colorscale, lighting = _compute_surface_style(
            elevation,
            landform_type=landform_type,
            render_style=render_style,
            elev_min=elev_min,
            elev_max=elev_max,
            texture_payload=None,
        )

        frame_layout = None
        if camera_motion != "fixed":
            frame_layout = go.Layout(
                scene=dict(
                    camera=_get_motion_camera(
                        camera_settings,
                        motion_mode=camera_motion,
                        frame_idx=idx,
                        total_frames=total_frames,
                        cinematic_zoom=cinematic_zoom,
                    )
                )
            )

        frame_overlay_type = dense_overlay_types[idx] if dense_overlay_types is not None else overlay_type
        overlay_field = None
        if dense_process_history is not None:
            overlay_field = _extract_overlay_field(dense_process_history[idx], frame_overlay_type, elevation.shape)

        frames.append(
            go.Frame(
                data=_build_history_surface_traces(
                    elevation=elevation,
                    x=x,
                    y=y,
                    surfacecolor=surfacecolor,
                    colorscale=colorscale,
                    lighting=lighting,
                    overlay_field=overlay_field,
                    overlay_type=frame_overlay_type,
                    overlay_offset=overlay_offset,
                ),
                name=frame_ids[idx],
                layout=frame_layout,
                traces=list(range(2 if overlay_field is not None else 1)),
            )
        )

    initial_surfacecolor, initial_colorscale, initial_lighting = _compute_surface_style(
        dense_history[0],
        landform_type=landform_type,
        render_style=render_style,
        elev_min=elev_min,
        elev_max=elev_max,
        texture_payload=None,
    )

    initial_overlay_type = dense_overlay_types[0] if dense_overlay_types is not None else overlay_type
    initial_overlay_field = None
    if dense_process_history is not None:
        initial_overlay_field = _extract_overlay_field(dense_process_history[0], initial_overlay_type, dense_history[0].shape)

    fig = go.Figure(
        data=_build_history_surface_traces(
            elevation=dense_history[0],
            x=x,
            y=y,
            surfacecolor=initial_surfacecolor,
            colorscale=initial_colorscale,
            lighting=initial_lighting,
            overlay_field=initial_overlay_field,
            overlay_type=initial_overlay_type,
            overlay_offset=overlay_offset,
        ),
        frames=frames,
    )

    sliders = []
    if show_slider:
        sliders = [{
            'active': 0,
            'yanchor': 'top',
            'xanchor': 'left',
            'currentvalue': {
                'font': {'size': 14, 'color': 'white'},
                'prefix': '형성 시간: ',
                'suffix': '',
                'visible': True,
                'xanchor': 'center'
            },
            'transition': {'duration': transition_duration_ms, 'easing': 'cubic-in-out'},
            'pad': {'b': 10, 't': 50},
            'len': 0.9,
            'x': 0.05,
            'y': 0,
            'steps': [
                {
                    'args': [[frames[idx].name], {'frame': {'duration': frame_duration_ms, 'redraw': True}, 'mode': 'immediate', 'transition': {'duration': transition_duration_ms}}],
                    'label': frame_labels[idx],
                    'method': 'animate'
                }
                for idx in range(len(frames))
            ]
        }]

    updatemenus = []
    if show_controls:
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
                    'label': '재생',
                    'method': 'animate',
                    'args': [
                        frame_ids,
                        {
                            'frame': {'duration': frame_duration_ms, 'redraw': True},
                            'fromcurrent': False,
                            'mode': 'immediate',
                            'transition': {'duration': transition_duration_ms, 'easing': 'cubic-in-out'}
                        }
                    ]
                },
                {
                    'label': '정지',
                    'method': 'animate',
                    'args': [
                        [None],
                        {
                            'frame': {'duration': 0, 'redraw': True},
                            'mode': 'immediate',
                            'transition': {'duration': 0}
                        }
                    ]
                },
                {
                    'label': '처음부터',
                    'method': 'animate',
                    'args': [
                        [frame_ids[0]],
                        {
                            'frame': {'duration': 0, 'redraw': True},
                            'mode': 'immediate',
                            'transition': {'duration': 0}
                        }
                    ]
                }
            ]
        }]

    z_scales = {
        'arid': 0.25,
        'coastal': 0.35,
        'river': 0.4,
        'glacial': 0.5,
        'tectonic': 0.55,
        'volcanic': 0.6,
        'karst': 0.35,
        'mesa_butte': 0.5,
        'pedestal_rock': 0.7,
        'tower_karst': 0.7,
        'shield_volcano': 0.3,
        'stratovolcano': 0.7,
        'folded_range': 0.55,
        'horn': 0.7,
        'fjord': 0.5,
        'wadi': 0.5,
        'pediment': 0.4,
        'canyon': 0.6,
    }
    z_aspect = z_scales.get(detailed_type)
    if z_aspect is None:
        z_aspect = z_scales.get(landform_type, 0.4)

    initial_camera = camera_settings
    if camera_motion != "fixed":
        initial_camera = _get_motion_camera(
            camera_settings,
            motion_mode=camera_motion,
            frame_idx=0,
            total_frames=max(total_frames, 2),
            cinematic_zoom=cinematic_zoom,
        )
    elif cinematic_zoom != 1.0:
        initial_camera = _get_motion_camera(
            camera_settings,
            motion_mode='sweep',
            frame_idx=0,
            total_frames=max(total_frames, 2),
            cinematic_zoom=cinematic_zoom,
        )

    fig.update_layout(
        title=dict(text=title, font=dict(color='white', size=18)),
        uirevision='terrain_history_anim',
        font=dict(
            family='Malgun Gothic, Apple SD Gothic Neo, NanumGothic, sans-serif',
            color='#ffffff',
        ),
        scene=dict(
            xaxis=dict(title='X (m)', backgroundcolor='#1a1a2e', gridcolor='#444', color='#cccccc'),
            yaxis=dict(title='Y (m)', backgroundcolor='#1a1a2e', gridcolor='#444', color='#cccccc'),
            zaxis=dict(title='Elevation', backgroundcolor='#1a1a2e', gridcolor='#444', color='#cccccc'),
            bgcolor='#0e1117',
            camera=initial_camera,
            uirevision='terrain_history_scene',
            aspectmode='manual',
            aspectratio=dict(x=1, y=1, z=z_aspect)
        ),
        paper_bgcolor='#0e1117',
        plot_bgcolor='#0e1117',
        height=720,
        margin=dict(l=10, r=10, t=80, b=80),
        updatemenus=updatemenus,
        sliders=sliders,
    )

    return fig


def create_history_animation_embed_html(
    figure: go.Figure,
    frame_duration_ms: int = 180,
    transition_duration_ms: int = 120,
    height: int = 760,
) -> str:
    if figure is None or go is None:
        return ""

    try:
        import plotly.io as pio
    except Exception:
        return ""

    frame_names = [frame.name for frame in (figure.frames or []) if getattr(frame, "name", None)]
    if not frame_names:
        return ""

    frame_duration_ms = max(int(frame_duration_ms), 0)
    transition_duration_ms = max(int(transition_duration_ms), 0)
    wrapper_id = f"history-animation-{uuid.uuid4().hex}"
    plot_html = pio.to_html(
        figure,
        full_html=False,
        include_plotlyjs=True,
        auto_play=False,
        config={
            "responsive": True,
            "displayModeBar": True,
            "scrollZoom": False,
        },
    )

    return f"""
<div id="{wrapper_id}" style="width:100%; min-height:{int(height)}px;">
{plot_html}
</div>
<script>
(function() {{
  const wrapper = document.getElementById("{wrapper_id}");
  if (!wrapper) return;
  if (!window.Plotly) return;
  const frameNames = {json.dumps(frame_names, ensure_ascii=False)};
  if (!frameNames.length) return;

  let attempts = 0;
  const timer = window.setInterval(() => {{
    attempts += 1;
    const plot = wrapper.querySelector('.js-plotly-plot');
    if (!plot || !plot.data || !plot.data.length) {{
      if (attempts >= 40) {{
        window.clearInterval(timer);
      }}
      return;
    }}

    try {{
      window.Plotly.animate(plot, frameNames, {{
        frame: {{ duration: {frame_duration_ms}, redraw: true }},
        transition: {{ duration: {transition_duration_ms}, easing: 'cubic-in-out' }},
        mode: 'immediate',
        fromcurrent: false
      }});
      window.clearInterval(timer);
    }} catch (error) {{
      if (attempts >= 40) {{
        window.clearInterval(timer);
      }}
    }}
  }}, 250);
}})();
</script>
"""


def _compute_surface_style(
    elevation: np.ndarray,
    landform_type: str,
    render_style: str,
    elev_min: float,
    elev_max: float,
    texture_payload: Optional[dict] = None,
):
    if render_style == "satellite":
        if texture_payload is not None:
            hill = _hillshade(elevation)
            base_idx = texture_payload["index"]
            surfacecolor = np.clip((0.72 * base_idx) + (0.28 * hill), 0.0, 1.0)
            colorscale = texture_payload["colorscale"]
        else:
            surfacecolor = _build_satellite_index(elevation, elev_min, elev_max)
            colorscale = _get_satellite_colorscale(landform_type)
        lighting = dict(ambient=0.45, diffuse=0.75, roughness=0.85, specular=0.08)
    else:
        surfacecolor = _build_terrain_index(elevation, elev_min, elev_max)
        colorscale = _get_colorscale(landform_type)
        lighting = dict(ambient=0.35, diffuse=0.65, roughness=0.9, specular=0.12)

    return surfacecolor, colorscale, lighting


def _prepare_texture_payload(texture_map: Optional[np.ndarray], grid_size: int) -> Optional[dict]:
    if texture_map is None or Image is None:
        return None

    try:
        arr = np.asarray(texture_map)
        if arr.ndim == 2:
            arr = np.stack([arr, arr, arr], axis=-1)
        if arr.ndim != 3:
            return None

        if arr.shape[2] > 3:
            arr = arr[:, :, :3]

        if arr.dtype != np.uint8:
            arr = arr.astype(np.float32)
            if arr.max() <= 1.0:
                arr = arr * 255.0
            arr = np.clip(arr, 0, 255).astype(np.uint8)

        pil = Image.fromarray(arr).convert("RGB")
        if hasattr(Image, "Resampling"):
            pil = pil.resize((grid_size, grid_size), Image.Resampling.BILINEAR)
        else:
            pil = pil.resize((grid_size, grid_size), Image.BILINEAR)

        rgb = np.asarray(pil, dtype=np.float32) / 255.0
        lum = (0.2126 * rgb[:, :, 0]) + (0.7152 * rgb[:, :, 1]) + (0.0722 * rgb[:, :, 2])
        idx = (lum - float(lum.min())) / max(float(lum.max() - lum.min()), 1e-9)
        colorscale = _build_texture_colorscale(rgb, idx)
        return {"index": idx, "colorscale": colorscale}
    except Exception:
        return None


def _build_texture_colorscale(rgb: np.ndarray, idx: np.ndarray):
    flat_idx = idx.reshape(-1)
    flat_rgb = rgb.reshape(-1, 3)
    levels = np.linspace(0.0, 1.0, 14)

    colorscale = []
    for lv in levels:
        pick = int(np.argmin(np.abs(flat_idx - lv)))
        color = np.clip(flat_rgb[pick] * 255.0, 0, 255).astype(int)
        colorscale.append([float(lv), f"rgb({color[0]},{color[1]},{color[2]})"])

    if colorscale[0][0] != 0.0:
        colorscale.insert(0, [0.0, colorscale[0][1]])
    if colorscale[-1][0] != 1.0:
        colorscale.append([1.0, colorscale[-1][1]])
    return colorscale


def _build_terrain_index(elevation: np.ndarray, elev_min: float, elev_max: float) -> np.ndarray:
    norm = (elevation - elev_min) / max(elev_max - elev_min, 1e-9)
    dy, dx = np.gradient(elevation)
    slope = np.sqrt(dx**2 + dy**2)
    slope_norm = slope / max(float(np.percentile(slope, 99)), 1e-9)
    idx = (0.72 * norm) + (0.28 * (1.0 - np.clip(slope_norm, 0.0, 1.0)))
    return np.clip(idx, 0.0, 1.0)


def _build_satellite_index(elevation: np.ndarray, elev_min: float, elev_max: float) -> np.ndarray:
    norm = (elevation - elev_min) / max(elev_max - elev_min, 1e-9)

    dy, dx = np.gradient(elevation)
    slope = np.sqrt(dx**2 + dy**2)
    slope_norm = np.clip(slope / max(float(np.percentile(slope, 99)), 1e-9), 0.0, 1.0)

    hill = _hillshade(elevation)
    terrain_base = (0.6 * norm) + (0.4 * hill)

    # Pseudo vegetation/moisture mask for a satellite-like texture.
    vegetation = np.clip((1.0 - norm) * 0.8 + (1.0 - slope_norm) * 0.4, 0.0, 1.0)
    rocky = np.clip(norm * 0.7 + slope_norm * 0.5, 0.0, 1.0)
    texture = (0.55 * vegetation) + (0.45 * rocky)

    noise = np.random.normal(0.0, 0.03, elevation.shape)
    idx = np.clip((0.55 * terrain_base) + (0.45 * texture) + noise, 0.0, 1.0)

    # Low elevations get ocean-like tones.
    water_mask = norm < 0.08
    idx[water_mask] = np.clip(norm[water_mask] * 0.25, 0.0, 0.18)
    return idx


def _hillshade(elevation: np.ndarray, azimuth_deg: float = 320.0, altitude_deg: float = 45.0) -> np.ndarray:
    dy, dx = np.gradient(elevation.astype(float))
    slope = np.pi / 2.0 - np.arctan(np.sqrt(dx * dx + dy * dy))
    aspect = np.arctan2(-dx, dy)

    azimuth = np.deg2rad(azimuth_deg)
    altitude = np.deg2rad(altitude_deg)
    hs = (
        np.sin(altitude) * np.sin(slope)
        + np.cos(altitude) * np.cos(slope) * np.cos(azimuth - aspect)
    )
    hs = (hs - hs.min()) / max(float(hs.max() - hs.min()), 1e-9)
    return np.clip(hs, 0.0, 1.0)


def _get_satellite_colorscale(landform_type: str):
    # Terrain-first scale with ocean + vegetation + rock + snow transitions.
    if landform_type == "arid":
        return [
            [0.00, "#06204a"],
            [0.14, "#0d4d8f"],
            [0.20, "#b99a6b"],
            [0.32, "#c8aa75"],
            [0.52, "#b38d5b"],
            [0.72, "#8c6b45"],
            [0.90, "#8d8d8d"],
            [1.00, "#f3f3f3"],
        ]
    return [
        [0.00, "#06204a"],
        [0.14, "#0d4d8f"],
        [0.20, "#d6c08e"],
        [0.34, "#3f7f4a"],
        [0.52, "#2e5f38"],
        [0.70, "#6a5a45"],
        [0.88, "#8f8f8f"],
        [1.00, "#f4f4f4"],
    ]


def _get_recommended_camera_motion(landform_type: str, detailed_type: str = None) -> str:
    orbit_types = {
        'shield_volcano',
        'stratovolcano',
        'tower_karst',
        'horn',
        'arete',
        'folded_range',
    }
    sweep_types = {
        'alluvial_fan',
        'delta',
        'bird_foot_delta',
        'free_meander',
        'meander',
        'braided_river',
        'ria_coast',
        'estuary',
        'fjord',
        'coastal_cliff',
        'sea_arch',
        'spit_lagoon',
        'tombolo',
        'v_valley',
        'u_valley',
        'karst_doline',
    }
    if detailed_type in orbit_types:
        return 'orbit'
    if detailed_type in sweep_types or landform_type in {'coastal'}:
        return 'sweep'
    return 'sweep'


def _get_motion_camera(
    base_camera: dict,
    motion_mode: str,
    frame_idx: int,
    total_frames: int,
    cinematic_zoom: float,
) -> dict:
    if motion_mode == "fixed" or total_frames <= 1:
        return base_camera

    eye = dict(base_camera.get("eye", {"x": 1.6, "y": -1.6, "z": 0.8}))
    center = dict(base_camera.get("center", {"x": 0, "y": 0, "z": -0.1}))
    up = dict(base_camera.get("up", {"x": 0, "y": 0, "z": 1}))

    t = frame_idx / max(total_frames - 1, 1)
    theta = 2.0 * np.pi * t

    radius = np.sqrt(eye["x"] ** 2 + eye["y"] ** 2) / max(cinematic_zoom, 1e-6)
    z_base = eye["z"] / max(cinematic_zoom, 1e-6)

    if motion_mode == "orbit":
        new_eye = {
            "x": float(radius * np.cos(theta)),
            "y": float(radius * np.sin(theta)),
            "z": float(z_base),
        }
    else:  # sweep
        # Keep the opening frame on the textbook camera, then drift across the
        # landform so even short teaching animations show a visible viewpoint change.
        sweep = (1.0 - np.cos(np.pi * t)) * radius * 0.45
        rise = np.sin(np.pi * t) * z_base * 0.1
        new_eye = {
            "x": float(eye["x"] / max(cinematic_zoom, 1e-6)),
            "y": float((eye["y"] / max(cinematic_zoom, 1e-6)) + sweep),
            "z": float(z_base + rise),
        }

    return {"eye": new_eye, "center": center, "up": up}


def _get_colorscale(landform_type: str):
    """吏???좏삎???곕Ⅸ 而щ윭?ㅼ???諛섑솚"""
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
    """吏???좏삎蹂?理쒖쟻 移대찓??媛곷룄 諛섑솚
    
    媛?吏???좏삎???뺤꽦 怨쇱젙????蹂댁씠??媛곷룄濡??ㅼ젙
    
    Args:
        landform_type: ?遺꾨쪟 ('river', 'glacial', 'volcanic', ??
        detailed_type: ?몃? 吏??('alluvial_fan', 'delta', 'meander', ??
    """
    # 1. ?몃? 吏?뺣퀎 移대찓??(?곗꽑 ?곸슜)
    detailed_cameras = {
        # === ?섏쿇 吏??===
        'alluvial_fan': dict(
            # ?좎긽吏: ?곗??먯꽌 ?됱?濡??대젮?ㅻ낫??媛곷룄 (遺梨꾧섦 ?꾩껜媛 蹂댁씠寃?
            eye=dict(x=0.0, y=-2.1, z=1.6),
            center=dict(x=0, y=0.25, z=-0.15),
            up=dict(x=0, y=0, z=1)
        ),
        'delta': dict(
            # ?쇨컖二? ?꾩뿉??遺꾧린 ?섎줈 ?⑦꽩??蹂댁씠寃?
            eye=dict(x=0.0, y=-1.9, z=1.8),
            center=dict(x=0, y=0.2, z=-0.2),
            up=dict(x=0, y=0, z=1)
        ),
        'bird_foot_delta': dict(
            # 議곗”???쇨컖二? 六쀬뼱?섍????섎줈媛 蹂댁씠寃?
            eye=dict(x=0.0, y=-2.0, z=1.5),
            center=dict(x=0, y=0.25, z=-0.2),
            up=dict(x=0, y=0, z=1)
        ),
        'free_meander': dict(
            # ?먯쑀怨〓쪟: 痢〓㈃?먯꽌 S??怨≪꽑??蹂댁씠寃?
            eye=dict(x=1.8, y=-0.8, z=1.0),
            center=dict(x=0, y=0, z=-0.1),
            up=dict(x=0, y=0, z=1)
        ),
        'incised_meander': dict(
            # 媛먯엯怨〓쪟: ?섏븞?④뎄媛 蹂댁씠?꾨줉 ?쎄컙 ?믪씠
            eye=dict(x=1.5, y=-1.2, z=1.2),
            center=dict(x=0, y=0, z=-0.15),
            up=dict(x=0, y=0, z=1)
        ),
        'v_valley': dict(
            # V?먭끝: 怨꾧끝 源딆씠媛 蹂댁씠寃?痢〓㈃?먯꽌
            eye=dict(x=2.0, y=-0.5, z=0.8),
            center=dict(x=0, y=0, z=-0.1),
            up=dict(x=0, y=0, z=1)
        ),
        'braided_river': dict(
            # 留앹긽?섏쿇: ?꾩뿉???⑦꽩 蹂댁씠寃?
            eye=dict(x=0.3, y=-1.8, z=1.6),
            center=dict(x=0, y=0.15, z=-0.1),
            up=dict(x=0, y=0, z=1)
        ),
        'waterfall': dict(
            # ??룷: ?숈감媛 蹂댁씠寃?痢〓㈃?먯꽌
            eye=dict(x=2.0, y=-0.3, z=0.6),
            center=dict(x=0, y=0, z=-0.1),
            up=dict(x=0, y=0, z=1)
        ),
        'perched_river': dict(
            # 泥쒖젙泥? ?먯뿰?쒕갑 ?믪씠媛 蹂댁씠寃?
            eye=dict(x=1.8, y=-1.0, z=0.8),
            center=dict(x=0, y=0, z=0),
            up=dict(x=0, y=0, z=1)
        ),
        
        # === 鍮숉븯 吏??===
        'u_valley': dict(
            # U?먭끝: 痢〓㈃?먯꽌 U???⑤㈃ 蹂댁씠寃?
            eye=dict(x=2.0, y=-0.3, z=0.6),
            center=dict(x=0, y=0, z=-0.1),
            up=dict(x=0, y=0, z=1)
        ),
        'cirque': dict(
            # 沅뚭끝: ?대?媛 蹂댁씠寃??쎄컙 ?꾩뿉??
            eye=dict(x=1.2, y=-1.5, z=1.3),
            center=dict(x=0, y=0, z=-0.2),
            up=dict(x=0, y=0, z=1)
        ),
        'horn': dict(
            # ?몃Ⅸ: 毓곗”??遊됱슦由ш? 蹂댁씠寃?痢〓㈃?먯꽌 ??쾶
            eye=dict(x=1.8, y=-1.5, z=0.7),
            center=dict(x=0, y=0, z=0.1),
            up=dict(x=0, y=0, z=1)
        ),
        'fjord': dict(
            # ?쇱삤瑜대뱶: 湲몄씠媛 蹂댁씠寃??곷쪟?먯꽌
            eye=dict(x=0.3, y=-2.2, z=1.0),
            center=dict(x=0, y=0.2, z=-0.15),
            up=dict(x=0, y=0, z=1)
        ),
        'drumlin': dict(
            # ?쒕읆由? ?좎꽑??蹂댁씠寃?痢〓㈃ ??? 媛곷룄
            eye=dict(x=2.0, y=-0.8, z=0.5),
            center=dict(x=0, y=0, z=0),
            up=dict(x=0, y=0, z=1)
        ),
        'moraine': dict(
            # 鍮숉눜?? ?명삎 ?댁쟻 蹂댁씠寃??꾩뿉??
            eye=dict(x=0.8, y=-1.8, z=1.5),
            center=dict(x=0, y=0.1, z=-0.2),
            up=dict(x=0, y=0, z=1)
        ),
        'arete': dict(
            # ?꾨젅?? ?좎뭅濡쒖슫 ?μ꽑 蹂댁씠寃?
            eye=dict(x=1.5, y=-1.5, z=0.8),
            center=dict(x=0, y=0, z=0),
            up=dict(x=0, y=0, z=1)
        ),
        
        # === ?붿궛 吏??===
        'shield_volcano': dict(
            # ?쒖긽?붿궛: ?꾨쭔??寃쎌궗 蹂댁씠寃???? 媛곷룄
            eye=dict(x=2.2, y=-1.0, z=0.5),
            center=dict(x=0, y=0, z=0),
            up=dict(x=0, y=0, z=1)
        ),
        'stratovolcano': dict(
            # ?깆링?붿궛: 湲됯꼍??蹂댁씠寃?痢〓㈃
            eye=dict(x=2.0, y=-1.2, z=0.7),
            center=dict(x=0, y=0, z=0.1),
            up=dict(x=0, y=0, z=1)
        ),
        'caldera': dict(
            # 移쇰뜲?? 遺꾪솕援??대? 蹂댁씠寃??꾩뿉??
            eye=dict(x=0.8, y=-1.5, z=1.5),
            center=dict(x=0, y=0, z=-0.1),
            up=dict(x=0, y=0, z=1)
        ),
        'crater_lake': dict(
            # ?붽뎄?? ?몄닔 蹂댁씠寃??꾩뿉??
            eye=dict(x=0.6, y=-1.6, z=1.6),
            center=dict(x=0, y=0, z=-0.1),
            up=dict(x=0, y=0, z=1)
        ),
        'lava_plateau': dict(
            # ?⑹븫?吏: ?됲깂硫?蹂댁씠寃???? 媛곷룄
            eye=dict(x=1.8, y=-1.5, z=0.6),
            center=dict(x=0, y=0, z=0),
            up=dict(x=0, y=0, z=1)
        ),
        
        # === ?댁븞 吏??===
        'coastal_cliff': dict(
            # ?댁븞?덈꼍: ?덈꼍硫?蹂댁씠寃?諛붾떎?먯꽌
            eye=dict(x=0.3, y=-2.2, z=0.7),
            center=dict(x=0, y=0.15, z=-0.1),
            up=dict(x=0, y=0, z=1)
        ),
        'spit_lagoon': dict(
            # ?ъ랬+?앺샇: ?꾩뿉???뺥깭 蹂댁씠寃?
            eye=dict(x=0.5, y=-1.8, z=1.6),
            center=dict(x=0, y=0.1, z=-0.1),
            up=dict(x=0, y=0, z=1)
        ),
        'tombolo': dict(
            # ?↔퀎?ъ＜: ?곌껐遺 蹂댁씠寃?
            eye=dict(x=1.5, y=-1.5, z=1.2),
            center=dict(x=0, y=0, z=-0.1),
            up=dict(x=0, y=0, z=1)
        ),
        'ria_coast': dict(
            # 由ъ븘?? ?깅땲 ?댁븞??蹂댁씠寃??꾩뿉??
            eye=dict(x=0.3, y=-1.8, z=1.8),
            center=dict(x=0, y=0.1, z=-0.2),
            up=dict(x=0, y=0, z=1)
        ),
        'sea_arch': dict(
            # ?댁떇?꾩튂: ?꾩튂 ?뺥깭 蹂댁씠寃?痢〓㈃
            eye=dict(x=1.8, y=0.8, z=0.6),
            center=dict(x=0, y=0, z=0),
            up=dict(x=0, y=0, z=1)
        ),
        
        # === 嫄댁“ 吏??===
        'barchan': dict(
            # 諛붾Ⅴ?? 珥덉듅???뺥깭 蹂댁씠寃???? 媛곷룄
            eye=dict(x=2.0, y=-0.8, z=0.5),
            center=dict(x=0, y=0, z=0),
            up=dict(x=0, y=0, z=1)
        ),
        'transverse_dune': dict(
            # ?≪궗援? ?μ꽑 蹂댁씠寃?痢〓㈃
            eye=dict(x=2.2, y=-0.5, z=0.5),
            center=dict(x=0, y=0, z=0),
            up=dict(x=0, y=0, z=1)
        ),
        'star_dune': dict(
            # ?깆궗援? 諛⑹궗??蹂댁씠寃??꾩뿉??
            eye=dict(x=1.0, y=-1.5, z=1.4),
            center=dict(x=0, y=0, z=-0.1),
            up=dict(x=0, y=0, z=1)
        ),
        'mesa_butte': dict(
            # 硫붿궗/酉고듃: ?⑥븷 蹂댁씠寃?痢〓㈃
            eye=dict(x=2.0, y=-1.2, z=0.7),
            center=dict(x=0, y=0, z=0),
            up=dict(x=0, y=0, z=1)
        ),
        'pedestal_rock': dict(
            # 踰꾩꽢諛붿쐞: 以꾧린 蹂댁씠寃?痢〓㈃ ??쾶
            eye=dict(x=2.2, y=-0.5, z=0.4),
            center=dict(x=0, y=0, z=0.1),
            up=dict(x=0, y=0, z=1)
        ),
        
        # === 移대Ⅴ?ㅽ듃 吏??===
        'karst_doline': dict(
            # ?뚮━?? ?⑤ぐ 蹂댁씠寃??꾩뿉??
            eye=dict(x=0.8, y=-1.5, z=1.6),
            center=dict(x=0, y=0, z=-0.2),
            up=dict(x=0, y=0, z=1)
        ),
        'uvala': dict(
            # ?곕컻?? 蹂듯빀 ?⑤ぐ 蹂댁씠寃??꾩뿉??
            eye=dict(x=0.6, y=-1.6, z=1.7),
            center=dict(x=0, y=0, z=-0.2),
            up=dict(x=0, y=0, z=1)
        ),
        'tower_karst': dict(
            # ?묒뭅瑜댁뒪?? ???뺥깭 蹂댁씠寃???? 媛곷룄
            eye=dict(x=2.0, y=-1.0, z=0.6),
            center=dict(x=0, y=0, z=0.1),
            up=dict(x=0, y=0, z=1)
        ),
    }
    
    # ?몃? 吏??移대찓?쇨? ?덉쑝硫??ъ슜
    if detailed_type and detailed_type in detailed_cameras:
        return detailed_cameras[detailed_type]
    
    # 2. ?遺꾨쪟 移대찓??(fallback)
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
            eye=dict(x=0.5, y=-1.8, z=0.9),
            center=dict(x=0, y=0.15, z=-0.1),
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
    
    # 3. 湲곕낯媛?
    return dict(
        eye=dict(x=1.5, y=-1.5, z=1.0),
        center=dict(x=0, y=0, z=-0.1),
        up=dict(x=0, y=0, z=1)
    )


def _get_optimal_camera(landform_type: str, detailed_type: str = None, camera_profile: str | None = None) -> dict:
    """Return a textbook-style camera that prioritizes landform readability."""

    textbook_profiles = {
        "planform_front": dict(
            eye=dict(x=0.12, y=-2.35, z=1.95),
            center=dict(x=0, y=0.18, z=-0.18),
            up=dict(x=0, y=0, z=1),
        ),
        "planform_oblique": dict(
            eye=dict(x=0.9, y=-2.0, z=1.35),
            center=dict(x=0, y=0.06, z=-0.12),
            up=dict(x=0, y=0, z=1),
        ),
        "valley_profile": dict(
            eye=dict(x=2.25, y=-0.35, z=0.74),
            center=dict(x=0, y=0.02, z=-0.12),
            up=dict(x=0, y=0, z=1),
        ),
        "basin_overlook": dict(
            eye=dict(x=0.58, y=-1.5, z=1.72),
            center=dict(x=0, y=0, z=-0.18),
            up=dict(x=0, y=0, z=1),
        ),
        "relief_oblique": dict(
            eye=dict(x=1.95, y=-1.2, z=0.82),
            center=dict(x=0, y=0, z=0.04),
            up=dict(x=0, y=0, z=1),
        ),
        "coastal_front": dict(
            eye=dict(x=0.18, y=-2.3, z=0.92),
            center=dict(x=0, y=0.18, z=-0.08),
            up=dict(x=0, y=0, z=1),
        ),
        "fan_textbook": dict(
            eye=dict(x=0.04, y=-2.6, z=1.82),
            center=dict(x=0, y=0.28, z=-0.2),
            up=dict(x=0, y=0, z=1),
        ),
        "delta_textbook": dict(
            eye=dict(x=0.08, y=-2.58, z=2.12),
            center=dict(x=0, y=0.28, z=-0.24),
            up=dict(x=0, y=0, z=1),
        ),
        "fjord_textbook": dict(
            eye=dict(x=0.62, y=-2.48, z=1.16),
            center=dict(x=0, y=0.3, z=-0.18),
            up=dict(x=0, y=0, z=1),
        ),
        "cliff_textbook": dict(
            eye=dict(x=0.96, y=-1.92, z=0.88),
            center=dict(x=0, y=0.22, z=-0.06),
            up=dict(x=0, y=0, z=1),
        ),
    }

    detailed_cameras = {
        "alluvial_fan": textbook_profiles["fan_textbook"],
        "delta": textbook_profiles["delta_textbook"],
        "bird_foot_delta": textbook_profiles["delta_textbook"],
        "arcuate_delta": textbook_profiles["delta_textbook"],
        "cuspate_delta": textbook_profiles["delta_textbook"],
        "free_meander": textbook_profiles["planform_front"],
        "meander": textbook_profiles["planform_front"],
        "braided_river": textbook_profiles["planform_front"],
        "spit_lagoon": textbook_profiles["planform_front"],
        "ria_coast": textbook_profiles["planform_front"],
        "estuary": textbook_profiles["planform_front"],
        "incised_meander": dict(
            eye=dict(x=1.45, y=-1.3, z=1.05),
            center=dict(x=0, y=0, z=-0.14),
            up=dict(x=0, y=0, z=1),
        ),
        "perched_river": textbook_profiles["planform_oblique"],
        "moraine": textbook_profiles["planform_oblique"],
        "tombolo": textbook_profiles["planform_oblique"],
        "v_valley": textbook_profiles["valley_profile"],
        "u_valley": textbook_profiles["valley_profile"],
        "waterfall": dict(
            eye=dict(x=2.15, y=-0.2, z=0.72),
            center=dict(x=0, y=0.03, z=-0.08),
            up=dict(x=0, y=0, z=1),
        ),
        "fjord": textbook_profiles["fjord_textbook"],
        "cirque": textbook_profiles["basin_overlook"],
        "caldera": textbook_profiles["basin_overlook"],
        "crater_lake": textbook_profiles["basin_overlook"],
        "karst_doline": textbook_profiles["basin_overlook"],
        "uvala": textbook_profiles["basin_overlook"],
        "karren": textbook_profiles["basin_overlook"],
        "horn": textbook_profiles["relief_oblique"],
        "arete": textbook_profiles["relief_oblique"],
        "tower_karst": textbook_profiles["relief_oblique"],
        "shield_volcano": dict(
            eye=dict(x=1.95, y=-1.05, z=0.58),
            center=dict(x=0, y=0, z=0.02),
            up=dict(x=0, y=0, z=1),
        ),
        "stratovolcano": dict(
            eye=dict(x=1.85, y=-1.25, z=0.82),
            center=dict(x=0, y=0, z=0.08),
            up=dict(x=0, y=0, z=1),
        ),
        "folded_range": dict(
            eye=dict(x=2.0, y=-1.0, z=0.86),
            center=dict(x=0, y=0, z=0.04),
            up=dict(x=0, y=0, z=1),
        ),
        "lava_plateau": dict(
            eye=dict(x=1.7, y=-1.45, z=0.7),
            center=dict(x=0, y=0, z=0),
            up=dict(x=0, y=0, z=1),
        ),
        "coastal_cliff": textbook_profiles["cliff_textbook"],
        "sea_arch": dict(
            eye=dict(x=1.75, y=-0.85, z=0.65),
            center=dict(x=0, y=0.02, z=0.02),
            up=dict(x=0, y=0, z=1),
        ),
        "drumlin": dict(
            eye=dict(x=1.95, y=-0.95, z=0.58),
            center=dict(x=0, y=0, z=-0.02),
            up=dict(x=0, y=0, z=1),
        ),
        "barchan": dict(
            eye=dict(x=2.0, y=-0.85, z=0.52),
            center=dict(x=0, y=0, z=0),
            up=dict(x=0, y=0, z=1),
        ),
        "transverse_dune": dict(
            eye=dict(x=2.1, y=-0.6, z=0.52),
            center=dict(x=0, y=0, z=0),
            up=dict(x=0, y=0, z=1),
        ),
        "star_dune": dict(
            eye=dict(x=0.95, y=-1.55, z=1.35),
            center=dict(x=0, y=0, z=-0.08),
            up=dict(x=0, y=0, z=1),
        ),
        "mesa_butte": dict(
            eye=dict(x=2.0, y=-1.2, z=0.72),
            center=dict(x=0, y=0, z=0),
            up=dict(x=0, y=0, z=1),
        ),
        "pedestal_rock": dict(
            eye=dict(x=2.15, y=-0.55, z=0.42),
            center=dict(x=0, y=0, z=0.08),
            up=dict(x=0, y=0, z=1),
        ),
    }

    if camera_profile and camera_profile in textbook_profiles:
        return textbook_profiles[camera_profile]

    if detailed_type and detailed_type in detailed_cameras:
        return detailed_cameras[detailed_type]

    category_cameras = {
        "river": textbook_profiles["planform_front"],
        "glacial": textbook_profiles["valley_profile"],
        "volcanic": textbook_profiles["relief_oblique"],
        "coastal": textbook_profiles["coastal_front"],
        "arid": textbook_profiles["relief_oblique"],
        "karst": textbook_profiles["basin_overlook"],
        "tectonic": textbook_profiles["relief_oblique"],
    }

    if landform_type in category_cameras:
        return category_cameras[landform_type]

    return dict(
        eye=dict(x=1.5, y=-1.5, z=1.0),
        center=dict(x=0, y=0, z=-0.1),
        up=dict(x=0, y=0, z=1),
    )


def get_multi_angle_cameras() -> dict:
    """?ㅼ쨷 ?쒖젏 移대찓???꾨━??
    
    X異??뺣㈃), Y異?痢〓㈃), Z異??됰㈃??, ?깃컖?ъ쁺 4媛吏 ?쒖젏
    """
    return {
        "기본 사각 뷰": dict(
            eye=dict(x=1.5, y=-1.5, z=1.2),
            center=dict(x=0, y=0, z=-0.1),
            up=dict(x=0, y=0, z=1)
        ),
        "왼쪽 측면 (X+)": dict(
            eye=dict(x=2.5, y=0, z=0.3),
            center=dict(x=0, y=0, z=0),
            up=dict(x=0, y=0, z=1)
        ),
        "오른쪽 측면 (X-)": dict(
            eye=dict(x=-2.5, y=0, z=0.3),
            center=dict(x=0, y=0, z=0),
            up=dict(x=0, y=0, z=1)
        ),
        "정면 (Y-)": dict(
            eye=dict(x=0, y=-2.5, z=0.3),
            center=dict(x=0, y=0, z=0),
            up=dict(x=0, y=0, z=1)
        ),
        "후면 (Y+)": dict(
            eye=dict(x=0, y=2.5, z=0.3),
            center=dict(x=0, y=0, z=0),
            up=dict(x=0, y=0, z=1)
        ),
        "탑뷰 (Z+)": dict(
            eye=dict(x=0, y=0, z=2.5),
            center=dict(x=0, y=0, z=0),
            up=dict(x=0, y=1, z=0)
        ),
        "대각선 낮은 뷰": dict(
            eye=dict(x=2.0, y=-2.0, z=0.5),
            center=dict(x=0, y=0, z=-0.1),
            up=dict(x=0, y=0, z=1)
        ),
        "상류/하류 뷰": dict(
            eye=dict(x=-0.3, y=-2.5, z=1.5),
            center=dict(x=0, y=0.2, z=-0.2),
            up=dict(x=0, y=0, z=1)
        )
    }


