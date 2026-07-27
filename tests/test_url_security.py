import unittest

from app.services.url_security import UnsafeURLError, is_public_ip, normalize_url


class URLSecurityTests(unittest.TestCase):
    def test_normalizes_public_http_url(self) -> None:
        self.assertEqual(
            normalize_url(" HTTPS://Example.COM/path?q=1#fragment "),
            "https://example.com/path?q=1",
        )

    def test_rejects_non_http_scheme(self) -> None:
        with self.assertRaises(UnsafeURLError):
            normalize_url("file:///etc/passwd")

    def test_rejects_credentials_and_nonstandard_port(self) -> None:
        with self.assertRaises(UnsafeURLError):
            normalize_url("https://user:secret@example.com/")
        with self.assertRaises(UnsafeURLError):
            normalize_url("https://example.com:8443/")

    def test_rejects_local_hostnames(self) -> None:
        for url in (
            "http://localhost/",
            "http://service.internal/",
            "http://printer.local/",
        ):
            with self.subTest(url=url), self.assertRaises(UnsafeURLError):
                normalize_url(url)

    def test_public_ip_classification(self) -> None:
        self.assertTrue(is_public_ip("8.8.8.8"))
        for address in ("127.0.0.1", "10.0.0.1", "169.254.169.254", "::1"):
            with self.subTest(address=address):
                self.assertFalse(is_public_ip(address))


if __name__ == "__main__":
    unittest.main()
