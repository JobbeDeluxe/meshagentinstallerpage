import json
import os
import tempfile
import unittest
from pathlib import Path

from app import create_app


class MeshInstallerAppTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.codes_file = Path(self.tmp.name) / "codes.json"
        os.environ["CODES_FILE"] = str(self.codes_file)
        os.environ["ADMIN_PASSWORD"] = "test-password"
        os.environ["SECRET_KEY"] = "test-secret"
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()
        os.environ.pop("CODES_FILE", None)
        os.environ.pop("ADMIN_PASSWORD", None)
        os.environ.pop("SECRET_KEY", None)

    def test_lookup_returns_download_for_known_code(self):
        self.codes_file.write_text(
            json.dumps(
                {
                    "A3F7K2": {
                        "name": "Mamas Laptop",
                        "download_url": "https://mesh.example.de/agent.exe",
                    }
                }
            ),
            encoding="utf-8",
        )

        response = self.client.post("/api/lookup", json={"code": "a3f-7k2"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["name"], "Mamas Laptop")
        self.assertEqual(response.json["download_url"], "https://mesh.example.de/agent.exe")

    def test_lookup_rejects_unknown_code(self):
        response = self.client.post("/api/lookup", json={"code": "NOPE"})

        self.assertEqual(response.status_code, 404)
        self.assertFalse(response.json["ok"])

    def test_admin_can_create_code(self):
        with self.client.session_transaction() as session:
            session["admin"] = True
            session["csrf_token"] = "token"

        response = self.client.post(
            "/admin/codes",
            data={
                "csrf_token": "token",
                "code": "family1",
                "name": "Familien PC",
                "download_url": "https://mesh.example.de/family.exe",
            },
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 302)
        saved = json.loads(self.codes_file.read_text(encoding="utf-8"))
        self.assertEqual(saved["FAMILY1"]["name"], "Familien PC")

    def test_admin_rejects_invalid_url(self):
        with self.client.session_transaction() as session:
            session["admin"] = True
            session["csrf_token"] = "token"

        response = self.client.post(
            "/admin/codes",
            data={
                "csrf_token": "token",
                "code": "family1",
                "name": "Familien PC",
                "download_url": "not-a-link",
            },
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(self.codes_file.exists())


if __name__ == "__main__":
    unittest.main()
