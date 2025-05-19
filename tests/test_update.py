"""
Unit test for update checker for the application
"""
import sys
import json
import unittest
import urllib.request
import urllib.error
import ssl
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt6.QtWidgets import QApplication
from src.utils.update_checker import UpdateChecker, CURRENT_VERSION

# Ensure we have a Qt event loop for signals
app = QApplication.instance() or QApplication(sys.argv)

class FakeResponse:
    def __init__(self, payload: dict):
        self._data = json.dumps(payload).encode('utf-8')
    def read(self):
        return self._data
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        pass

class TestUpdateChecker(unittest.TestCase):
    def setUp(self):
        # Restore original urlopen after every test
        self._orig_urlopen = urllib.request.urlopen

    def tearDown(self):
        urllib.request.urlopen = self._orig_urlopen

    def test_is_newer_version(self):
        # older, same, and newer
        self.assertTrue(UpdateChecker._is_newer_version(None, "1.0.3"))
        self.assertFalse(UpdateChecker._is_newer_version(None, CURRENT_VERSION))
        self.assertFalse(UpdateChecker._is_newer_version(None, "0.9.9"))
        self.assertTrue(UpdateChecker._is_newer_version(None, "1.0.2.1"))

    def test_update_available_signal(self):
        # Simulate a remote version > CURRENT_VERSION
        fake = {"version": "2.0.0"}
        urllib.request.urlopen = lambda *args, **kwargs: FakeResponse(fake)

        checker = UpdateChecker(silent=True)
        received = []
        checker.update_available.connect(lambda info: received.append(info))

        checker.check_for_updates()
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]["version"], "2.0.0")

    def test_no_update_available_signal(self):
        # Simulate remote == CURRENT_VERSION
        fake = {"version": CURRENT_VERSION}
        urllib.request.urlopen = lambda *args, **kwargs: FakeResponse(fake)

        checker = UpdateChecker(silent=True)
        received = []
        checker.no_update_available.connect(lambda: received.append(True))

        checker.check_for_updates()
        self.assertEqual(len(received), 1)

    def test_error_occurred_signal_on_ssl_fail(self):
        # Simulate an SSL error on urlopen
        class FakeSSLReason(ssl.SSLError): pass
        class FakeURLError(urllib.error.URLError):
            def __init__(self):
                super().__init__(FakeSSLReason("handshake fail"))

        urllib.request.urlopen = lambda *args, **kwargs: (_ for _ in ()).throw(FakeURLError())

        checker = UpdateChecker(silent=True)
        received = []
        checker.error_occurred.connect(lambda msg: received.append(msg))

        checker.check_for_updates()
        self.assertEqual(len(received), 1)
        self.assertIn("SSL handshake failed", received[0])

if __name__ == "__main__":
    unittest.main()