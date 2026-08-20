import unittest

from daily_metrics import build_daily_metrics, summarize_metrics


class DailyMetricsTest(unittest.TestCase):
    def test_merges_four_sources_and_keeps_grad_breakdown(self):
        ads = [{"media": "Digmedia", "ad_id": "ad_sp", "category": "3年生", "subcategory": "intern", "placement": "見出し1", "device": "SP", "start_date": None, "end_date": None}]
        pv = [{"date": "20260819", "media": "Digmedia", "category": "3年生", "subcategory": "intern", "page_views": 100}]
        clicks = [
            {"date": "20260819", "media": "Digmedia", "ad_id": "ad_sp", "article_id": "1", "clicks": 3},
            {"date": "20260819", "media": "Digmedia", "ad_id": "ad_sp", "article_id": "2", "clicks": 2},
        ]
        cvs = [
            {"date": "20260819", "media": "Digmedia", "ad_id": "ad_sp", "graduation_year": 2028, "cv_source": "LINE", "cv_count": 1},
            {"date": "20260819", "media": "Digmedia", "ad_id": "ad_sp", "graduation_year": 2028, "cv_source": "会員登録", "cv_count": 2},
            {"date": "20260819", "media": "Digmedia", "ad_id": "ad_sp", "graduation_year": 2029, "cv_source": "会員登録", "cv_count": 1},
        ]
        daily, by_grad = build_daily_metrics(ads, pv, clicks, cvs)
        self.assertEqual(daily[0]["impressions"], 70)
        self.assertEqual(daily[0]["clicks"], 5)
        self.assertEqual(daily[0]["cv"], 4)
        self.assertEqual(by_grad, [
            {"date": "20260819", "media": "Digmedia", "ad_id": "ad_sp", "graduation_year": 2028, "cv": 3},
            {"date": "20260819", "media": "Digmedia", "ad_id": "ad_sp", "graduation_year": 2029, "cv": 1},
        ])

    def test_summary_calculates_rates_after_summing_period(self):
        daily = [
            {"impressions": 100, "clicks": 10, "cv": 2},
            {"impressions": 300, "clicks": 10, "cv": 6},
        ]
        by_grad = [{"graduation_year": 2028, "cv": 6}, {"graduation_year": 2029, "cv": 2}]
        summary = summarize_metrics(daily, by_grad, 2028)
        self.assertEqual(summary["ctr"], 5.0)
        self.assertEqual(summary["cvr"], 40.0)
        self.assertEqual(summary["graduation_cv"], 6)
        self.assertEqual(summary["graduation_cv_rate"], 75.0)

    def test_zero_denominators_return_none(self):
        summary = summarize_metrics([], [], 2028)
        self.assertIsNone(summary["ctr"])
        self.assertIsNone(summary["cvr"])
        self.assertIsNone(summary["graduation_cv_rate"])


if __name__ == "__main__":
    unittest.main()
