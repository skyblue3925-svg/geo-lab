from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
GALLERY_SOURCE = ROOT / "pages" / "1_📖_Gallery.py"
SHOWCASE_SOURCE = ROOT / "app" / "utils" / "gallery_showcase.py"


def test_gallery_renders_3d_preview_before_expensive_card_grid():
    source = GALLERY_SOURCE.read_text(encoding="utf-8")

    preview_pos = source.index('st.markdown("### 선택한 예시 미리보기")')
    card_grid_pos = source.index('st.markdown("### 수업용 예시")')

    assert preview_pos < card_grid_pos


def test_gallery_avoids_new_streamlit_stretch_width_api():
    source = GALLERY_SOURCE.read_text(encoding="utf-8")

    assert 'width="stretch"' not in source


def test_gallery_intro_copy_is_korean():
    source = GALLERY_SOURCE.read_text(encoding="utf-8")

    assert "High School Lesson Catalog" not in source
    assert "Preview unavailable" not in source


def test_gallery_catalog_mode_uses_fast_static_3d_preview():
    source = GALLERY_SOURCE.read_text(encoding="utf-8")
    catalog_block = source[
        source.index("    if is_catalog_mode:") : source.index("    else:", source.index("    if is_catalog_mode:"))
    ]

    assert 'animation_mode = "수동 단계"' in catalog_block


def test_gallery_card_grid_does_not_block_first_3d_render_with_thumbnails():
    source = GALLERY_SOURCE.read_text(encoding="utf-8")
    card_grid_block = source[source.index('st.markdown("### 수업용 예시")') :]

    assert "build_landform_thumbnail(" not in card_grid_block


def test_gallery_cinematic_media_is_opt_in_to_keep_first_tab_fast():
    source = GALLERY_SOURCE.read_text(encoding="utf-8")

    assert "show_cinematic_media = st.checkbox(" in source
    assert '"시네마틱 파일 미리보기 로드"' in source
    assert "value=False" in source


def test_gallery_showcase_labels_are_korean():
    source = SHOWCASE_SOURCE.read_text(encoding="utf-8")

    for english_label in (
        "River Systems",
        "Delta Showcase",
        "Glacial Forms",
        "Volcanic Relief",
        "Karst Landscapes",
        "Arid Terrain",
        "Coastal Change",
    ):
        assert english_label not in source
