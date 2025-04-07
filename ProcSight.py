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

##############################################################################
# 1. Custom Process Table Model
##############################################################################
class ProcessTableModel(QAbstractTableModel):
    def __init__(self, processes=None):
        super().__init__()
        self.header = ["PID", "Name", "CPU %", "Memory %"]
        self.processes = processes or []

    def data(self, index, role):
        if not index.isValid():
            return None
        row, col = index.row(), index.column()
        if role == Qt.DisplayRole:
            return self.processes[row][col]
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignCenter
        return None

    def rowCount(self, parent=None):
        return len(self.processes)

    def columnCount(self, parent=None):
        return len(self.header)

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self.header[section]
            else:
                return section
        return None

    def updateProcesses(self, processes):
        self.beginResetModel()
        self.processes = processes
        self.endResetModel()
