import unittest

from app.services.extractor import ExtractionError, extract_visible_text


class ExtractorTests(unittest.TestCase):
    def test_extracts_main_text_and_drops_common_noise(self) -> None:
        html = """
        <html>
          <head><style>.x { color: red }</style></head>
          <body>
            <header>共通ヘッダー</header>
            <nav>メニュー</nav>
            <main>
              <h1>求人情報</h1>
              <p>時給 1,500円</p>
              <div class="cookie-banner">Cookieを許可</div>
              <p>応募受付中</p>
            </main>
            <footer>共通フッター</footer>
          </body>
        </html>
        """
        self.assertEqual(
            extract_visible_text(html),
            "求人情報\n時給 1,500円\n応募受付中",
        )

    def test_rejects_empty_page(self) -> None:
        with self.assertRaises(ExtractionError):
            extract_visible_text("<html><script>hello()</script></html>")

    def test_collapses_spaces_and_duplicate_lines(self) -> None:
        html = "<p>  在庫   あり </p><p>在庫 あり</p>"
        self.assertEqual(extract_visible_text(html), "在庫 あり")

    def test_void_tag_inside_excluded_element_does_not_hide_later_text(self) -> None:
        html = "<form><input name='q'></form><main><p>この文章は残る</p></main>"
        self.assertEqual(extract_visible_text(html), "この文章は残る")


if __name__ == "__main__":
    unittest.main()
