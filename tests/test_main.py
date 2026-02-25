import logging
import pathlib
import sys
import types

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

# Provide lightweight stubs so main.py can be imported without system Qt libraries.
qtwidgets = types.ModuleType("PyQt6.QtWidgets")
qtwidgets.QApplication = type("QApplication", (), {})
qtwidgets.QStyleFactory = type("QStyleFactory", (), {"keys": staticmethod(lambda: ["Fusion", "Windows"])})

qtgui = types.ModuleType("PyQt6.QtGui")
qtgui.QFont = type("QFont", (), {})

pyqt6 = types.ModuleType("PyQt6")

qt_material = types.ModuleType("qt_material")
qt_material.apply_stylesheet = lambda *args, **kwargs: None

sys.modules.setdefault("PyQt6", pyqt6)
sys.modules["PyQt6.QtWidgets"] = qtwidgets
sys.modules["PyQt6.QtGui"] = qtgui
sys.modules["qt_material"] = qt_material

from main import parse_args, setup_logging


def test_parse_args_supports_injected_argv():
    args = parse_args(["--debug", "--log-file", "app.log", "input1.txt", "input2.txt"])

    assert args.debug is True
    assert args.log_file == "app.log"
    assert args.files == ["input1.txt", "input2.txt"]


def test_setup_logging_replaces_existing_handlers(tmp_path):
    root = logging.getLogger()
    original_handlers = list(root.handlers)
    try:
        setup_logging(debug=True)
        first_count = len(root.handlers)

        logfile = tmp_path / "app.log"
        setup_logging(log_file=str(logfile), debug=False)

        assert len(root.handlers) == first_count + 1
        assert any(isinstance(handler, logging.FileHandler) for handler in root.handlers)
    finally:
        for handler in list(root.handlers):
            root.removeHandler(handler)
        for handler in original_handlers:
            root.addHandler(handler)
