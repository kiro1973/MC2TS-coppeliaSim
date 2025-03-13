from PyQt5.QtGui import QPixmap, QPainter, QColor, QBrush, QPen
from PyQt5.QtWidgets import QWidget
class CircleWidget(QWidget):
    def __init__(self, color, size=15, parent=None):
        super().__init__(parent)
        self.color = color
        self.size = size
        self.setFixedSize(size, size)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw border (black circle)
        pen = QPen(QColor('black'), 2)
        painter.setPen(pen)
        brush = QBrush(QColor(self.color))
        painter.setBrush(brush)
        
        # Draw circle
        painter.drawEllipse(1, 1, self.size-2, self.size-2)