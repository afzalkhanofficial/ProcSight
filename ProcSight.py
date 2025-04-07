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

    ############################################################################
    # 2.1. Set Fusion Style and Custom Dark Palette
    ############################################################################
    def initAppStyle(self):
        app.setStyle("Fusion")
        darkPalette = QPalette()
        darkPalette.setColor(QPalette.Window, QColor(36, 36, 36))
        darkPalette.setColor(QPalette.WindowText, Qt.white)
        darkPalette.setColor(QPalette.Base, QColor(45, 45, 45))
        darkPalette.setColor(QPalette.AlternateBase, QColor(36, 36, 36))
        darkPalette.setColor(QPalette.ToolTipBase, Qt.white)
        darkPalette.setColor(QPalette.ToolTipText, Qt.white)
        darkPalette.setColor(QPalette.Text, Qt.white)
        darkPalette.setColor(QPalette.Button, QColor(45, 45, 45))
        darkPalette.setColor(QPalette.ButtonText, Qt.white)
        darkPalette.setColor(QPalette.BrightText, Qt.red)
        darkPalette.setColor(QPalette.Highlight, QColor("#0078d4"))
        darkPalette.setColor(QPalette.HighlightedText, Qt.white)
        app.setPalette(darkPalette)

    def applyShadow(self, widget):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        shadow.setColor(QColor(0, 0, 0, 160))
        widget.setGraphicsEffect(shadow)

    ############################################################################
    # 2.2. Pages: Processes + Performance (Tabbed)
    ############################################################################
    def createProcessesPage(self):
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(20, 20, 20, 20)

        # Filter row
        filter_layout = QHBoxLayout()
        filter_label = QLabel("Filter Processes:")
        filter_label.setFont(QFont("Segoe UI Variable", 11, QFont.Medium))
        self.filterLineEdit = QLineEdit()
        self.filterLineEdit.setPlaceholderText("Type a process name...")
        self.filterLineEdit.textChanged.connect(self.filterChanged)
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.filterLineEdit)
        filter_layout.addStretch()
        page_layout.addLayout(filter_layout)

        # Process Table
        self.processModel = ProcessTableModel([])
        self.proxyModel = QSortFilterProxyModel()
        self.proxyModel.setSourceModel(self.processModel)
        self.proxyModel.setFilterKeyColumn(1)
        self.proxyModel.setFilterCaseSensitivity(Qt.CaseInsensitive)

        self.tableView = QTableView()
        self.tableView.setModel(self.proxyModel)
        self.tableView.setSortingEnabled(True)
        self.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tableView.customContextMenuRequested.connect(self.openContextMenu)
        page_layout.addWidget(self.tableView)

        return page

    def createPerformancePage(self):
        """
        Create a Performance page with tabs for CPU, Memory, Disk, Network, GPU.
        Each tab has a PyQtGraph chart + a details panel.
        """
        performanceWidget = QWidget()
        layout = QVBoxLayout(performanceWidget)
        layout.setContentsMargins(0, 0, 0, 0)

        # QTabWidget to hold resource tabs
        self.perfTabs = QTabWidget()
        self.perfTabs.setObjectName("PerfTabs")
        layout.addWidget(self.perfTabs)

        # CPU tab
        self.cpuTab = self.createCpuTab()
        self.perfTabs.addTab(self.cpuTab, "CPU")

        # Memory tab
        self.memoryTab = self.createMemoryTab()
        self.perfTabs.addTab(self.memoryTab, "Memory")

        # Disk tab
        self.diskTab = self.createDiskTab()
        self.perfTabs.addTab(self.diskTab, "Disk")

        # Network tab
        self.networkTab = self.createNetworkTab()
        self.perfTabs.addTab(self.networkTab, "Network")

        # GPU tab (placeholder)
        self.gpuTab = self.createGpuTab()
        self.perfTabs.addTab(self.gpuTab, "GPU")

        return performanceWidget
