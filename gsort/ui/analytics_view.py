"""
Analytics view component for gSort Professional.
Displays visualization results from the analytics module.
"""

import os
import io
import logging
from typing import Dict, Optional, List
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget, QScrollArea,
    QSplitter, QTextEdit, QComboBox, QPushButton, QFileDialog, QApplication
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QPixmap, QImage

from gsort.analytics.analyzer import AnalyticsResult


class MatplotlibCanvas(FigureCanvas):
    """Canvas for displaying matplotlib figures in Qt"""
    
    def __init__(self, figure: Figure):
        super().__init__(figure)
        self.setMinimumHeight(300)


class AnalyticsView(QWidget):
    """Widget for displaying analytics results and visualizations"""
    
    def __init__(self):
        super().__init__()
        
        self.logger = logging.getLogger(__name__)
        self.results: Dict[str, AnalyticsResult] = {}
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the UI components"""
        # Main layout
        layout = QVBoxLayout(self)
        
        # Tab widget to show different analysis results
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        
        # Add a welcome tab
        self.welcome_tab = QWidget()
        welcome_layout = QVBoxLayout(self.welcome_tab)
        
        welcome_label = QLabel("Welcome to the Analytics Dashboard")
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_label.setFont(QFont("Segoe UI", 14))
        
        instructions_label = QLabel(
            "Run analysis on your combo data to see visualizations and insights here.\n\n"
            "The analytics dashboard provides:\n"
            "• Domain distribution analysis\n"
            "• Password strength evaluation\n"
            "• Pattern detection\n"
            "• Email-password correlation analysis"
        )
        instructions_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instructions_label.setFont(QFont("Segoe UI", 11))
        
        welcome_layout.addStretch()
        welcome_layout.addWidget(welcome_label)
        welcome_layout.addWidget(instructions_label)
        welcome_layout.addStretch()
        
        self.tab_widget.addTab(self.welcome_tab, "Welcome")
        
        layout.addWidget(self.tab_widget)
    
    def set_results(self, results: Dict[str, AnalyticsResult]):
        """
        Set analytics results and update the display.
        
        Args:
            results: Dictionary mapping analysis names to AnalyticsResult objects
        """
        self.results = results
        self._update_display()
    
    def _update_display(self):
        """Update the display with current results"""
        # Clear existing tabs (except welcome)
        while self.tab_widget.count() > 1:
            self.tab_widget.removeTab(1)
        
        if not self.results:
            return
        
        # Remove welcome tab if we have results
        if self.tab_widget.count() > 0:
            self.tab_widget.removeTab(0)
        
        # Add a tab for each analysis result
        for name, result in self.results.items():
            # Create the tab content
            tab = self._create_result_tab(result)
            
            # Add tab with appropriate title
            tab_title = self._get_tab_title(name)
            self.tab_widget.addTab(tab, tab_title)
    
    def _create_result_tab(self, result: AnalyticsResult) -> QWidget:
        """
        Create a tab widget for displaying a single analysis result.
        
        Args:
            result: The analysis result to display
            
        Returns:
            QWidget containing the visualization and summary
        """
        # Create the tab widget and layout
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Add title and description
        title_label = QLabel(result.title)
        title_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        layout.addWidget(title_label)
        
        description_label = QLabel(result.description)
        description_label.setFont(QFont("Segoe UI", 10))
        description_label.setWordWrap(True)
        layout.addWidget(description_label)
        
        # Add a splitter to divide summary and figures
        splitter = QSplitter(Qt.Orientation.Vertical)
        layout.addWidget(splitter)
        
        # Add summary text
        summary_widget = QTextEdit()
        summary_widget.setReadOnly(True)
        summary_widget.setFont(QFont("Segoe UI", 10))
        summary_widget.setText(result.summary)
        summary_widget.setMaximumHeight(150)
        splitter.addWidget(summary_widget)
        
        # Container for figures
        figures_widget = QWidget()
        figures_layout = QVBoxLayout(figures_widget)
        
        # Add figures if present
        if result.figures:
            for i, fig in enumerate(result.figures):
                # Create canvas for the figure
                canvas = MatplotlibCanvas(fig)
                figures_layout.addWidget(canvas)
        
        # Add a scroll area for figures
        scroll_area = QScrollArea()
        scroll_area.setWidget(figures_widget)
        scroll_area.setWidgetResizable(True)
        splitter.addWidget(scroll_area)
        
        # Add export buttons
        button_layout = QHBoxLayout()
        
        export_data_btn = QPushButton("Export Data")
        export_data_btn.clicked.connect(lambda: self._export_data(result))
        button_layout.addWidget(export_data_btn)
        
        export_image_btn = QPushButton("Export Images")
        export_image_btn.clicked.connect(lambda: self._export_images(result))
        button_layout.addWidget(export_image_btn)
        
        layout.addLayout(button_layout)
        
        return tab
    
    def _get_tab_title(self, name: str) -> str:
        """
        Get a user-friendly tab title from the analysis name.
        
        Args:
            name: The internal name of the analysis
            
        Returns:
            User-friendly tab title
        """
        # Map internal names to user-friendly titles
        title_map = {
            "domain_analysis": "Domains",
            "password_strength": "Strength",
            "password_patterns": "Patterns",
            "email_password_correlation": "Correlation"
        }
        
        return title_map.get(name, name.replace("_", " ").title())
    
    def _export_data(self, result: AnalyticsResult):
        """
        Export the data from an analysis result.
        
        Args:
            result: The analysis result to export
        """
        # Show save dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Data",
            "",
            "JSON Files (*.json);;CSV Files (*.csv);;Excel Files (*.xlsx)"
        )
        
        if not file_path:
            return
        
        try:
            import json
            import pandas as pd
            
            # Determine format from extension
            _, ext = os.path.splitext(file_path)
            ext = ext.lower()
            
            if ext == '.json':
                # Export as JSON
                with open(file_path, 'w') as f:
                    json.dump(result.data, f, indent=2)
            
            elif ext == '.csv' or ext == '.xlsx':
                # Try to convert data to DataFrame
                try:
                    # Handle different data structures
                    if isinstance(result.data, dict):
                        # Try to find a suitable structure to export
                        for key, value in result.data.items():
                            if isinstance(value, dict) and all(isinstance(v, (int, float)) for v in value.values()):
                                # Simple key-value dict
                                df = pd.DataFrame({
                                    'key': list(value.keys()),
                                    'value': list(value.values())
                                })
                                break
                            elif isinstance(value, list) and value and isinstance(value[0], dict):
                                # List of dicts
                                df = pd.DataFrame(value)
                                break
                        else:
                            # If no suitable structure found, export flattened data
                            flattened = []
                            for key, value in result.data.items():
                                if isinstance(value, dict):
                                    for k, v in value.items():
                                        flattened.append({'category': key, 'key': k, 'value': v})
                                else:
                                    flattened.append({'category': 'main', 'key': key, 'value': value})
                            df = pd.DataFrame(flattened)
                    else:
                        # Convert as is
                        df = pd.DataFrame(result.data)
                    
                    # Export based on format
                    if ext == '.csv':
                        df.to_csv(file_path, index=False)
                    else:
                        df.to_excel(file_path, index=False)
                
                except Exception as e:
                    self.logger.error(f"Error converting data to DataFrame: {e}")
                    # Fall back to JSON if conversion fails
                    json_path = file_path + '.json'
                    with open(json_path, 'w') as f:
                        json.dump(result.data, f, indent=2)
                    self.logger.info(f"Exported data as JSON to {json_path}")
                    return
            
            self.logger.info(f"Exported data to {file_path}")
        
        except Exception as e:
            self.logger.error(f"Error exporting data: {e}")
    
    def _export_images(self, result: AnalyticsResult):
        """
        Export the figures from an analysis result as images.
        
        Args:
            result: The analysis result to export
        """
        if not result.figures:
            return
        
        # Show save dialog for directory
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Select Directory for Images"
        )
        
        if not dir_path:
            return
        
        try:
            # Export each figure
            for i, fig in enumerate(result.figures):
                # Create file path
                file_path = os.path.join(dir_path, f"{result.title.replace(' ', '_')}_{i+1}.png")
                
                # Save figure
                fig.savefig(file_path, dpi=300, bbox_inches='tight')
            
            self.logger.info(f"Exported {len(result.figures)} images to {dir_path}")
        
        except Exception as e:
            self.logger.error(f"Error exporting images: {e}")