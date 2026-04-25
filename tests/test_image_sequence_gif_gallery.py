from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def test_image_sequence_gif_assets_are_listed_after_build():
    from app.services.animation_assets import list_image_sequence_gif_assets

    assets = list_image_sequence_gif_assets()

    assert assets
    assert all(asset.gif_path.suffix == ".gif" for asset in assets)
    assert all(asset.gif_path.exists() for asset in assets)
    assert all(asset.source_webp_path.exists() for asset in assets)


def test_image_sequence_gif_assets_use_teaching_landform_groups():
    from app.services.animation_assets import list_image_sequence_gif_assets

    assets = list_image_sequence_gif_assets()
    categories = {asset.category for asset in assets}

    assert "하천 지형" in categories
    assert "빙하 지형" in categories
    assert "해안 지형" in categories
    assert "river_delta" not in categories
    assert "image_sequence" not in categories


def test_image_sequence_filmstrip_grid_uses_metadata():
    from app.services.animation_assets import image_sequence_grid_for_landform, load_storyboard_panel_image

    assert image_sequence_grid_for_landform("maar") == (6, 6, 36)
    assert load_storyboard_panel_image("maar", 1.0) is not None


def test_gif_gallery_page_and_sidebar_link_exist():
    page = ROOT / "pages" / "10_GIF_Gallery.py"
    nav = (ROOT / "app" / "beta_navigation.py").read_text(encoding="utf-8")

    assert page.exists()
    source = page.read_text(encoding="utf-8")
    assert "list_image_sequence_gif_assets" in source
    assert "GIF 갤러리" in source
    assert "st.container(border=True)" not in source
    assert "use_column_width=True" not in source
    assert 'width="stretch"' not in source
    assert "use_container_width=True" not in source
    assert "image_stretch(st," in source
    assert "ordered_landform_group_labels" in source
    assert "/GIF_Gallery" in nav
