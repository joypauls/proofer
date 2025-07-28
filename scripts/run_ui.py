import subprocess
import sys
from pathlib import Path

UI_FILE = "ui.py"


def main():
    script_path = Path(__file__).parent / UI_FILE

    try:
        subprocess.run(
            [sys.executable, "-m", "streamlit", "run", str(script_path)], check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Error running Streamlit: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nStreamlit app stopped.")


if __name__ == "__main__":
    main()
