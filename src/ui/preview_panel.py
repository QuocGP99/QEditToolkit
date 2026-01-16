from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, 
                             QHBoxLayout, QSlider, QStyle, QSizePolicy, QFrame)
from PyQt6.QtCore import Qt, QUrl, QSize
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
import os

class PreviewPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(320)
        self.setStyleSheet("background-color: #252525; border-left: 1px solid #333;")
        
        self.setup_ui()
        self.current_asset = None
        
        # Media Player Setup
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)
        
        # Connect signals
        self.media_player.mediaStatusChanged.connect(self.handle_media_status)
        self.play_btn.clicked.connect(self.toggle_playback)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # 1. Header
        header = QLabel("PREVIEW")
        header.setStyleSheet("color: #888; font-weight: bold; margin: 10px;")
        layout.addWidget(header)
        
        # 2. Preview Area Container
        self.preview_container = QFrame()
        self.preview_container.setStyleSheet("background-color: #1e1e1e; border: 1px solid #333;")
        self.preview_container.setFixedSize(300, 200)
        
        container_layout = QVBoxLayout(self.preview_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        
        # Video Widget
        self.video_widget = QVideoWidget()
        self.video_widget.hide()
        container_layout.addWidget(self.video_widget)
        
        # Image Label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setScaledContents(True)
        self.image_label.hide()
        container_layout.addWidget(self.image_label)
        
        layout.addWidget(self.preview_container, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # 3. Controls (only for video/audio)
        self.controls_widget = QWidget()
        controls_layout = QHBoxLayout(self.controls_widget)
        controls_layout.setContentsMargins(10, 0, 10, 0)
        
        self.play_btn = QPushButton()
        self.play_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.play_btn.setFixedSize(32, 32)
        controls_layout.addWidget(self.play_btn)
        
        layout.addWidget(self.controls_widget)
        self.controls_widget.hide()
        
        # 4. Info Area
        self.info_label = QLabel("Select an asset to preview")
        self.info_label.setStyleSheet("color: #ccc; margin: 10px;")
        self.info_label.setWordWrap(True)
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        layout.addWidget(self.info_label)
        layout.addStretch()

    def update_preview(self, asset_data):
        self.current_asset = asset_data
        self.media_player.stop()
        self.video_widget.hide()
        self.image_label.hide()
        self.controls_widget.hide()
        
        if not asset_data:
            self.info_label.setText("Select an asset to preview")
            return

        file_path = asset_data.get('file_path')
        file_type = asset_data.get('file_type')
        preview_path = asset_data.get('preview_path')
        file_name = asset_data.get('file_name')
        
        # Update Info
        info_text = f"<b>Name:</b> {file_name}<br><b>Type:</b> {file_type}"
        self.info_label.setText(info_text)
        
        if not file_path or not os.path.exists(file_path):
            self.info_label.setText(info_text + "<br><font color='red'>File not found</font>")
            return

        # Handle Content
        if file_type == 'video' or file_type == 'audio':
            self.video_widget.show()
            self.controls_widget.show()
            self.media_player.setSource(QUrl.fromLocalFile(file_path))
            self.play_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
            if file_type == 'audio':
                # Show specific visual for audio?
                pass
        
        elif file_type in ['image', 'drfx', 'macro', 'transition', 'effect', 'title', 'generator']:
            self.image_label.show()
            if preview_path and os.path.exists(preview_path):
                pixmap = QPixmap(preview_path)
                self.image_label.setPixmap(pixmap.scaled(
                    self.image_label.size(), 
                    Qt.AspectRatioMode.KeepAspectRatio, 
                    Qt.TransformationMode.SmoothTransformation
                ))
            else:
                self.image_label.setText("No Preview")

    def toggle_playback(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
            self.play_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        else:
            self.media_player.play()
            self.play_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause))

    def handle_media_status(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.play_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
