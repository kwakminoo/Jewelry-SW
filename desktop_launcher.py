"""PyInstaller-compatible native desktop entry point."""

from jewelry.main import main


if __name__ == "__main__":
    raise SystemExit(main())
