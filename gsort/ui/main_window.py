"""
Main window implementation for gSort Professional.
"""

import os
import sys
import logging
import queue
import random
import threading
from typing import List, Dict, Optional, Any
from datetime import datetime

from PyQt6.QtWidgets import (
    QMainWindow, QApplication, QToolBar, QToolButton, QMenu,
    QTextEdit, QFileDialog, QMessageBox, QInputDialog, QDialog, QDockWidget,
    QStatusBar, QProgressBar, QVBoxLayout, QHBoxLayout, QWidget, QLabel,
    QComboBox, QSplitter, QTabWidget
)
from PyQt6.QtGui import QIcon, QFont, QKeySequence, QTextCursor, QPixmap, QAction
from PyQt6.QtCore import Qt, QSettings, QSize, QThread, pyqtSignal, QTimer, QEvent

from qt_material import apply_stylesheet

from gsort.core.processor import ComboProcessor, ProcessingStats
from gsort.analytics.analyzer import ComboAnalytics, AnalyticsResult
from gsort.export.exporter import ComboExporter
from gsort.ui.analytics_view import AnalyticsView
from gsort.ui.preferences_dialog import PreferencesDialog
from gsort.ui.filter_dialog import FilterDialog
from gsort.ui.batch_dialog import BatchOperationsDialog


class ProcessingWorker(QThread):
    """
    Worker thread for processing combo files.
    """
    progress = pyqtSignal(int, int)
    finished = pyqtSignal(list, ProcessingStats)
    error = pyqtSignal(str)
    
    def __init__(self, file_paths: List[str], max_workers: int = 8):
        super().__init__()
        self.file_paths = file_paths
        self.max_workers = max_workers
    
    def run(self):
        try:
            processor = ComboProcessor(max_workers=self.max_workers)
            combos, stats = processor.process_files(
                self.file_paths,
                progress_callback=self._update_progress
            )
            self.finished.emit(combos, stats)
        except Exception as e:
            self.error.emit(str(e))
    
    def _update_progress(self, processed: int, total: int):
        """Update progress callback for processor"""
        self.progress.emit(processed, total)


class MainWindow(QMainWindow):
    """
    Main application window.
    """
    
    def __init__(self):
        super().__init__()
        
        # Set a normalized, readable default application font
        app_font = QFont("Consolas", 14)
        QApplication.setFont(app_font)
        
        # Setup logging
        self.log_queue = queue.Queue()
        self.logger = logging.getLogger(__name__)
        
        # Setup application state
        self._init_state()
        
        # Initialize UI components
        self._init_ui()
        
        # Load settings
        self._load_settings()
        
        # Set window properties
        self.setWindowTitle("gSort Professional")
        self.showMaximized()
        
        # Start the log polling timer
        self.log_timer = QTimer()
        self.log_timer.timeout.connect(self._poll_log_queue)
        self.log_timer.start(100)  # Poll every 100ms
        
        self.logger.info("Application started")
    
    def _init_state(self):
        """Initialize application state variables"""
        # User settings
        self.settings = QSettings("gSort", "Professional")
        self.theme_name = "dark_blue"
        self.thread_count = 8
        self.preview_count = 100
        self.auto_analyze = True
        
        # Data state
        self.combos = []
        self.original_combos = []
        self.analytics_results = {}
    
    def _init_ui(self):
        """Initialize UI components"""
        # Set up central splitter
        self.central_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.setCentralWidget(self.central_splitter)
        
        # Text area for combo preview
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setPlaceholderText("Load combo files to begin processing...")
        
        # Analytics view (right side)
        self.analytics_view = AnalyticsView()
        
        # Add widgets to splitter
        self.central_splitter.addWidget(self.text_area)
        self.central_splitter.addWidget(self.analytics_view)
        self.central_splitter.setStretchFactor(0, 1)
        self.central_splitter.setStretchFactor(1, 2)
        self.central_splitter.setHandleWidth(8)
        
        # Status bar with progress
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setMaximumHeight(18)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("%p% (%v / %m)")
        
        self.status_bar.addPermanentWidget(self.progress_bar)
        self.status_bar.showMessage("Ready")
        
        # Log dock widget
        self.log_dock = QDockWidget("Log", self)
        self.log_dock.setAllowedAreas(Qt.BottomDockWidgetArea)
        
        self.log_widget = QTextEdit()
        self.log_widget.setReadOnly(True)
        self.log_widget.setMaximumHeight(150)
        
        self.log_dock.setWidget(self.log_widget)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.log_dock)
        
        # Create toolbars
        self._create_toolbars()
        
        # Create menus
        self._create_menus()
        
        # Add spacing and margins for a modern look
        self.setContentsMargins(16, 16, 16, 16)
        self.centralWidget().setContentsMargins(8, 8, 8, 8)
        self.status_bar.setContentsMargins(8, 4, 8, 4)
        self.main_toolbar.setContentsMargins(8, 4, 8, 4)
    
    def _create_toolbars(self):
        """Create application toolbars"""
        # Main toolbar
        self.main_toolbar = QToolBar("Main")
        self.main_toolbar.setMovable(False)
        self.main_toolbar.setIconSize(QSize(32, 32))
        self.main_toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        
        # File actions
        self.open_action = QAction(QIcon.fromTheme("document-open", QIcon("resources/icons/open.png")), "Open", self)
        self.open_action.setShortcut(QKeySequence.Open)
        self.open_action.triggered.connect(self.open_files)
        self.main_toolbar.addAction(self.open_action)
        
        self.save_action = QAction(QIcon.fromTheme("document-save", QIcon("resources/icons/save.png")), "Save", self)
        self.save_action.setShortcut(QKeySequence.Save)
        self.save_action.triggered.connect(self.save_combos)
        self.main_toolbar.addAction(self.save_action)
        
        self.main_toolbar.addSeparator()
        
        # Analysis actions
        self.analyze_action = QAction(QIcon.fromTheme("document-properties", QIcon("resources/icons/analyze.png")), "Analyze", self)
        self.analyze_action.triggered.connect(self.analyze_combos)
        self.main_toolbar.addAction(self.analyze_action)
        
        self.export_report_action = QAction(QIcon.fromTheme("x-office-document", QIcon("resources/icons/report.png")), "Export Report", self)
        self.export_report_action.triggered.connect(self.export_report)
        self.main_toolbar.addAction(self.export_report_action)
        
        self.main_toolbar.addSeparator()
        
        # Combo operations dropdown
        self.ops_button = QToolButton()
        self.ops_button.setIcon(QIcon.fromTheme("edit", QIcon("resources/icons/operations.png")))
        self.ops_button.setText("Operations")
        self.ops_button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.ops_button.setPopupMode(QToolButton.InstantPopup)
        
        self.ops_menu = QMenu()
        
        # Filter operations
        self.filter_submenu = self.ops_menu.addMenu("Filter")
        self.filter_submenu.addAction("Custom Filter", self.filter_custom)
        self.filter_submenu.addAction("Filter by Domain", self.filter_by_domain)
        self.filter_submenu.addAction("Filter by Password Length", self.filter_by_password_length)
        self.filter_submenu.addAction("Filter with Symbols", self.filter_with_symbols)
        self.filter_submenu.addAction("Extract .edu Emails", self.extract_edu)
        
        # Transform operations
        self.transform_submenu = self.ops_menu.addMenu("Transform")
        self.transform_submenu.addAction("Append to Password", self.append_to_password)
        self.transform_submenu.addAction("Prepend to Password", self.prepend_to_password)
        self.transform_submenu.addAction("Capitalize Password", self.capitalize_password)
        self.transform_submenu.addAction("Batch Replace", self.batch_replace)
        
        # Sort operations
        self.sort_submenu = self.ops_menu.addMenu("Sort")
        self.sort_submenu.addAction("Sort by Email", self.sort_by_email)
        self.sort_submenu.addAction("Sort by Domain", self.sort_by_domain)
        self.sort_submenu.addAction("Sort by Password Length", self.sort_by_password_length)
        self.sort_submenu.addAction("Randomize", self.randomize_combos)
        
        # Other operations
        self.ops_menu.addSeparator()
        self.ops_menu.addAction("Domain Statistics", self.show_domain_stats)
        self.ops_menu.addAction("Password Statistics", self.show_password_stats)
        self.ops_menu.addAction("Batch Operations", self.batch_operations)
        self.ops_menu.addSeparator()
        self.ops_menu.addAction("Reset to Original", self.reset_to_original)
        
        self.ops_button.setMenu(self.ops_menu)
        self.main_toolbar.addWidget(self.ops_button)
        
        self.main_toolbar.addSeparator()
        
        # Settings and help
        self.settings_action = QAction(QIcon.fromTheme("preferences-system", QIcon("resources/icons/settings.png")), "Settings", self)
        self.settings_action.triggered.connect(self.show_preferences)
        self.main_toolbar.addAction(self.settings_action)
        
        self.about_action = QAction(QIcon.fromTheme("help-about", QIcon("resources/icons/about.png")), "About", self)
        self.about_action.triggered.connect(self.show_about)
        self.main_toolbar.addAction(self.about_action)
        
        self.addToolBar(self.main_toolbar)
    
    def _create_menus(self):
        """Create application menus"""
        self.menu_bar = self.menuBar()
        
        # File menu
        self.file_menu = self.menu_bar.addMenu("&File")
        self.file_menu.addAction(self.open_action)
        self.file_menu.addAction(self.save_action)
        
        self.export_menu = self.file_menu.addMenu("Export As")
        self.export_menu.addAction("Text File", lambda: self.export_combos("text"))
        self.export_menu.addAction("CSV", lambda: self.export_combos("csv"))
        self.export_menu.addAction("Excel", lambda: self.export_combos("excel"))
        self.export_menu.addAction("JSON", lambda: self.export_combos("json"))
        
        self.file_menu.addSeparator()
        self.file_menu.addAction("Exit", self.close)
        
        # Edit menu
        self.edit_menu = self.menu_bar.addMenu("&Edit")
        self.edit_menu.addAction("Copy Selected Combos", self.copy_selected_combos)
        self.edit_menu.addAction("Select All", self.text_area.selectAll)
        self.edit_menu.addSeparator()
        self.edit_menu.addAction("Reset to Original", self.reset_to_original)
        
        # Operations menu (duplicate from toolbar dropdown)
        self.operations_menu = self.menu_bar.addMenu("&Operations")
        
        # Filter submenu
        self.menu_filter = self.operations_menu.addMenu("Filter")
        self.menu_filter.addAction("Custom Filter", self.filter_custom)
        self.menu_filter.addAction("Filter by Domain", self.filter_by_domain)
        self.menu_filter.addAction("Filter by Password Length", self.filter_by_password_length)
        self.menu_filter.addAction("Filter with Symbols", self.filter_with_symbols)
        self.menu_filter.addAction("Extract .edu Emails", self.extract_edu)
        
        # Transform submenu
        self.menu_transform = self.operations_menu.addMenu("Transform")
        self.menu_transform.addAction("Append to Password", self.append_to_password)
        self.menu_transform.addAction("Prepend to Password", self.prepend_to_password)
        self.menu_transform.addAction("Capitalize Password", self.capitalize_password)
        self.menu_transform.addAction("Batch Replace", self.batch_replace)
        
        # Sort submenu
        self.menu_sort = self.operations_menu.addMenu("Sort")
        self.menu_sort.addAction("Sort by Email", self.sort_by_email)
        self.menu_sort.addAction("Sort by Domain", self.sort_by_domain)
        self.menu_sort.addAction("Sort by Password Length", self.sort_by_password_length)
        self.menu_sort.addAction("Randomize", self.randomize_combos)
        
        # Other operations
        self.operations_menu.addSeparator()
        self.operations_menu.addAction("Domain Statistics", self.show_domain_stats)
        self.operations_menu.addAction("Password Statistics", self.show_password_stats)
        self.operations_menu.addAction("Batch Operations", self.batch_operations)
        
        # Analysis menu
        self.analysis_menu = self.menu_bar.addMenu("&Analysis")
        self.analysis_menu.addAction("Analyze Combos", self.analyze_combos)
        self.analysis_menu.addAction("Export Report", self.export_report)
        self.analysis_menu.addSeparator()
        self.analysis_menu.addAction("Domain Analysis", lambda: self.run_specific_analysis("domain"))
        self.analysis_menu.addAction("Password Strength Analysis", lambda: self.run_specific_analysis("strength"))
        self.analysis_menu.addAction("Password Pattern Analysis", lambda: self.run_specific_analysis("patterns"))
        self.analysis_menu.addAction("Email-Password Correlation", lambda: self.run_specific_analysis("correlation"))
        
        # View menu
        self.view_menu = self.menu_bar.addMenu("&View")
        self.view_menu.addAction("Show/Hide Log", self.toggle_log_view)
        
        # Theme submenu
        self.theme_menu = self.view_menu.addMenu("Theme")
        self.theme_menu.addAction("Dark Blue", lambda: self.change_theme("dark_blue"))
        self.theme_menu.addAction("Dark Cyan", lambda: self.change_theme("dark_cyan"))
        self.theme_menu.addAction("Dark Purple", lambda: self.change_theme("dark_purple"))
        self.theme_menu.addAction("Dark Amber", lambda: self.change_theme("dark_amber"))
        self.theme_menu.addAction("Light Blue", lambda: self.change_theme("light_blue"))
        self.theme_menu.addAction("Light Cyan", lambda: self.change_theme("light_cyan"))
        self.theme_menu.addAction("Light Purple", lambda: self.change_theme("light_purple"))
        self.theme_menu.addAction("Light Amber", lambda: self.change_theme("light_amber"))
        
        # Help menu
        self.help_menu = self.menu_bar.addMenu("&Help")
        self.help_menu.addAction("Documentation", self.show_documentation)
        self.help_menu.addAction("Check for Updates", self.check_updates)
        self.help_menu.addSeparator()
        self.help_menu.addAction("About", self.show_about)
    
    def _load_settings(self):
        """Load user settings"""
        self.theme_name = self.settings.value("appearance/theme", "dark_blue")
        self.thread_count = int(self.settings.value("processing/thread_count", 8))
        self.preview_count = int(self.settings.value("preview/count", 100))
        self.auto_analyze = self.settings.value("processing/auto_analyze", "true") == "true"
        
        # Apply theme
        self.apply_theme(self.theme_name)
        
        # Restore window state if available
        geometry = self.settings.value("window/geometry")
        if geometry:
            self.restoreGeometry(geometry)
        
        state = self.settings.value("window/state")
        if state:
            self.restoreState(state)
    
    def _poll_log_queue(self):
        """Poll the log queue and update the log widget"""
        try:
            while True:
                record = self.log_queue.get_nowait()
                self.log_widget.append(record)
                self.log_queue.task_done()
        except queue.Empty:
            pass
    
    def apply_theme(self, theme_name: str):
        """Apply the specified theme to the application"""
        # Map theme names to qt-material theme names
        theme_map = {
            "dark_blue": "dark_blue.xml",
            "dark_cyan": "dark_cyan.xml",
            "dark_purple": "dark_purple.xml",
            "dark_amber": "dark_amber.xml",
            "light_blue": "light_blue.xml",
            "light_cyan": "light_cyan.xml",
            "light_purple": "light_purple.xml",
            "light_amber": "light_amber.xml"
        }
        
        theme_file = theme_map.get(theme_name, "dark_blue.xml")
        try:
            apply_stylesheet(QApplication.instance(), theme=theme_file)
            self.theme_name = theme_name
            self.logger.info(f"Applied theme: {theme_name}")
        except Exception as e:
            self.logger.error(f"Error applying theme: {e}")
    
    def change_theme(self, theme_name: str):
        """Change the application theme"""
        self.apply_theme(theme_name)
        self.settings.setValue("appearance/theme", theme_name)
    
    def toggle_log_view(self):
        """Toggle visibility of the log dock widget"""
        self.log_dock.setVisible(not self.log_dock.isVisible())
    
    def show_preferences(self):
        """Show the preferences dialog"""
        dialog = PreferencesDialog(
            self.preview_count,
            self.thread_count,
            self.auto_analyze,
            self
        )
        
        if dialog.exec() == QDialog.Accepted:
            # Get values from dialog
            self.preview_count = dialog.preview_count
            self.thread_count = dialog.thread_count
            self.auto_analyze = dialog.auto_analyze
            
            # Save settings
            self.settings.setValue("preview/count", self.preview_count)
            self.settings.setValue("processing/thread_count", self.thread_count)
            self.settings.setValue("processing/auto_analyze", "true" if self.auto_analyze else "false")
            
            # Update display if needed
            self.update_combo_display()
            
            self.logger.info("Preferences updated")
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Save window state
        self.settings.setValue("window/geometry", self.saveGeometry())
        self.settings.setValue("window/state", self.saveState())
        
        # Accept the event
        event.accept()
    
    # File operations
    
    def open_files(self):
        """Open combo files and start processing"""
        # Show file dialog
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Open Combo Files",
            "",
            "Text Files (*.txt);;All Files (*.*)"
        )
        
        if not files:
            return
        
        # Start processing
        self.progress_bar.setValue(0)
        self.status_bar.showMessage("Processing files...")
        
        # Create and start worker thread
        self.worker = ProcessingWorker(files, max_workers=self.thread_count)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.processing_finished)
        self.worker.error.connect(self.processing_error)
        self.worker.start()
        
        # Disable file operations while processing
        self.open_action.setEnabled(False)
        self.save_action.setEnabled(False)
    
    def update_progress(self, processed: int, total: int):
        """Update progress bar during file processing"""
        if total > 0:
            percentage = int(processed * 100 / total)
            self.progress_bar.setValue(percentage)
            self.progress_bar.setFormat(f"{percentage}% ({processed:,} / {total:,} bytes)")
    
    def processing_finished(self, combos: List[str], stats: ProcessingStats):
        """Handle completion of combo processing"""
        self.combos = combos
        self.original_combos = combos.copy()
        
        # Update UI
        self.update_combo_display()
        
        # Re-enable file operations
        self.open_action.setEnabled(True)
        self.save_action.setEnabled(True)
        
        # Update status
        self.status_bar.showMessage(
            f"Processing complete: {len(combos):,} unique combos, {stats.duplicates_removed:,} duplicates removed, "
            f"processed in {stats.processing_time_ms/1000:.1f}s"
        )
        
        # Run analytics if auto-analyze is enabled
        if self.auto_analyze and combos:
            self.analyze_combos()
    
    def processing_error(self, error_msg: str):
        """Handle processing error"""
        QMessageBox.critical(self, "Processing Error", error_msg)
        
        # Re-enable file operations
        self.open_action.setEnabled(True)
        self.save_action.setEnabled(True)
        
        self.status_bar.showMessage("Processing failed")
    
    def update_combo_display(self):
        """Update the combo preview in the text area"""
        self.text_area.clear()
        
        if not self.combos:
            self.text_area.setPlaceholderText("No combos loaded")
            return
        
        # Create header text
        header = f"Total Combos: {len(self.combos):,}\n"
        if self.original_combos and len(self.combos) != len(self.original_combos):
            header += f"Original Count: {len(self.original_combos):,}\n"
        
        header += f"\nShowing {min(self.preview_count, len(self.combos)):,} sample combos:\n\n"
        
        # Get sample combos
        sample_count = min(self.preview_count, len(self.combos))
        if sample_count < len(self.combos):
            # Random sample if we have more combos than preview count
            sample_combos = random.sample(self.combos, sample_count)
        else:
            # Otherwise show all
            sample_combos = self.combos
        
        # Display combos
        self.text_area.setText(header + "\n".join(sample_combos))
    
    def save_combos(self):
        """Save combos to a file"""
        if not self.combos:
            QMessageBox.warning(self, "No Data", "No combos available to save.")
            return
        
        # Show save dialog
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Save Combos",
            "",
            "Text Files (*.txt);;CSV Files (*.csv);;Excel Files (*.xlsx);;JSON Files (*.json)"
        )
        
        if not file_path:
            return
        
        # Determine format based on extension or filter
        if file_path.lower().endswith('.csv'):
            format_type = "csv"
        elif file_path.lower().endswith('.xlsx'):
            format_type = "excel"
        elif file_path.lower().endswith('.json'):
            format_type = "json"
        else:
            format_type = "text"
            # Ensure .txt extension
            if not file_path.lower().endswith('.txt'):
                file_path += ".txt"
        
        # Export using the determined format
        self.export_combos(format_type, file_path)
    
    def export_combos(self, format_type: str, file_path: Optional[str] = None):
        """Export combos in the specified format"""
        if not self.combos:
            QMessageBox.warning(self, "No Data", "No combos available to export.")
            return
        
        if file_path is None:
            # Show save dialog with appropriate extension
            extensions = {
                "text": "Text Files (*.txt)",
                "csv": "CSV Files (*.csv)",
                "excel": "Excel Files (*.xlsx)",
                "json": "JSON Files (*.json)"
            }
            
            default_ext = extensions.get(format_type, "Text Files (*.txt)")
            
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                f"Export Combos as {format_type.upper()}",
                "",
                default_ext
            )
            
            if not file_path:
                return
        
        # Create exporter
        exporter = ComboExporter()
        success = False
        
        # Export based on format
        if format_type == "text":
            success = exporter.export_text(self.combos, file_path)
        elif format_type == "csv":
            success = exporter.export_csv(self.combos, file_path)
        elif format_type == "excel":
            success = exporter.export_excel(self.combos, file_path)
        elif format_type == "json":
            success = exporter.export_json(self.combos, file_path)
        
        # Show result
        if success:
            self.status_bar.showMessage(f"Exported {len(self.combos):,} combos to {file_path}")
            self.logger.info(f"Exported {len(self.combos):,} combos as {format_type} to {file_path}")
        else:
            QMessageBox.critical(self, "Export Error", f"Failed to export combos as {format_type}.")
    
    def copy_selected_combos(self):
        """Copy selected combos to clipboard"""
        selected_text = self.text_area.textCursor().selectedText()
        if selected_text:
            QApplication.clipboard().setText(selected_text)
            self.status_bar.showMessage("Copied selected text to clipboard")
    
    # Analysis operations
    
    def analyze_combos(self):
        """Run full analysis on loaded combos"""
        if not self.combos:
            QMessageBox.warning(self, "No Data", "No combos available to analyze.")
            return
        
        self.status_bar.showMessage("Running analysis...")
        
        # Run in a separate thread to keep UI responsive
        def run_analysis():
            try:
                analyzer = ComboAnalytics()
                self.analytics_results = analyzer.full_analysis(self.combos)
                
                # Update UI in the main thread
                QApplication.instance().postEvent(
                    self,
                    AnalysisCompletedEvent(self.analytics_results)
                )
            except Exception as e:
                self.logger.error(f"Analysis error: {e}")
                QApplication.instance().postEvent(
                    self,
                    AnalysisErrorEvent(str(e))
                )
        
        threading.Thread(target=run_analysis).start()
    
    def run_specific_analysis(self, analysis_type: str):
        """Run a specific analysis type"""
        if not self.combos:
            QMessageBox.warning(self, "No Data", "No combos available to analyze.")
            return
        
        self.status_bar.showMessage(f"Running {analysis_type} analysis...")
        
        # Run in a separate thread to keep UI responsive
        def run_analysis():
            try:
                analyzer = ComboAnalytics()
                result = None
                
                if analysis_type == "domain":
                    result = {"domain_analysis": analyzer.domain_analysis(self.combos)}
                elif analysis_type == "strength":
                    result = {"password_strength": analyzer.password_strength_analysis(self.combos)}
                elif analysis_type == "patterns":
                    result = {"password_patterns": analyzer.password_pattern_analysis(self.combos)}
                elif analysis_type == "correlation":
                    result = {"email_password_correlation": analyzer.email_password_correlation(self.combos)}
                
                if result:
                    # Update UI in the main thread
                    QApplication.instance().postEvent(
                        self,
                        AnalysisCompletedEvent(result)
                    )
            except Exception as e:
                self.logger.error(f"Analysis error: {e}")
                QApplication.instance().postEvent(
                    self,
                    AnalysisErrorEvent(str(e))
                )
        
        threading.Thread(target=run_analysis).start()
    
    def analysis_completed(self, results: Dict[str, AnalyticsResult]):
        """Handle completion of analysis"""
        # Update our stored results with the new ones
        self.analytics_results.update(results)
        
        # Update the analytics view
        self.analytics_view.set_results(self.analytics_results)
        
        self.status_bar.showMessage("Analysis complete")
    
    def analysis_error(self, error_msg: str):
        """Handle analysis error"""
        QMessageBox.critical(self, "Analysis Error", error_msg)
        self.status_bar.showMessage("Analysis failed")
    
    def export_report(self):
        """Export analytics results as a report"""
        if not self.analytics_results:
            QMessageBox.warning(self, "No Data", "No analytics results available to export.")
            return
        
        # Show save dialog
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export Analytics Report",
            "",
            "PDF Report (*.pdf);;HTML Report (*.html);;Excel Report (*.xlsx);;JSON Data (*.json)"
        )
        
        if not file_path:
            return
        
        # Create exporter
        exporter = ComboExporter()
        
        # Export report
        try:
            success = exporter.export_analytics_report(
                self.analytics_results,
                file_path,
                include_figures=True
            )
            
            if success:
                self.status_bar.showMessage(f"Exported analytics report to {file_path}")
                self.logger.info(f"Exported analytics report to {file_path}")
            else:
                QMessageBox.critical(self, "Export Error", "Failed to export analytics report.")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Error exporting report: {e}")
    
    # Combo operations
    
    def filter_custom(self):
        """Apply a custom filter to combos"""
        if not self.combos:
            QMessageBox.warning(self, "No Data", "No combos available to filter.")
            return
        
        pattern, ok = QInputDialog.getText(
            self,
            "Custom Filter",
            "Enter regular expression pattern to filter out:"
        )
        
        if not ok or not pattern:
            return
        
        try:
            processor = ComboProcessor()
            filtered = processor.filter_by_regex(self.combos, pattern, invert=True)
            
            # Update combos
            self.combos = filtered
            self.update_combo_display()
            
            removed = len(self.original_combos) - len(self.combos)
            self.status_bar.showMessage(f"Filter applied: {removed:,} combos removed, {len(self.combos):,} remaining")
            self.logger.info(f"Custom filter applied: {removed:,} combos removed")
        except Exception as e:
            QMessageBox.critical(self, "Filter Error", f"Error applying filter: {e}")
    
    def filter_by_domain(self):
        """Filter combos by email domain"""
        if not self.combos:
            QMessageBox.warning(self, "No Data", "No combos available to filter.")
            return
        
        domain, ok = QInputDialog.getText(
            self,
            "Filter by Domain",
            "Enter domain to keep (e.g., gmail.com):"
        )
        
        if not ok or not domain:
            return
        
        try:
            processor = ComboProcessor()
            filtered = processor.filter_by_domain(self.combos, [domain])
            
            # Update combos
            self.combos = filtered
            self.update_combo_display()
            
            self.status_bar.showMessage(f"Domain filter applied: {len(self.combos):,} combos remaining")
            self.logger.info(f"Domain filter applied: {len(self.combos):,} combos with domain {domain}")
        except Exception as e:
            QMessageBox.critical(self, "Filter Error", f"Error applying filter: {e}")
    
    def filter_by_password_length(self):
        """Filter combos by password length"""
        if not self.combos:
            QMessageBox.warning(self, "No Data", "No combos available to filter.")
            return
        
        dialog = FilterDialog(FilterDialog.TYPE_PASSWORD_LENGTH)
        if dialog.exec() != QDialog.Accepted:
            return
        
        min_length = dialog.min_value
        max_length = dialog.max_value
        
        try:
            processor = ComboProcessor()
            filtered = processor.filter_by_password_length(self.combos, min_length, max_length)
            
            # Update combos
            self.combos = filtered
            self.update_combo_display()
            
            self.status_bar.showMessage(
                f"Password length filter applied: {len(self.combos):,} combos with length {min_length}-{max_length}"
            )
            self.logger.info(f"Password length filter applied: {min_length}-{max_length}")
        except Exception as e:
            QMessageBox.critical(self, "Filter Error", f"Error applying filter: {e}")
    
    def filter_with_symbols(self):
        """Filter combos to keep only those with symbols in password"""
        if not self.combos:
            QMessageBox.warning(self, "No Data", "No combos available to filter.")
            return
        
        try:
            processor = ComboProcessor()
            filtered = processor.filter_by_regex(self.combos, r':[^:]*[!@#$%^&*()_+\-=\[\]{}|;:\'",.<>?/\\]')
            
            # Update combos
            self.combos = filtered
            self.update_combo_display()
            
            self.status_bar.showMessage(f"Symbol filter applied: {len(self.combos):,} combos with symbols")
            self.logger.info(f"Symbol filter applied: {len(self.combos):,} combos with symbols")
        except Exception as e:
            QMessageBox.critical(self, "Filter Error", f"Error applying filter: {e}")
    
    def extract_edu(self):
        """Extract .edu email addresses"""
        if not self.combos:
            QMessageBox.warning(self, "No Data", "No combos available to filter.")
            return
        
        try:
            processor = ComboProcessor()
            filtered = processor.filter_by_regex(self.combos, r'@.*\.edu\b')
            
            # Update combos
            self.combos = filtered
            self.update_combo_display()
            
            self.status_bar.showMessage(f"Extracted {len(self.combos):,} .edu combos")
            self.logger.info(f"Extracted {len(self.combos):,} .edu combos")
        except Exception as e:
            QMessageBox.critical(self, "Filter Error", f"Error applying filter: {e}")
    
    def append_to_password(self):
        """Append text to all passwords"""
        if not self.combos:
            QMessageBox.warning(self, "No Data", "No combos available to modify.")
            return
        
        suffix, ok = QInputDialog.getText(
            self,
            "Append to Passwords",
            "Enter text to append to all passwords:"
        )
        
        if not ok or not suffix:
            return
        
        try:
            processor = ComboProcessor()
            modified = processor.modify_passwords(self.combos, 'append', suffix)
            
            # Update combos
            self.combos = modified
            self.update_combo_display()
            
            self.status_bar.showMessage(f"Appended '{suffix}' to {len(self.combos):,} passwords")
            self.logger.info(f"Appended '{suffix}' to {len(self.combos):,} passwords")
        except Exception as e:
            QMessageBox.critical(self, "Modification Error", f"Error modifying passwords: {e}")
    
    def prepend_to_password(self):
        """Prepend text to all passwords"""
        if not self.combos:
            QMessageBox.warning(self, "No Data", "No combos available to modify.")
            return
        
        prefix, ok = QInputDialog.getText(
            self,
            "Prepend to Passwords",
            "Enter text to prepend to all passwords:"
        )
        
        if not ok or not prefix:
            return
        
        try:
            processor = ComboProcessor()
            modified = processor.modify_passwords(self.combos, 'prepend', prefix)
            
            # Update combos
            self.combos = modified
            self.update_combo_display()
            
            self.status_bar.showMessage(f"Prepended '{prefix}' to {len(self.combos):,} passwords")
            self.logger.info(f"Prepended '{prefix}' to {len(self.combos):,} passwords")
        except Exception as e:
            QMessageBox.critical(self, "Modification Error", f"Error modifying passwords: {e}")
    
    def capitalize_password(self):
        """Capitalize the first letter of passwords"""
        if not self.combos:
            QMessageBox.warning(self, "No Data", "No combos available to modify.")
            return
        
        try:
            processor = ComboProcessor()
            modified = processor.modify_passwords(self.combos, 'capitalize', '')
            
            # Update combos
            self.combos = modified
            self.update_combo_display()
            
            self.status_bar.showMessage(f"Capitalized {len(self.combos):,} passwords")
            self.logger.info(f"Capitalized {len(self.combos):,} passwords")
        except Exception as e:
            QMessageBox.critical(self, "Modification Error", f"Error modifying passwords: {e}")
    
    def batch_replace(self):
        """Perform batch text replacement"""
        if not self.combos:
            QMessageBox.warning(self, "No Data", "No combos available to modify.")
            return
        
        old_text, ok1 = QInputDialog.getText(
            self,
            "Batch Replace",
            "Enter text to replace:"
        )
        
        if not ok1 or not old_text:
            return
        
        new_text, ok2 = QInputDialog.getText(
            self,
            "Batch Replace",
            "Enter replacement text:"
        )
        
        if not ok2:
            return
        
        try:
            # Create replacer string in format old:new
            replacer = f"{old_text}:{new_text}"
            
            processor = ComboProcessor()
            modified = processor.modify_passwords(self.combos, 'replace', replacer)
            
            # Update combos
            self.combos = modified
            self.update_combo_display()
            
            self.status_bar.showMessage(f"Replaced '{old_text}' with '{new_text}' in combos")
            self.logger.info(f"Replaced '{old_text}' with '{new_text}' in combos")
        except Exception as e:
            QMessageBox.critical(self, "Modification Error", f"Error performing replacement: {e}")
    
    def sort_by_email(self):
        """Sort combos by email"""
        if not self.combos:
            QMessageBox.warning(self, "No Data", "No combos available to sort.")
            return
        
        try:
            processor = ComboProcessor()
            operations = [{'type': 'sort', 'params': {'key': 'combo'}}]
            sorted_combos = processor.batch_process(self.combos, operations)
            
            # Update combos
            self.combos = sorted_combos
            self.update_combo_display()
            
            self.status_bar.showMessage(f"Sorted {len(self.combos):,} combos by email")
            self.logger.info(f"Sorted {len(self.combos):,} combos by email")
        except Exception as e:
            QMessageBox.critical(self, "Sort Error", f"Error sorting combos: {e}")
    
    def sort_by_domain(self):
        """Sort combos by domain"""
        if not self.combos:
            QMessageBox.warning(self, "No Data", "No combos available to sort.")
            return
        
        try:
            processor = ComboProcessor()
            operations = [{'type': 'sort', 'params': {'key': 'domain'}}]
            sorted_combos = processor.batch_process(self.combos, operations)
            
            # Update combos
            self.combos = sorted_combos
            self.update_combo_display()
            
            self.status_bar.showMessage(f"Sorted {len(self.combos):,} combos by domain")
            self.logger.info(f"Sorted {len(self.combos):,} combos by domain")
        except Exception as e:
            QMessageBox.critical(self, "Sort Error", f"Error sorting combos: {e}")
    
    def sort_by_password_length(self):
        """Sort combos by password length"""
        if not self.combos:
            QMessageBox.warning(self, "No Data", "No combos available to sort.")
            return
        
        try:
            processor = ComboProcessor()
            operations = [{'type': 'sort', 'params': {'key': 'password_length'}}]
            sorted_combos = processor.batch_process(self.combos, operations)
            
            # Update combos
            self.combos = sorted_combos
            self.update_combo_display()
            
            self.status_bar.showMessage(f"Sorted {len(self.combos):,} combos by password length")
            self.logger.info(f"Sorted {len(self.combos):,} combos by password length")
        except Exception as e:
            QMessageBox.critical(self, "Sort Error", f"Error sorting combos: {e}")
    
    def randomize_combos(self):
        """Randomize combo order"""
        if not self.combos:
            QMessageBox.warning(self, "No Data", "No combos available to randomize.")
            return
        
        try:
            processor = ComboProcessor()
            operations = [{'type': 'shuffle'}]
            randomized = processor.batch_process(self.combos, operations)
            
            # Update combos
            self.combos = randomized
            self.update_combo_display()
            
            self.status_bar.showMessage(f"Randomized {len(self.combos):,} combos")
            self.logger.info(f"Randomized {len(self.combos):,} combos")
        except Exception as e:
            QMessageBox.critical(self, "Randomize Error", f"Error randomizing combos: {e}")
    
    def show_domain_stats(self):
        """Show domain statistics"""
        if not self.combos:
            QMessageBox.warning(self, "No Data", "No combos available for analysis.")
            return
        
        try:
            processor = ComboProcessor()
            domain_stats = processor.get_domain_stats(self.combos)
            
            # Convert to sorted list of tuples
            stats_list = sorted(domain_stats.items(), key=lambda x: x[1], reverse=True)
            
            # Format for display
            stats_text = "Domain Statistics:\n\n"
            stats_text += "Domain".ljust(30) + "Count".ljust(10) + "Percentage\n"
            stats_text += "-" * 50 + "\n"
            
            total = sum(domain_stats.values())
            for domain, count in stats_list[:50]:  # Show top 50
                percentage = (count / total) * 100
                stats_text += f"{domain.ljust(30)}{str(count).ljust(10)}{percentage:.2f}%\n"
            
            # Show in message box
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Domain Statistics")
            msg_box.setText(stats_text)
            msg_box.setDetailedText("\n".join([f"{domain}: {count}" for domain, count in stats_list]))
            msg_box.exec()
            
            self.status_bar.showMessage("Domain statistics generated")
        except Exception as e:
            QMessageBox.critical(self, "Statistics Error", f"Error generating domain stats: {e}")
    
    def show_password_stats(self):
        """Show password statistics"""
        if not self.combos:
            QMessageBox.warning(self, "No Data", "No combos available for analysis.")
            return
        
        # Run dedicated analysis to get more detailed password stats
        self.run_specific_analysis("strength")
    
    def batch_operations(self):
        """Open batch operations dialog"""
        if not self.combos:
            QMessageBox.warning(self, "No Data", "No combos available to process.")
            return
        
        dialog = BatchOperationsDialog(self.combos)
        if dialog.exec() == QDialog.Accepted and dialog.processed_combos:
            # Update combos
            self.combos = dialog.processed_combos
            self.update_combo_display()
            
            self.status_bar.showMessage(f"Batch operations applied: {len(self.combos):,} combos remaining")
            self.logger.info(f"Batch operations applied, {len(self.combos):,} combos remaining")
    
    def reset_to_original(self):
        """Reset combos to original state"""
        if not self.original_combos:
            QMessageBox.warning(self, "No Data", "No original combo data available.")
            return
        
        # Confirm with user
        reply = QMessageBox.question(
            self,
            "Reset Combos",
            "Reset to original combo data? This will undo all modifications.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.combos = self.original_combos.copy()
            self.update_combo_display()
            
            self.status_bar.showMessage(f"Reset to original data: {len(self.combos):,} combos")
            self.logger.info(f"Reset to original data: {len(self.combos):,} combos")
    
    # Help functions
    
    def show_documentation(self):
        """Show documentation"""
        QMessageBox.information(
            self,
            "Documentation",
            "Documentation is available online at https://github.com/krackn88/gsort-professional/wiki"
        )
    
    def check_updates(self):
        """Check for updates"""
        # This would normally connect to a server to check for updates
        QMessageBox.information(
            self,
            "Check for Updates",
            "You are running the latest version of gSort Professional."
        )
    
    def show_about(self):
        """Show about dialog"""
        about_text = """
        <h2>gSort Professional</h2>
        <p>Version 2.0.0</p>
        <p>High-performance tool for processing and analyzing email:password combinations</p>
        <p>&copy; 2025 gSort Professional</p>
        """
        
        QMessageBox.about(self, "About gSort Professional", about_text)

    def event(self, event):
        if customEventHandler(self, event):
            return True
        return super().event(event)


# Custom event for analysis completion
class AnalysisCompletedEvent(QEvent):
    """Custom event for when analysis is completed"""
    EVENT_TYPE = QEvent.Type(QEvent.registerEventType())
    
    def __init__(self, results: Dict[str, AnalyticsResult]):
        super().__init__(self.EVENT_TYPE)
        self.results = results


class AnalysisErrorEvent(QEvent):
    """Custom event for when analysis fails"""
    EVENT_TYPE = QEvent.Type(QEvent.registerEventType())
    
    def __init__(self, error_msg: str):
        super().__init__(self.EVENT_TYPE)
        self.error_msg = error_msg


# Add event handlers to QMainWindow
def customEventHandler(self, event):
    """Handle custom events"""
    if event.type() == AnalysisCompletedEvent.EVENT_TYPE:
        self.analysis_completed(event.results)
        return True
    elif event.type() == AnalysisErrorEvent.EVENT_TYPE:
        self.analysis_error(event.error_msg)
        return True
    return False