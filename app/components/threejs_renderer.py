"""Three.js-based experimental terrain viewer for image-sequence assets."""

from __future__ import annotations

import json
from textwrap import dedent

import numpy as np

from app.services.animation_assets import (
    StoryboardAsset,
    get_landform_asset_bundle,
    read_image_data_uri,
    sample_landform_surface_sequence,
)


def _build_surface_payload(landform_id: str, *, grid_size: int, surface_frames: int) -> dict:
    surfaces = sample_landform_surface_sequence(
        landform_id,
        frame_count=surface_frames,
        grid_size=grid_size,
    )
    stacked = np.stack(surfaces).astype(float)
    z_min = float(np.min(stacked))
    z_max = float(np.max(stacked))
    span = max(z_max - z_min, 1e-6)
    normalized = (stacked - z_min) / span
    flattened = [np.flipud(frame).reshape(-1).round(5).tolist() for frame in normalized]
    return {
        "gridSize": grid_size,
        "surfaceFrames": flattened,
        "surfaceFrameCount": len(flattened),
        "heightScale": 18.0,
    }


def create_threejs_terrain_viewer_html(
    asset: StoryboardAsset,
    *,
    viewer_height: int = 640,
    grid_size: int = 48,
    surface_frames: int = 10,
) -> str | None:
    bundle = get_landform_asset_bundle(asset.landform_id)
    if bundle is None:
        return None

    filmstrip_path = bundle.get("filmstrip_path")
    if filmstrip_path is None or not filmstrip_path.exists():
        return None

    entry = bundle.get("image_sequence_entry") or {}
    payload = {
        "title": asset.title,
        "landformId": asset.landform_id,
        "filmstripDataUri": read_image_data_uri(filmstrip_path),
        "filmstripCols": 5,
        "filmstripRows": 6,
        "textureFrameCount": int(entry.get("frame_count") or 30),
        "fps": int(entry.get("fps") or 12),
        "viewerHeight": int(viewer_height),
    }
    payload.update(
        _build_surface_payload(
            asset.landform_id,
            grid_size=grid_size,
            surface_frames=surface_frames,
        )
    )

    config_json = json.dumps(payload, ensure_ascii=False)
    return dedent(
        f"""
        <div id="threejs-terrain-root" style="width:100%;height:{viewer_height}px;position:relative;overflow:hidden;background:#020617;border-radius:6px;">
          <div id="threejs-terrain-label" style="position:absolute;left:16px;top:14px;z-index:5;color:#e2e8f0;font:600 14px/1.4 system-ui,sans-serif;letter-spacing:0;">
            Three.js 실험 뷰어
          </div>
          <div id="threejs-terrain-meta" style="position:absolute;left:16px;top:36px;z-index:5;color:#94a3b8;font:12px/1.4 system-ui,sans-serif;">
            이미지 시퀀스 필름스트립 + 절차적 지형 표면
          </div>
          <div id="threejs-terrain-stage" style="position:absolute;right:16px;top:14px;z-index:5;color:#e2e8f0;font:600 13px/1.4 system-ui,sans-serif;"></div>
          <canvas id="threejs-terrain-canvas" style="display:block;width:100%;height:100%;"></canvas>
        </div>
        <script type="module">
          import * as THREE from "https://unpkg.com/three@0.160.0/build/three.module.js";

          const payload = {config_json};
          const root = document.getElementById("threejs-terrain-root");
          const canvas = document.getElementById("threejs-terrain-canvas");
          const stageLabel = document.getElementById("threejs-terrain-stage");

          const renderer = new THREE.WebGLRenderer({{ canvas, antialias: true, alpha: true }});
          renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
          renderer.setSize(root.clientWidth, root.clientHeight, false);

          const scene = new THREE.Scene();
          scene.background = new THREE.Color(0x020617);
          scene.fog = new THREE.Fog(0x020617, 90, 180);

          const camera = new THREE.PerspectiveCamera(38, root.clientWidth / root.clientHeight, 0.1, 400);
          const ambientLight = new THREE.AmbientLight(0xffffff, 1.55);
          scene.add(ambientLight);

          const keyLight = new THREE.DirectionalLight(0xffffff, 1.6);
          keyLight.position.set(24, 42, 18);
          scene.add(keyLight);

          const rimLight = new THREE.DirectionalLight(0x8ec5ff, 0.6);
          rimLight.position.set(-28, 18, -22);
          scene.add(rimLight);

          const planeSize = 82;
          const geometry = new THREE.PlaneGeometry(
            planeSize,
            planeSize,
            payload.gridSize - 1,
            payload.gridSize - 1,
          );
          geometry.rotateX(-Math.PI / 2);

          const textureLoader = new THREE.TextureLoader();
          const filmstripTexture = textureLoader.load(payload.filmstripDataUri);
          filmstripTexture.wrapS = THREE.ClampToEdgeWrapping;
          filmstripTexture.wrapT = THREE.ClampToEdgeWrapping;
          filmstripTexture.repeat.set(1 / payload.filmstripCols, 1 / payload.filmstripRows);
          filmstripTexture.offset.set(0, 1 - 1 / payload.filmstripRows);
          filmstripTexture.colorSpace = THREE.SRGBColorSpace;

          const terrainMaterial = new THREE.MeshStandardMaterial({{
            map: filmstripTexture,
            displacementScale: 0,
            roughness: 0.95,
            metalness: 0.02,
          }});
          const terrainMesh = new THREE.Mesh(geometry, terrainMaterial);
          terrainMesh.position.y = 0;
          scene.add(terrainMesh);

          const waterGeometry = new THREE.CircleGeometry(42, 96);
          waterGeometry.rotateX(-Math.PI / 2);
          const waterMaterial = new THREE.MeshPhysicalMaterial({{
            color: 0x194b73,
            transparent: true,
            opacity: 0.2,
            roughness: 0.14,
            metalness: 0.0,
            transmission: 0.1,
          }});
          const waterMesh = new THREE.Mesh(waterGeometry, waterMaterial);
          waterMesh.position.set(0, -1.8, 0);
          scene.add(waterMesh);

          const vertexBuffer = geometry.attributes.position.array;
          const surfaceFrames = payload.surfaceFrames;
          const surfaceFrameCount = Math.max(payload.surfaceFrameCount || 1, 1);
          const textureFrameCount = Math.max(payload.textureFrameCount || 1, 1);

          function applyTextureFrame(frameIndex) {{
            const cellIndex = ((frameIndex % textureFrameCount) + textureFrameCount) % textureFrameCount;
            const col = cellIndex % payload.filmstripCols;
            const row = Math.floor(cellIndex / payload.filmstripCols);
            filmstripTexture.offset.x = col / payload.filmstripCols;
            filmstripTexture.offset.y = 1 - ((row + 1) / payload.filmstripRows);
            filmstripTexture.needsUpdate = true;
          }}

          function applySurface(playhead) {{
            const maxIndex = surfaceFrameCount - 1;
            const scaled = Math.max(0, Math.min(maxIndex, playhead * maxIndex));
            const a = Math.floor(scaled);
            const b = Math.min(maxIndex, a + 1);
            const t = scaled - a;
            const surfaceA = surfaceFrames[a];
            const surfaceB = surfaceFrames[b];

            for (let i = 0; i < surfaceA.length; i += 1) {{
              vertexBuffer[i * 3 + 1] = ((surfaceA[i] * (1 - t)) + (surfaceB[i] * t)) * payload.heightScale;
            }}
            geometry.attributes.position.needsUpdate = true;
            geometry.computeVertexNormals();
          }}

          function updateCamera(elapsedMs) {{
            const t = elapsedMs * 0.00014;
            const azimuth = -0.45 + Math.sin(t * 0.8) * 0.6 + Math.sin(t * 0.37) * 0.18;
            const radius = 76 + Math.sin(t * 0.51) * 7;
            const y = 26 + Math.sin(t * 0.95) * 5.5;
            camera.position.set(Math.cos(azimuth) * radius, y, Math.sin(azimuth) * radius);
            camera.lookAt(0, 10, 0);
          }}

          function renderFrame(elapsedMs) {{
            const texturePlayhead = (elapsedMs / 1000) * payload.fps;
            const textureFrame = Math.floor(texturePlayhead) % textureFrameCount;
            const normalizedPlayhead = (textureFrameCount <= 1) ? 0 : (textureFrame / (textureFrameCount - 1));

            applyTextureFrame(textureFrame);
            applySurface(normalizedPlayhead);
            updateCamera(elapsedMs);

            stageLabel.textContent = `${{payload.title}}  |  frame ${{String(textureFrame + 1).padStart(2, "0")}} / ${{textureFrameCount}}`;
            renderer.render(scene, camera);
            requestAnimationFrame(renderFrame);
          }}

          const resizeObserver = new ResizeObserver(() => {{
            const width = root.clientWidth;
            const height = root.clientHeight;
            renderer.setSize(width, height, false);
            camera.aspect = width / height;
            camera.updateProjectionMatrix();
          }});
          resizeObserver.observe(root);

          applyTextureFrame(0);
          applySurface(0);
          updateCamera(0);
          renderer.render(scene, camera);
          requestAnimationFrame(renderFrame);
        </script>
        """
    ).strip()
