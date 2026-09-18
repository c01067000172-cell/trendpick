import unittest

import seo_automation


class SeoAutomationTests(unittest.TestCase):
    def test_public_urls_exclude_demo_and_escape_ids(self):
        urls = seo_automation.public_urls([
            {"id": "real item/1", "demo": False},
            {"id": "demo", "demo": True},
            {"id": ""},
        ])
        self.assertIn("https://www.maspick.co.kr/products/real%20item%2F1", urls)
        self.assertNotIn("https://www.maspick.co.kr/products/demo", urls)
        self.assertEqual(urls, sorted(set(urls)))

    def test_key_is_valid_indexnow_shape(self):
        self.assertGreaterEqual(len(seo_automation.INDEXNOW_KEY), 8)
        self.assertLessEqual(len(seo_automation.INDEXNOW_KEY), 128)
        self.assertTrue(all(c in "0123456789abcdef-" for c in seo_automation.INDEXNOW_KEY.lower()))


if __name__ == "__main__":
    unittest.main()
