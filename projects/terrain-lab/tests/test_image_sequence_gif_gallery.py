from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def test_image_sequence_gif_assets_are_listed_after_build():
    from app.services.animation_assets import list_image_sequence_gif_assets

    assets = list_image_sequence_gif_assets()

    assert assets
    assert all(asset.gif_path.suffix == ".gif" for asset in assets)
    assert all(asset.gif_path.exists() for asset in assets)
    assert all(asset.source_webp_path.exists() for asset in assets)


def test_image_sequence_gif_assets_use_teaching_landform_groups():
    from app.services.animation_assets import LANDFORM_GROUP_LABELS, list_image_sequence_gif_assets

    assets = list_image_sequence_gif_assets()
    categories = {asset.category for asset in assets}

    assert LANDFORM_GROUP_LABELS["river"] in categories
    assert LANDFORM_GROUP_LABELS["glacial"] in categories
    assert LANDFORM_GROUP_LABELS["coastal"] in categories
    assert "river_delta" not in categories
    assert "image_sequence" not in categories


def test_image_sequence_filmstrip_grid_uses_metadata():
    from app.services.animation_assets import image_sequence_grid_for_landform, load_storyboard_panel_image

    assert image_sequence_grid_for_landform("maar") == (5, 6, 30)
    assert load_storyboard_panel_image("maar", 1.0) is not None


def test_gif_gallery_page_and_sidebar_link_exist():
    terrain_src = ROOT / "projects" / "terrain-lab" / "src"
    page = terrain_src / "pages" / "10_GIF_Gallery.py"
    nav = (terrain_src / "app" / "beta_navigation.py").read_text(encoding="utf-8")

    assert page.exists()
    source = page.read_text(encoding="utf-8")
    assert "list_image_sequence_gif_assets" in source
    assert "GIF" in source
    assert "st.container(border=True)" not in source
    assert "use_column_width=True" not in source
    assert 'width="stretch"' not in source
    assert "use_container_width=True" not in source
    assert "image_stretch(st," in source
    assert "ordered_landform_group_labels" in source
    assert "/GIF_Gallery" in nav
