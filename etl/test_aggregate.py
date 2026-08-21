import unittest
from aggregate import Ad, allocate_impressions, count_submissions

class AggregateTest(unittest.TestCase):
    def test_gives_each_ad_the_full_device_share(self):
        ads=[Ad("digmedia","a_sp","SP"),Ad("digmedia","b_sp","SP"),Ad("digmedia","a_pc","PC")]
        result=allocate_impressions(100,ads)
        self.assertEqual(result[("digmedia","a_sp")],70)
        self.assertEqual(result[("digmedia","b_sp")],70)
        self.assertEqual(result[("digmedia","a_pc")],30)

    def test_counts_repeat_submissions(self):
        rows=[{"media":"digmedia","ad_id":"a"},{"media":"digmedia","ad_id":"a"}]
        self.assertEqual(count_submissions(rows)[("digmedia","a")],2)

if __name__ == "__main__": unittest.main()
