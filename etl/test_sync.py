import os
import unittest
from datetime import date
from unittest.mock import patch

from sync import default_sync_range, sync_range_from_environment


class SyncDateTest(unittest.TestCase):
    def test_default_is_previous_month_start_through_yesterday(self):
        self.assertEqual(default_sync_range(date(2026,8,20)), ("2026-07-01","2026-08-19"))

    def test_january_crosses_year(self):
        self.assertEqual(default_sync_range(date(2026,1,1)), ("2025-12-01","2025-12-31"))

    def test_manual_range_can_be_overridden(self):
        with patch.dict(os.environ,{"SYNC_START_DATE":"2026-08-01","SYNC_END_DATE":"2026-08-10"},clear=True):
            self.assertEqual(sync_range_from_environment(), ("2026-08-01","2026-08-10"))


if __name__ == "__main__": unittest.main()
