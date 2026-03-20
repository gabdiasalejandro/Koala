import unittest
from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parents[3]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from koala.render.geometry import synoptic_brace_path_data


class SynopticBracePathDataTests(unittest.TestCase):
    def test_builds_brace_without_parent_chase_segment(self) -> None:
        path_data = synoptic_brace_path_data(
            [
                (100.0, 200.0),
                (150.0, 100.0),
                (160.0, 100.0),
                (150.0, 300.0),
                (160.0, 300.0),
            ]
        )

        self.assertEqual(
            path_data,
            "M 160.00 100.00 "
            "Q 150.00 100.00 150.00 108.00 "
            "L 150.00 190.00 "
            "L 140.00 200.00 "
            "L 150.00 210.00 "
            "L 150.00 292.00 "
            "Q 150.00 300.00 160.00 300.00",
        )

    def test_clamps_peak_to_top_when_parent_is_above_group(self) -> None:
        path_data = synoptic_brace_path_data(
            [
                (100.0, 40.0),
                (150.0, 100.0),
                (160.0, 100.0),
                (150.0, 300.0),
                (160.0, 300.0),
            ]
        )

        self.assertEqual(
            path_data,
            "M 160.00 100.00 "
            "Q 150.00 100.00 150.00 108.00 "
            "L 150.00 108.00 "
            "L 140.00 118.00 "
            "L 150.00 128.00 "
            "L 150.00 292.00 "
            "Q 150.00 300.00 160.00 300.00",
        )

    def test_returns_none_for_incomplete_brace_contract(self) -> None:
        self.assertIsNone(
            synoptic_brace_path_data(
                [
                    (100.0, 200.0),
                    (150.0, 100.0),
                    (160.0, 100.0),
                    (150.0, 300.0),
                ]
            )
        )


if __name__ == "__main__":
    unittest.main()
