from __future__ import annotations

import json
import shutil
import sys
import time
import unittest
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[3]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import koala
from koala.core.shared.io import load_input_text
from koala.render.shared.export import ExportConverter
from koala.render.shared.themes import ThemeCatalog


TREE_LAYOUTS = ("tree", "synoptic", "synoptic_boxes", "radial")
TEXT_ALIGN_SEQUENCE = ("left", "justify")
TREE_TYPOGRAPHIES = ("default", "radial")
MATRIX_TYPOGRAPHIES = ("formal", "default")
PAGE_SIZES = ("a4", "a4_landscape", "square")
BACKGROUND_COLORS = ("#F7F4ED", "#F1F7FB", "#F8F3FF", "#F4F9F1")
TREE_MOCKS = {
    "left": ROOT_DIR / "tests/end_to_end/mocks/alignment_left.txt",
    "justify": ROOT_DIR / "tests/end_to_end/mocks/alignment_justify.txt",
}
MATRIX_MOCK = ROOT_DIR / "tests/end_to_end/mocks/comparative_matrix.txt"


@dataclass(frozen=True)
class E2ECase:
    index: int
    document_type: str
    layout: str
    theme: str
    text_align: str
    typography: str
    page_size: str
    show_node_numbers: bool
    background: str | None

    @property
    def case_id(self) -> str:
        node_numbers = "numbers_on" if self.show_node_numbers else "numbers_off"
        return (
            f"{self.index:02d}_{self.document_type}_{self.layout}_{self.theme}_"
            f"{self.text_align}_{self.typography}_{self.page_size}_{node_numbers}"
        )

    @property
    def mock_path(self) -> Path:
        if self.document_type == "matrix":
            return MATRIX_MOCK
        return TREE_MOCKS[self.text_align]

    @property
    def output_dir(self) -> Path:
        return ROOT_DIR / "tests/end_to_end/output" / self.document_type / self.theme

    @property
    def output_stem(self) -> str:
        return f"{self.index:02d}_{self.layout}_{self.text_align}_{self.typography}_{self.page_size}"


class RenderEndToEndTest(unittest.TestCase):
    output_root = ROOT_DIR / "tests/end_to_end/output"
    manifest_path = ROOT_DIR / "tests/end_to_end/e2e_manifest.json"
    manifest: list[dict[str, object]] = []
    summary: dict[str, object] = {}

    @classmethod
    def setUpClass(cls) -> None:
        if cls.output_root.exists():
            shutil.rmtree(cls.output_root)
        cls.output_root.mkdir(parents=True, exist_ok=True)
        if cls.manifest_path.exists():
            cls.manifest_path.unlink()
        cls.manifest = []
        cls.summary = {}

    @classmethod
    def tearDownClass(cls) -> None:
        cls.manifest_path.write_text(
            json.dumps(cls.manifest, indent=2, ensure_ascii=True, sort_keys=True),
            encoding="utf-8",
        )
        if cls.summary:
            print(
                "E2E summary: "
                f"diagrams={cls.summary['diagrams']} "
                f"exports={cls.summary['exports']} "
                f"files={cls.summary['files']} "
                f"types={cls.summary['type_count']} ({cls.summary['types']}) "
                f"render_svg={cls.summary['render_svg_seconds']:.3f}s "
                f"write_svg={cls.summary['write_svg_seconds']:.3f}s "
                f"png_medium={cls.summary['png_medium_seconds']:.3f}s "
                f"png_high={cls.summary['png_high_seconds']:.3f}s "
                f"pdf={cls.summary['pdf_seconds']:.3f}s"
            )

    def test_render_gallery(self) -> None:
        cases = self._build_cases()
        for case in cases:
            with self.subTest(case=case.case_id):
                result, render_seconds = self._render_case(case)
                output_paths, export_timings = self._write_outputs(case, result)
                timings = {"render_svg": render_seconds, **export_timings}
                svg_text = output_paths["svg"].read_text(encoding="utf-8")

                self._assert_settings(case, result)
                self._assert_svg_structure(case, result, svg_text)
                self._assert_theme_serialization(case, result, svg_text)
                self._assert_exports(output_paths)
                self._record_manifest(case, output_paths, timings)
        self._record_summary(cases)

    @staticmethod
    def _build_cases() -> list[E2ECase]:
        cases: list[E2ECase] = []
        index = 0

        for theme in ThemeCatalog.available_names():
            for layout in TREE_LAYOUTS:
                cases.append(_case(index, "tree", layout, theme))
                index += 1
            cases.append(_case(index, "matrix", "matrix", theme))
            index += 1

        return cases

    def _render_case(self, case: E2ECase):
        started_at = time.perf_counter()
        result = koala.render_text(
            load_input_text(str(case.mock_path)),
            type=case.document_type,
            layout=case.layout,
            theme=case.theme,
            typography=case.typography,
            size=case.page_size,
            text_align=case.text_align,
            show_node_numbers=case.show_node_numbers,
            background=case.background,
        )
        return result, time.perf_counter() - started_at

    def _write_outputs(self, case: E2ECase, result) -> tuple[dict[str, Path], dict[str, float]]:
        case.output_dir.mkdir(parents=True, exist_ok=True)
        svg_path = case.output_dir / f"{case.output_stem}.svg"
        png_medium_path = case.output_dir / f"{case.output_stem}.medium.png"
        png_high_path = case.output_dir / f"{case.output_stem}.high.png"
        pdf_path = case.output_dir / f"{case.output_stem}.pdf"

        started_at = time.perf_counter()
        svg_path.write_text(result.svg, encoding="utf-8")
        write_svg_seconds = time.perf_counter() - started_at

        started_at = time.perf_counter()
        png_medium = ExportConverter.convert(result, format="png", quality="medium")
        png_medium_seconds = time.perf_counter() - started_at

        started_at = time.perf_counter()
        png_high = ExportConverter.convert(result, format="png", quality="high")
        png_high_seconds = time.perf_counter() - started_at

        started_at = time.perf_counter()
        pdf = ExportConverter.convert(result, format="pdf", quality="high", title=result.title)
        pdf_seconds = time.perf_counter() - started_at

        ExportConverter.write(png_medium, png_medium_path)
        ExportConverter.write(png_high, png_high_path)
        ExportConverter.write(pdf, pdf_path)

        return (
            {
                "svg": svg_path,
                "png_medium": png_medium_path,
                "png_high": png_high_path,
                "pdf": pdf_path,
            },
            {
                "write_svg": write_svg_seconds,
                "png_medium": png_medium_seconds,
                "png_high": png_high_seconds,
                "pdf": pdf_seconds,
            },
        )

    def _assert_settings(self, case: E2ECase, result) -> None:
        self.assertIsNone(result.output_svg)
        self.assertEqual(result.document_type, case.document_type)
        self.assertEqual(result.context.settings.layout_kind, case.layout)
        self.assertEqual(result.context.settings.theme_name, case.theme)
        self.assertEqual(result.context.settings.page_size_name, case.page_size)
        self.assertEqual(result.context.settings.typography_name, case.typography)
        self.assertEqual(result.context.settings.typography.text_align, case.text_align)
        self.assertEqual(result.context.settings.show_node_numbers, case.show_node_numbers)
        self.assertEqual(result.context.settings.background_color, case.background)

    def _assert_svg_structure(self, case: E2ECase, result, svg_text: str) -> None:
        self.assertEqual(result.svg, svg_text)
        self.assertIn("<svg", svg_text)
        self.assertIn("transform=", svg_text)
        self.assertIn("<text", svg_text)

        if case.document_type == "matrix":
            self.assertIn("<rect", svg_text)
            self.assertIn("Cuadro comparativo", svg_text)
            self.assertNotIn("marker-end", svg_text)
        elif case.layout == "synoptic":
            self.assertNotIn("<rect", svg_text)
            self.assertNotIn("marker-end", svg_text)
        else:
            self.assertIn("<rect", svg_text)

        if case.background is not None:
            self.assertIn(f'style="background-color:{case.background}"', svg_text)
        else:
            self.assertNotIn("background-color:", svg_text)

    def _assert_theme_serialization(self, case: E2ECase, result, svg_text: str) -> None:
        theme = ThemeCatalog.resolve(case.theme)
        present_kinds = {
            node.kind.strip().lower() if node.kind else "default"
            for node in result.context.parsed.node_index.values()
        }

        if case.document_type == "matrix":
            self.assertIn(theme.edge_color, svg_text)
            self.assertIn(theme.default_node.fill, svg_text)
            self.assertIn(theme.default_node.body, svg_text)
            self.assertIn(theme.style_for("main").fill, svg_text)
            self.assertIn(theme.style_for("hl").fill, svg_text)
            self.assertIn(theme.style_for("soft").fill, svg_text)
            return

        self.assertIn(theme.default_node.title, svg_text)
        if case.layout != "synoptic":
            self.assertIn(theme.edge_color, svg_text)
            self.assertIn(theme.relation_color, svg_text)
            self.assertIn(theme.default_node.fill, svg_text)

        for kind in present_kinds:
            if kind == "default":
                continue
            self.assertIn(theme.style_for(kind).title, svg_text)
            if case.layout != "synoptic":
                self.assertIn(theme.style_for(kind).fill, svg_text)

        number_labels = self._number_label_count(result, svg_text)
        if case.layout != "synoptic" and case.show_node_numbers:
            self.assertIn(theme.number_pill_bg, svg_text)
            self.assertIn(theme.number_pill_text, svg_text)
            self.assertGreater(number_labels, 0)
        else:
            self.assertEqual(number_labels, 0)

    @staticmethod
    def _number_label_count(result, svg_text: str) -> int:
        node_numbers = set(result.context.parsed.node_index.keys())
        root = ET.fromstring(svg_text)
        count = 0
        for element in root.iter():
            if not element.tag.endswith("text"):
                continue
            if element.attrib.get("font-size") != "6.5":
                continue
            if (element.text or "").strip() in node_numbers:
                count += 1
        return count

    def _assert_exports(self, output_paths: dict[str, Path]) -> None:
        self.assertTrue(output_paths["svg"].exists())
        self.assertTrue(output_paths["png_medium"].exists())
        self.assertTrue(output_paths["png_high"].exists())
        self.assertTrue(output_paths["pdf"].exists())
        self.assertTrue(output_paths["png_medium"].read_bytes().startswith(b"\x89PNG\r\n\x1a\n"))
        self.assertTrue(output_paths["png_high"].read_bytes().startswith(b"\x89PNG\r\n\x1a\n"))
        self.assertTrue(output_paths["pdf"].read_bytes().startswith(b"%PDF"))
        self.assertGreater(output_paths["svg"].stat().st_size, 500)
        self.assertGreater(output_paths["png_medium"].stat().st_size, 500)
        self.assertGreater(output_paths["png_high"].stat().st_size, 500)
        self.assertGreater(output_paths["png_high"].stat().st_size, output_paths["png_medium"].stat().st_size)
        self.assertGreater(output_paths["pdf"].stat().st_size, 500)

    @classmethod
    def _record_manifest(
        cls,
        case: E2ECase,
        output_paths: dict[str, Path],
        timings: dict[str, float],
    ) -> None:
        cls.manifest.append(
            {
                "case": asdict(case),
                "case_id": case.case_id,
                "outputs": {
                    extension: str(path.relative_to(ROOT_DIR))
                    for extension, path in sorted(output_paths.items())
                },
                "sizes_bytes": {
                    extension: path.stat().st_size
                    for extension, path in sorted(output_paths.items())
                },
                "timings_seconds": {
                    name: round(seconds, 6)
                    for name, seconds in sorted(timings.items())
                },
            }
        )

    @classmethod
    def _record_summary(cls, cases: list[E2ECase]) -> None:
        types = sorted({case.document_type for case in cases})
        export_count = len(cases) * 3
        file_count = len(cases) * 4
        timing_totals = {
            "render_svg": 0.0,
            "write_svg": 0.0,
            "png_medium": 0.0,
            "png_high": 0.0,
            "pdf": 0.0,
        }
        for entry in cls.manifest:
            timings = entry.get("timings_seconds", {})
            if not isinstance(timings, dict):
                continue
            for name in timing_totals:
                seconds = timings.get(name, 0.0)
                if isinstance(seconds, int | float):
                    timing_totals[name] += float(seconds)

        cls.summary = {
            "diagrams": len(cases),
            "exports": export_count,
            "files": file_count,
            "type_count": len(types),
            "types": ", ".join(types),
            "render_svg_seconds": timing_totals["render_svg"],
            "write_svg_seconds": timing_totals["write_svg"],
            "png_medium_seconds": timing_totals["png_medium"],
            "png_high_seconds": timing_totals["png_high"],
            "pdf_seconds": timing_totals["pdf"],
        }


def _case(index: int, document_type: str, layout: str, theme: str) -> E2ECase:
    text_align = TEXT_ALIGN_SEQUENCE[index % len(TEXT_ALIGN_SEQUENCE)]
    typographies = MATRIX_TYPOGRAPHIES if document_type == "matrix" else TREE_TYPOGRAPHIES
    return E2ECase(
        index=index,
        document_type=document_type,
        layout=layout,
        theme=theme,
        text_align=text_align,
        typography=typographies[index % len(typographies)],
        page_size=PAGE_SIZES[index % len(PAGE_SIZES)],
        show_node_numbers=document_type == "tree" and index % 2 == 0,
        background=BACKGROUND_COLORS[(index // 2) % len(BACKGROUND_COLORS)] if index % 3 == 0 else None,
    )


if __name__ == "__main__":
    unittest.main(verbosity=2)
