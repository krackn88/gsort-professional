"""
Research features for gSort Professional.
This module adds research-oriented menu and functionality.
"""

import logging
from typing import List, Dict, Any, Optional

from PyQt6.QtWidgets import (
    QMenu, QMessageBox
)
from PyQt6.QtGui import QAction

from gsort.ui.evolution_dialog import PasswordEvolutionDialog


def add_research_menu(main_window):
    """
    Add a research menu to the main window.
    
    Args:
        main_window: The main window instance to add the menu to
    """
    # Create research menu
    research_menu = main_window.menu_bar.addMenu("&Research")
    
    # Password evolution action
    evolve_action = QAction("Password Evolution Simulator", main_window)
    evolve_action.setStatusTip("Simulate how users change passwords when prompted")
    evolve_action.triggered.connect(lambda: show_password_evolution_dialog(main_window))
    research_menu.addAction(evolve_action)
    
    # Add separator
    research_menu.addSeparator()
    
    # Password patterns action
    patterns_action = QAction("Analyze Password Patterns", main_window)
    patterns_action.setStatusTip("Analyze common patterns in passwords")
    patterns_action.triggered.connect(lambda: analyze_password_patterns(main_window))
    research_menu.addAction(patterns_action)
    
    # Security analysis action
    security_action = QAction("Security Analysis", main_window)
    security_action.setStatusTip("Analyze password security across the dataset")
    security_action.triggered.connect(lambda: analyze_security(main_window))
    research_menu.addAction(security_action)
    
    # Also add a button to the operations menu
    evolve_menu_action = QAction("Password Evolution Simulator", main_window)
    evolve_menu_action.triggered.connect(lambda: show_password_evolution_dialog(main_window))
    main_window.operations_menu.addSeparator()
    main_window.operations_menu.addAction(evolve_menu_action)
    
    # Add a toolbar button if desired
    # (Code would go here)
    
    return research_menu


def show_password_evolution_dialog(main_window):
    """
    Show the password evolution dialog.
    
    Args:
        main_window: The main window instance
    """
    if not main_window.combos:
        QMessageBox.warning(
            main_window,
            "No Data",
            "No password combinations available for evolution simulation."
        )
        return
    
    dialog = PasswordEvolutionDialog(main_window.combos, main_window)
    
    if dialog.exec_() == PasswordEvolutionDialog.Accepted and dialog.evolved_combos:
        # Update combos with evolved versions
        main_window.combos = dialog.evolved_combos
        main_window.update_combo_display()
        
        # Update status
        num_changed = sum(1 for orig, evolved in zip(main_window.original_combos, dialog.evolved_combos) 
                          if orig != evolved)
        main_window.status_bar.showMessage(f"Applied password evolution: {num_changed:,} passwords modified")
        
        # Log the operation
        main_window.logger.info(f"Applied password evolution: {num_changed:,} passwords modified")


def analyze_password_patterns(main_window):
    """
    Analyze password patterns in the dataset.
    
    Args:
        main_window: The main window instance
    """
    if not main_window.combos:
        QMessageBox.warning(
            main_window,
            "No Data",
            "No password combinations available for pattern analysis."
        )
        return
    
    # This would normally launch a specialized analysis
    # For now, run the password pattern analysis in the analytics module
    main_window.run_specific_analysis("patterns")


def analyze_security(main_window):
    """
    Analyze password security across the dataset.
    
    Args:
        main_window: The main window instance
    """
    if not main_window.combos:
        QMessageBox.warning(
            main_window,
            "No Data",
            "No password combinations available for security analysis."
        )
        return
    
    # This would normally launch a specialized security analysis
    # For now, run the password strength analysis in the analytics module
    main_window.run_specific_analysis("strength")