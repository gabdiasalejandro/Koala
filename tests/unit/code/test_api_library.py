import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[3]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import koala
from koala.cli import main as cli_main


class LibraryApiTests(unittest.TestCase):
    EXPORT_SAMPLE_TEXT = (
        "@theme jungle\n"
        "@size a4_landscape\n\n"
        "main:: 1 Strategic Map\n"
        "High level direction for the product.\n\n"
        "supports -> 1.1 API\n"
        "Server-friendly exports in memory.\n\n"
        "documents -> 1.2 Output\n"
        "SVG, PNG, and decorated PDF.\n"
    )

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

    def test_render_text_accepts_explicit_tree_type(self) -> None:
        result = koala.render_text(
            "1 Root\nBody.\n",
            type="tree",
            layout="tree",
            theme="academic",
        )

        self.assertEqual(result.document_type, "tree")
        self.assertEqual(result.context.settings.layout_kind, "tree")

    def test_render_text_accepts_explicit_matrix_type(self) -> None:
        result = koala.render_text(
            "matrix:: Decision Matrix\n"
            "columns:: Criterion | Option A | Option B\n"
            "row:: Cost | Lower initial cost | Higher initial cost\n"
            "row:: Fit | Good for teams | Strong for governance\n"
            "footer:: Recommendation | Choose the option that best matches operating maturity.\n",
            type="matrix",
            layout="matrix",
            theme="academic",
            typography="formal",
        )

        self.assertEqual(result.document_type, "matrix")
        self.assertEqual(result.context.settings.layout_kind, "matrix")
        self.assertIn("Decision Matrix", result.svg)
        self.assertIn("<rect", result.svg)

    def test_render_text_accepts_explicit_flowchart_type(self) -> None:
        result = koala.render_text(
            "flowchart:: Publish\n\n"
            "start:: draft :: Draft\n"
            "decision:: review :: Approved?\n"
            "end:: done :: Done\n\n"
            "draft -> review\n"
            "review -> done :: yes\n",
            type="flowchart",
            layout="flowchart",
            theme="ocean",
            typography="default",
        )

        self.assertEqual(result.document_type, "flowchart")
        self.assertEqual(result.context.settings.layout_kind, "flowchart")
        self.assertIn("Approved?", result.svg)
        self.assertIn("<polygon", result.svg)

    def test_available_typographies_exposes_academic_formal_and_casual_presets(self) -> None:
        self.assertEqual(koala.available_document_types(), ("flowchart", "matrix", "tree"))

        all_typographies = koala.available_typographies()
        tree_typographies = koala.available_typographies(type="tree")
        matrix_typographies = koala.available_typographies(type="matrix")
        flowchart_typographies = koala.available_typographies(type="flowchart")

        for name in ("academic", "formal", "casual"):
            self.assertIn(name, all_typographies)
            self.assertIn(name, tree_typographies)
            self.assertIn(name, matrix_typographies)
            self.assertIn(name, flowchart_typographies)
        self.assertIn("radial", tree_typographies)
        self.assertNotIn("radial", matrix_typographies)
        self.assertNotIn("radial", flowchart_typographies)

    def test_render_text_accepts_new_typography_presets_from_python_api(self) -> None:
        tree_result = koala.render_text(
            "1 Root\nBody.\n",
            type="tree",
            layout="tree",
            typography="academic",
        )
        matrix_result = koala.render_text(
            "matrix:: Decision Matrix\n"
            "columns:: Criterion | Option A | Option B\n"
            "row:: Cost | Lower initial cost | Higher initial cost\n",
            type="matrix",
            layout="matrix",
            typography="casual",
        )

        self.assertEqual(tree_result.context.settings.typography_name, "academic")
        self.assertIn("Times New Roman", tree_result.svg)
        self.assertEqual(matrix_result.context.settings.typography_name, "casual")
        self.assertIn("Trebuchet MS", matrix_result.svg)
        self.assertIn("Verdana", matrix_result.svg)

    def test_cli_typographies_can_be_filtered_by_document_type(self) -> None:
        stdout = io.StringIO()

        with redirect_stdout(stdout):
            exit_code = cli_main(["typographies", "--type", "matrix"])

        output = stdout.getvalue().splitlines()
        self.assertEqual(exit_code, 0)
        self.assertIn("academic", output)
        self.assertIn("casual", output)
        self.assertIn("formal", output)
        self.assertNotIn("radial", output)

    def test_render_text_rejects_unknown_document_type(self) -> None:
        with self.assertRaises(koala.UnknownDocumentTypeError):
            koala.render_text(
                "1 Root\nBody.\n",
                type="timeline",
                layout="tree",
                theme="academic",
            )

    def test_tree_type_rejects_matrix_syntax(self) -> None:
        with self.assertRaises(koala.DocumentTypeMismatchError):
            koala.render_text(
                "matrix:: Comparison\ncolumns:: A | B\nrow:: Cost | Low\n",
                type="tree",
                layout="tree",
                theme="academic",
            )

    def test_matrix_type_rejects_tree_syntax(self) -> None:
        with self.assertRaises(koala.DocumentTypeMismatchError):
            koala.render_text(
                "main:: 1 Strategic Map\nBody.\n",
                type="matrix",
                layout="matrix",
                theme="academic",
            )

    def test_render_text_rejects_non_string_text_with_domain_error(self) -> None:
        with self.assertRaises(koala.InvalidRenderConfigError):
            koala.render_text(123, type="tree", layout="tree")  # type: ignore[arg-type]

    def test_render_text_rejects_invalid_text_align_with_domain_error(self) -> None:
        with self.assertRaises(koala.InvalidRenderConfigError):
            koala.render_text(
                "1 Root\nBody.\n",
                type="tree",
                layout="tree",
                text_align="center",
            )

    def test_export_text_rejects_invalid_format_type_with_domain_error(self) -> None:
        with self.assertRaises(koala.InvalidRenderConfigError):
            koala.export_text(
                "1 Root\nBody.\n",
                type="tree",
                layout="tree",
                format=123,  # type: ignore[arg-type]
            )

    def test_render_text_can_enforce_server_side_input_limits(self) -> None:
        with self.assertRaises(koala.InputLimitExceededError):
            koala.render_text(
                "1 Root\nBody.\n\n1.1 Child\nBody.\n",
                type="tree",
                layout="tree",
                max_nodes=1,
            )

    def test_validate_text_can_treat_warnings_as_limit_errors(self) -> None:
        with self.assertRaises(koala.InputLimitExceededError):
            koala.validate_text(
                "1.2 Missing parent\nBody.\n",
                type="tree",
                layout="tree",
                max_warnings=0,
            )

    def test_safe_render_text_renders_tree_with_server_defaults(self) -> None:
        result = koala.safe_render_text(
            "1 Root\nBody.\n",
            type="tree",
            layout="tree",
            theme="academic",
        )

        self.assertEqual(result.document_type, "tree")
        self.assertIsNone(result.output_svg)
        self.assertIn("<svg", result.svg)

    def test_safe_render_text_rejects_warnings_by_default(self) -> None:
        with self.assertRaises(koala.InputLimitExceededError):
            koala.safe_render_text(
                "1.2 Missing parent\nBody.\n",
                type="tree",
                layout="tree",
            )

    def test_safe_render_text_allows_warning_limit_override(self) -> None:
        result = koala.safe_render_text(
            "1.2 Missing parent\nBody.\n",
            type="tree",
            layout="tree",
            max_warnings=2,
        )

        self.assertEqual(result.document_type, "tree")
        self.assertGreater(len(result.context.parsed.warnings), 0)

    def test_safe_render_text_rejects_flowchart_for_now(self) -> None:
        with self.assertRaises(koala.InvalidRenderConfigError):
            koala.safe_render_text(
                "flowchart:: Publish\nstep:: draft\n",
                type="flowchart",
                layout="flowchart",
            )

    def test_safe_export_text_returns_svg_bytes_without_writing(self) -> None:
        export = koala.safe_export_text(
            "matrix:: Decision Matrix\n"
            "columns:: Criterion | Option A | Option B\n"
            "row:: Cost | Low | High\n",
            type="matrix",
            layout="matrix",
            format="svg",
            max_warnings=0,
        )

        self.assertEqual(export.media_type, "image/svg+xml")
        self.assertIsNone(export.output_path)
        self.assertIn(b"<svg", export.content)

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

    def test_export_text_generates_svg_png_and_decorated_pdf_samples(self) -> None:
        output_dir = ROOT_DIR / "output" / "export_samples"
        output_dir.mkdir(parents=True, exist_ok=True)

        svg = koala.export_text(
            self.EXPORT_SAMPLE_TEXT,
            format="svg",
            layout="tree",
            theme="jungle",
            output=output_dir / "sample.svg",
        )
        png = koala.export_text(
            self.EXPORT_SAMPLE_TEXT,
            format="png",
            quality="medium",
            layout="tree",
            theme="jungle",
            output=output_dir / "sample.medium.png",
        )
        pdf = koala.export_text(
            self.EXPORT_SAMPLE_TEXT,
            format="pdf",
            quality="high",
            layout="tree",
            theme="jungle",
            output=output_dir / "sample.high.pdf",
        )

        self.assertEqual(svg.media_type, "image/svg+xml")
        self.assertEqual(png.media_type, "image/png")
        self.assertEqual(pdf.media_type, "application/pdf")
        self.assertTrue(svg.content.startswith(b"<?xml") or b"<svg" in svg.content[:200])
        self.assertTrue(png.content.startswith(b"\x89PNG\r\n\x1a\n"))
        self.assertTrue(pdf.content.startswith(b"%PDF"))
        self.assertEqual(svg.output_path, output_dir / "sample.svg")
        self.assertEqual(png.output_path, output_dir / "sample.medium.png")
        self.assertEqual(pdf.output_path, output_dir / "sample.high.pdf")
        self.assertTrue(svg.output_path.exists())
        self.assertTrue(png.output_path.exists())
        self.assertTrue(pdf.output_path.exists())
        self.assertGreater(len(png.content), len(svg.content))
        self.assertGreater(len(pdf.content), 500)


if __name__ == "__main__":
    unittest.main()
