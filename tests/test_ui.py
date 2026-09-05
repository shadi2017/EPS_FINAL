"""Smoke coverage for navigation and duplicate Streamlit element keys."""
import unittest
from streamlit.testing.v1 import AppTest
from eps_studio.core import ROOT


class WorkspaceTests(unittest.TestCase):
    def test_navigation_has_no_duplicate_keys(self):
        app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
        self.assertFalse(app.exception)
        self.assertFalse(app.error)
        app.radio[0].set_value("Photo framing").run()
        self.assertFalse(app.exception)
        self.assertFalse(app.error, [error.value for error in app.error])
        self.assertEqual(app.title[0].value, "Photo Studio")
        app.radio[0].set_value("Certificates").run()
        self.assertFalse(app.exception)
        self.assertFalse(app.error)


if __name__ == "__main__":
    unittest.main()
