from PIL import Image

from scripts.import_filmstrip_sequence import (
    default_fps_for_frame_count,
    infer_filmstrip_grid,
    split_filmstrip,
)


def make_five_by_five_filmstrip() -> Image.Image:
    image = Image.new("RGB", (1536, 1024), (80, 120, 90))
    draw_color = (255, 255, 255)
    for col in range(1, 5):
        x = round(col * image.width / 5)
        for offset in range(-1, 2):
            for y in range(image.height):
                image.putpixel((x + offset, y), draw_color)
    for row in range(1, 5):
        y = round(row * image.height / 5)
        for offset in range(-1, 2):
            for x in range(image.width):
                image.putpixel((x, y + offset), draw_color)
    return image


def test_infers_five_by_five_grid_from_generated_filmstrip_separators():
    image = make_five_by_five_filmstrip()

    assert infer_filmstrip_grid(image) == (5, 5)


def test_auto_split_keeps_twenty_five_panel_cells_separate():
    colors = [
        ((index * 37) % 255, (index * 67) % 255, (index * 97) % 255)
        for index in range(25)
    ]
    filmstrip = Image.new("RGB", (1536, 1024), (255, 255, 255))
    for index, color in enumerate(colors):
        col = index % 5
        row = index // 5
        left = round(col * filmstrip.width / 5) + 2
        top = round(row * filmstrip.height / 5) + 2
        right = round((col + 1) * filmstrip.width / 5) - 2
        bottom = round((row + 1) * filmstrip.height / 5) - 2
        tile = Image.new("RGB", (right - left, bottom - top), color)
        filmstrip.paste(tile, (left, top))
    path = "tests/.tmp_twenty_five_panel.png"
    try:
        filmstrip.save(path)
        frames = split_filmstrip(path, cols=None, rows=None, trim_px=0, target_size=128)
    finally:
        import os

        if os.path.exists(path):
            os.remove(path)

    assert len(frames) == 25
    assert [frame.getpixel((64, 64)) for frame in frames] == colors


def test_six_panel_contact_sheets_default_to_slower_teaching_fps():
    assert default_fps_for_frame_count(6) == 2
    assert default_fps_for_frame_count(25) == 7
