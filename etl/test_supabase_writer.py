import unittest

from supabase_writer import SupabaseWriter, build_ingest_payload


class FakeResponse:
    ok = True
    status_code = 200
    text = ""
    def json(self): return 12


class SupabaseWriterTest(unittest.TestCase):
    def test_builds_db_payload_and_excludes_unknown_ads(self):
        result = {
            "ads":[{"media":"Digmedia","ad_id":"known_sp","device":"SP","placement":"見出し1","category":"3年生","subcategory":"intern","start_date":"20260801","end_date":""}],
            "daily_metrics":[
                {"date":"20260819","media":"Digmedia","ad_id":"known_sp","impressions":70,"clicks":3,"cv":1,"allocation_status":"配賦済み"},
                {"date":"20260819","media":"Digmedia","ad_id":"unknown","impressions":0,"clicks":1,"cv":0,"allocation_status":"対象PVなし"},
            ],
            "cv_by_grad":[{"date":"20260819","media":"Digmedia","ad_id":"known_sp","graduation_year":2028,"cv":1}],
        }
        payload = build_ingest_payload(result,"20260819","20260819","manual")
        self.assertEqual(len(payload["p_ads"]),1)
        self.assertEqual(payload["p_ads"][0]["start_date"],"2026-08-01")
        self.assertEqual(len(payload["p_metrics"]),1)
        self.assertEqual(payload["p_grad_metrics"][0]["graduation_year"],2028)
        self.assertEqual(payload["p_issues"][0]["issue_type"],"ad_not_found")

    def test_sends_the_complete_ad_master_even_without_metrics(self):
        result = {
            "ads":[
                {"media":"Digmedia","ad_id":"a_sp","device":"SP","placement":"見出し1","category":"就活","subcategory":"面接"},
                {"media":"就活市場","ad_id":"b_pc","device":"PC","placement":"記事中","category":"就活","subcategory":"ES"},
            ],
            "daily_metrics":[], "cv_by_grad":[],
        }
        payload = build_ingest_payload(result,"20260819","20260819","schedule")
        self.assertEqual([row["ad_id"] for row in payload["p_ads"]], ["a_sp","b_pc"])

    def test_splits_metrics_by_day_and_completes_sync(self):
        calls=[]
        def post(url,**kwargs): calls.append((url,kwargs)); return FakeResponse()
        writer=SupabaseWriter("https://example.supabase.co","secret",post=post)
        result={
            "ads":[{"media":"Digmedia","ad_id":"a_sp","device":"SP","placement":"見出し1"}],
            "daily_metrics":[
                {"date":"20260819","media":"Digmedia","ad_id":"a_sp","impressions":1,"clicks":1,"cv":0,"allocation_status":"配賦済み"},
                {"date":"20260820","media":"Digmedia","ad_id":"a_sp","impressions":2,"clicks":1,"cv":1,"allocation_status":"配賦済み"},
            ],
            "cv_by_grad":[],
        }
        self.assertEqual(writer.save(result,"20260819","20260820","manual"),12)
        self.assertTrue(calls[0][0].endswith("/rpc/sync_ad_master"))
        self.assertTrue(calls[1][0].endswith("/rpc/replace_ad_metrics"))
        self.assertEqual(calls[1][1]["json"]["p_start_date"], "2026-08-19")
        self.assertTrue(calls[2][0].endswith("/rpc/replace_ad_metrics"))
        self.assertEqual(calls[2][1]["json"]["p_start_date"], "2026-08-20")
        self.assertTrue(calls[3][0].endswith("/rpc/record_sync_success"))
        self.assertEqual(calls[0][1]["headers"]["apikey"],"secret")

    def test_retries_idempotent_chunk_after_520(self):
        calls=[]
        class FailedResponse(FakeResponse):
            ok=False
            status_code=520
            text="error code: 520"
        responses=[FailedResponse(), FakeResponse(), FakeResponse(), FakeResponse()]
        def post(url,**kwargs): calls.append(url); return responses.pop(0)
        writer=SupabaseWriter("https://example.supabase.co","secret",post=post,sleep=lambda _seconds: None)
        result={"ads":[{"media":"Digmedia","ad_id":"a_sp","device":"SP","placement":"見出し1"}],"daily_metrics":[],"cv_by_grad":[]}
        writer.save(result,"20260819","20260819","manual")
        self.assertEqual(calls[0],calls[1])

    def test_ad_master_target_does_not_replace_daily_metrics(self):
        calls=[]
        def post(url,**kwargs): calls.append(url); return FakeResponse()
        writer=SupabaseWriter("https://example.supabase.co","secret",post=post)
        result={"ads":[{"media":"Digmedia","ad_id":"a_sp","device":"SP","placement":"見出し1"}],"daily_metrics":[],"cv_by_grad":[]}
        writer.save(result,"20260819","20260819","manual",{"ad_master"})
        self.assertTrue(calls[0].endswith("/rpc/sync_ad_master"))
        self.assertFalse(any(url.endswith("/rpc/replace_ad_metrics") for url in calls))

    def test_click_target_uses_component_rpc_and_preserves_other_columns(self):
        calls=[]
        def post(url,**kwargs): calls.append((url,kwargs["json"])); return FakeResponse()
        writer=SupabaseWriter("https://example.supabase.co","secret",post=post)
        result={"ads":[{"media":"Digmedia","ad_id":"a_sp","device":"SP","placement":"見出し1"}],"daily_metrics":[],"cv_by_grad":[]}
        writer.save(result,"20260819","20260819","manual",{"clicks"})
        component=[call for call in calls if call[0].endswith("/rpc/replace_ad_metric_components")][0]
        self.assertEqual(component[1]["p_components"],["clicks"])
        self.assertEqual(component[1]["p_metrics"],[])
        self.assertFalse(any(url.endswith("/rpc/sync_ad_master") for url,_ in calls))


if __name__ == "__main__": unittest.main()
