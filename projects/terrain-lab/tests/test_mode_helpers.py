import pytest

from app.utils.mode_helpers import describe_learning_stage


@pytest.mark.parametrize(
    ("progress", "expected_title"),
    [
        (0.00, "1단계: 초기 조건"),
        (0.30, "2단계: 변화 시작"),
        (0.60, "3단계: 형태 강화"),
        (0.95, "4단계: 결과 해석"),
    ],
)
def test_describe_learning_stage_exposes_caption_focus_and_question(progress, expected_title):
    result = describe_learning_stage(progress)

    assert result["title"] == expected_title
    assert result["caption"]
    assert result["focus"]
    assert result["question"]
    assert result["summary"]


def test_describe_learning_stage_clamps_out_of_range_progress():
    early = describe_learning_stage(-1)
    late = describe_learning_stage(2)

    assert early["title"] == "1단계: 초기 조건"
    assert late["title"] == "4단계: 결과 해석"
