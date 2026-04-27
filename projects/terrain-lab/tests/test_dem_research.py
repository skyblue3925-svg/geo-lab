import numpy as np

from app.services.dem_research import (
    analyze_dem_surface,
    compare_observed_modeled_dem,
    dem_research_cards,
    estimate_process_mix_from_dem,
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
    assert cards[0][0] == "기복"
    assert any("하천" in hint or "사면" in hint for hint in hints)
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


def test_compare_observed_modeled_dem_reports_error_fields():
    observed = np.array([[10.0, 9.0], [7.0, 5.0]])
    modeled = np.array([[9.0, 9.0], [8.0, 4.0]])

    comparison = compare_observed_modeled_dem(observed, modeled, target_size=16)

    assert comparison["difference"].shape == (16, 16)
    assert comparison["absolute_difference"].shape == (16, 16)
    assert comparison["summary"]["rmse"] > 0.0
    assert comparison["summary"]["mae"] > 0.0
    assert 0.0 <= comparison["summary"]["fit_score"] <= 1.0


def test_estimate_process_mix_from_dem_returns_ranked_processes():
    dem = np.array(
        [
            [20.0, 18.0, 15.0, 12.0],
            [19.0, 16.0, 12.0, 8.0],
            [16.0, 12.0, 7.0, 4.0],
            [12.0, 8.0, 4.0, 1.0],
        ]
    )
    analysis = analyze_dem_surface(dem)

    estimate = estimate_process_mix_from_dem(analysis)

    assert estimate["ranked_processes"]
    assert estimate["scores"]["fluvial"] >= 0.0
    assert estimate["scores"]["hillslope"] >= 0.0
    assert estimate["recommended_preset"]
    assert estimate["interpretation"]
    assert "우선 후보" in estimate["interpretation"]
