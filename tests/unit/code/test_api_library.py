import sys
import tempfile
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[3]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import koala


class LibraryApiTests(unittest.TestCase):
    def test_render_text_returns_svg_in_memory(self) -> None:
        result = koala.render_text(
            "1 Root\nBody.\n",
            layout="tree",
            theme="academic",
        )

        self.assertIsNone(result.output_svg)
        self.assertIn("<svg", result.svg)
        self.assertIn("<text", result.svg)
        self.assertEqual(result.context.settings.layout_kind, "tree")

    def test_render_text_hides_node_numbers_by_default(self) -> None:
        result = koala.render_text(
            "1 Root\nBody.\n",
            layout="tree",
            theme="academic",
        )

        self.assertFalse(result.context.settings.show_node_numbers)

    def test_compile_text_legacy_persists_svg_and_returns_svg_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base_dir = Path(tmp_dir)

            result = koala.compile_text(
                "1 Root\nBody.\n",
                layout="tree",
                theme="academic",
                base_dir=base_dir,
                output_name="diagram",
            )

            expected_output = base_dir / "diagram.tree.svg"

            self.assertEqual(result.output_svg, expected_output)
            self.assertIsNotNone(result.output_svg)
            self.assertTrue(result.output_svg.exists())
            self.assertEqual(result.output_svg.read_text(encoding="utf-8"), result.svg)

    def test_compile_text_resolves_relative_explicit_output_against_base_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base_dir = Path(tmp_dir)

            result = koala.compile_text(
                "1 Root\nBody.\n",
                layout="tree",
                theme="academic",
                base_dir=base_dir,
                output="exports/custom_diagram",
            )

            self.assertEqual(result.output_svg, base_dir / "exports" / "custom_diagram.svg")
            self.assertIsNotNone(result.output_svg)
            self.assertTrue(result.output_svg.exists())

    def test_compile_text_ignores_output_dir_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base_dir = Path(tmp_dir)

            result = koala.compile_text(
                "@output-dir redirected\n1 Root\nBody.\n",
                layout="tree",
                theme="academic",
                base_dir=base_dir,
                output_name="diagram",
            )

            self.assertEqual(result.output_svg, base_dir / "diagram.tree.svg")
            self.assertTrue((base_dir / "diagram.tree.svg").exists())
            self.assertFalse((base_dir / "redirected").exists())

    def test_save_text_writes_txt_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base_dir = Path(tmp_dir)

            output_path = koala.save_text(
                "1 Root\nBody.\n",
                "drafts/example",
                base_dir=base_dir,
            )

            self.assertEqual(output_path, (base_dir / "drafts" / "example.txt").resolve())
            self.assertTrue(output_path.exists())
            self.assertEqual(output_path.read_text(encoding="utf-8"), "1 Root\nBody.\n")


if __name__ == "__main__":
    unittest.main()
