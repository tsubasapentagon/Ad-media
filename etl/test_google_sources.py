import json
import os
import tempfile
import unittest
from unittest.mock import patch

from google_sources import load_service_account_info, spread_init


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

    def test_retries_temporary_sheets_503(self):
        class Response:
            status_code = 503
        class TemporaryError(Exception):
            response = Response()
        class Worksheet:
            calls = 0
            def get_all_values(self):
                self.calls += 1
                if self.calls == 1:
                    raise TemporaryError("unavailable")
                return [["ok"]]
        worksheet = Worksheet()
        class Spreadsheet:
            def worksheet(self, _name): return worksheet
        class Client:
            def open_by_key(self, _key): return Spreadsheet()
        with patch("google_sources.sheets_client", return_value=Client()), patch("google_sources.time.sleep") as sleep:
            self.assertEqual(spread_init("sheet", "tab"), [["ok"]])
            sleep.assert_called_once_with(1)


if __name__ == "__main__": unittest.main()
