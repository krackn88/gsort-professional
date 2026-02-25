"""
Entry point for gSort Professional.
"""

import argparse
import logging
import sys
from typing import Optional, Sequence

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication, QStyleFactory
from qt_material import apply_stylesheet

from gsort import __version__


def setup_logging(log_file: Optional[str] = None, debug: bool = False) -> None:
    """Configure root logging handlers for console and optional file output."""
    level = logging.DEBUG if debug else logging.INFO
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Reset existing handlers to avoid duplicate log lines when setup is called repeatedly.
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    if log_file:
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
            logging.info("Logging to file: %s", log_file)
        except OSError as error:
            logging.error("Failed to set up file logging: %s", error)


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="gSort Professional")

    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--log-file", type=str, help="Path to log file")
    parser.add_argument("--style", type=str, choices=QStyleFactory.keys(), help="Qt style to use")
    parser.add_argument("--version", action="store_true", help="Show version information and exit")
    parser.add_argument("files", nargs="*", help="Files to open at startup")

    return parser.parse_args(argv)


def show_version() -> None:
    """Display version information."""
    print(f"gSort Professional v{__version__}")
    print("Copyright (c) 2025")
    print("https://github.com/krackn88/gsort-professional")


def main() -> int:
    """Main entry point."""
    args = parse_args()

    if args.version:
        show_version()
        return 0

    setup_logging(args.log_file, args.debug)

    from gsort.ui.main_window import MainWindow
    from gsort.ui.research_features import add_research_menu

    app = QApplication(sys.argv)
    app.setApplicationName("gSort Professional")
    app.setApplicationVersion(__version__)
    app.setOrganizationName("gSort")
    app.setOrganizationDomain("gsort.pro")

    app.setStyle(args.style if args.style else "Fusion")

    apply_stylesheet(app, theme="dark_cyan.xml")
    font = QFont("Segoe UI", 18)
    if not font.exactMatch():
        font = QFont("Arial", 18)
    app.setFont(font)

    window = MainWindow()
    add_research_menu(window)
    window.show()

    if args.files:
        logging.info("Opening files from command line: %s", args.files)
        # TODO: Implement opening files on startup in MainWindow.

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
