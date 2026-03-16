from pathlib import Path
import runpy


TEST_FILE = Path(__file__).with_name("test_render_e2e.py")


if __name__ == "__main__":
    runpy.run_path(str(TEST_FILE), run_name="__main__")
