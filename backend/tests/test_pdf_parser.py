import io
import unittest
from pypdf import PdfWriter

from app.services.pdf_parser import chunk_pdf_pages, parse_pdf_bytes


def create_sample_pdf_bytes(page_texts: list[str]) -> bytes:
    """Helper to create a PDF with synthetic pages in memory."""
    from pypdf.generic import (
        ArrayObject,
        DecodedStreamObject,
        DictionaryObject,
        NameObject,
        NumberObject,
    )

    writer = PdfWriter()
    for text in page_texts:
        # Create a basic page using PdfWriter's blank page and text stream
        page = writer.add_blank_page(width=612, height=792)
        # In pypdf, we can add a text stream or annotation for clean test extraction
        # Alternatively, write standard PDF content stream
        content_stream = f"BT /F1 12 Tf 72 712 Td ({text}) Tj ET".encode("latin1")
        stream_obj = DecodedStreamObject()
        stream_obj.set_data(content_stream)
        page[NameObject("/Contents")] = stream_obj

        # Add Font resource
        font_dict = DictionaryObject({
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        })
        page[NameObject("/Resources")] = DictionaryObject({
            NameObject("/Font"): DictionaryObject({
                NameObject("/F1"): font_dict,
            })
        })

    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


class TestPdfParser(unittest.TestCase):
    def test_parse_valid_multipage_pdf(self):
        page_1 = "Nexa One Smartphone User Manual. Specifications: 5000mAh battery, 33W charging."
        page_2 = "Troubleshooting Guide. If your screen is unresponsive, press power and volume up for 10 seconds."
        pdf_bytes = create_sample_pdf_bytes([page_1, page_2])

        full_text, pages = parse_pdf_bytes(pdf_bytes, filename="nexa_manual.pdf")
        self.assertIn("Nexa One Smartphone", full_text)
        self.assertIn("Troubleshooting Guide", full_text)
        self.assertEqual(len(pages), 2)
        self.assertEqual(pages[0]["page"], 1)
        self.assertIn("5000mAh", pages[0]["text"])
        self.assertEqual(pages[1]["page"], 2)
        self.assertIn("unresponsive", pages[1]["text"])

    def test_parse_empty_or_invalid_bytes(self):
        with self.assertRaises(ValueError) as ctx:
            parse_pdf_bytes(b"", filename="empty.pdf")
        self.assertIn("Empty", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx2:
            parse_pdf_bytes(b"not a valid pdf document header", filename="corrupt.pdf")
        self.assertIn("corrupt", str(ctx2.exception).lower())

    def test_chunk_pdf_pages_metadata_retention(self):
        pages = [
            {
                "page": 1,
                "text": "Nexa One Smartphone Specs.\n\n" * 15,  # Long enough to create multiple chunks
            },
            {
                "page": 2,
                "text": "Warranty terms and RMA return policy details.\n\n" * 10,
            },
        ]
        chunks = chunk_pdf_pages(pages, filename="nexa_one.pdf", chunk_size=300, chunk_overlap=50)
        self.assertGreater(len(chunks), 2)

        for c in chunks:
            self.assertIn("chunk_text", c)
            self.assertIn("metadata", c)
            self.assertIn("page", c["metadata"])
            self.assertEqual(c["metadata"]["filename"], "nexa_one.pdf")
            self.assertEqual(c["metadata"]["source_type"], "pdf")


if __name__ == "__main__":
    unittest.main()

