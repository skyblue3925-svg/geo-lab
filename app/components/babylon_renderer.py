"""Babylon.js-based experimental terrain viewer for image-sequence assets."""

from __future__ import annotations

import json
from textwrap import dedent
from typing import Any

from app.services.animation_assets import (
    StoryboardAsset,
    get_landform_asset_bundle,
    read_image_data_uri,
)
from app.services.terrain_3d_payload import build_terrain_3d_payload


def create_babylon_terrain_viewer_html(
    asset: StoryboardAsset,
    *,
    viewer_height: int = 640,
    grid_size: int = 48,
    surface_frames: int = 10,
    terrain_payload: dict[str, Any] | None = None,
) -> str | None:
    bundle = get_landform_asset_bundle(asset.landform_id)
    if bundle is None:
        return None

    filmstrip_path = bundle.get("filmstrip_path")
    if filmstrip_path is None or not filmstrip_path.exists():
        return None

    entry = bundle.get("image_sequence_entry") or {}
    if terrain_payload is None:
        terrain_payload = build_terrain_3d_payload(
            asset.landform_id,
            grid_size=grid_size,
            frame_count=surface_frames,
        )
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
    payload.update(terrain_payload)
    payload["title"] = asset.title

    config_json = json.dumps(payload, ensure_ascii=False)
    return dedent(
        f"""
        <div id="babylon-terrain-root" style="width:100%;height:{viewer_height}px;position:relative;overflow:hidden;background:#020617;border-radius:6px;">
          <div id="babylon-terrain-label" style="position:absolute;left:16px;top:14px;z-index:5;color:#e2e8f0;font:600 14px/1.4 system-ui,sans-serif;letter-spacing:0;">
            Babylon.js 실험 지형 뷰어
          </div>
          <div id="babylon-terrain-meta" style="position:absolute;left:16px;top:36px;z-index:5;color:#94a3b8;font:12px/1.4 system-ui,sans-serif;">
            이미지 시퀀스 필름스트립 + 샘플 지형 높이장
          </div>
          <div id="babylon-terrain-stage" style="position:absolute;right:16px;top:14px;z-index:5;color:#e2e8f0;font:600 13px/1.4 system-ui,sans-serif;"></div>
          <canvas id="babylon-terrain-canvas" style="display:block;width:100%;height:100%;touch-action:none;"></canvas>
        </div>
        <script src="https://cdn.babylonjs.com/babylon.js"></script>
        <script>
          (() => {{
            const payload = {config_json};
            const root = document.getElementById("babylon-terrain-root");
            const canvas = document.getElementById("babylon-terrain-canvas");
            const stageLabel = document.getElementById("babylon-terrain-stage");

            const engine = new BABYLON.Engine(canvas, true, {{
              preserveDrawingBuffer: true,
              stencil: true,
            }});
            engine.setHardwareScalingLevel(Math.max(1, 1 / Math.min(window.devicePixelRatio || 1, 2)));

            const scene = new BABYLON.Scene(engine);
            scene.clearColor = new BABYLON.Color4(0.01, 0.02, 0.06, 1);
            scene.fogMode = BABYLON.Scene.FOGMODE_LINEAR;
            scene.fogColor = new BABYLON.Color3(0.01, 0.02, 0.06);
            scene.fogStart = 90;
            scene.fogEnd = 180;

            const camera = new BABYLON.ArcRotateCamera(
              "terrainCamera",
              -Math.PI * 0.38,
              Math.PI * 0.34,
              92,
              new BABYLON.Vector3(0, 9, 0),
              scene,
            );
            camera.lowerRadiusLimit = 58;
            camera.upperRadiusLimit = 132;
            camera.lowerBetaLimit = Math.PI * 0.18;
            camera.upperBetaLimit = Math.PI * 0.48;
            camera.wheelPrecision = 42;
            camera.panningSensibility = 0;
            camera.attachControl(canvas, true);

            const ambientLight = new BABYLON.HemisphericLight("ambientLight", new BABYLON.Vector3(0, 1, 0), scene);
            ambientLight.intensity = 0.72;
            ambientLight.groundColor = new BABYLON.Color3(0.08, 0.13, 0.19);

            const keyLight = new BABYLON.DirectionalLight("keyLight", new BABYLON.Vector3(-0.45, -0.9, -0.35), scene);
            keyLight.position = new BABYLON.Vector3(32, 54, 24);
            keyLight.intensity = 1.65;

            const rimLight = new BABYLON.DirectionalLight("rimLight", new BABYLON.Vector3(0.6, -0.45, 0.45), scene);
            rimLight.position = new BABYLON.Vector3(-32, 24, -28);
            rimLight.diffuse = new BABYLON.Color3(0.52, 0.73, 1);
            rimLight.intensity = 0.42;

            const gridSize = payload.gridSize;
            const planeSize = 82;
            const halfSize = planeSize / 2;
            const positions = [];
            const normals = [];
            const uvs = [];
            const indices = [];

            for (let z = 0; z < gridSize; z += 1) {{
              for (let x = 0; x < gridSize; x += 1) {{
                const u = x / (gridSize - 1);
                const v = z / (gridSize - 1);
                positions.push((u * planeSize) - halfSize, 0, (v * planeSize) - halfSize);
                normals.push(0, 1, 0);
                uvs.push(u, 1 - v);
              }}
            }}

            for (let z = 0; z < gridSize - 1; z += 1) {{
              for (let x = 0; x < gridSize - 1; x += 1) {{
                const a = z * gridSize + x;
                const b = a + 1;
                const c = a + gridSize;
                const d = c + 1;
                indices.push(a, c, b, b, c, d);
              }}
            }}

            const terrainVertexData = new BABYLON.VertexData();
            terrainVertexData.positions = positions;
            terrainVertexData.normals = normals;
            terrainVertexData.uvs = uvs;
            terrainVertexData.indices = indices;

            const terrainMesh = new BABYLON.Mesh("terrainMesh", scene);
            terrainVertexData.applyToMesh(terrainMesh, true);

            const filmstripTexture = new BABYLON.Texture(payload.filmstripDataUri, scene, false, true, BABYLON.Texture.TRILINEAR_SAMPLINGMODE);
            filmstripTexture.wrapU = BABYLON.Texture.CLAMP_ADDRESSMODE;
            filmstripTexture.wrapV = BABYLON.Texture.CLAMP_ADDRESSMODE;
            filmstripTexture.uScale = 1 / payload.filmstripCols;
            filmstripTexture.vScale = 1 / payload.filmstripRows;
            filmstripTexture.uOffset = 0;
            filmstripTexture.vOffset = 1 - (1 / payload.filmstripRows);

            const processOverlayTexture = new BABYLON.DynamicTexture(
              "processOverlayTexture",
              {{ width: payload.gridSize, height: payload.gridSize }},
              scene,
              false,
            );
            const processOverlayContext = processOverlayTexture.getContext();

            const terrainMaterial = new BABYLON.StandardMaterial("terrainMaterial", scene);
            terrainMaterial.diffuseTexture = filmstripTexture;
            terrainMaterial.emissiveTexture = processOverlayTexture;
            terrainMaterial.emissiveColor = new BABYLON.Color3(0.42, 0.42, 0.42);
            terrainMaterial.specularColor = new BABYLON.Color3(0.03, 0.04, 0.05);
            terrainMaterial.roughness = 0.96;
            terrainMaterial.backFaceCulling = false;
            terrainMesh.material = terrainMaterial;

            const waterMesh = BABYLON.MeshBuilder.CreateDisc("waterPlane", {{ radius: 42, tessellation: 96 }}, scene);
            waterMesh.rotation.x = Math.PI / 2;
            waterMesh.position.y = -1.8;
            const waterMaterial = new BABYLON.StandardMaterial("waterMaterial", scene);
            waterMaterial.diffuseColor = new BABYLON.Color3(0.09, 0.28, 0.43);
            waterMaterial.emissiveColor = new BABYLON.Color3(0.01, 0.04, 0.07);
            waterMaterial.alpha = 0.22;
            waterMaterial.specularColor = new BABYLON.Color3(0.55, 0.75, 0.9);
            waterMesh.material = waterMaterial;

            const surfaceFrames = payload.surfaceFrames;
            const waterDepthFrames = payload.waterDepthFrames || [];
            const erosionFrames = payload.erosionFrames || [];
            const depositionFrames = payload.depositionFrames || [];
            const processLabels = payload.processLabels || [];
            const surfaceFrameCount = Math.max(payload.surfaceFrameCount || 1, 1);
            const textureFrameCount = Math.max(payload.textureFrameCount || 1, 1);

            function applyTextureFrame(frameIndex) {{
              const cellIndex = ((frameIndex % textureFrameCount) + textureFrameCount) % textureFrameCount;
              const col = cellIndex % payload.filmstripCols;
              const row = Math.floor(cellIndex / payload.filmstripCols);
              filmstripTexture.uOffset = col / payload.filmstripCols;
              filmstripTexture.vOffset = 1 - ((row + 1) / payload.filmstripRows);
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
                positions[i * 3 + 1] = ((surfaceA[i] * (1 - t)) + (surfaceB[i] * t)) * payload.heightScale;
              }}
              BABYLON.VertexData.ComputeNormals(positions, indices, normals);
              terrainMesh.updateVerticesData(BABYLON.VertexBuffer.PositionKind, positions);
              terrainMesh.updateVerticesData(BABYLON.VertexBuffer.NormalKind, normals);
              terrainMesh.refreshBoundingInfo();
            }}

            function pickProcessFrame(frameSet, frameIndex) {{
              if (!Array.isArray(frameSet) || frameSet.length === 0) return [];
              return frameSet[Math.max(0, Math.min(frameSet.length - 1, frameIndex))] || [];
            }}

            function paintProcessOverlay(surfaceIndex) {{
              const water = pickProcessFrame(waterDepthFrames, surfaceIndex);
              const erosion = pickProcessFrame(erosionFrames, surfaceIndex);
              const deposition = pickProcessFrame(depositionFrames, surfaceIndex);
              const imageData = processOverlayContext.createImageData(payload.gridSize, payload.gridSize);
              for (let i = 0; i < payload.gridSize * payload.gridSize; i += 1) {{
                const w = Math.max(0, Math.min(1, Number(water[i] || 0)));
                const e = Math.max(0, Math.min(1, Number(erosion[i] || 0)));
                const d = Math.max(0, Math.min(1, Number(deposition[i] || 0)));
                const signal = Math.max(w, e, d);
                imageData.data[i * 4] = Math.min(255, Math.round((e * 235) + (d * 224) + (w * 32)));
                imageData.data[i * 4 + 1] = Math.min(255, Math.round((e * 82) + (d * 184) + (w * 150)));
                imageData.data[i * 4 + 2] = Math.min(255, Math.round((e * 52) + (d * 78) + (w * 255)));
                imageData.data[i * 4 + 3] = Math.round(signal * 180);
              }}
              processOverlayContext.putImageData(imageData, 0, 0);
              processOverlayTexture.update(false);
            }}

            function renderFrame() {{
              const elapsedMs = performance.now();
              const texturePlayhead = (elapsedMs / 1000) * payload.fps;
              const textureFrame = Math.floor(texturePlayhead) % textureFrameCount;
              const normalizedPlayhead = (textureFrameCount <= 1) ? 0 : (textureFrame / (textureFrameCount - 1));
              const surfaceIndex = Math.round(normalizedPlayhead * (surfaceFrameCount - 1));

              applyTextureFrame(textureFrame);
              applySurface(normalizedPlayhead);
              paintProcessOverlay(surfaceIndex);
              const processLabel = processLabels[surfaceIndex % Math.max(processLabels.length, 1)] || "지형 변화";
              stageLabel.textContent = `${{payload.title}} | frame ${{String(textureFrame + 1).padStart(2, "0")}} / ${{textureFrameCount}} | ${{processLabel}}`;
              scene.render();
            }}

            const resizeObserver = new ResizeObserver(() => {{
              engine.resize();
            }});
            resizeObserver.observe(root);

            applyTextureFrame(0);
            applySurface(0);
            paintProcessOverlay(0);
            scene.render();
            engine.runRenderLoop(renderFrame);
          }})();
        </script>
        """
    ).strip()
