"""Run from the skill root: PYTHONPATH=scripts python3 -m unittest discover -s tests"""

import base64
import json
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

from archdesign.adapters.docx_reader import DocxReader
from archdesign.adapters.fs_store import FilesystemExtractionStore
from archdesign.adapters.image_reader import ImageReader
from archdesign.adapters.pdf_reader import PdfReader
from archdesign.adapters.text_reader import TextReader
from archdesign.application.use_cases import ExtractDocuments
from archdesign.domain.documents import DocumentKind, ExtractionResult, SourceDocument
from archdesign.domain.errors import DocumentError

PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGP4z8DwHwAFAAH/q842iQAAAABJRU5ErkJggg=="
)
NS = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
DOCUMENT_XML = f"""<?xml version="1.0" encoding="UTF-8"?>
<w:document {NS}><w:body>
<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>Collections analytics</w:t></w:r></w:p>
<w:p><w:r><w:t>We need payment propensity scores.</w:t></w:r></w:p>
<w:p><w:pPr><w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr></w:pPr><w:r><w:t>Sources: CRM, SMS</w:t></w:r></w:p>
<w:tbl><w:tr><w:tc><w:p><w:r><w:t>Metric</w:t></w:r></w:p></w:tc><w:tc><w:p><w:r><w:t>Value</w:t></w:r></w:p></w:tc></w:tr>
<w:tr><w:tc><w:p><w:r><w:t>Accounts</w:t></w:r></w:p></w:tc><w:tc><w:p><w:r><w:t>2M</w:t></w:r></w:p></w:tc></w:tr></w:tbl>
</w:body></w:document>"""


def make_docx(path, xml=DOCUMENT_XML, media=None):
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("word/document.xml", xml)
        for name, data in (media or {}).items():
            zf.writestr(f"word/media/{name}", data)


def make_pdf(path):
    content = b"BT /F1 18 Tf 20 50 Td (Orders pipeline) Tj ET"
    path.write_bytes(
        b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 300 100]/Contents 4 0 R"
        b"/Resources<</Font<</F1 5 0 R>>>>>>endobj\n"
        + b"4 0 obj<</Length %d>>stream\n" % len(content) + content + b"\nendstream endobj\n"
        b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
        b"trailer<</Root 1 0 R/Size 6>>\n%%EOF\n"
    )


class TmpDirTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)


class DocxReaderTest(TmpDirTest):
    def test_extracts_headings_lists_tables_and_images(self):
        path = self.tmp / "case.docx"
        make_docx(path, media={"image1.png": PNG, "chart.emf": b"vector"})
        doc = DocxReader().read(str(path))
        self.assertEqual(doc.kind, DocumentKind.DOCX)
        self.assertIn("# Collections analytics", doc.text)
        self.assertIn("- Sources: CRM, SMS", doc.text)
        self.assertIn("| Accounts | 2M |", doc.text)
        self.assertIn("|---|---|", doc.text)
        self.assertEqual([i.name for i in doc.images], ["image1.png"])
        self.assertTrue(any("chart.emf" in w for w in doc.warnings))

    def test_refuses_doctype(self):
        path = self.tmp / "evil.docx"
        make_docx(path, xml='<?xml version="1.0"?><!DOCTYPE x [<!ENTITY a "b">]><w:document ' + NS + "/>")
        with self.assertRaises(DocumentError) as ctx:
            DocxReader().read(str(path))
        self.assertIn("DOCTYPE", str(ctx.exception))

    def test_not_a_zip_and_missing_file(self):
        bad = self.tmp / "bad.docx"
        bad.write_bytes(b"not a zip")
        with self.assertRaises(DocumentError):
            DocxReader().read(str(bad))
        with self.assertRaises(DocumentError):
            DocxReader().read(str(self.tmp / "missing.docx"))


class ImageAndTextReaderTest(TmpDirTest):
    def test_image_is_passed_through(self):
        path = self.tmp / "diagram.png"
        path.write_bytes(PNG)
        doc = ImageReader().read(str(path))
        self.assertEqual(doc.images[0].data, PNG)
        self.assertTrue(doc.warnings)

    def test_fake_image_is_rejected(self):
        path = self.tmp / "fake.png"
        path.write_bytes(b"<html>not an image</html>")
        with self.assertRaises(DocumentError):
            ImageReader().read(str(path))

    def test_text_reader(self):
        path = self.tmp / "case.md"
        path.write_text("# Case\nhello", encoding="utf-8")
        self.assertIn("hello", TextReader().read(str(path)).text)


@unittest.skipUnless(shutil.which("pdftotext") and shutil.which("pdftoppm"), "poppler is not installed")
class PdfReaderTest(TmpDirTest):
    def test_short_pdf_is_rasterized_with_warning(self):
        path = self.tmp / "case.pdf"
        make_pdf(path)
        doc = PdfReader().read(str(path))
        self.assertIn("Orders pipeline", doc.text)
        self.assertTrue(doc.images and doc.images[0].data.startswith(b"\x89PNG"))
        self.assertTrue(any("little or no text" in w for w in doc.warnings))

    def test_missing_tool_message_is_actionable(self):
        path = self.tmp / "case.pdf"
        make_pdf(path)
        with self.assertRaises(DocumentError) as ctx:
            PdfReader(which=lambda name: None, pypdf_loader=lambda: None).read(str(path))
        self.assertIn("poppler-utils", str(ctx.exception))
        self.assertIn("pypdf", str(ctx.exception))


class PdfFallbackTest(TmpDirTest):
    """Without poppler (for example on Windows) text comes from pypdf when it is installed."""

    def test_uses_pypdf_when_poppler_is_missing(self):
        class FakePage:
            def extract_text(self):
                return "Orders pipeline " * 10

        class FakePyPdf:
            def __init__(self, path):
                self.pages = [FakePage()]

        path = self.tmp / "case.pdf"
        path.write_bytes(b"%PDF-1.4")
        doc = PdfReader(which=lambda name: None, pypdf_loader=lambda: FakePyPdf).read(str(path))
        self.assertIn("Orders pipeline", doc.text)
        self.assertEqual(doc.images, ())
        self.assertEqual(doc.warnings, ())

    def test_low_text_without_pdftoppm_warns_instead_of_failing(self):
        class EmptyPage:
            def extract_text(self):
                return ""

        class FakePyPdf:
            def __init__(self, path):
                self.pages = [EmptyPage()]

        path = self.tmp / "scan.pdf"
        path.write_bytes(b"%PDF-1.4")
        doc = PdfReader(which=lambda name: None, pypdf_loader=lambda: FakePyPdf).read(str(path))
        self.assertTrue(any("could not be rasterized" in w for w in doc.warnings))


class ExtractDocumentsTest(TmpDirTest):
    def test_end_to_end_writes_files_and_manifest(self):
        docx = self.tmp / "case.docx"
        make_docx(docx, media={"image1.png": PNG})
        png = self.tmp / "sketch.png"
        png.write_bytes(PNG)
        out = self.tmp / "out"
        use_case = ExtractDocuments([DocxReader(), ImageReader()], FilesystemExtractionStore(str(out)))
        results = use_case.execute([str(docx), str(png)])
        self.assertEqual(len(results), 2)
        self.assertIn("Collections analytics", (out / "case" / "text.md").read_text(encoding="utf-8"))
        self.assertTrue((out / "case" / "media" / "01-image1.png").exists())
        manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual([m["kind"] for m in manifest], ["docx", "image"])

    def test_same_name_twice_does_not_overwrite(self):
        a, b = self.tmp / "a" / "case.md", self.tmp / "b" / "case.md"
        for p, text in ((a, "first"), (b, "second")):
            p.parent.mkdir()
            p.write_text(text)
        out = self.tmp / "out"
        ExtractDocuments([TextReader()], FilesystemExtractionStore(str(out))).execute([str(a), str(b)])
        self.assertEqual((out / "case" / "text.md").read_text(), "first")
        self.assertEqual((out / "case_2" / "text.md").read_text(), "second")

    def test_unsupported_type_lists_supported_ones(self):
        legacy = self.tmp / "old.doc"
        legacy.write_bytes(b"x")
        use_case = ExtractDocuments([TextReader()], FilesystemExtractionStore(str(self.tmp / "o")))
        with self.assertRaises(DocumentError) as ctx:
            use_case.execute([str(legacy)])
        self.assertIn(".docx", str(ctx.exception))
        self.assertIn(".md", str(ctx.exception))

    def test_use_case_works_with_fakes_only(self):
        class FakeReader:
            suffixes = (".xyz",)

            def read(self, path):
                return SourceDocument("n.xyz", DocumentKind.TEXT, "hi")

        class FakeStore:
            def __init__(self):
                self.manifest = None

            def save(self, document):
                return ExtractionResult(document.name, document.kind, "d", len(document.text), (), ())

            def write_manifest(self, results):
                self.manifest = results
                return "m"

        store = FakeStore()
        results = ExtractDocuments([FakeReader()], store).execute(["file.xyz"])
        self.assertEqual(results[0].characters, 2)
        self.assertEqual(store.manifest, results)


if __name__ == "__main__":
    unittest.main()
