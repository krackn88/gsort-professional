"""
Batch operations dialog for gSort Professional.
Allows applying multiple operations to combos in sequence.
"""

import logging
from typing import List, Dict, Any, Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, 
    QSpinBox, QLineEdit, QPushButton, QComboBox, QListWidget,
    QWidget, QGroupBox, QRadioButton, QButtonGroup, QCheckBox,
    QListWidgetItem, QMessageBox, QProgressBar, QFileDialog
)
from PyQt6.QtCore import Qt, QSize

from gsort.core.processor import ComboProcessor


class BatchOperationsDialog(QDialog):
    """Dialog for applying multiple operations to combos in sequence"""
    
    def __init__(self, combos: List[str], parent=None):
        super().__init__(parent)
        
        self.logger = logging.getLogger(__name__)
        self.combos = combos
        self.processed_combos = None
        self.operations = []
        
        # Set up the dialog
        self.setWindowTitle("Batch Operations")
        self.resize(800, 600)
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the UI components"""
        # Main layout
        layout = QVBoxLayout(self)
        
        # Top section: operation selector
        top_layout = QHBoxLayout()
        
        # Operation type group
        op_group = QGroupBox("Operation Type")
        op_layout = QVBoxLayout(op_group)
        
        self.op_type_combo = QComboBox()
        self.op_type_combo.addItems([
            "Filter by Domain",
            "Filter by Password Length",
            "Filter by Regex",
            "Modify Password",
            "Sort",
            "Randomize"
        ])
        self.op_type_combo.currentIndexChanged.connect(self._update_op_config)
        
        op_layout.addWidget(self.op_type_combo)
        top_layout.addWidget(op_group)
        
        # Operation configuration group
        self.op_config_group = QGroupBox("Operation Configuration")
        self.op_config_layout = QVBoxLayout(self.op_config_group)
        
        # Placeholder for dynamic content
        top_layout.addWidget(self.op_config_group, 2)
        
        # Add button
        add_button = QPushButton("Add Operation")
        add_button.clicked.connect(self._add_operation)
        top_layout.addWidget(add_button)
        
        layout.addLayout(top_layout)
        
        # Middle section: operation list
        self.op_list = QListWidget()
        self.op_list.setSelectionMode(QListWidget.SingleSelection)
        self.op_list.setMinimumHeight(200)
        
        layout.addWidget(QLabel("Operations Queue:"))
        layout.addWidget(self.op_list)
        
        # Operation controls
        op_controls = QHBoxLayout()
        
        remove_button = QPushButton("Remove Selected")
        remove_button.clicked.connect(self._remove_operation)
        
        clear_button = QPushButton("Clear All")
        clear_button.clicked.connect(self._clear_operations)
        
        move_up_button = QPushButton("Move Up")
        move_up_button.clicked.connect(self._move_up)
        
        move_down_button = QPushButton("Move Down")
        move_down_button.clicked.connect(self._move_down)
        
        op_controls.addWidget(remove_button)
        op_controls.addWidget(clear_button)
        op_controls.addWidget(move_up_button)
        op_controls.addWidget(move_down_button)
        
        layout.addLayout(op_controls)
        
        # Bottom section: preview and run
        stats_layout = QHBoxLayout()
        
        original_count_label = QLabel(f"Original Count: {len(self.combos):,}")
        self.current_count_label = QLabel(f"Current Count: {len(self.combos):,}")
        
        stats_layout.addWidget(original_count_label)
        stats_layout.addWidget(self.current_count_label)
        
        layout.addLayout(stats_layout)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        
        preview_button = QPushButton("Preview")
        preview_button.clicked.connect(self._preview_operations)
        
        run_button = QPushButton("Apply All")
        run_button.setDefault(True)
        run_button.clicked.connect(self._run_operations)
        
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(preview_button)
        button_layout.addWidget(run_button)
        
        layout.addLayout(button_layout)
        
        # Initialize the first configuration panel
        self._update_op_config()
    
    def _update_op_config(self):
        """Update the operation configuration panel based on selected type"""
        # Clear existing widgets
        while self.op_config_layout.count():
            item = self.op_config_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Get selected operation type
        op_index = self.op_type_combo.currentIndex()
        
        # Create configuration panel based on type
        if op_index == 0:  # Filter by Domain
            self._create_domain_config()
        elif op_index == 1:  # Filter by Password Length
            self._create_length_config()
        elif op_index == 2:  # Filter by Regex
            self._create_regex_config()
        elif op_index == 3:  # Modify Password
            self._create_modify_config()
        elif op_index == 4:  # Sort
            self._create_sort_config()
        elif op_index == 5:  # Randomize
            self._create_randomize_config()
    
    def _create_domain_config(self):
        """Create configuration panel for domain filtering"""
        form = QFormLayout()
        
        self.domain_edit = QLineEdit()
        self.domain_edit.setPlaceholderText("e.g., gmail.com")
        
        form.addRow(QLabel("Domain:"), self.domain_edit)
        self.op_config_layout.addLayout(form)
    
    def _create_length_config(self):
        """Create configuration panel for password length filtering"""
        form = QFormLayout()
        
        self.min_length = QSpinBox()
        self.min_length.setRange(1, 100)
        self.min_length.setValue(8)
        
        self.max_length = QSpinBox()
        self.max_length.setRange(1, 100)
        self.max_length.setValue(32)
        
        # Connect to ensure min <= max
        self.min_length.valueChanged.connect(self._update_min_max)
        self.max_length.valueChanged.connect(self._update_min_max)
        
        form.addRow(QLabel("Minimum Length:"), self.min_length)
        form.addRow(QLabel("Maximum Length:"), self.max_length)
        self.op_config_layout.addLayout(form)
    
    def _create_regex_config(self):
        """Create configuration panel for regex filtering"""
        form = QFormLayout()
        
        self.regex_edit = QLineEdit()
        self.regex_edit.setPlaceholderText("Regular expression pattern")
        
        form.addRow(QLabel("Pattern:"), self.regex_edit)
        self.op_config_layout.addLayout(form)
        
        # Match options
        match_group = QGroupBox("Match Options")
        match_layout = QVBoxLayout(match_group)
        
        self.match_include = QRadioButton("Keep matching combos")
        self.match_exclude = QRadioButton("Remove matching combos")
        self.match_include.setChecked(True)
        
        match_layout.addWidget(self.match_include)
        match_layout.addWidget(self.match_exclude)
        
        self.op_config_layout.addWidget(match_group)
    
    def _create_modify_config(self):
        """Create configuration panel for password modification"""
        form = QFormLayout()
        
        self.modify_type = QComboBox()
        self.modify_type.addItems([
            "Append Text", 
            "Prepend Text", 
            "Capitalize First Letter",
            "Replace Text"
        ])
        self.modify_type.currentIndexChanged.connect(self._update_modify_fields)
        
        form.addRow(QLabel("Modification:"), self.modify_type)
        self.op_config_layout.addLayout(form)
        
        # Dynamic fields container
        self.modify_fields = QWidget()
        self.modify_layout = QFormLayout(self.modify_fields)
        
        self.op_config_layout.addWidget(self.modify_fields)
        
        # Initialize fields
        self._update_modify_fields()
    
    def _update_modify_fields(self):
        """Update modification fields based on selected type"""
        # Clear existing fields
        while self.modify_layout.count():
            item = self.modify_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        modify_index = self.modify_type.currentIndex()
        
        if modify_index == 0:  # Append
            self.text_edit = QLineEdit()
            self.text_edit.setPlaceholderText("Text to append")
            self.modify_layout.addRow(QLabel("Append:"), self.text_edit)
        
        elif modify_index == 1:  # Prepend
            self.text_edit = QLineEdit()
            self.text_edit.setPlaceholderText("Text to prepend")
            self.modify_layout.addRow(QLabel("Prepend:"), self.text_edit)
        
        elif modify_index == 2:  # Capitalize
            # No additional fields needed
            self.modify_layout.addRow(QLabel("Capitalizes the first letter of each password"))
        
        elif modify_index == 3:  # Replace
            self.old_text = QLineEdit()
            self.old_text.setPlaceholderText("Text to find")
            self.modify_layout.addRow(QLabel("Find:"), self.old_text)
            
            self.new_text = QLineEdit()
            self.new_text.setPlaceholderText("Replacement text")
            self.modify_layout.addRow(QLabel("Replace with:"), self.new_text)
    
    def _create_sort_config(self):
        """Create configuration panel for sorting"""
        form = QFormLayout()
        
        self.sort_field = QComboBox()
        self.sort_field.addItems([
            "Email",
            "Domain",
            "Password Length"
        ])
        
        self.sort_order = QComboBox()
        self.sort_order.addItems([
            "Ascending",
            "Descending"
        ])
        
        form.addRow(QLabel("Sort by:"), self.sort_field)
        form.addRow(QLabel("Order:"), self.sort_order)
        self.op_config_layout.addLayout(form)
    
    def _create_randomize_config(self):
        """Create configuration panel for randomization"""
        # No configuration needed
        self.op_config_layout.addWidget(QLabel("This operation will randomize the order of all combos."))
    
    def _update_min_max(self):
        """Ensure min value is not greater than max value"""
        min_val = self.min_length.value()
        max_val = self.max_length.value()
        
        if min_val > max_val:
            if self.sender() == self.min_length:
                self.max_length.setValue(min_val)
            else:
                self.min_length.setValue(max_val)
    
    def _add_operation(self):
        """Add current operation to the queue"""
        # Get operation type
        op_index = self.op_type_combo.currentIndex()
        
        # Create operation dictionary
        operation = {
            "type": "",
            "params": {},
            "description": ""
        }
        
        # Fill in details based on type
        if op_index == 0:  # Filter by Domain
            domain = self.domain_edit.text().strip()
            if not domain:
                QMessageBox.warning(self, "Invalid Input", "Please enter a domain.")
                return
            
            operation["type"] = "filter_domain"
            operation["params"] = {"domains": [domain]}
            operation["description"] = f"Filter by Domain: {domain}"
        
        elif op_index == 1:  # Filter by Password Length
            min_len = self.min_length.value()
            max_len = self.max_length.value()
            
            operation["type"] = "filter_length"
            operation["params"] = {"min_length": min_len, "max_length": max_len}
            operation["description"] = f"Filter by Password Length: {min_len}-{max_len}"
        
        elif op_index == 2:  # Filter by Regex
            pattern = self.regex_edit.text()
            if not pattern:
                QMessageBox.warning(self, "Invalid Input", "Please enter a regex pattern.")
                return
            
            invert = self.match_exclude.isChecked()
            
            operation["type"] = "filter_regex"
            operation["params"] = {"pattern": pattern, "invert": invert}
            operation["description"] = f"Filter by Regex: {pattern} ({'exclude' if invert else 'include'} matches)"
        
        elif op_index == 3:  # Modify Password
            modify_index = self.modify_type.currentIndex()
            
            if modify_index == 0:  # Append
                text = self.text_edit.text()
                if not text:
                    QMessageBox.warning(self, "Invalid Input", "Please enter text to append.")
                    return
                
                operation["type"] = "modify"
                operation["params"] = {"operation": "append", "value": text}
                operation["description"] = f"Append to Password: '{text}'"
            
            elif modify_index == 1:  # Prepend
                text = self.text_edit.text()
                if not text:
                    QMessageBox.warning(self, "Invalid Input", "Please enter text to prepend.")
                    return
                
                operation["type"] = "modify"
                operation["params"] = {"operation": "prepend", "value": text}
                operation["description"] = f"Prepend to Password: '{text}'"
            
            elif modify_index == 2:  # Capitalize
                operation["type"] = "modify"
                operation["params"] = {"operation": "capitalize", "value": ""}
                operation["description"] = "Capitalize Password First Letter"
            
            elif modify_index == 3:  # Replace
                old_text = self.old_text.text()
                new_text = self.new_text.text()
                if not old_text:
                    QMessageBox.warning(self, "Invalid Input", "Please enter text to find.")
                    return
                
                value = f"{old_text}:{new_text}"
                operation["type"] = "modify"
                operation["params"] = {"operation": "replace", "value": value}
                operation["description"] = f"Replace in Password: '{old_text}' → '{new_text}'"
        
        elif op_index == 4:  # Sort
            field_index = self.sort_field.currentIndex()
            reverse = self.sort_order.currentIndex() == 1
            
            field_map = ["combo", "domain", "password_length"]
            field = field_map[field_index]
            
            operation["type"] = "sort"
            operation["params"] = {"key": field, "reverse": reverse}
            operation["description"] = f"Sort by {self.sort_field.currentText()} ({self.sort_order.currentText()})"
        
        elif op_index == 5:  # Randomize
            operation["type"] = "shuffle"
            operation["params"] = {}
            operation["description"] = "Randomize Order"
        
        # Add operation to the list
        self.operations.append(operation)
        self.op_list.addItem(operation["description"])
    
    def _remove_operation(self):
        """Remove the selected operation from the queue"""
        selected = self.op_list.currentRow()
        if selected >= 0:
            self.op_list.takeItem(selected)
            del self.operations[selected]
    
    def _clear_operations(self):
        """Clear all operations from the queue"""
        self.op_list.clear()
        self.operations = []
    
    def _move_up(self):
        """Move the selected operation up in the queue"""
        selected = self.op_list.currentRow()
        if selected > 0:
            # Swap operations
            self.operations[selected], self.operations[selected-1] = self.operations[selected-1], self.operations[selected]
            
            # Update list widget
            item = self.op_list.takeItem(selected)
            self.op_list.insertItem(selected-1, item)
            self.op_list.setCurrentRow(selected-1)
    
    def _move_down(self):
        """Move the selected operation down in the queue"""
        selected = self.op_list.currentRow()
        if selected < self.op_list.count() - 1 and selected >= 0:
            # Swap operations
            self.operations[selected], self.operations[selected+1] = self.operations[selected+1], self.operations[selected]
            
            # Update list widget
            item = self.op_list.takeItem(selected)
            self.op_list.insertItem(selected+1, item)
            self.op_list.setCurrentRow(selected+1)
    
    def _preview_operations(self):
        """Preview the result of applying operations"""
        if not self.operations:
            QMessageBox.information(self, "No Operations", "No operations have been added.")
            return
        
        # Process combos
        processor = ComboProcessor()
        result = processor.batch_process(self.combos, self.operations)
        
        # Update count label
        self.current_count_label.setText(f"Preview Count: {len(result):,}")
        
        # Show summary
        QMessageBox.information(
            self,
            "Preview Result",
            f"Original count: {len(self.combos):,}\n"
            f"After operations: {len(result):,}\n"
            f"Difference: {len(self.combos) - len(result):,}"
        )
    
    def _run_operations(self):
        """Apply all operations and accept the dialog"""
        if not self.operations:
            QMessageBox.information(self, "No Operations", "No operations have been added.")
            return
        
        # Process combos
        processor = ComboProcessor()
        self.processed_combos = processor.batch_process(self.combos, self.operations)
        
        # Log results
        self.logger.info(
            f"Batch operations applied: {len(self.operations)} operations, "
            f"{len(self.combos):,} → {len(self.processed_combos):,} combos"
        )
        
        # Accept the dialog
        self.accept()