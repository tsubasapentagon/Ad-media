import unittest

from impressions import allocate_daily_impressions


class ImpressionsTest(unittest.TestCase):
    def test_gives_each_placement_the_full_70_30_device_share(self):
        pv = [{"date": "20260819", "media": "Digmedia", "category": "3年生", "subcategory": "intern", "page_views": 101}]
        ads = [
            {"media": "Digmedia", "ad_id": "b_sp", "category": "3年生", "subcategory": "intern", "placement": "見出し2", "device": "SP"},
            {"media": "Digmedia", "ad_id": "a_sp", "category": "3年生", "subcategory": "intern", "placement": "見出し1", "device": "SP"},
            {"media": "Digmedia", "ad_id": "a_pc", "category": "3年生", "subcategory": "intern", "placement": "見出し1", "device": "PC"},
        ]
        result = allocate_daily_impressions(pv, ads)
        values = {row["ad_id"]: row["impressions"] for row in result}
        self.assertEqual(values, {"a_pc": 30, "a_sp": 71, "b_sp": 71})

    def test_does_not_divide_impressions_between_different_placements(self):
        pv = [{"date": "20260819", "media": "Digmedia", "category": "ES", "subcategory": "es", "page_views": 1000}]
        ads = [
            {"media": "Digmedia", "ad_id": "A_sp", "category": "ES", "subcategory": "es", "placement": "見出し1", "device": "SP"},
            {"media": "Digmedia", "ad_id": "B_sp", "category": "ES", "subcategory": "es", "placement": "見出し2", "device": "SP"},
        ]
        result = allocate_daily_impressions(pv, ads)
        self.assertEqual({row["ad_id"]: row["impressions"] for row in result}, {"A_sp": 700, "B_sp": 700})

    def test_divides_impressions_between_ab_ads_in_same_placement(self):
        pv = [{"date": "20260819", "media": "Digmedia", "category": "ES", "subcategory": "es", "page_views": 1000}]
        ads = [
            {"media": "Digmedia", "ad_id": "A_sp", "category": "ES", "subcategory": "es", "placement": "見出し1", "device": "SP"},
            {"media": "Digmedia", "ad_id": "B_sp", "category": "ES", "subcategory": "es", "placement": "見出し1", "device": "SP"},
        ]
        result = allocate_daily_impressions(pv, ads)
        self.assertEqual({row["ad_id"]: row["impressions"] for row in result}, {"A_sp": 350, "B_sp": 350})

    def test_allocates_only_within_same_media_and_subcategory(self):
        pv = [{"date": "20260819", "media": "就活市場", "category": "選考", "subcategory": "面接", "page_views": 10}]
        ads = [
            {"media": "就活市場", "ad_id": "target_sp", "category": "選考", "subcategory": "面接", "placement": "見出し1", "device": "SP"},
            {"media": "Digmedia", "ad_id": "other_sp", "category": "選考", "subcategory": "面接", "placement": "見出し1", "device": "SP"},
        ]
        result = allocate_daily_impressions(pv, ads)
        by_id = {row["ad_id"]: row for row in result}
        self.assertEqual(by_id["target_sp"]["impressions"], 7)
        self.assertEqual(by_id["other_sp"]["impressions"], 0)

    def test_unknown_device_is_kept_with_zero_and_status(self):
        pv = [{"date": "20260819", "media": "Digmedia", "category": "3年生", "subcategory": "intern", "page_views": 10}]
        ads = [{"media": "Digmedia", "ad_id": "legacy", "category": "3年生", "subcategory": "intern", "placement": "見出し1", "device": "不明"}]
        result = allocate_daily_impressions(pv, ads)
        self.assertEqual(result[0]["impressions"], 0)
        self.assertEqual(result[0]["allocation_status"], "端末不明")

    def test_rows_are_sorted_for_analysis(self):
        pv = [{"date": "20260819", "media": "Digmedia", "category": "3年生", "subcategory": "intern", "page_views": 10}]
        ads = [
            {"media": "Digmedia", "ad_id": "z_sp", "category": "3年生", "subcategory": "intern", "placement": "見出し2", "device": "SP"},
            {"media": "Digmedia", "ad_id": "a_sp", "category": "3年生", "subcategory": "intern", "placement": "見出し1", "device": "SP"},
        ]
        result = allocate_daily_impressions(pv, ads)
        self.assertEqual([row["ad_id"] for row in result], ["a_sp", "z_sp"])

    def test_allocates_only_during_inclusive_placement_period(self):
        pv = [
            {"date": "20260819", "media": "Digmedia", "category": "3年生", "subcategory": "intern", "page_views": 10},
            {"date": "20260820", "media": "Digmedia", "category": "3年生", "subcategory": "intern", "page_views": 10},
        ]
        ads = [{"media": "Digmedia", "ad_id": "ad_sp", "category": "3年生", "subcategory": "intern", "placement": "見出し1", "device": "SP", "start_date": "20260801", "end_date": "20260819"}]
        result = allocate_daily_impressions(pv, ads)
        by_date = {row["date"]: row for row in result}
        self.assertEqual(by_date["20260819"]["impressions"], 7)
        self.assertEqual(by_date["20260820"]["impressions"], 0)
        self.assertEqual(by_date["20260820"]["allocation_status"], "掲載期間外")


if __name__ == "__main__":
    unittest.main()
