import sys
import threading
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTextEdit, QLineEdit, QPushButton, 
                             QLabel, QFrame, QScrollArea)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QObject
from PyQt6.QtGui import QColor, QFont, QIcon, QMovie

class ChatMessage(QWidget):
    def __init__(self, text, sender="user"):
        super().__init__()
        layout = QHBoxLayout()
        self.label = QLabel(text)
        self.label.setWordWrap(True)
        self.label.setFont(QFont("Outfit", 12))
        self.label.setContentsMargins(15, 10, 15, 10)
        
        if sender == "user":
            self.label.setStyleSheet("background-color: #3b82f6; color: white; border-radius: 15px; margin-left: 50px;")
            layout.addStretch()
            layout.addWidget(self.label)
        else:
            self.label.setStyleSheet("background-color: #1e293b; color: #f8fafc; border-radius: 15px; margin-right: 50px;")
            layout.addWidget(self.label)
            layout.addStretch()
            
        self.setLayout(layout)

class Signals(QObject):
    message_received = pyqtSignal(str, str)
    status_updated = pyqtSignal(str)
    voice_text_ready = pyqtSignal(str)   # fills input field with recognized text
    mic_active = pyqtSignal(bool)        # toggles mic button appearance

class DesktopAssistantUI(QMainWindow):
    def __init__(self, on_input_callback, on_voice_callback):
        super().__init__()
        self.on_input = on_input_callback
        self.on_voice = on_voice_callback
        self.signals = Signals()
        self.init_ui()
        
        self.signals.message_received.connect(self.add_message)
        self.signals.status_updated.connect(self.set_status)
        self.signals.voice_text_ready.connect(self.set_input_text)
        self.signals.mic_active.connect(self.set_mic_active)

    def init_ui(self):
        self.setWindowTitle("Smart Planner AI Assistant")
        self.setFixedSize(400, 600)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Main Container
        self.container = QFrame(self)
        self.container.setFixedSize(400, 600)
        self.container.setStyleSheet("""
            QFrame {
                background-color: #0f172a; 
                border-radius: 20px; 
                border: 1px solid #1e293b;
            }
        """)
        
        layout = QVBoxLayout(self.container)
        
        # Header (Draggable)
        header = QFrame()
        header.setFixedHeight(60)
        header.setStyleSheet("background: transparent; border: none;")
        header_layout = QHBoxLayout(header)
        
        title = QLabel("🎓 Smart Study Assistant")
        title.setStyleSheet("color: white; font-weight: bold; font-size: 16px; border: none;")
        header_layout.addWidget(title)
        
        close_btn = QPushButton("×")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet("background: transparent; color: #94a3b8; font-size: 24px; border: none;")
        close_btn.clicked.connect(self.close)
        header_layout.addWidget(close_btn)
        
        layout.addWidget(header)

        # Chat Area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background-color: #0f172a; border: none;")
        
        self.chat_content = QWidget()
        self.chat_content.setStyleSheet("background-color: transparent;")
        self.chat_layout = QVBoxLayout(self.chat_content)
        self.chat_layout.addStretch()
        self.scroll.setWidget(self.chat_content)
        layout.addWidget(self.scroll)

        # Status Bar
        self.status_label = QLabel("Assistant Ready")
        self.status_label.setStyleSheet("color: #64748b; font-size: 11px; margin-left: 10px; border: none;")
        layout.addWidget(self.status_label)

        # Input Area
        input_container = QFrame()
        input_container.setFixedHeight(60)
        input_container.setStyleSheet("background-color: #1e293b; border-radius: 30px; margin-bottom: 5px;")
        input_layout = QHBoxLayout(input_container)
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type a command...")
        self.input_field.setStyleSheet("background: transparent; color: white; border: none; font-size: 14px; padding-left: 10px;")
        self.input_field.returnPressed.connect(self.handle_send)
        input_layout.addWidget(self.input_field)
        
        self.mic_btn = QPushButton("🎙️")
        self.mic_btn.setFixedSize(40, 40)
        self.mic_btn.setStyleSheet("background-color: #3b82f6; border-radius: 20px; font-size: 18px; color: white; border: none;")
        self.mic_btn.clicked.connect(self.handle_voice_click)
        input_layout.addWidget(self.mic_btn)
        
        layout.addWidget(input_container)
        
        self.setCentralWidget(self.container)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if hasattr(self, 'drag_pos'):
            delta = event.globalPosition().toPoint() - self.drag_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.drag_pos = event.globalPosition().toPoint()

    def add_message(self, text, sender="bot"):
        msg = ChatMessage(text, sender)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, msg)
        # Scroll to bottom
        self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum() + 200)

    def set_status(self, text):
        self.status_label.setText(text)

    def set_input_text(self, text):
        """Show recognized voice text in the input field."""
        self.input_field.setText(text)

    def set_mic_active(self, active: bool):
        if active:
            self.mic_btn.setStyleSheet("background-color: #ef4444; border-radius: 20px; font-size: 18px; color: white; border: none;")
            self.mic_btn.setText("⏹️")
        else:
            self.mic_btn.setStyleSheet("background-color: #3b82f6; border-radius: 20px; font-size: 18px; color: white; border: none;")
            self.mic_btn.setText("🎙️")

    def handle_voice_click(self):
        if self.on_voice:
            self.on_voice()

    def handle_send(self):
        text = self.input_field.text()
        if text.strip() and self.on_input:
            self.add_message(text, "user")
            self.input_field.clear()
            self.on_input(text)

def run_ui(on_input, on_voice):
    app = QApplication(sys.argv)
    ui = DesktopAssistantUI(on_input, on_voice)
    ui.show()
    return app, ui
