from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def test_image_sequence_gif_assets_are_listed_after_build():
    from app.services.animation_assets import list_image_sequence_gif_assets

    assets = list_image_sequence_gif_assets()

    assert assets
    assert all(asset.gif_path.suffix == ".gif" for asset in assets)
    assert all(asset.gif_path.exists() for asset in assets)
    assert all(asset.source_webp_path.exists() for asset in assets)


def test_gif_gallery_page_and_sidebar_link_exist():
    page = ROOT / "pages" / "10_GIF_Gallery.py"
    nav = (ROOT / "app" / "beta_navigation.py").read_text(encoding="utf-8")

    assert page.exists()
    source = page.read_text(encoding="utf-8")
    assert "list_image_sequence_gif_assets" in source
    assert "GIF 갤러리" in source
    assert "st.container(border=True)" not in source
    assert "/GIF_Gallery" in nav
