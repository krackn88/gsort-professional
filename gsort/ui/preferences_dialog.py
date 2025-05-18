"""
Preferences dialog for gSort Professional.
"""

import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, 
    QSpinBox, QCheckBox, QPushButton, QComboBox
)
from PyQt5.QtCore import Qt


class PreferencesDialog(QDialog):
    """Dialog for setting application preferences"""
    
    def __init__(self, preview_count: int, thread_count: int, auto_analyze: bool, parent=None):
        super().__init__(parent)
        
        self.logger = logging.getLogger(__name__)
        
        # Store initial values
        self.preview_count = preview_count
        self.thread_count = thread_count
        self.auto_analyze = auto_analyze
        
        # Set up the dialog
        self.setWindowTitle("Preferences")
        self.resize(400, 300)
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the UI components"""
        # Main layout
        layout = QVBoxLayout(self)
        
        # Form layout for settings
        form_layout = QFormLayout()
        
        # Preview count setting
        self.preview_spin = QSpinBox()
        self.preview_spin.setRange(10, 1000)
        self.preview_spin.setValue(self.preview_count)
        self.preview_spin.setSingleStep(10)
        self.preview_spin.setToolTip("Number of combos to display in the preview area")
        form_layout.addRow(QLabel("Preview Count:"), self.preview_spin)
        
        # Thread count setting
        self.thread_spin = QSpinBox()
        self.thread_spin.setRange(1, 32)
        self.thread_spin.setValue(self.thread_count)
        self.thread_spin.setToolTip("Number of worker threads for processing (higher = faster, but uses more CPU)")
        form_layout.addRow(QLabel("Worker Threads:"), self.thread_spin)
        
        # Auto analyze setting
        self.auto_analyze_check = QCheckBox("Automatically run analysis after processing")
        self.auto_analyze_check.setChecked(self.auto_analyze)
        self.auto_analyze_check.setToolTip("When enabled, analysis will run automatically after files are processed")
        
        # Button layout
        button_layout = QHBoxLayout()
        
        # Cancel button
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        
        # Apply button
        apply_button = QPushButton("Apply")
        apply_button.setDefault(True)
        apply_button.clicked.connect(self.accept)
        
        # Add buttons to layout
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(apply_button)
        
        # Add layouts to main layout
        layout.addLayout(form_layout)
        layout.addWidget(self.auto_analyze_check)
        layout.addStretch()
        layout.addLayout(button_layout)
    
    def accept(self):
        """Handle dialog acceptance"""
        # Update values from widgets
        self.preview_count = self.preview_spin.value()
        self.thread_count = self.thread_spin.value()
        self.auto_analyze = self.auto_analyze_check.isChecked()
        
        self.logger.info(
            f"Preferences updated: preview_count={self.preview_count}, "
            f"thread_count={self.thread_count}, auto_analyze={self.auto_analyze}"
        )
        
        # Accept the dialog
        super().accept()