from __future__ import annotations

import json
import shutil
import sys
import unittest
from dataclasses import asdict, dataclass
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.io import load_input_text
from core.parser import parse_concept_text
from render.models import SvgRenderRequest
from render.svg_render import render_svg
from render.themes import ThemeCatalog


LAYOUTS = ("tree", "synoptic", "synoptic_boxes", "radial")
TEXT_ALIGN_MOCKS = {
    "left": ROOT_DIR / "tests/end_to_end/mocks/alignment_left.txt",
    "justify": ROOT_DIR / "tests/end_to_end/mocks/alignment_justify.txt",
}
PAGE_SIZES = ("a4", "a4_landscape", "square")
SHOW_NODE_NUMBERS = (True, False)


@dataclass(frozen=True)
class E2ECase:
    index: int
    layout: str
    theme: str
    text_align: str
    page_size: str
    show_node_numbers: bool

    @property
    def case_id(self) -> str:
        node_numbers = "numbers_on" if self.show_node_numbers else "numbers_off"
        return (
            f"{self.index:02d}_{self.layout}_{self.theme}_{self.text_align}_"
            f"{self.page_size}_{node_numbers}"
        )

    @property
    def mock_path(self) -> Path:
        return TEXT_ALIGN_MOCKS[self.text_align]

    @property
    def output_dir_name(self) -> str:
        return f"tests/end_to_end/output/{self.theme}/{self.text_align}"

    @property
    def output_svg_name(self) -> str:
        node_numbers = "numbers_on" if self.show_node_numbers else "numbers_off"
        return f"{self.index:02d}_{self.layout}_{self.page_size}_{node_numbers}.svg"


class RenderEndToEndTest(unittest.TestCase):
    output_root = ROOT_DIR / "tests/end_to_end/output"
    manifest_path = ROOT_DIR / "tests/end_to_end/e2e_manifest.json"
    manifest: list[dict[str, object]] = []

    @classmethod
    def setUpClass(cls) -> None:
        if cls.output_root.exists():
            shutil.rmtree(cls.output_root)
        cls.output_root.mkdir(parents=True, exist_ok=True)
        if cls.manifest_path.exists():
            cls.manifest_path.unlink()
        cls.manifest = []

    @classmethod
    def tearDownClass(cls) -> None:
        cls.manifest_path.write_text(
            json.dumps(cls.manifest, indent=2, ensure_ascii=True, sort_keys=True),
            encoding="utf-8",
        )

    def test_render_matrix(self) -> None:
        for case in self._build_cases():
            with self.subTest(case=case.case_id):
                result = self._render_case(case)
                svg_text = result.output_svg.read_text(encoding="utf-8")

                self._assert_settings(case, result)
                self._assert_svg_structure(case, svg_text)
                self._assert_theme_serialization(case, result, svg_text)
                self._record_manifest(case, result)

    @staticmethod
    def _build_cases() -> list[E2ECase]:
        cases: list[E2ECase] = []
        index = 0

        for theme in ThemeCatalog.available_names():
            for layout in LAYOUTS:
                for text_align in TEXT_ALIGN_MOCKS:
                    cases.append(
                        E2ECase(
                            index=index,
                            layout=layout,
                            theme=theme,
                            text_align=text_align,
                            page_size=PAGE_SIZES[index % len(PAGE_SIZES)],
                            show_node_numbers=SHOW_NODE_NUMBERS[index % len(SHOW_NODE_NUMBERS)],
                        )
                    )
                    index += 1

        return cases

    def _render_case(self, case: E2ECase):
        source_text = load_input_text(str(case.mock_path))
        parsed = parse_concept_text(source_text)
        parsed.metadata["show-node-numbers"] = "true" if case.show_node_numbers else "false"

        request = SvgRenderRequest(
            parsed=parsed,
            base_dir=ROOT_DIR,
            output_dir_name=case.output_dir_name,
            default_output_dir_name="tests/end_to_end/output",
            layout_kind=case.layout,
            theme_name=case.theme,
            page_size_name=case.page_size,
        )
        result = render_svg(request)
        final_svg = self.output_root / case.theme / case.text_align / case.output_svg_name
        result.output_svg.replace(final_svg)
        return result.__class__(output_svg=final_svg, context=result.context)

    def _assert_settings(self, case: E2ECase, result) -> None:
        self.assertTrue(result.output_svg.exists(), f"No se generó {case.case_id}.")
        self.assertEqual(result.context.settings.layout_kind, case.layout)
        self.assertEqual(result.context.settings.theme_name, case.theme)
        self.assertEqual(result.context.settings.page_size_name, case.page_size)
        self.assertEqual(result.context.settings.typography.text_align, case.text_align)
        self.assertEqual(result.context.settings.show_node_numbers, case.show_node_numbers)
        self.assertEqual(
            result.output_svg,
            self.output_root / case.theme / case.text_align / case.output_svg_name,
        )

    def _assert_svg_structure(self, case: E2ECase, svg_text: str) -> None:
        self.assertIn("<svg", svg_text)
        self.assertIn("transform=", svg_text)
        self.assertIn("<text", svg_text)

        if case.layout == "synoptic":
            self.assertNotIn("<rect", svg_text)
            self.assertNotIn("marker-end", svg_text)
        else:
            self.assertIn("<rect", svg_text)

    def _assert_theme_serialization(self, case: E2ECase, result, svg_text: str) -> None:
        theme = ThemeCatalog.resolve(case.theme)
        present_kinds = {
            node.kind.strip().lower() if node.kind else "default"
            for node in result.context.parsed.node_index.values()
        }

        if case.layout == "synoptic":
            self.assertNotIn(theme.edge_color, svg_text)
            self.assertNotIn(theme.relation_color, svg_text)
        else:
            self.assertIn(theme.edge_color, svg_text)
            self.assertIn(theme.relation_color, svg_text)

        self.assertIn(theme.default_node.title, svg_text)

        for kind in present_kinds:
            if kind == "default":
                continue
            self.assertIn(theme.style_for(kind).title, svg_text)

        if case.layout != "synoptic":
            self.assertIn(theme.default_node.fill, svg_text)
            for kind in present_kinds:
                if kind == "default":
                    continue
                self.assertIn(theme.style_for(kind).fill, svg_text)

        if case.layout != "synoptic" and case.show_node_numbers:
            self.assertIn(theme.number_pill_bg, svg_text)
            self.assertIn(theme.number_pill_text, svg_text)
        else:
            self.assertNotIn(theme.number_pill_bg, svg_text)

    @classmethod
    def _record_manifest(cls, case: E2ECase, result) -> None:
        cls.manifest.append(
            {
                "case": asdict(case),
                "case_id": case.case_id,
                "output_svg": str(result.output_svg.relative_to(ROOT_DIR)),
                "size_bytes": result.output_svg.stat().st_size,
            }
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
