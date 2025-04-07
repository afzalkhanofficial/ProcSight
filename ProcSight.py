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

##############################################################################
# 2. Main Application Window (Processes + Performance Only)
##############################################################################
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Modern Task Manager & Hardware Monitor")
        self.resize(1280, 840)

        # Set up overall style: Fusion + Dark palette
        self.initAppStyle()

        # Apply additional style sheet for custom theming
        self.setStyleSheet(self.modernStyleSheet())

        # Main container layout
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setCentralWidget(main_widget)

        # Left navigation (sidebar)
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(220)
        self.sidebar.setSpacing(10)
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setSelectionMode(QAbstractItemView.SingleSelection)
        self.applyShadow(self.sidebar)

        # Example icons (replace with valid file paths or remove if not needed)
        processes_item = QListWidgetItem(" Processes")
        processes_item.setIcon(QIcon("process_icon.png"))
        performance_item = QListWidgetItem(" Performance")
        performance_item.setIcon(QIcon("performance_icon.png"))

        # Add only these two items
        self.sidebar.addItem(processes_item)
        self.sidebar.addItem(performance_item)

        # Stacked pages on the right
        self.stackedWidget = QStackedWidget()
        self.processesPage = self.createProcessesPage()
        self.performancePage = self.createPerformancePage()  # Now multi-tab

        self.stackedWidget.addWidget(self.processesPage)
        self.stackedWidget.addWidget(self.performancePage)

        # Layout arrangement
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.stackedWidget)

        # Connect sidebar selection
        self.sidebar.currentRowChanged.connect(self.stackedWidget.setCurrentIndex)
        self.sidebar.setCurrentRow(0)

        # Timer for real-time updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.updateAllData)
        self.timer.start(1000)

        # For performance deltas
        self.lastNet = psutil.net_io_counters()
        self.lastDisk = psutil.disk_io_counters()

        # We'll store up to 60 data points (1 minute at 1-second intervals)
        self.maxDataPoints = 60

        # CPU
        self.cpuData = []
        # Memory
        self.memData = []
        # Disk
        self.diskReadData = []
        self.diskWriteData = []
        # Network
        self.netUpData = []
        self.netDownData = []
        # GPU (placeholder)
        self.gpuData = []

        # Configure pyqtgraph for a matching dark theme
        pg.setConfigOption("background", "#262626")
        pg.setConfigOption("foreground", "#E0E0E0")
