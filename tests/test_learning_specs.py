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
)

GRID = 60


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
                _, meta_lo = generate_stage(spec["landform"], GRID, lo, spec.get("generator"))
                _, meta_hi = generate_stage(spec["landform"], GRID, hi, spec.get("generator"))
                ok_lo, why_lo = evaluate_check(task["check"], meta_lo)
                ok_hi, why_hi = evaluate_check(task["check"], meta_hi)
                self.assertFalse(ok_lo, f"{sid}/{level['id']}: 범위 시작에서 이미 통과 ({why_lo})")
                self.assertTrue(ok_hi, f"{sid}/{level['id']}: 범위 끝에서도 실패 ({why_hi})")

    def test_validator_catches_broken_spec(self):
        spec = load_spec(list_specs()["alluvial_fan_basic"])
        spec["levels"][0]["task"]["answer"] = 99
        spec["levels"][1]["stage_range"] = [0.9, 0.1]
        errors = validate_spec(spec)
        self.assertTrue(any("answer" in e for e in errors))
        self.assertTrue(any("stage_range" in e for e in errors))

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
