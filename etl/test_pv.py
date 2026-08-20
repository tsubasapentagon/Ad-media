import unittest

from pv import ARTICLE_CONFIG, build_pv_records, extract_article_id, normalize_article_master


class PvTest(unittest.TestCase):
    def test_extracts_only_numeric_article_ids(self):
        self.assertEqual(extract_article_id("/article/12345"), "12345")
        self.assertEqual(extract_article_id("/article/12345/"), "12345")
        self.assertIsNone(extract_article_id("/columns/12345"))

    def test_normalizes_media_specific_article_columns(self):
        digmedia = normalize_article_master([["id", "Category"], ["10", "intern"]], ARTICLE_CONFIG[0])
        market = normalize_article_master([["ID", "カテゴリ"], ["20", "面接"]], ARTICLE_CONFIG[1])
        self.assertEqual(digmedia, {"10": "intern"})
        self.assertEqual(market, {"20": "面接"})

    def test_duplicate_article_id_uses_latest_category(self):
        values = [["id", "Category"], ["311443", "intern"], ["311443", "面接"]]
        self.assertEqual(normalize_article_master(values, ARTICLE_CONFIG[0]), {"311443": "面接"})

    def test_groups_same_date_and_article_and_merges_category(self):
        rows = [
            {"date": "20260819", "pagePath": "/article/10", "screenPageViews": "12"},
            {"date": "20260819", "pagePath": "/article/10/", "screenPageViews": "3"},
            {"date": "20260819", "pagePath": "/other/10", "screenPageViews": "99"},
        ]
        result = build_pv_records("Digmedia", rows, {"10": "intern"}, {"intern": "3年生"})
        self.assertEqual(result, [{
            "date": "20260819", "media": "Digmedia", "article_id": "10",
            "category": "3年生", "subcategory": "intern", "page_views": 15,
        }])

    def test_unmapped_article_or_category_is_visible(self):
        rows = [{"date": "20260819", "pagePath": "/article/99", "screenPageViews": "1"}]
        result = build_pv_records("就活市場", rows, {}, {})
        self.assertEqual(result[0]["category"], "未設定")
        self.assertEqual(result[0]["subcategory"], "未設定")


if __name__ == "__main__":
    unittest.main()
