import email.message, io, tempfile, unittest, urllib.error
from pathlib import Path
from unittest import mock

from bowl_index import archive
from bowl_index.db import connect, migrate


class Response(io.BytesIO):
    def __init__(self, body, content_type="text/html"):
        super().__init__(body)
        self.status = 200
        self.headers = email.message.Message()
        self.headers["Content-Type"] = content_type


def redirect(url, location):
    headers = email.message.Message()
    headers["Location"] = location
    return urllib.error.HTTPError(url, 301, "Moved", headers, None)


class CaptureRobotsTests(unittest.TestCase):
    """`ibi capture` honours wildcard robots rules on every hop, and fails closed."""
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        self.conn = connect(self.root / "db.sqlite3"); migrate(self.conn)
        self.opened = []

    def tearDown(self):
        self.conn.close(); self.temp.cleanup()

    def capture(self, url, robots, pages):
        def fake_open(target):
            self.opened.append(target)
            page = pages[target]
            if isinstance(page, Exception):
                raise page
            return Response(page)
        with mock.patch.object(archive, "_fetch_robots", return_value=robots), \
                mock.patch.object(archive, "_open", side_effect=fake_open):
            return archive.capture_url(self.conn, url, archive_root=self.root / "archive")

    def test_wildcard_disallow_blocks_capture(self):
        robots = (200, b"User-agent: *\nDisallow: */archivelot*\n")
        with self.assertRaises(PermissionError):
            self.capture("https://x.com/en-gb/archivelot/1", robots, {})
        self.assertEqual(self.opened, [])

    def test_redirect_into_a_disallowed_path_is_not_followed(self):
        robots = (200, b"User-agent: *\nDisallow: */archivelot*\n")
        start, archived = "https://x.com/en-gb/lot-1", "https://x.com/en-gb/archivelot/1"
        with self.assertRaises(PermissionError):
            self.capture(start, robots, {start: redirect(start, "/en-gb/archivelot/1")})
        self.assertEqual(self.opened, [start])
        self.assertNotIn(archived, self.opened)

    def test_permitted_redirect_is_followed_and_original_url_recorded(self):
        robots = (200, b"User-agent: *\nDisallow: /private\n")
        start, moved = "https://x.com/old", "https://x.com/new"
        row = self.capture(start, robots, {start: redirect(start, "/new"), moved: b"<html>ok</html>"})
        self.assertEqual(self.opened, [start, moved])
        self.assertEqual(row["url"], start)

    def test_robots_status_codes(self):
        page = {"https://x.com/a": b"ok"}
        for status, allowed in [(404, True), (410, True), (401, False), (403, False), (500, False)]:
            self.opened = []
            if allowed:
                self.capture("https://x.com/a", (status, b""), page)
            else:
                with self.assertRaises(PermissionError):
                    self.capture("https://x.com/a", (status, b""), page)
            self.assertEqual(bool(self.opened), allowed, status)

    def test_unreachable_robots_is_not_permission(self):
        with mock.patch.object(archive, "_fetch_robots", side_effect=OSError("down")):
            self.assertEqual(archive.robots_allowed("https://x.com/a"),
                             (False, "robots.txt could not be verified"))


if __name__ == "__main__":
    unittest.main()
