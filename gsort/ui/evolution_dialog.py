"""
Password Evolution Dialog for gSort Professional.
Allows users to generate evolved password combinations.
"""

import logging
from typing import List, Dict, Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, 
    QSpinBox, QRadioButton, QButtonGroup, QGroupBox,
    QPushButton, QComboBox, QProgressBar, QMessageBox,
    QCheckBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from gsort.core.password_evolution import PasswordEvolutionSimulator


class EvolutionWorker(QThread):
    """Worker thread for password evolution"""
    
    finished = pyqtSignal(list)
    progress = pyqtSignal(int)
    
    def __init__(self, combos: List[str], percentage: int, strategy: str):
        super().__init__()
        self.combos = combos
        self.percentage = percentage
        self.strategy = strategy
    
    def run(self):
        """Run the evolution process"""
        simulator = PasswordEvolutionSimulator()
        evolved_combos = simulator.generate_evolved_combos(
            self.combos, 
            self.percentage, 
            self.strategy
        )
        self.finished.emit(evolved_combos)


class PasswordEvolutionDialog(QDialog):
    """Dialog for evolving passwords"""
    
    def __init__(self, combos: List[str], parent=None):
        super().__init__(parent)
        
        self.logger = logging.getLogger(__name__)
        self.combos = combos
        self.evolved_combos = None
        
        # Set up the dialog
        self.setWindowTitle("Password Evolution Simulator")
        self.resize(500, 500)
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the UI components"""
        # Main layout
        layout = QVBoxLayout(self)
        
        # Info label
        info_label = QLabel(
            "This feature simulates how users typically change their passwords "
            "when prompted by websites. It applies research-based patterns to "
            "create realistic password evolutions."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Form layout for settings
        form_layout = QFormLayout()
        
        # Percentage setting
        self.percentage_spin = QSpinBox()
        self.percentage_spin.setRange(1, 100)
        self.percentage_spin.setValue(100)
        self.percentage_spin.setSuffix("%")
        self.percentage_spin.setToolTip("Percentage of passwords to evolve")
        form_layout.addRow(QLabel("Passwords to Evolve:"), self.percentage_spin)
        
        # Strategy selection
        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems([
            "Random (Realistic Mix)",
            "Increment Numbers",
            "Character Substitution",
            "Change Capitalization",
            "Append Temporal Info",
            "Add/Change Symbols",
            "Combined Strategies"
        ])
        self.strategy_combo.setToolTip("Strategy to use for password evolution")
        form_layout.addRow(QLabel("Evolution Strategy:"), self.strategy_combo)
        
        layout.addLayout(form_layout)
        
        # Evolution patterns info
        self._add_evolution_patterns_info(layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        # Cancel button
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        
        # Generate button
        self.generate_button = QPushButton("Generate Evolved Passwords")
        self.generate_button.setDefault(True)
        self.generate_button.clicked.connect(self.generate_evolved_passwords)
        
        # Add buttons to layout
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(self.generate_button)
        
        layout.addLayout(button_layout)
    
    def _add_evolution_patterns_info(self, layout):
        """Add information about password evolution patterns"""
        patterns_group = QGroupBox("Common Password Change Patterns")
        patterns_layout = QVBoxLayout(patterns_group)
        
        patterns = [
            "<b>Incremental Changes</b> (70-80%): Adding or incrementing numbers, changing single characters",
            "<b>Seasonal/Temporal</b> (15-20%): Adding month/year or seasonal references",
            "<b>Character Substitution</b> (40-50%): Changing letters to similar-looking symbols (a→4, e→3)",
            "<b>Structure Preservation</b> (80-90%): Maintaining password length and base words"
        ]
        
        for pattern in patterns:
            label = QLabel(pattern)
            label.setTextFormat(Qt.RichText)
            patterns_layout.addWidget(label)
        
        layout.addWidget(patterns_group)
    
    def generate_evolved_passwords(self):
        """Generate evolved passwords based on settings"""
        if not self.combos:
            QMessageBox.warning(self, "No Data", "No password combinations available to evolve.")
            return
        
        # Get settings
        percentage = self.percentage_spin.value()
        
        # Map strategy selection to internal strategy name
        strategy_map = {
            0: "random",      # Random (Realistic Mix)
            1: "increment",   # Increment Numbers
            2: "substitute",  # Character Substitution
            3: "capitalize",  # Change Capitalization
            4: "append",      # Append Temporal Info
            5: "symbol",      # Add/Change Symbols
            6: "combined"     # Combined Strategies
        }
        strategy = strategy_map[self.strategy_combo.currentIndex()]
        
        # Disable buttons during processing
        self.generate_button.setEnabled(False)
        
        # Create and start worker thread
        self.worker = EvolutionWorker(self.combos, percentage, strategy)
        self.worker.finished.connect(self.evolution_completed)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.start()
    
    def evolution_completed(self, evolved_combos):
        """Handle completion of evolution process"""
        self.evolved_combos = evolved_combos
        
        # Calculate stats
        original_count = len(self.combos)
        evolved_count = sum(1 for orig, evolved in zip(self.combos, evolved_combos) if orig != evolved)
        
        # Show summary
        QMessageBox.information(
            self,
            "Evolution Complete",
            f"Generated {evolved_count:,} evolved passwords.\n\n"
            f"The evolved passwords simulate how users typically modify their "
            f"passwords when prompted to change them by websites."
        )
        
        # Re-enable buttons
        self.generate_button.setEnabled(True)
        
        # Accept dialog if we have results
        if evolved_count > 0:
            self.accept()