from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def _read_page(name_fragment: str) -> tuple[Path, str]:
    pages_dir = ROOT / "pages"
    page_path = next(path for path in pages_dir.iterdir() if name_fragment in path.name)
    return page_path, page_path.read_text(encoding="utf-8").lstrip("\ufeff")


def test_gallery_page_source_compiles():
    page_path, source = _read_page("Gallery.py")
    compile(source, str(page_path), "exec")


def test_overview_page_source_compiles():
    page_path, source = _read_page("Overview.py")
    compile(source, str(page_path), "exec")


def test_lab_page_source_compiles():
    page_path, source = _read_page("Lab.py")
    compile(source, str(page_path), "exec")


def test_research_page_source_compiles():
    page_path, source = _read_page("Research.py")
    compile(source, str(page_path), "exec")


def test_home_view_source_compiles():
    module_path = ROOT / "app" / "home_view.py"
    source = module_path.read_text(encoding="utf-8").lstrip("\ufeff")
    compile(source, str(module_path), "exec")


def test_higher_ed_page_source_compiles():
    page_path, source = _read_page("Higher_Ed.py")
    compile(source, str(page_path), "exec")


def test_high_school_world_geography_page_source_compiles():
    page_path, source = _read_page("High_School_Geography.py")
    compile(source, str(page_path), "exec")
