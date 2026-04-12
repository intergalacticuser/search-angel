"""Tests for privacy anonymizer."""

from search_angel.privacy.anonymizer import Anonymizer


class TestAnonymizer:
    def setup_method(self):
        self.anonymizer = Anonymizer(rotation_hours=24)

    def test_hash_ip_returns_hex(self):
        result = self.anonymizer.hash_ip("192.168.1.1")
        assert len(result) == 16
        assert all(c in "0123456789abcdef" for c in result)

    def test_same_ip_same_hash(self):
        h1 = self.anonymizer.hash_ip("10.0.0.1")
        h2 = self.anonymizer.hash_ip("10.0.0.1")
        assert h1 == h2

    def test_different_ips_different_hashes(self):
        h1 = self.anonymizer.hash_ip("10.0.0.1")
        h2 = self.anonymizer.hash_ip("10.0.0.2")
        assert h1 != h2

    def test_strip_headers_removes_sensitive(self):
        headers = {
            "user-agent": "Mozilla/5.0",
            "referer": "https://example.com",
            "cookie": "session=abc123",
            "content-type": "application/json",
            "accept": "application/json",
        }
        cleaned = Anonymizer.strip_headers(headers)
        assert "user-agent" not in cleaned
        assert "referer" not in cleaned
        assert "cookie" not in cleaned
        assert "content-type" in cleaned
        assert "accept" in cleaned

    def test_hash_ip_not_raw_ip(self):
        ip = "192.168.1.100"
        hashed = self.anonymizer.hash_ip(ip)
        assert ip not in hashed
        assert "192" not in hashed
