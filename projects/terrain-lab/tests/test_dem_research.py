import numpy as np

from app.services.dem_research import (
    analyze_dem_surface,
    dem_research_cards,
    load_csv_dem,
    normalize_dem_layer,
    process_hints_from_dem,
    resample_dem,
)


def test_load_csv_dem_parses_missing_values_as_nan():
    dem = load_csv_dem("10,11,12\n9,,7\n6,nan,4\n")

    assert dem.shape == (3, 3)
    assert np.isnan(dem[1, 1])
    assert np.isnan(dem[2, 1])
    assert dem[0, 0] == 10


def test_resample_dem_returns_engine_safe_shape_and_preserves_range():
    source = np.array([[10.0, 8.0], [6.0, 4.0]])

    resampled = resample_dem(source, 4)

    assert resampled.shape == (16, 16)
    assert float(np.nanmax(resampled)) <= 10.0
    assert float(np.nanmin(resampled)) >= 4.0


def test_analyze_dem_surface_returns_slope_curvature_and_drainage():
    dem = np.array(
        [
            [10.0, 9.0, 8.0],
            [9.0, 8.0, 7.0],
            [8.0, 7.0, 6.0],
        ]
    )

    analysis = analyze_dem_surface(dem)

    assert analysis["slope"].shape == dem.shape
    assert analysis["curvature"].shape == dem.shape
    assert analysis["drainage_area"].shape == dem.shape
    assert float(analysis["slope"].max()) > 0
    assert float(analysis["drainage_area"].max()) > float(analysis["drainage_area"].mean())
    assert analysis["summary"]["relief"] == 4.0


def test_dem_research_cards_and_hints_are_ui_safe():
    dem = np.array(
        [
            [12.0, 10.0, 8.0, 7.0],
            [11.0, 9.0, 6.0, 5.0],
            [10.0, 7.0, 4.0, 3.0],
            [9.0, 6.0, 3.0, 1.0],
        ]
    )
    analysis = analyze_dem_surface(dem)

    cards = dem_research_cards(analysis)
    hints = process_hints_from_dem(analysis)
    normalized_slope = normalize_dem_layer(analysis, "slope")

    assert len(cards) == 4
    assert all(card[0] and card[1] and card[2] for card in cards)
    assert hints
    assert normalized_slope.shape == dem.shape
    assert 0.0 <= float(normalized_slope.min()) <= float(normalized_slope.max()) <= 1.0


def test_normalize_dem_layer_rejects_unknown_layer():
    analysis = analyze_dem_surface(np.arange(16, dtype=float).reshape(4, 4))

    try:
        normalize_dem_layer(analysis, "unknown")
    except KeyError as exc:
        assert "Unknown DEM layer" in str(exc)
    else:
        raise AssertionError("normalize_dem_layer should reject unknown keys")
