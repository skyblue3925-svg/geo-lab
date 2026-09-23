"""
학습 스펙 검증 테스트

- 번들된 스펙이 모두 schema 검증을 통과하는가
- 각 레벨의 단계에서 엔진이 지형을 만들어 내는가
- slider_target 과제가 범위 시작에서는 실패하고 범위 끝에서는 통과하는가
  (시작부터 통과하면 학생이 슬라이더를 움직일 이유가 없다)
"""
import os
import sys
import unittest

sys.path.insert(0, os.getcwd())

from learning import (
    validate_spec, load_spec, list_specs, generate_stage, evaluate_check, available_landforms,
    describe_check_keys,
)

GRID = 60
# 학습 페이지 해상도 슬라이더(30~120) 범위에서 판정이 달라지면 안 된다.
CHECK_GRIDS = (40, 60, 100)


class TestLearningSpecs(unittest.TestCase):
    def setUp(self):
        self.specs = {sid: load_spec(p) for sid, p in list_specs().items()}
        self.assertGreaterEqual(len(self.specs), 3, "번들 스펙이 3개 이상 있어야 합니다.")

    def test_all_specs_validate(self):
        known = available_landforms()
        for sid, spec in self.specs.items():
            errors = validate_spec(spec, known_landforms=known)
            self.assertEqual(errors, [], f"{sid}: {errors}")
            self.assertEqual(spec["id"], sid, f"{sid}: id 가 파일명과 달라요")

    def test_levels_render(self):
        for sid, spec in self.specs.items():
            for level in spec["levels"]:
                stages = [level["stage"]] if "stage" in level else level["stage_range"]
                for s in stages:
                    elev, meta = generate_stage(spec["landform"], GRID, s, spec.get("generator"))
                    self.assertEqual(elev.shape, (GRID, GRID), f"{sid}/{level['id']} @ {s}")
                    self.assertIn("_stage", meta)

    def test_slider_targets_need_movement(self):
        for sid, spec in self.specs.items():
            for level in spec["levels"]:
                task = level["task"]
                if task["type"] != "slider_target":
                    continue
                lo, hi = level["stage_range"]
                for grid in CHECK_GRIDS:
                    where = f"{sid}/{level['id']} @ 해상도 {grid}"
                    _, meta_lo = generate_stage(spec["landform"], grid, lo, spec.get("generator"))
                    _, meta_hi = generate_stage(spec["landform"], grid, hi, spec.get("generator"))
                    ok_lo, why_lo = evaluate_check(task["check"], meta_lo)
                    ok_hi, why_hi = evaluate_check(task["check"], meta_hi)
                    self.assertFalse(ok_lo, f"{where}: 범위 시작에서 이미 통과 ({why_lo})")
                    self.assertTrue(ok_hi, f"{where}: 범위 끝에서도 실패 ({why_hi})")

    def test_slider_pass_point_is_resolution_independent(self):
        """같은 슬라이더 과제가 해상도에 따라 통과 시점이 크게 달라지면 안 된다."""
        for sid, spec in self.specs.items():
            for level in spec["levels"]:
                if level["task"]["type"] != "slider_target":
                    continue
                lo, hi = level["stage_range"]
                steps = [round(lo + i * 0.02, 2) for i in range(int(round((hi - lo) / 0.02)) + 1)]
                first_pass = {}
                for grid in CHECK_GRIDS:
                    for s in steps:
                        _, meta = generate_stage(spec["landform"], grid, s, spec.get("generator"))
                        if evaluate_check(level["task"]["check"], meta)[0]:
                            first_pass[grid] = s
                            break
                spread = max(first_pass.values()) - min(first_pass.values())
                self.assertLessEqual(spread, 0.1, f"{sid}/{level['id']}: 해상도별 통과 시점 {first_pass}")

    def test_validator_catches_broken_spec(self):
        spec = load_spec(list_specs()["alluvial_fan_basic"])
        spec["levels"][0]["task"]["answer"] = 99
        spec["levels"][1]["stage_range"] = [0.9, 0.1]
        errors = validate_spec(spec)
        self.assertTrue(any("answer" in e for e in errors))
        self.assertTrue(any("stage_range" in e for e in errors))

    def test_terrain_metrics_available_everywhere(self):
        """메타데이터가 없는 지형도 공통 판정값을 받는다."""
        for lf in ("karren", "uvala", "tower_karst", "estuary"):
            _, meta = generate_stage(lf, GRID, 1.0)
            for key in ("relief", "max_elevation", "min_elevation", "water_fraction"):
                self.assertIn(key, meta, f"{lf}: {key} 없음")

    def test_describe_check_keys(self):
        rows = {r["key"]: r for r in describe_check_keys("ria_coast")}
        self.assertIn("flooded_valleys", rows)
        self.assertEqual(rows["flooded_valleys"]["values"], [1.0, 3.0, 5.0])
        self.assertFalse(rows["flooded_valleys"]["resolution_dependent"])
        self.assertTrue(rows["water_fraction"]["resolution_dependent"])
        self.assertNotIn("num_valleys", rows, "단계에 따라 변하지 않는 키는 빠져야 함")
        self.assertNotIn("stage_description", rows)

    def test_check_ops(self):
        meta = {"flag": True, "n": 2.0, "arr": [1, 2, 3], "items": ["a"]}
        self.assertTrue(evaluate_check({"key": "flag", "op": "truthy"}, meta)[0])
        self.assertTrue(evaluate_check({"key": "n", "op": "gte", "value": 1.5}, meta)[0])
        self.assertFalse(evaluate_check({"key": "n", "op": "lte", "value": 1.5}, meta)[0])
        self.assertTrue(evaluate_check({"key": "arr", "op": "contains", "value": 3}, meta)[0])
        self.assertTrue(evaluate_check({"key": "items", "op": "len_gte", "value": 1}, meta)[0])
        self.assertFalse(evaluate_check({"key": "missing", "op": "truthy"}, meta)[0])


if __name__ == "__main__":
    unittest.main()
