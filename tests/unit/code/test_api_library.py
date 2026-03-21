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
    def test_radial_relation_labels_get_resolved_geometry_without_affecting_tree_edges(self) -> None:
        source_text = (
            "1 Root\n"
            "Body.\n\n"
            "supports -> 1.1 First branch\n"
            "Body.\n\n"
            "documents -> 1.2 Second branch\n"
            "Body.\n\n"
            "1.1.1 Leaf A\n"
            "Body.\n\n"
            "1.2.1 Leaf B\n"
            "Body.\n"
        )

        radial_result = koala.render_text(
            source_text,
            layout="radial",
            theme="academic",
            size="a4",
        )
        radial_edges = [edge for edge in radial_result.context.scene.edges if edge.relation_label]

        self.assertTrue(radial_edges)
        self.assertTrue(any(edge.label_bounds is not None for edge in radial_edges))
        self.assertTrue(all(abs(edge.label_angle) <= 35.0 for edge in radial_edges))
        self.assertNotIn('opacity="0.4"', radial_result.svg)

        for edge in radial_edges:
            self.assertIsNotNone(edge.label_bounds)
            assert edge.label_bounds is not None
            for box in radial_result.context.scene.boxes.values():
                overlaps = not (
                    edge.label_bounds[2] <= box.x
                    or (box.x + box.width) <= edge.label_bounds[0]
                    or edge.label_bounds[3] <= box.y
                    or (box.y + box.height) <= edge.label_bounds[1]
                )
                self.assertFalse(overlaps, f"El label '{edge.relation_label}' invadio el nodo {box.node.number}.")

        tree_context = koala.inspect_text(
            source_text,
            layout="tree",
            theme="academic",
            size="a4",
        )
        tree_edges = [edge for edge in tree_context.scene.edges if edge.relation_label]

        self.assertTrue(tree_edges)
        self.assertTrue(all(edge.label_angle == 0.0 for edge in tree_edges))
        self.assertTrue(all(edge.label_bounds is None for edge in tree_edges))

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
