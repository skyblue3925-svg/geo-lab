"""
지형 생성기 스모크 테스트

갤러리 해상도 슬라이더(30~200)와 형성 단계(0~1) 조합에서
모든 생성기가 예외 없이 올바른 크기의 배열을 돌려주는지 확인한다.
(카렌·용암대지가 특정 해상도에서 ZeroDivisionError 로 멈추던 회귀 방지)
"""
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.getcwd())

from engine.ideal_landforms import ANIMATED_LANDFORM_GENERATORS, IDEAL_LANDFORM_GENERATORS

GRID_SIZES = (30, 50, 60, 70, 100)
STAGES = (0.0, 0.5, 0.6, 1.0)


class TestGeneratorsSmoke(unittest.TestCase):
    def test_static_generators(self):
        for key, fn in IDEAL_LANDFORM_GENERATORS.items():
            for gs in GRID_SIZES:
                with self.subTest(landform=key, grid=gs):
                    elev = np.asarray(fn(gs))
                    self.assertEqual(elev.shape, (gs, gs))
                    self.assertTrue(np.isfinite(elev).all())

    def test_animated_generators(self):
        for key, fn in ANIMATED_LANDFORM_GENERATORS.items():
            for gs in GRID_SIZES:
                for st in STAGES:
                    with self.subTest(landform=key, grid=gs, stage=st):
                        result = fn(gs, st)
                        elev = np.asarray(result[0] if isinstance(result, tuple) else result)
                        self.assertEqual(elev.shape, (gs, gs))
                        self.assertTrue(np.isfinite(elev).all())


if __name__ == "__main__":
    unittest.main()
