import unittest

from ad_master import (
    CATEGORY_SHEET,
    SOURCE_CONFIG,
    device_from_ad_id,
    load_all_ad_records,
    normalize_category_mapping,
    normalize_sheet_values,
)


class AdMasterTest(unittest.TestCase):
    def test_device_is_derived_from_id_suffix(self):
        self.assertEqual(device_from_ad_id("CenterD2003_sp"), "SP")
        self.assertEqual(device_from_ad_id("CenterD2003_PC"), "PC")
        self.assertEqual(device_from_ad_id("unknown"), "不明")

    def test_digmedia_uses_fourth_row_as_header(self):
        values = [
            ["説明"], [""], [""],
            ["ID", "カテゴリ", "詳細", "CVポイント", "LP番号", "進捗", "開始日", "終了日"],
            ["CenterD2003_sp", "自己分析", "見出し5", "会員登録", "12", "稼働中", "2026/03/05", ""],
            ["", "空行", "", "", ""],
        ]
        self.assertEqual(normalize_sheet_values(values, SOURCE_CONFIG[0]), [{
            "media": "Digmedia", "ad_id": "CenterD2003_sp", "category": "",
            "subcategory": "自己分析",
            "placement": "見出し5", "cv_point": "会員登録", "lp_number": "12", "device": "SP",
            "status": "稼働中", "start_date": "20260305", "end_date": None, "comment": "",
        }])

    def test_market_and_venture_column_names_are_normalized(self):
        sheets = {
            "digmediaデータ": [[""], [""], [""], ["ID", "カテゴリ", "詳細", "CVポイント", "LP番号", "進捗", "開始日", "終了日"]],
            "マスターデータ": [["ID", "カテゴリ", "詳細", "CVポイント", "LP", "進捗", "開始日", "終了日"], ["TopS1_pc", "面接", "記事中段", "登録", "5", "稼働中", "2026/01/01", ""]],
            "ベンチャー就活ナビ": [["ID", "カテゴリ", "位置", "CVポイント", "LP", "進捗", "開始日", "終了日", "コンテンツ"], ["TopV1_sp", "ES", "見出し1", "登録", "8", "終了", "2026/01/01", "2026/08/01", "ES添削"]],
            CATEGORY_SHEET: [["カテゴリ設定", "細分化", "個別カテゴリ"], ["面接", "選考対策", "面接"], ["ES", "選考対策", "ES"]],
        }
        rows = load_all_ad_records(lambda _key, tab: sheets[tab])
        self.assertEqual(rows[0]["media"], "就活市場")
        self.assertEqual(rows[0]["placement"], "記事中段")
        self.assertEqual(rows[1]["media"], "ベンチャー就活")
        self.assertEqual(rows[1]["lp_number"], "8")
        self.assertEqual(rows[1]["comment"], "ES添削")
        self.assertEqual(rows[1]["end_date"], "20260801")

    def test_duplicate_id_in_same_media_is_rejected(self):
        sheets = {
            "digmediaデータ": [[""], [""], [""], ["ID", "カテゴリ", "詳細", "CVポイント", "LP番号", "進捗", "開始日", "終了日"], ["same_sp", "A", "見出し1", "登録", "1", "稼働中", "", ""], ["same_sp", "A", "見出し2", "登録", "2", "稼働中", "", ""]],
            "マスターデータ": [["ID", "カテゴリ", "詳細", "CVポイント", "LP", "進捗", "開始日", "終了日"]],
            "ベンチャー就活ナビ": [["ID", "カテゴリ", "位置", "CVポイント", "LP", "進捗", "開始日", "終了日"]],
            CATEGORY_SHEET: [["カテゴリ設定", "細分化", "個別カテゴリ"]],
        }
        with self.assertRaisesRegex(ValueError, "Digmedia/same_sp"):
            load_all_ad_records(lambda _key, tab: sheets[tab])

    def test_category_is_merged_case_insensitively(self):
        sheets = {
            "digmediaデータ": [[""], [""], [""], ["ID", "カテゴリ", "詳細", "CVポイント", "LP番号", "進捗", "開始日", "終了日"], ["ad_sp", "intern", "見出し1", "登録", "1", "稼働中", "", ""]],
            "マスターデータ": [["ID", "カテゴリ", "詳細", "CVポイント", "LP", "進捗", "開始日", "終了日"]],
            "ベンチャー就活ナビ": [["ID", "カテゴリ", "位置", "CVポイント", "LP", "進捗", "開始日", "終了日"]],
            CATEGORY_SHEET: [["カテゴリ設定", "細分化", "個別カテゴリ"], ["Intern", "3年生", "インターン"]],
        }
        row = load_all_ad_records(lambda _key, tab: sheets[tab])[0]
        self.assertEqual(row["subcategory"], "intern")
        self.assertEqual(row["category"], "3年生")

    def test_conflicting_case_variants_are_rejected(self):
        values = [["カテゴリ設定", "細分化", "個別カテゴリ"], ["Intern", "3年生", "インターン"], ["intern", "別カテゴリ", "インターン"]]
        with self.assertRaisesRegex(ValueError, "競合"):
            normalize_category_mapping(values)

    def test_unmapped_subcategory_is_visible_as_unset(self):
        sheets = {
            "digmediaデータ": [[""], [""], [""], ["ID", "カテゴリ", "詳細", "CVポイント", "LP番号", "進捗", "開始日", "終了日"], ["ad_sp", "未登録の小カテゴリ", "見出し1", "登録", "1", "稼働中", "", ""]],
            "マスターデータ": [["ID", "カテゴリ", "詳細", "CVポイント", "LP", "進捗", "開始日", "終了日"]],
            "ベンチャー就活ナビ": [["ID", "カテゴリ", "位置", "CVポイント", "LP", "進捗", "開始日", "終了日"]],
            CATEGORY_SHEET: [["カテゴリ設定", "細分化", "個別カテゴリ"]],
        }
        row = load_all_ad_records(lambda _key, tab: sheets[tab])[0]
        self.assertEqual(row["category"], "未設定")


if __name__ == "__main__":
    unittest.main()
