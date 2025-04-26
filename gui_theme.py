from PyQt5.QtGui import QPalette, QColor, QFont
from PyQt5.QtCore import Qt

class Theme:
    class Light:
        # Main colors
        PRIMARY = "#0078d7"
        SECONDARY = "#305090"
        BACKGROUND = "#f5f5f7"
        CARD_BACKGROUND = "#ffffff"
        TEXT = "#202020"
        TEXT_SECONDARY = "#505050"
        BORDER = "#e0e0e0"
        SUCCESS = "#28a745"
        WARNING = "#ffc107"
        DANGER = "#dc3545"
        INFO = "#17a2b8"
        
        # Specific components
        HEADER_BACKGROUND = "#ffffff"
        SIDEBAR_BACKGROUND = "#eaeaea"
        MENU_HOVER = "#e0e0e0"
        
        # Font settings
        FONT_FAMILY = "Segoe UI"
        FONT_SIZE = 10
        
        @classmethod
        def get_palette(cls):
            palette = QPalette()
            palette.setColor(QPalette.Window, QColor(cls.BACKGROUND))
            palette.setColor(QPalette.WindowText, QColor(cls.TEXT))
            palette.setColor(QPalette.Base, QColor(cls.CARD_BACKGROUND))
            palette.setColor(QPalette.AlternateBase, QColor(cls.BACKGROUND))
            palette.setColor(QPalette.ToolTipBase, QColor(cls.CARD_BACKGROUND))
            palette.setColor(QPalette.ToolTipText, QColor(cls.TEXT))
            palette.setColor(QPalette.Text, QColor(cls.TEXT))
            palette.setColor(QPalette.Button, QColor(cls.CARD_BACKGROUND))
            palette.setColor(QPalette.ButtonText, QColor(cls.TEXT))
            palette.setColor(QPalette.BrightText, Qt.white)
            palette.setColor(QPalette.Link, QColor(cls.PRIMARY))
            palette.setColor(QPalette.Highlight, QColor(cls.PRIMARY))
            palette.setColor(QPalette.HighlightedText, Qt.white)
            return palette
    
    class Dark:
        # Main colors
        PRIMARY = "#2196f3"
        SECONDARY = "#4f83cc"
        BACKGROUND = "#121212"
        CARD_BACKGROUND = "#1e1e1e"
        TEXT = "#ffffff"
        TEXT_SECONDARY = "#aaaaaa"
        BORDER = "#333333"
        SUCCESS = "#43a047"
        WARNING = "#ffb300"
        DANGER = "#e53935"
        INFO = "#039be5"
        
        # Specific components
        HEADER_BACKGROUND = "#1e1e1e"
        SIDEBAR_BACKGROUND = "#252525"
        MENU_HOVER = "#2d2d2d"
        
        # Font settings
        FONT_FAMILY = "Segoe UI"
        FONT_SIZE = 10
        
        @classmethod
        def get_palette(cls):
            palette = QPalette()
            palette.setColor(QPalette.Window, QColor(cls.BACKGROUND))
            palette.setColor(QPalette.WindowText, QColor(cls.TEXT))
            palette.setColor(QPalette.Base, QColor(cls.CARD_BACKGROUND))
            palette.setColor(QPalette.AlternateBase, QColor(cls.BACKGROUND))
            palette.setColor(QPalette.ToolTipBase, QColor(cls.CARD_BACKGROUND))
            palette.setColor(QPalette.ToolTipText, QColor(cls.TEXT))
            palette.setColor(QPalette.Text, QColor(cls.TEXT))
            palette.setColor(QPalette.Button, QColor(cls.CARD_BACKGROUND))
            palette.setColor(QPalette.ButtonText, QColor(cls.TEXT))
            palette.setColor(QPalette.BrightText, QColor(cls.TEXT))
            palette.setColor(QPalette.Link, QColor(cls.PRIMARY))
            palette.setColor(QPalette.Highlight, QColor(cls.PRIMARY))
            palette.setColor(QPalette.HighlightedText, QColor(cls.TEXT))
            return palette

def apply_theme(app, theme_class=Theme.Light):
    # Set palette
    app.setPalette(theme_class.get_palette())
    
    # Set default font
    font = QFont(theme_class.FONT_FAMILY, theme_class.FONT_SIZE)
    app.setFont(font)
    
    return app

def get_stylesheet(theme_class=Theme.Light):
    # Base stylesheet for the application
    return f"""
    QMainWindow, QDialog {{
        background-color: {theme_class.BACKGROUND};
    }}
    
    QWidget {{
        color: {theme_class.TEXT};
        font-family: "{theme_class.FONT_FAMILY}";
    }}
    
    QLabel {{
        color: {theme_class.TEXT};
    }}
    
    QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox {{
        background-color: {theme_class.CARD_BACKGROUND};
        border: 1px solid {theme_class.BORDER};
        border-radius: 4px;
        padding: 5px;
        color: {theme_class.TEXT};
    }}
    
    QPlainTextEdit, QTextEdit {{
        font-family: "Consolas", "Courier New", monospace;
    }}
    
    QPushButton {{
        background-color: {theme_class.PRIMARY};
        color: white;
        border: none;
        border-radius: 4px;
        padding: 8px 16px;
        font-weight: bold;
    }}
    
    QPushButton:hover {{
        background-color: {theme_class.SECONDARY};
    }}
    
    QPushButton:disabled {{
        background-color: {theme_class.BORDER};
        color: {theme_class.TEXT_SECONDARY};
    }}
    
    QTabWidget::pane {{
        border: 1px solid {theme_class.BORDER};
        border-radius: 4px;
    }}
    
    QTabBar::tab {{
        background-color: {theme_class.SIDEBAR_BACKGROUND};
        color: {theme_class.TEXT_SECONDARY};
        padding: 8px 16px;
        margin-right: 2px;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
    }}
    
    QTabBar::tab:selected {{
        background-color: {theme_class.CARD_BACKGROUND};
        color: {theme_class.TEXT};
        border-bottom: 2px solid {theme_class.PRIMARY};
    }}
    
    QProgressBar {{
        background-color: {theme_class.CARD_BACKGROUND};
        border-radius: 4px;
        color: white;
        text-align: center;
    }}
    
    QProgressBar::chunk {{
        background-color: {theme_class.PRIMARY};
        border-radius: 4px;
    }}
    
    QStatusBar {{
        background-color: {theme_class.HEADER_BACKGROUND};
        color: {theme_class.TEXT_SECONDARY};
    }}
    
    QGroupBox {{
        border: 1px solid {theme_class.BORDER};
        border-radius: 4px;
        margin-top: 0.5em;
        padding-top: 1em;
        font-weight: bold;
    }}
    
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 5px;
        color: {theme_class.TEXT};
    }}
    
    QTableView {{
        background-color: {theme_class.CARD_BACKGROUND};
        border: 1px solid {theme_class.BORDER};
        border-radius: 4px;
    }}
    
    QHeaderView::section {{
        background-color: {theme_class.SIDEBAR_BACKGROUND};
        color: {theme_class.TEXT};
        padding: 5px;
        border: 1px solid {theme_class.BORDER};
    }}
    
    QScrollBar:vertical {{
        border: none;
        background: {theme_class.BACKGROUND};
        width: 10px;
        margin: 0px;
    }}
    
    QScrollBar::handle:vertical {{
        background: {theme_class.BORDER};
        border-radius: 5px;
        min-height: 20px;
    }}
    
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    
    QMenuBar {{
        background-color: {theme_class.HEADER_BACKGROUND};
    }}
    
    QMenuBar::item {{
        spacing: 3px;
        padding: 3px 10px;
        background: transparent;
        color: {theme_class.TEXT};
    }}
    
    QMenuBar::item:selected {{
        background-color: {theme_class.MENU_HOVER};
        color: {theme_class.TEXT};
    }}
    
    QCheckBox {{
        spacing: 5px;
    }}
    
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
    }}
    """