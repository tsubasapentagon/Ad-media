import unittest

from click_data import build_click_records


ADS = [
    {
        "media": "Digmedia",
        "ad_id": "CenterD2003_sp",
        "category": "3年生",
        "subcategory": "intern",
        "placement": "見出し5",
        "device": "SP",
    },
    {
        "media": "就活市場",
        "ad_id": "CenterD2003_sp",
        "category": "別カテゴリ",
        "subcategory": "別小カテゴリ",
        "placement": "記事中段",
        "device": "SP",
    },
]


class ClickTest(unittest.TestCase):
    def test_merges_ad_metadata_with_media_scoped_id(self):
        rows = [{
            "date": "20260819",
            "customEvent:広告ID": "CenterD2003_sp",
            "pagePath": "/article/123",
            "eventCount": "4",
        }]
        result = build_click_records("Digmedia", rows, ADS)
        self.assertEqual(result[0]["category"], "3年生")
        self.assertEqual(result[0]["subcategory"], "intern")
        self.assertEqual(result[0]["placement"], "見出し5")
        self.assertEqual(result[0]["article_id"], "123")
        self.assertEqual(result[0]["device"], "SP")

    def test_ignores_empty_and_not_set_ids(self):
        rows = [
            {"date": "20260819", "ID": "", "pagePath": "/article/1", "eventCount": "3"},
            {"date": "20260819", "ID": "(not set)", "pagePath": "/article/1", "eventCount": "5"},
        ]
        self.assertEqual(build_click_records("Digmedia", rows, ADS), [])

    def test_groups_duplicate_ga4_rows(self):
        rows = [
            {"date": "20260819", "ID": "CenterD2003_sp", "pagePath": "/article/1", "eventCount": "2"},
            {"date": "20260819", "ID": "CenterD2003_sp", "pagePath": "/article/1/", "eventCount": "3"},
        ]
        result = build_click_records("Digmedia", rows, ADS)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["clicks"], 5)

    def test_keeps_click_for_unknown_ad_id(self):
        rows = [{"date": "20260819", "ID": "unknown", "pagePath": "/article/1", "eventCount": "1"}]
        result = build_click_records("Digmedia", rows, ADS)
        self.assertEqual(result[0]["ad_id"], "unknown")
        self.assertEqual(result[0]["category"], "未設定")
        self.assertEqual(result[0]["placement"], "未設定")
        self.assertEqual(result[0]["device"], "不明")


if __name__ == "__main__":
    unittest.main()
