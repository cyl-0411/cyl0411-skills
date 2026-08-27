import argparse
import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "normalize_conference_metadata.py"
SPEC = importlib.util.spec_from_file_location("normalizer", SCRIPT)
normalizer = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(normalizer)


class NormalizeConferenceMetadataTests(unittest.TestCase):
    def args(self, conference=None, year=None, collection=None):
        return argparse.Namespace(conference=conference, year=year, collection=collection)

    def test_two_venues_and_years_get_distinct_collections(self):
        first = normalizer.normalize(
            {"venue": "Example Systems Conference", "year": 2024, "id": "A-1", "title": "Paper A"},
            1,
            self.args(),
        )
        second = normalizer.normalize(
            {"conference_name": "Quantum Workshop", "publication_year": 2027, "paperId": "B-1", "title": "Paper B"},
            2,
            self.args(),
        )
        self.assertEqual(first["collection"], "example-systems-conference-2024")
        self.assertEqual(second["collection"], "quantum-workshop-2027")
        self.assertNotEqual(first["collection"], second["collection"])

    def test_fallbacks_and_field_aliases(self):
        record = normalizer.normalize(
            {
                "title": "Portable Metadata",
                "DOI": "https://doi.org/10.1234/example",
                "author": [{"name": "A. Author"}, {"name": "B. Author"}],
                "pdf_url": "https://example.org/paper.pdf",
            },
            1,
            self.args("Portable Conference", "2030", "portable-2030"),
        )
        self.assertEqual(record["paper_id"], "10.1234/example")
        self.assertEqual(record["authors"], "A. Author; B. Author")
        self.assertEqual(record["citation_pdf_url"], "https://example.org/paper.pdf")
        self.assertEqual(record["collection"], "portable-2030")

    def test_json_container_variants(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "input.json"
            source.write_text('{"papers": [{"title": "One"}]}', encoding="utf-8")
            self.assertEqual(normalizer.load_records(source), [{"title": "One"}])


if __name__ == "__main__":
    unittest.main()
