import numpy as np

from engine.analysis import HypsometricResult, ProfileResult, calculate_hypsometric_curve
from app.utils.research_compare import (
    align_reference_dem,
    build_research_comparison_report,
    build_research_comparison_summary,
    compute_profile_error_stats,
    export_comparison_report_markdown_bytes,
    export_profile_comparison_csv_bytes,
    summarize_hypsometric_difference,
)


def _make_profile(elevation):
    elevation = np.asarray(elevation, dtype=float)
    return ProfileResult(
        distance=np.arange(elevation.size, dtype=float),
        elevation=elevation,
        slope=np.zeros(elevation.size, dtype=float),
        points=[(0, idx) for idx in range(elevation.size)],
    )


def _make_hypso(hi):
    return HypsometricResult(
        relative_area=np.array([0.0, 1.0]),
        relative_elevation=np.array([1.0, 0.0]),
        hypsometric_integral=float(hi),
        stage="Synthetic",
    )


def test_align_reference_dem_resamples_to_target_shape():
    target = np.zeros((4, 4), dtype=float)
    reference = np.array([[0.0, 1.0], [2.0, 3.0]], dtype=float)

    aligned = align_reference_dem(target, reference)

    assert aligned.shape == target.shape
    assert np.isclose(aligned[0, 0], 0.0)
    assert np.isclose(aligned[-1, -1], 3.0)


def test_summarize_hypsometric_difference_covers_all_branches():
    assert summarize_hypsometric_difference(0.0) == "\ub450 DEM\uc758 \uc0c1\ub300 \uace0\ub3c4-\uba74\uc801 \ubd84\ud3ec\uac00 \uac70\uc758 \uac19\uc2b5\ub2c8\ub2e4."
    assert "\ub192\uc740 \uc9c0\ub300" in summarize_hypsometric_difference(0.05)
    assert "\ub354 \uce68\uc2dd" in summarize_hypsometric_difference(-0.05)


def test_compute_profile_error_stats_returns_rmse_mae_and_peak():
    current = _make_profile([1.0, 3.0, 5.0])
    reference = _make_profile([0.0, 1.0, 4.0])

    stats = compute_profile_error_stats(current, reference)

    np.testing.assert_allclose(stats["error"], np.array([1.0, 2.0, 1.0]))
    assert np.isclose(stats["rmse"], np.sqrt(2.0))
    assert np.isclose(stats["mae"], 4.0 / 3.0)
    assert np.isclose(stats["peak_abs_error"], 2.0)


def test_build_research_comparison_summary_includes_new_profile_metrics_and_brief():
    cross_stats = {"rmse": 1.2, "mae": 0.8, "peak_abs_error": 2.3}
    long_stats = {"rmse": 1.5, "mae": 1.0, "peak_abs_error": 2.8}

    summary = build_research_comparison_summary(
        reference_name="reference.asc",
        reference_shape=(32, 24),
        reference_cell_size=5.0,
        stats_cmp={"mean_diff": 0.2, "rmse": 1.1, "mae": 0.9, "correlation": 0.95},
        current_hypso=_make_hypso(0.62),
        reference_hypso=_make_hypso(0.55),
        cross_stats=cross_stats,
        long_stats=long_stats,
        compare_cross_row=10,
        compare_long_col=12,
    )

    assert summary["reference_name"] == "reference.asc"
    assert summary["reference_shape"] == [32, 24]
    assert summary["cross_section_row"] == 10
    assert summary["longitudinal_col"] == 12
    assert np.isclose(summary["hi_diff"], 0.07)
    assert summary["cross_profile_mae"] == cross_stats["mae"]
    assert summary["long_profile_peak_abs_error"] == long_stats["peak_abs_error"]
    assert "\ub192\uc740 \uc9c0\ub300" in summary["hi_message"]
    assert len(summary["brief"]) == 4


def test_export_profile_comparison_csv_bytes_contains_cross_and_long_rows():
    cross_current = _make_profile([1.0, 2.0])
    cross_reference = _make_profile([0.5, 1.5])
    long_current = _make_profile([3.0, 4.0])
    long_reference = _make_profile([2.5, 3.5])

    csv_bytes = export_profile_comparison_csv_bytes(
        cross_current=cross_current,
        cross_reference=cross_reference,
        cross_error=np.array([0.5, 0.5]),
        long_current=long_current,
        long_reference=long_reference,
        long_error=np.array([0.5, 0.5]),
    )
    csv_text = csv_bytes.decode("utf-8")

    assert "axis,index,distance_m,current_elevation,reference_elevation,error" in csv_text
    assert "cross,0,0.0,1.0,0.5,0.5" in csv_text
    assert "long,1,1.0,4.0,3.5,0.5" in csv_text


def test_calculate_hypsometric_curve_runs_on_current_numpy():
    elevation = np.array([[0.0, 1.0], [2.0, 3.0]], dtype=float)

    result = calculate_hypsometric_curve(elevation)

    assert 0.0 <= result.hypsometric_integral <= 1.0
    assert result.stage


def test_build_research_comparison_report_includes_alignment_limitations():
    cross_stats = {"rmse": 1.2, "mae": 0.8, "peak_abs_error": 2.3, "bias": 0.1, "normalized_rmse": 0.12}
    long_stats = {"rmse": 1.5, "mae": 1.0, "peak_abs_error": 2.8, "bias": -0.2, "normalized_rmse": 0.15}
    summary = build_research_comparison_summary(
        reference_name="reference.asc",
        reference_shape=(32, 24),
        reference_cell_size=5.0,
        stats_cmp={"mean_diff": 0.2, "rmse": 1.1, "mae": 0.9, "correlation": 0.95, "normalized_rmse": 0.08},
        current_hypso=_make_hypso(0.62),
        reference_hypso=_make_hypso(0.55),
        cross_stats=cross_stats,
        long_stats=long_stats,
        compare_cross_row=10,
        compare_long_col=12,
    )

    report = build_research_comparison_report(
        summary=summary,
        stats_cmp={
            "mean_diff": 0.2,
            "rmse": 1.1,
            "mae": 0.9,
            "correlation": 0.95,
            "normalized_rmse": 0.08,
            "bias": 0.2,
            "current_range": 12.0,
            "reference_range": 15.0,
            "valid_ratio": 0.97,
        },
        current_hypso=_make_hypso(0.62),
        reference_hypso=_make_hypso(0.55),
        cross_stats=cross_stats,
        long_stats=long_stats,
        current_shape=(40, 40),
        current_cell_size=10.0,
        reference_shape=(32, 24),
        reference_cell_size=5.0,
    )

    assert report["limitations"]
    assert "bilinear resampling" in report["limitations"][0]
    markdown = export_comparison_report_markdown_bytes(report).decode("utf-8")
    assert "## Limitations" in markdown
    assert "Cell size mismatch" in markdown
