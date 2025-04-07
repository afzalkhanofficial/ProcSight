import sys
import psutil
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QTableView, QHeaderView, QMenu, QMessageBox,
    QListWidget, QListWidgetItem, QStackedWidget, QAbstractItemView,
    QGraphicsDropShadowEffect, QTabWidget
)
from PyQt5.QtCore import (
    QTimer, Qt, QSortFilterProxyModel, QAbstractTableModel, QModelIndex
)
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon
import pyqtgraph as pg
