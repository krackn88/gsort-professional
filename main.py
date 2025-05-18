"""
Entry point for gSort Professional.
Updates main.py to include research features.
"""

import sys
import os
import logging
import argparse
from typing import List, Optional

from PyQt6.QtWidgets import QApplication, QStyleFactory
from PyQt6.QtCore import Qt, QCoreApplication
from PyQt6.QtGui import QFont

from gsort.ui.main_window import MainWindow
from gsort.ui.research_features import add_research_menu
from gsort import __version__
from qt_material import apply_stylesheet


def setup_logging(log_file: Optional[str] = None, debug: bool = False):
    """
    Set up logging configuration.
    
    Args:
        log_file: Optional path to log file
        debug: Whether to enable debug logging
    """
    level = logging.DEBUG if debug else logging.INFO
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    
    # Add file handler if specified
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
            logging.info(f"Logging to file: {log_file}")
        except Exception as e:
            logging.error(f"Failed to set up file logging: {e}")


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="gSort Professional")
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    parser.add_argument(
        "--log-file",
        type=str,
        help="Path to log file"
    )
    
    parser.add_argument(
        "--style",
        type=str,
        choices=QStyleFactory.keys(),
        help="Qt style to use"
    )
    
    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version information and exit"
    )
    
    parser.add_argument(
        "files",
        nargs="*",
        help="Files to open at startup"
    )
    
    return parser.parse_args()


def show_version():
    """Display version information"""
    print(f"gSort Professional v{__version__}")
    print("Copyright (c) 2025")
    print("https://github.com/krackn88/gsort-professional")


def main():
    """Main entry point"""
    # Parse command line arguments
    args = parse_args()
    
    # Show version if requested
    if args.version:
        show_version()
        return 0
    
    # Set up logging
    setup_logging(args.log_file, args.debug)
    
    # Create application
    app = QApplication(sys.argv)
    
    # Set application metadata
    app.setApplicationName("gSort Professional")
    app.setApplicationVersion(__version__)
    app.setOrganizationName("gSort")
    app.setOrganizationDomain("gsort.pro")
    
    # Apply style if specified
    if args.style:
        app.setStyle(args.style)
    else:
        app.setStyle("Fusion")  # Default to Fusion style
    
    # Apply qt-material theme and modern font
    apply_stylesheet(app, theme='dark_cyan.xml')
    # Use Segoe UI 18pt for readability, fallback to Arial
    font = QFont('Segoe UI', 18)
    if not font.exactMatch():
        font = QFont('Arial', 18)
    app.setFont(font)
    
    # Create main window
    window = MainWindow()
    
    # Add research features
    add_research_menu(window)
    
    # Show the window
    window.show()
    
    # Handle files to open at startup
    if args.files:
        logging.info(f"Opening files from command line: {args.files}")
        # TODO: Implement opening files on startup
        # This would be handled by the main window
    
    # Run the application
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())