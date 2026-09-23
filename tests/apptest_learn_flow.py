"""Streamlit AppTest 로 학습 페이지 흐름을 끝까지 걸어본다. 실행: python tests/apptest_learn_flow.py"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, os.getcwd())
from streamlit.testing.v1 import AppTest

PAGE = os.path.join(ROOT, "pages", "5_🎓_Learn.py")


def run(at):
    at.run(timeout=60)
    assert not at.exception, at.exception
    return at


def widget(at, kind, key):
    for w in getattr(at, kind):
        if w.key == key:
            return w
    raise KeyError(f"{kind} {key} not found; have {[w.key for w in getattr(at, kind)]}")


at = AppTest.from_file(PAGE, default_timeout=60)
run(at)
print("title:", at.header[0].value)
labels = widget(at, "radio", "learn_choice").options
print("options:", labels)

# 선상지 선택
fan_label = [l for l in labels if "선상지" in l][0]
widget(at, "radio", "learn_choice").set_value(fan_label)
run(at)
sid = "alluvial_fan_basic"

# L1: 객관식 오답 → 힌트 → 정답
widget(at, "radio", f"learn_choice_{sid}_L1").set_value("평지에 들어서며 유량이 갑자기 늘어나기 때문"); run(at)
widget(at, "button", f"learn_check_{sid}_L1").click(); run(at)
assert any("아직 아닙니다" in e.value for e in at.error), [e.value for e in at.error]
widget(at, "button", f"learn_hint_{sid}_L1").click(); run(at)
assert any("힌트 1" in w.value for w in at.warning)
widget(at, "radio", f"learn_choice_{sid}_L1").set_value("경사가 급하게 완만해져 하천의 운반력이 줄어들기 때문"); run(at)
widget(at, "button", f"learn_check_{sid}_L1").click(); run(at)
assert any("맞습니다" in s.value for s in at.success), [s.value for s in at.success]
print("L1 ok")

widget(at, "button", f"learn_next_{sid}").click(); run(at)

# L2: 슬라이더 목표 도달 전엔 객관식이 없어야 함
assert not any(w.key == f"learn_choice_{sid}_L2" for w in at.radio), "객관식이 너무 일찍 열림"
assert any("현재 판정" in i.value for i in at.info)
widget(at, "slider", f"learn_stage_{sid}_L2").set_value(0.66); run(at)
assert any("목표 상태 도달" in s.value for s in at.success)
widget(at, "checkbox", f"learn_zone_{sid}_L2").check(); run(at)
widget(at, "radio", f"learn_choice_{sid}_L2").set_value("모래(사)"); run(at)
widget(at, "button", f"learn_check_{sid}_L2").click(); run(at)
print("L2 ok")
widget(at, "button", f"learn_next_{sid}").click(); run(at)

# L3: 두 번 틀리면 풀이가 열리고 '풀이를 읽고 넘어가기' 가능
for _ in range(2):
    widget(at, "radio", f"learn_choice_{sid}_L3").set_value("바닷물이 지하로 들어와 솟아오르기 때문"); run(at)
    widget(at, "button", f"learn_check_{sid}_L3").click(); run(at)
assert any(w.key == f"learn_skip_{sid}_L3" for w in at.button), "풀이 후 넘어가기 버튼 없음"
widget(at, "button", f"learn_skip_{sid}_L3").click(); run(at)
widget(at, "button", f"learn_next_{sid}").click(); run(at)
print("L3 ok")

# L4 정답 → 정리
widget(at, "radio", f"learn_choice_{sid}_L4").set_value("물이 지하로 복류해 지표수가 부족하기 때문"); run(at)
widget(at, "button", f"learn_check_{sid}_L4").click(); run(at)
widget(at, "button", f"learn_next_{sid}").click(); run(at)
assert any("정리" in s.value for s in at.subheader), [s.value for s in at.subheader]
assert len(at.table) == 1
print("summary ok; table rows:", at.table[0].value.shape)

# 교사용 탭: 잘못된 스펙 검증 실패, 올바른 스펙 통과
widget(at, "text_area", "learn_paste").set_value('{"id": "x"}')
widget(at, "button", "learn_validate").click(); run(at)
assert any("검증 실패" in e.value for e in at.error)
good = open("learning/specs/free_meander_basic.json", encoding="utf-8").read().replace('"free_meander_basic"', '"my_meander"')
widget(at, "text_area", "learn_paste").set_value(good)
widget(at, "button", "learn_validate").click(); run(at)
assert any("검증 통과" in s.value for s in at.success), [s.value for s in at.success]
labels = widget(at, "radio", "learn_choice").options
assert any("검수 중" in l for l in labels), labels
print("teacher tab ok:", labels[-1])

# 해안절벽(generator 지정) 도 렌더되는지
widget(at, "radio", "learn_choice").set_value([l for l in labels if "파도" in l][0]); run(at)
assert any("L1" in w.key for w in at.radio)
print("coastal ok")
print("ALL OK")
