"""Application-wide styling definitions for a clean, minimalistic dark theme."""

# Dark Mode Color Palette
COLORS = {
    "primary": "#3b82f6",  # Bright blue
    "primary_hover": "#60a5fa",  # Lighter blue
    "success": "#10b981",  # Green
    "success_hover": "#34d399",
    "danger": "#ef4444",  # Red
    "danger_hover": "#f87171",
    "warning": "#f59e0b",  # Amber
    "background": "#0f1419",  # Very dark background
    "surface": "#1a1f2e",  # Dark surface
    "border": "#2d3748",  # Dark border
    "text": "#e2e8f0",  # Light text
    "text_muted": "#94a3b8",  # Muted light text
    "input_bg": "#1e293b",  # Dark input background
    "input_border": "#334155",  # Dark input border
    "input_focus": "#3b82f6",  # Bright blue focus
}

# Main application stylesheet
APP_STYLESHEET = f"""
/* Global styles */
QWidget {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
    color: {COLORS['text']};
}}

/* Main window */
QMainWindow {{
    background-color: {COLORS['surface']};
}}

/* Tabs */
QTabWidget::pane {{
    border: 1px solid {COLORS['border']};
    background-color: {COLORS['background']};
    border-radius: 4px;
    padding: 0px;
}}

QTabBar::tab {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-bottom: none;
    padding: 8px 16px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    min-width: 100px;
}}

QTabBar::tab:selected {{
    background-color: {COLORS['background']};
    border-bottom: 2px solid {COLORS['primary']};
    font-weight: 500;
}}

QTabBar::tab:hover:!selected {{
    background-color: #1e293b;
}}

/* Tables */
QTableWidget {{
    background-color: #1a1f2e;
    border: 1px solid #2d3748;
    border-radius: 4px;
    gridline-color: #2d3748;
    selection-background-color: #1e40af;
    selection-color: #ffffff;
    color: #e2e8f0;
    alternate-row-color: #1a1f2e;
    font-size: 14px;
}}

QTableWidget::item {{
    padding: 10px 12px;
    border: none;
    background-color: #1a1f2e;
    color: #e2e8f0;
}}

QTableWidget::item:selected {{
    background-color: #1e40af;
    color: #ffffff;
}}

QTableWidget::item:hover {{
    background-color: #1e293b;
}}

/* Fix top-left corner cell color */
QTableCornerButton::section {{
    background-color: #1a1f2e;
    border: none;
    border-bottom: 2px solid #2d3748;
    border-right: 1px solid #2d3748;
}}

/* Fix scrollbar corner (bottom-left area below row numbers) */
QAbstractScrollArea::corner {{
    background-color: #1a1f2e;
    border: none;
}}

QTableWidget QAbstractScrollArea::corner {{
    background-color: #1a1f2e;
    border: none;
}}

/* Fix row number header (vertical header) */
QHeaderView::section:vertical {{
    background-color: #1a1f2e;
    border: none;
    border-bottom: 1px solid #2d3748;
    border-right: 1px solid #2d3748;
    padding: 10px 12px;
    font-weight: 600;
    font-size: 14px;
    text-align: center;
    color: #e2e8f0;  /* Explicit bright text color for row numbers */
}}

QHeaderView::section:vertical:hover {{
    background-color: #1e293b;
}}

/* Horizontal header (column names) */
QHeaderView::section:horizontal {{
    background-color: #1a1f2e;
    border: none;
    border-bottom: 2px solid #2d3748;
    border-right: 1px solid #2d3748;
    padding: 10px 12px;
    font-weight: 600;
    font-size: 14px;
    text-align: left;
    color: #e2e8f0;
}}

QHeaderView::section:horizontal:hover {{
    background-color: #1e293b;
}}

/* Buttons */
QPushButton {{
    background-color: {COLORS['primary']};
    color: white;
    border: none;
    border-radius: 4px;
    padding: 8px 16px;
    font-weight: 500;
    min-width: 80px;
}}

QPushButton:hover {{
    background-color: {COLORS['primary_hover']};
}}

QPushButton:pressed {{
    background-color: #1e40af;
}}

QPushButton:disabled {{
    background-color: {COLORS['border']};
    color: {COLORS['text_muted']};
}}

/* Secondary button style */
QPushButton[styleClass="secondary"] {{
    background-color: {COLORS['surface']};
    color: {COLORS['text']};
    border: 1px solid {COLORS['border']};
}}

QPushButton[styleClass="secondary"]:hover {{
    background-color: #1e293b;
    border-color: {COLORS['input_focus']};
}}

/* Danger button style */
QPushButton[styleClass="danger"] {{
    background-color: {COLORS['danger']};
    color: white;
}}

QPushButton[styleClass="danger"]:hover {{
    background-color: {COLORS['danger_hover']};
}}

/* Input fields */
QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox {{
    background-color: {COLORS['input_bg']};
    border: 1px solid {COLORS['input_border']};
    border-radius: 4px;
    padding: 8px 12px;
    selection-background-color: #1e40af;
    color: {COLORS['text']};
}}

QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
    border: 2px solid {COLORS['input_focus']};
    padding: 7px 11px;
}}

QLineEdit:disabled, QTextEdit:disabled {{
    background-color: {COLORS['surface']};
    color: {COLORS['text_muted']};
}}

/* ComboBox */
QComboBox {{
    background-color: {COLORS['input_bg']};
    border: 1px solid {COLORS['input_border']};
    border-radius: 4px;
    padding: 8px 12px;
    min-width: 120px;
}}

QComboBox:hover {{
    border-color: {COLORS['text_muted']};
}}

QComboBox:focus {{
    border: 2px solid {COLORS['input_focus']};
}}

QComboBox::drop-down {{
    border: none;
    width: 20px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 6px solid {COLORS['text_muted']};
    margin-right: 8px;
}}

QComboBox QAbstractItemView {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    selection-background-color: #1e40af;
    selection-color: {COLORS['text']};
    padding: 4px;
    color: {COLORS['text']};
}}

/* Labels */
QLabel {{
    color: {COLORS['text']};
    padding: 2px;
}}

QLabel[styleClass="heading"] {{
    font-size: 18px;
    font-weight: 600;
    padding: 8px 0px;
}}

QLabel[styleClass="subheading"] {{
    font-size: 14px;
    font-weight: 500;
    color: {COLORS['text_muted']};
}}

QLabel[styleClass="muted"] {{
    color: {COLORS['text_muted']};
}}

/* Menu and Context Menus */
QMenu {{
    background-color: {COLORS['background']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 4px;
}}

QMenu::item {{
    padding: 8px 24px 8px 12px;
    border-radius: 2px;
}}

QMenu::item:selected {{
    background-color: #1e293b;
}}

QMenu::separator {{
    height: 1px;
    background-color: {COLORS['border']};
    margin: 4px 8px;
}}

/* MenuBar */
QMenuBar {{
    background-color: {COLORS['background']};
    border-bottom: 1px solid {COLORS['border']};
    padding: 4px;
}}

QMenuBar::item {{
    background-color: transparent;
    padding: 6px 12px;
    border-radius: 4px;
}}

QMenuBar::item:selected {{
    background-color: #1e293b;
}}

/* StatusBar */
QStatusBar {{
    background-color: {COLORS['surface']};
    border-top: 1px solid {COLORS['border']};
    padding: 4px 8px;
}}

/* ToolBar */
QToolBar {{
    background-color: {COLORS['background']};
    border: none;
    border-bottom: 1px solid {COLORS['border']};
    spacing: 8px;
    padding: 8px;
}}

QToolBar::separator {{
    width: 1px;
    background-color: {COLORS['border']};
    margin: 4px 8px;
}}

/* ScrollBar */
QScrollBar:vertical {{
    background-color: {COLORS['surface']};
    width: 12px;
    border-radius: 6px;
}}

QScrollBar::handle:vertical {{
    background-color: {COLORS['border']};
    border-radius: 6px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {COLORS['text_muted']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    background-color: {COLORS['surface']};
    height: 12px;
    border-radius: 6px;
}}

QScrollBar::handle:horizontal {{
    background-color: {COLORS['border']};
    border-radius: 6px;
    min-width: 30px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {COLORS['text_muted']};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

/* Progress Bar */
QProgressBar {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    text-align: center;
    height: 20px;
}}

QProgressBar::chunk {{
    background-color: {COLORS['primary']};
    border-radius: 3px;
}}

/* Dialogs */
QDialog {{
    background-color: {COLORS['background']};
}}

QMessageBox {{
    background-color: {COLORS['background']};
}}

QMessageBox QLabel {{
    min-width: 300px;
}}

/* GroupBox */
QGroupBox {{
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    margin-top: 12px;
    padding-top: 12px;
    font-weight: 500;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    background-color: {COLORS['background']};
}}

/* CheckBox and RadioButton */
QCheckBox, QRadioButton {{
    spacing: 8px;
}}

QCheckBox::indicator, QRadioButton::indicator {{
    width: 18px;
    height: 18px;
}}

QCheckBox::indicator:unchecked, QRadioButton::indicator:unchecked {{
    border: 2px solid {COLORS['input_border']};
    background-color: {COLORS['background']};
    border-radius: 3px;
}}

QCheckBox::indicator:checked {{
    border: 2px solid {COLORS['primary']};
    background-color: {COLORS['primary']};
    border-radius: 3px;
}}

QRadioButton::indicator:checked {{
    border: 2px solid {COLORS['primary']};
    background-color: {COLORS['primary']};
    border-radius: 9px;
}}

QCheckBox::indicator:hover, QRadioButton::indicator:hover {{
    border-color: {COLORS['primary']};
}}

/* Tooltips */
QToolTip {{
    background-color: {COLORS['text']};
    color: white;
    border: none;
    border-radius: 4px;
    padding: 6px 10px;
    opacity: 230;
}}
"""


def get_stylesheet() -> str:
    """Return the complete application stylesheet."""
    return APP_STYLESHEET
