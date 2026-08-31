from pathlib import Path
import sys
import unittest


SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from core.tiktok_public_download import (  # noqa: E402
    PublicTikTokDownloadError,
    extract_tiktok_post_id,
    parse_max_filesize,
    select_trusted_media_url,
)


class TikTokPublicDownloadTests(unittest.TestCase):
    def test_extracts_canonical_post_id(self) -> None:
        self.assertEqual(
            extract_tiktok_post_id("https://www.tiktok.com/@laladobby/video/7595615797821656342"),
            "7595615797821656342",
        )

    def test_rejects_non_tiktok_source(self) -> None:
        with self.assertRaises(PublicTikTokDownloadError):
            extract_tiktok_post_id("https://example.com/@laladobby/video/7595615797821656342")

    def test_selects_only_trusted_player_media_url(self) -> None:
        self.assertEqual(
            select_trusted_media_url(
                [
                    "https://evil.example/video.mp4",
                    "https://www.tiktok.com/aweme/v1/play/?item_id=7595615797821656342&token=test",
                ]
            ),
            "https://www.tiktok.com/aweme/v1/play/?item_id=7595615797821656342&token=test",
        )

    def test_rejects_untrusted_media_host(self) -> None:
        with self.assertRaises(PublicTikTokDownloadError):
            select_trusted_media_url(["https://evil.example/video.mp4"])

    def test_parses_binary_max_filesize(self) -> None:
        self.assertEqual(parse_max_filesize("500M"), 500 * 1024**2)


if __name__ == "__main__":
    unittest.main()
