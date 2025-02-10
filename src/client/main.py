import sys
from PyQt6.QtWidgets import (
    QApplication,
)

from ui import ChatAppUI

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatAppUI()
    window.show()
    sys.exit(app.exec())
