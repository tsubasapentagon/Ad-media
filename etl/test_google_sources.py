import json
import os
import tempfile
import unittest
from unittest.mock import patch

from google_sources import load_service_account_info


VALID = {"client_email":"sync@example.test","private_key":"secret","token_uri":"https://oauth2.test/token"}


class GoogleSourcesTest(unittest.TestCase):
    def test_loads_credentials_from_json_environment(self):
        with patch.dict(os.environ, {"GOOGLE_SERVICE_ACCOUNT_JSON":json.dumps(VALID)}, clear=True):
            self.assertEqual(load_service_account_info()["client_email"], "sync@example.test")

    def test_local_file_is_an_explicit_fallback(self):
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8") as file:
            json.dump(VALID, file); file.flush()
            with patch.dict(os.environ, {"GOOGLE_SERVICE_ACCOUNT_FILE":file.name}, clear=True):
                self.assertEqual(load_service_account_info()["token_uri"], VALID["token_uri"])

    def test_rejects_incomplete_credentials(self):
        with patch.dict(os.environ, {"GOOGLE_SERVICE_ACCOUNT_JSON":"{}"}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "必須項目"):
                load_service_account_info()


if __name__ == "__main__": unittest.main()
