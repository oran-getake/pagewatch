import unittest

from app.services.differ import compare_text


class DifferTests(unittest.TestCase):
    def test_reports_added_and_removed_lines(self) -> None:
        result = compare_text(
            "商品名\n価格 1,000円\n在庫なし",
            "商品名\n価格 900円\n在庫あり",
        )
        self.assertEqual(result.added_text, "価格 900円\n在庫あり")
        self.assertEqual(result.removed_text, "価格 1,000円\n在庫なし")
        self.assertFalse(result.truncated)

    def test_unchanged_text_has_empty_diff(self) -> None:
        result = compare_text("同じ文章", "同じ文章")
        self.assertEqual(result.added_text, "")
        self.assertEqual(result.removed_text, "")

    def test_long_diff_is_truncated(self) -> None:
        result = compare_text("old", "a" * 100, max_each=30)
        self.assertTrue(result.truncated)
        self.assertLessEqual(len(result.added_text), 30)


if __name__ == "__main__":
    unittest.main()
