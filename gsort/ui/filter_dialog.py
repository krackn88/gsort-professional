"""
Filter dialog for gSort Professional.
"""

import logging
from typing import List, Dict, Any, Optional

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, 
    QSpinBox, QLineEdit, QPushButton, QComboBox, QRadioButton,
    QButtonGroup, QGroupBox
)
from PyQt5.QtCore import Qt


class FilterDialog(QDialog):
    """Dialog for filtering combos with various criteria"""
    
    # Filter types
    TYPE_PASSWORD_LENGTH = "password_length"
    TYPE_DOMAIN = "domain"
    TYPE_REGEX = "regex"
    
    def __init__(self, filter_type: str, parent=None):
        super().__init__(parent)
        
        self.logger = logging.getLogger(__name__)
        self.filter_type = filter_type
        
        # Default values
        self.min_value = 1
        self.max_value = 100
        self.domain = ""
        self.regex_pattern = ""
        self.invert_match = False
        
        # Set up the dialog
        self.setWindowTitle("Filter Options")
        self.resize(400, 200)
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the UI components based on filter type"""
        # Main layout
        layout = QVBoxLayout(self)
        
        # Create appropriate filter UI
        if self.filter_type == self.TYPE_PASSWORD_LENGTH:
            self._init_length_filter()
        elif self.filter_type == self.TYPE_DOMAIN:
            self._init_domain_filter()
        elif self.filter_type == self.TYPE_REGEX:
            self._init_regex_filter()
        
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
        layout.addLayout(self.filter_layout)
        layout.addStretch()
        layout.addLayout(button_layout)
    
    def _init_length_filter(self):
        """Initialize UI for password length filter"""
        self.filter_layout = QFormLayout()
        
        # Min length
        self.min_spin = QSpinBox()
        self.min_spin.setRange(1, 100)
        self.min_spin.setValue(8)  # Default min length
        self.min_spin.setToolTip("Minimum password length to keep")
        self.filter_layout.addRow(QLabel("Minimum Length:"), self.min_spin)
        
        # Max length
        self.max_spin = QSpinBox()
        self.max_spin.setRange(1, 100)
        self.max_spin.setValue(32)  # Default max length
        self.max_spin.setToolTip("Maximum password length to keep")
        self.filter_layout.addRow(QLabel("Maximum Length:"), self.max_spin)
        
        # Connect signals
        self.min_spin.valueChanged.connect(self._update_min_max)
        self.max_spin.valueChanged.connect(self._update_min_max)
    
    def _init_domain_filter(self):
        """Initialize UI for domain filter"""
        self.filter_layout = QFormLayout()
        
        # Domain input
        self.domain_edit = QLineEdit()
        self.domain_edit.setPlaceholderText("e.g., gmail.com")
        self.domain_edit.setToolTip("Email domain to filter for")
        self.filter_layout.addRow(QLabel("Domain:"), self.domain_edit)
    
    def _init_regex_filter(self):
        """Initialize UI for regex filter"""
        self.filter_layout = QVBoxLayout()
        
        # Form layout for regex input
        form_layout = QFormLayout()
        
        # Regex input
        self.regex_edit = QLineEdit()
        self.regex_edit.setPlaceholderText("Regular expression pattern")
        self.regex_edit.setToolTip("Regular expression pattern to match against combos")
        form_layout.addRow(QLabel("Pattern:"), self.regex_edit)
        
        self.filter_layout.addLayout(form_layout)
        
        # Match options
        match_group = QGroupBox("Match Options")
        match_layout = QVBoxLayout(match_group)
        
        # Match behavior radio buttons
        self.match_include = QRadioButton("Keep matching combos")
        self.match_exclude = QRadioButton("Remove matching combos")
        self.match_include.setChecked(True)
        
        match_layout.addWidget(self.match_include)
        match_layout.addWidget(self.match_exclude)
        
        self.filter_layout.addWidget(match_group)
    
    def _update_min_max(self):
        """Ensure min value is not greater than max value"""
        min_val = self.min_spin.value()
        max_val = self.max_spin.value()
        
        if min_val > max_val:
            if self.sender() == self.min_spin:
                self.max_spin.setValue(min_val)
            else:
                self.min_spin.setValue(max_val)
    
    def accept(self):
        """Handle dialog acceptance"""
        # Update values from widgets based on filter type
        if self.filter_type == self.TYPE_PASSWORD_LENGTH:
            self.min_value = self.min_spin.value()
            self.max_value = self.max_spin.value()
            self.logger.info(f"Password length filter: {self.min_value}-{self.max_value}")
        
        elif self.filter_type == self.TYPE_DOMAIN:
            self.domain = self.domain_edit.text().strip()
            self.logger.info(f"Domain filter: {self.domain}")
        
        elif self.filter_type == self.TYPE_REGEX:
            self.regex_pattern = self.regex_edit.text()
            self.invert_match = self.match_exclude.isChecked()
            self.logger.info(f"Regex filter: {self.regex_pattern}, invert={self.invert_match}")
        
        # Accept the dialog
        super().accept()