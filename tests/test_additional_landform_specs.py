import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

EXPECTED_ADDITIONAL_IDS = {
    "oxbow_lake",
    "floodplain_natural_levee",
    "river_terrace",
    "sea_cave_stack",
    "wave_cut_platform",
    "barrier_island",
    "moraine",
    "drumlin",
    "esker",
    "maar",
    "lava_dome",
    "polje",
    "tidal_flat",
    "marine_terrace",
    "kettle_lake",
    "outwash_plain",
    "thermokarst",
    "cinder_cone",
}


def test_additional_landform_specs_are_registered():
    specs = json.loads((ROOT / "docs" / "TERRAIN_ADDITIONAL_IMAGE_SEQUENCE_SPECS.json").read_text(encoding="utf-8"))
    landforms = specs["landforms"]
    ids = {landform["id"] for landform in landforms}

    assert ids == EXPECTED_ADDITIONAL_IDS

    from app.services.animation_assets import landform_group_id_for_landform, title_for_landform
    from engine.ideal_landforms import ANIMATED_LANDFORM_GENERATORS, IDEAL_LANDFORM_GENERATORS

    for landform in landforms:
        landform_id = landform["id"]
        assert title_for_landform(landform_id) == landform["title_ko"]
        assert landform_group_id_for_landform(landform_id) == landform["group"]
        assert landform_id in ANIMATED_LANDFORM_GENERATORS
        assert landform_id in IDEAL_LANDFORM_GENERATORS


def test_additional_landform_3d_payloads_are_visible():
    from app.services.terrain_3d_payload import build_terrain_3d_payload

    for landform_id in sorted(EXPECTED_ADDITIONAL_IDS):
        payload = build_terrain_3d_payload(landform_id, grid_size=16, frame_count=3)

        assert payload["landformId"] == landform_id
        assert payload["surfaceFrameCount"] == 3
        assert max(payload["surfaceFrames"][-1]) > 0.0
