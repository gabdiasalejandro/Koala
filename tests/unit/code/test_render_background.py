import sys
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[3]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from koala.core.parser import parse_concept_text
from koala.render.context import RenderContextBuilder


class RenderBackgroundTests(unittest.TestCase):
    def test_resolves_background_from_metadata(self) -> None:
        parsed = parse_concept_text(
            """
            @background #f7f4ed
            1 Root
            Body.
            """
        )

        context = RenderContextBuilder.build(parsed)

        self.assertEqual(context.settings.background_color, "#F7F4ED")

    def test_explicit_background_overrides_metadata(self) -> None:
        parsed = parse_concept_text(
            """
            @background #f7f4ed
            1 Root
            Body.
            """
        )

        context = RenderContextBuilder.build(parsed, background_color="#f1f7fb")

        self.assertEqual(context.settings.background_color, "#F1F7FB")

    def test_invalid_background_raises_value_error(self) -> None:
        parsed = parse_concept_text(
            """
            @background azul
            1 Root
            Body.
            """
        )

        with self.assertRaises(ValueError):
            RenderContextBuilder.build(parsed)


if __name__ == "__main__":
    unittest.main()
