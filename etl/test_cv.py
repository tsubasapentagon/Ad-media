import unittest

from cv import (
    enrich_and_aggregate_cv_records,
    normalize_date,
    normalize_graduation_year,
    normalize_line_records,
    normalize_member_records,
)


class CvTest(unittest.TestCase):
    def test_normalizes_date_and_graduation_year(self):
        self.assertEqual(normalize_date("2026/08/19 12:34:56"), "20260819")
        self.assertEqual(normalize_graduation_year("2028年卒"), 2028)
        self.assertEqual(normalize_graduation_year("28卒"), 2028)

    def test_line_requires_phone_but_does_not_return_it(self):
        values = [
            ["説明"],
            ["友だち追加日", "流入経路", "流入経路詳細", "卒業年度", "電話番号"],
            ["20260819", "Digmedia", "ad_sp", "28卒", "09012345678"],
            ["20260819", "Digmedia", "ad_sp", "28卒", ""],
        ]
        result = normalize_line_records(values)
        self.assertEqual(len(result), 1)
        self.assertNotIn("電話番号", result[0])
        self.assertEqual(result[0]["cv_source"], "LINE")

    def test_member_submissions_keep_only_first_row_per_phone(self):
        values = [
            ["登録日時", "電話番号", "卒業予定［年］", "経由点(バナー)"],
            ["2026-08-19 10:00", "09011111111", "2028", "ad_sp"],
            ["2026-08-19 11:00", "09011111111", "2028", "ad_sp"],
        ]
        result = normalize_member_records(values, "Digmedia", "貼付：新Digmedia")
        self.assertEqual(len(result), 1)
        self.assertTrue(all("電話番号" not in row for row in result))

    def test_same_phone_is_deduplicated_separately_per_media_source(self):
        values = [
            ["登録日時", "電話番号", "卒業予定［年］", "経由点(バナー)"],
            ["2026-08-19", "09011111111", "2028", "ad_sp"],
        ]
        digmedia = normalize_member_records(values, "Digmedia", "貼付：新Digmedia")
        market = normalize_member_records(values, "就活市場", "貼付：就活市場")
        self.assertEqual(len(digmedia), 1)
        self.assertEqual(len(market), 1)

    def test_line_and_member_are_aggregated_together_but_sources_remain_visible(self):
        submissions = [
            {"date": "20260819", "media": "Digmedia", "ad_id": "ad_sp", "graduation_year": 2028, "cv_source": "LINE"},
            {"date": "20260819", "media": "Digmedia", "ad_id": "ad_sp", "graduation_year": 2028, "cv_source": "会員登録"},
            {"date": "20260819", "media": "Digmedia", "ad_id": "ad_sp", "graduation_year": 2028, "cv_source": "会員登録"},
        ]
        ads = [{"media": "Digmedia", "ad_id": "ad_sp", "category": "3年生", "subcategory": "intern", "placement": "見出し1", "device": "SP"}]
        result = enrich_and_aggregate_cv_records(submissions, ads)
        self.assertEqual(sum(row["cv_count"] for row in result), 3)
        self.assertEqual({row["cv_source"] for row in result}, {"LINE", "会員登録"})

    def test_unknown_ad_is_kept_for_data_quality_log(self):
        submissions = [{"date": "20260819", "media": "Digmedia", "ad_id": "unknown", "graduation_year": 2028, "cv_source": "会員登録"}]
        result = enrich_and_aggregate_cv_records(submissions, [])
        self.assertEqual(result[0]["category"], "未設定")
        self.assertEqual(result[0]["device"], "不明")


if __name__ == "__main__":
    unittest.main()
