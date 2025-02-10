import os
import sys
from PyQt6.QtWidgets import (
    QApplication,
)

parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, parent_dir)

from src.client.ui import ChatAppUI


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatAppUI()
    window.show()
    sys.exit(app.exec())
