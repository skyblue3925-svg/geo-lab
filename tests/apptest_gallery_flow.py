"""Streamlit AppTest 로 갤러리 두 복제본(pages/, app/pages/)을 확인한다. 실행: python tests/apptest_gallery_flow.py"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

from streamlit.testing.v1 import AppTest
for page in ("pages/1_📖_Gallery.py", "app/pages/1_📖_Gallery.py"):
    at = AppTest.from_file(os.path.join(ROOT, page), default_timeout=120); at.run()
    assert not at.exception, at.exception
    cat = lambda: [r for r in at.radio if r.key == "gallery_cat"][0]
    cat().set_value("⚠️ 자연재해"); at.run(); assert not at.exception, at.exception
    print(page, "info:", [i.value[:30] for i in at.info][-1])
    print("  stage desc:", [s.value for s in at.success][:1])
    cat().set_value("🏖️ 해안 지형"); at.run()
    sb = [s for s in at.selectbox if any("리아스" in o for o in s.options)][0]
    sb.set_value([o for o in sb.options if "리아스" in o][0]); at.run(); assert not at.exception, at.exception
    print("  ria stage desc:", [s.value for s in at.success][:1])
    cat().set_value("🦇 카르스트 지형"); at.run()
    sb = [s for s in at.selectbox if any("카렌" in o for o in s.options)][0]
    sb.set_value([o for o in sb.options if "카렌" in o][0]); at.run(); assert not at.exception, at.exception
    print("  karren at default res ok")
print("GALLERY OK")
