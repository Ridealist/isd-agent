"""Run with: python -m unittest discover -s test -p 'test_auth.py'."""

import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]
TEST_CODE = "테스트-entry-7294"


class EntryCodeTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {"ENTRY_CODE": TEST_CODE})
        self.env.start()
        self.addCleanup(self.env.stop)

    def app(self):
        app = AppTest.from_file(str(ROOT / "main.py")).run()
        self.assertFalse(app.exception)
        return app

    def login(self, app):
        app.text_input[0].input(TEST_CODE)
        app.button[0].click().run()
        self.assertFalse(app.exception)

    def test_empty_and_wrong_code_stay_on_login(self):
        app = self.app()
        self.assertEqual(app.text_input[0].label, "입장코드")
        self.assertEqual(app.text_input[0].proto.type, 1)
        app.button[0].click().run()
        self.assertIn("입력해주세요", app.error[0].value)
        app.text_input[0].input("wrong").run()
        app.button[0].click().run()
        self.assertIn("올바르지", app.error[0].value)
        self.assertNotIn("_entry_code_digest", app.session_state)
        self.assertFalse(app.exception)

    def test_login_persists_and_logout_clears_work(self):
        app = self.app()
        self.login(app)
        self.assertIn("Introducing ISD-Agent", app.title[0].value)
        session_id = app.session_state["session_id"]
        app.run()
        self.assertEqual(app.session_state["session_id"], session_id)
        app.session_state["final_report"] = "private work"
        next(b for b in app.button if b.label == "나가기").click().run()
        self.assertEqual(app.text_input[0].label, "입장코드")
        self.assertNotIn("final_report", app.session_state)
        self.assertNotIn("session_id", app.session_state)
        self.login(app)
        self.assertNotEqual(app.session_state["session_id"], session_id)

    def test_blank_configuration_blocks_entry(self):
        for value in ("", "   "):
            with self.subTest(value=value), patch.dict(os.environ, {"ENTRY_CODE": value}):
                app = self.app()
                self.assertIn("설정되지", app.error[0].value)
                self.assertEqual(len(app.text_input), 0)

    def test_secret_configuration_and_missing_configuration(self):
        with patch.dict(os.environ):
            os.environ.pop("ENTRY_CODE", None)
            app = AppTest.from_file(str(ROOT / "main.py"))
            app.secrets["ENTRY_CODE"] = TEST_CODE
            app.run()
            self.login(app)
            app = AppTest.from_file(str(ROOT / "main.py"))
            # Override any real local secrets, without loading a developer's code.
            app.secrets["ENTRY_CODE"] = None
            app.run()
            self.assertIn("설정되지", app.error[0].value)

    def test_code_change_invalidates_existing_session(self):
        app = self.app()
        self.login(app)
        app.session_state["final_report"] = "private work"
        with patch.dict(os.environ, {"ENTRY_CODE": "changed-code"}):
            app.run()
        self.assertEqual(app.text_input[0].label, "입장코드")
        self.assertNotIn("final_report", app.session_state)

    def test_old_login_flag_does_not_grant_access(self):
        app = self.app()
        app.session_state["logged_in"] = True
        app.run()
        self.assertEqual(app.text_input[0].label, "입장코드")

    def test_protected_routes_require_authentication(self):
        # Exercise the real router with cheap page bodies, without LLM/API calls.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "main.py").write_text((ROOT / "main.py").read_text())
            (root / "pages").mkdir()
            pages = sorted((ROOT / "pages").glob("*.py"))
            for page in pages:
                (root / "pages" / page.name).write_text(
                    'import streamlit as st\nst.title("Protected")\n'
                    'st.write("protected page")\nst.caption("Test page")\n'
                )
            for page in pages:
                with self.subTest(page=page.name):
                    app = AppTest.from_file(str(root / "main.py")).run()
                    app.switch_page("pages/" + page.name).run()
                    self.assertFalse(app.exception)
                    self.assertEqual(app.text_input[0].label, "입장코드")
                    self.assertFalse(any(
                        item.value == "protected page" for item in app.markdown
                    ))
                    self.login(app)
                    app.switch_page("pages/" + page.name).run()
                    self.assertFalse(app.exception)
                    self.assertEqual(app.markdown[0].value, "protected page")
                    next(b for b in app.button if b.label == "나가기").click().run()
                    self.assertEqual(app.text_input[0].label, "입장코드")


if __name__ == "__main__":
    unittest.main()
