import unittest
from unittest.mock import MagicMock, patch

from app import db


class TestKBDatabase(unittest.TestCase):
    @patch("app.db.connect")
    def test_upsert_knowledge_base_entry_with_pdf_metadata(self, mock_connect):
        mock_conn = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_conn
        mock_conn.execute.return_value.fetchone.return_value = {"id": 42}

        entry_id = db.upsert_knowledge_base_entry(
            section="smartphone",
            title="Nexa One Manual.pdf",
            content="Full user manual text",
            source_type="pdf",
            filename="Nexa One Manual.pdf",
        )
        self.assertEqual(entry_id, 42)
        args, kwargs = mock_conn.execute.call_args
        sql = args[0]
        params = args[1]
        self.assertIn("source_type", sql)
        self.assertIn("filename", sql)
        self.assertIn("pdf", params)
        self.assertIn("Nexa One Manual.pdf", params)

    @patch("app.db.connect")
    def test_get_knowledge_base_entries_includes_source_type(self, mock_connect):
        mock_conn = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_conn
        mock_conn.execute.return_value.fetchall.return_value = [
            {
                "id": 1,
                "section": "smartphone",
                "title": "Specs",
                "content": "Tech specs",
                "source_type": "text",
                "filename": None,
                "updated_at": "2026-11-15T00:00:00Z",
            },
            {
                "id": 2,
                "section": "smartphone",
                "title": "Manual.pdf",
                "content": "PDF extracted text",
                "source_type": "pdf",
                "filename": "Manual.pdf",
                "updated_at": "2026-11-15T00:00:00Z",
            },
        ]

        items = db.get_knowledge_base_entries(section="smartphone")
        self.assertEqual(len(items), 2)
        self.assertEqual(items[1]["source_type"], "pdf")
        self.assertEqual(items[1]["filename"], "Manual.pdf")


if __name__ == "__main__":
    unittest.main()

