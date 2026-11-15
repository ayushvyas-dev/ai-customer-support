import io
import unittest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app, create_token
from tests.test_pdf_parser import create_sample_pdf_bytes


class TestKBUploadAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.token = create_token("admin_user")
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_upload_valid_pdf_success(self):
        sample_pdf = create_sample_pdf_bytes([
            "Nexa One specifications. 5000mAh battery, 33W fast charging.",
            "Display specs: 6.7 inch AMOLED 120Hz."
        ])

        with patch("app.db.upsert_knowledge_base_entry", return_value=101), \
             patch("app.main.index_pdf_document", return_value=4):
            files = {"file": ("nexa_one_specs.pdf", sample_pdf, "application/pdf")}
            data = {"section": "smartphone", "title": "Nexa One Official Specs"}
            res = self.client.post("/api/knowledge-base/upload", headers=self.headers, files=files, data=data)

        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["id"], 101)
        self.assertEqual(body["title"], "Nexa One Official Specs")
        self.assertEqual(body["section"], "smartphone")
        self.assertEqual(body["pages"], 2)
        self.assertEqual(body["chunks"], 4)
        self.assertEqual(body["status"], "indexed")

    def test_upload_rejects_non_pdf_file(self):
        files = {"file": ("malicious.txt", b"plain text content", "text/plain")}
        data = {"section": "smartphone"}
        res = self.client.post("/api/knowledge-base/upload", headers=self.headers, files=files, data=data)
        self.assertEqual(res.status_code, 400)
        self.assertIn("Only PDF files", res.json()["detail"])

    def test_upload_rejects_unauthorized(self):
        sample_pdf = create_sample_pdf_bytes(["Test content"])
        files = {"file": ("test.pdf", sample_pdf, "application/pdf")}
        data = {"section": "smartphone"}
        res = self.client.post("/api/knowledge-base/upload", files=files, data=data)
        self.assertEqual(res.status_code, 401)


if __name__ == "__main__":
    unittest.main()
