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

    ############################################################################
    # 2.2.1. Individual Resource Tabs (CPU, Memory, Disk, Network, GPU)
    ############################################################################
    def createCpuTab(self):
        cpuWidget = QWidget()
        layout = QHBoxLayout(cpuWidget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Left: CPU Graph
        self.cpuPlot = pg.PlotWidget(title="CPU Usage (Last 60s)")
        self.cpuPlot.showGrid(x=True, y=True, alpha=0.2)
        self.cpuPlot.setYRange(0, 100)
        self.cpuPlot.setLabel("left", "Usage (%)")
        self.cpuPlot.setLabel("bottom", "Time (s)")
        pen = pg.mkPen(color="#0078D4", width=2)
        self.cpuCurve = self.cpuPlot.plot(pen=pen, name="CPU")
        self.cpuCurve.setFillLevel(0)
        self.cpuCurve.setBrush(pg.mkBrush("#0078D420"))
        layout.addWidget(self.cpuPlot, stretch=2)

        # Right: CPU Info Panel
        infoPanel = QWidget()
        infoLayout = QVBoxLayout(infoPanel)
        infoPanel.setFixedWidth(220)

        self.cpuLabel_Usage = QLabel("Usage: 0.0%")
        self.cpuLabel_Speed = QLabel("Speed: ??? GHz")
        self.cpuLabel_Cores = QLabel("Cores: ???")
        self.cpuLabel_Threads = QLabel("Threads: ???")

        for lbl in [self.cpuLabel_Usage, self.cpuLabel_Speed,
                    self.cpuLabel_Cores, self.cpuLabel_Threads]:
            lbl.setStyleSheet("font-size: 12px; margin-bottom: 6px;")
            infoLayout.addWidget(lbl)

        infoLayout.addStretch()
        layout.addWidget(infoPanel, stretch=1)

        return cpuWidget

    def createMemoryTab(self):
        memWidget = QWidget()
        layout = QHBoxLayout(memWidget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Left: Memory Graph
        self.memPlot = pg.PlotWidget(title="Memory Usage (Last 60s)")
        self.memPlot.showGrid(x=True, y=True, alpha=0.2)
        self.memPlot.setYRange(0, 100)
        self.memPlot.setLabel("left", "Usage (%)")
        self.memPlot.setLabel("bottom", "Time (s)")
        pen = pg.mkPen(color="#009966", width=2)
        self.memCurve = self.memPlot.plot(pen=pen, name="Memory")
        self.memCurve.setFillLevel(0)
        self.memCurve.setBrush(pg.mkBrush("#00996620"))
        layout.addWidget(self.memPlot, stretch=2)

        # Right: Memory Info
        infoPanel = QWidget()
        infoLayout = QVBoxLayout(infoPanel)
        infoPanel.setFixedWidth(220)

        self.memLabel_Usage = QLabel("Usage: 0.0%")
        self.memLabel_Total = QLabel("Total: 0.0 GB")
        self.memLabel_Available = QLabel("Available: 0.0 GB")
        self.memLabel_Used = QLabel("Used: 0.0 GB")

        for lbl in [self.memLabel_Usage, self.memLabel_Total,
                    self.memLabel_Available, self.memLabel_Used]:
            lbl.setStyleSheet("font-size: 12px; margin-bottom: 6px;")
            infoLayout.addWidget(lbl)

        infoLayout.addStretch()
        layout.addWidget(infoPanel, stretch=1)

        return memWidget

    def createDiskTab(self):
        diskWidget = QWidget()
        layout = QHBoxLayout(diskWidget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Left: Disk I/O Graph
        self.diskPlot = pg.PlotWidget(title="Disk I/O (KB/s, Last 60s)")
        self.diskPlot.showGrid(x=True, y=True, alpha=0.2)
        self.diskPlot.setLabel("left", "KB/s")
        self.diskPlot.setLabel("bottom", "Time (s)")
        pen_read = pg.mkPen(color="#CC3300", width=2)
        pen_write = pg.mkPen(color="#00CC99", width=2)
        self.diskReadCurve = self.diskPlot.plot(pen=pen_read, name="Read")
        self.diskWriteCurve = self.diskPlot.plot(pen=pen_write, name="Write")
        layout.addWidget(self.diskPlot, stretch=2)

        # Right: Disk Info
        infoPanel = QWidget()
        infoLayout = QVBoxLayout(infoPanel)
        infoPanel.setFixedWidth(220)

        self.diskLabel_Read = QLabel("Read: 0 KB/s")
        self.diskLabel_Write = QLabel("Write: 0 KB/s")
        self.diskLabel_Capacity = QLabel("Capacity: ???")
        self.diskLabel_ActiveTime = QLabel("Active Time: ??? (N/A)")

        for lbl in [self.diskLabel_Read, self.diskLabel_Write,
                    self.diskLabel_Capacity, self.diskLabel_ActiveTime]:
            lbl.setStyleSheet("font-size: 12px; margin-bottom: 6px;")
            infoLayout.addWidget(lbl)

        infoLayout.addStretch()
        layout.addWidget(infoPanel, stretch=1)

        return diskWidget

    def createNetworkTab(self):
        netWidget = QWidget()
        layout = QHBoxLayout(netWidget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Left: Network Speed Graph
        self.netPlot = pg.PlotWidget(title="Network (KB/s, Last 60s)")
        self.netPlot.showGrid(x=True, y=True, alpha=0.2)
        self.netPlot.setLabel("left", "KB/s")
        self.netPlot.setLabel("bottom", "Time (s)")
        pen_up = pg.mkPen(color="#0066CC", width=2)
        pen_down = pg.mkPen(color="#CCAA00", width=2)
        self.netUpCurve = self.netPlot.plot(pen=pen_up, name="Upload")
        self.netDownCurve = self.netPlot.plot(pen=pen_down, name="Download")
        layout.addWidget(self.netPlot, stretch=2)

        # Right: Network Info
        infoPanel = QWidget()
        infoLayout = QVBoxLayout(infoPanel)
        infoPanel.setFixedWidth(220)

        self.netLabel_Up = QLabel("Upload: 0 KB/s")
        self.netLabel_Down = QLabel("Download: 0 KB/s")
        self.netLabel_Sent = QLabel("Total Sent: ??? MB")
        self.netLabel_Recv = QLabel("Total Received: ??? MB")

        for lbl in [self.netLabel_Up, self.netLabel_Down,
                    self.netLabel_Sent, self.netLabel_Recv]:
            lbl.setStyleSheet("font-size: 12px; margin-bottom: 6px;")
            infoLayout.addWidget(lbl)

        infoLayout.addStretch()
        layout.addWidget(infoPanel, stretch=1)

        return netWidget

    def createGpuTab(self):
        gpuWidget = QWidget()
        layout = QHBoxLayout(gpuWidget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # GPU Usage Graph (placeholder)
        self.gpuPlot = pg.PlotWidget(title="GPU Usage (Placeholder)")
        self.gpuPlot.showGrid(x=True, y=True, alpha=0.2)
        self.gpuPlot.setLabel("left", "Usage (%)")
        self.gpuPlot.setLabel("bottom", "Time (s)")
        pen_gpu = pg.mkPen(color="#AA00FF", width=2)
        self.gpuCurve = self.gpuPlot.plot(pen=pen_gpu, name="GPU")
        self.gpuCurve.setFillLevel(0)
        self.gpuCurve.setBrush(pg.mkBrush("#AA00FF20"))
        layout.addWidget(self.gpuPlot, stretch=2)

        # Right: GPU Info
        infoPanel = QWidget()
        infoLayout = QVBoxLayout(infoPanel)
        infoPanel.setFixedWidth(220)

        self.gpuLabel_Usage = QLabel("Usage: ???")
        self.gpuLabel_Memory = QLabel("Memory: ???")
        self.gpuLabel_Driver = QLabel("Driver Version: ???")
        self.gpuLabel_Clocks = QLabel("Clocks: ???")

        for lbl in [self.gpuLabel_Usage, self.gpuLabel_Memory,
                    self.gpuLabel_Driver, self.gpuLabel_Clocks]:
            lbl.setStyleSheet("font-size: 12px; margin-bottom: 6px;")
            infoLayout.addWidget(lbl)

        infoLayout.addStretch()
        layout.addWidget(infoPanel, stretch=1)

        return gpuWidget

    ############################################################################
    # 2.3. Data Updates (Process Table + Performance)
    ############################################################################
    def updateAllData(self):
        self.updateProcessTable()
        self.updatePerformanceCharts()

    def updateProcessTable(self):
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                info = proc.info
                processes.append([
                    str(info['pid']),
                    str(info['name']),
                    f"{info['cpu_percent']:.1f}",
                    f"{info['memory_percent']:.1f}"
                ])
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        self.processModel.updateProcesses(processes)

    def updatePerformanceCharts(self):
        # 1) CPU
        cpu = psutil.cpu_percent()
        self.cpuData.append(cpu)
        if len(self.cpuData) > self.maxDataPoints:
            self.cpuData.pop(0)
        self.cpuCurve.setData(self.cpuData)
        self.cpuLabel_Usage.setText(f"Usage: {cpu:.1f}%")

        # CPU frequency, cores, threads
        freq = psutil.cpu_freq()
        if freq:
            self.cpuLabel_Speed.setText(f"Speed: {freq.current/1000:.2f} GHz")
        self.cpuLabel_Cores.setText(f"Cores: {psutil.cpu_count(logical=False)}")
        self.cpuLabel_Threads.setText(f"Threads: {psutil.cpu_count(logical=True)}")

        # 2) Memory
        mem = psutil.virtual_memory()
        mem_percent = mem.percent
        mem_total_gb = mem.total / (1024**3)
        mem_used_gb = (mem.total - mem.available) / (1024**3)
        mem_avail_gb = mem.available / (1024**3)

        self.memData.append(mem_percent)
        if len(self.memData) > self.maxDataPoints:
            self.memData.pop(0)
        self.memCurve.setData(self.memData)

        self.memLabel_Usage.setText(f"Usage: {mem_percent:.1f}%")
        self.memLabel_Total.setText(f"Total: {mem_total_gb:.1f} GB")
        self.memLabel_Available.setText(f"Available: {mem_avail_gb:.1f} GB")
        self.memLabel_Used.setText(f"Used: {mem_used_gb:.1f} GB")

        # 3) Network
        currentNet = psutil.net_io_counters()
        upSpeed = (currentNet.bytes_sent - self.lastNet.bytes_sent) / 1024.0
        downSpeed = (currentNet.bytes_recv - self.lastNet.bytes_recv) / 1024.0
        self.lastNet = currentNet

        self.netUpData.append(upSpeed)
        self.netDownData.append(downSpeed)
        if len(self.netUpData) > self.maxDataPoints:
            self.netUpData.pop(0)
        if len(self.netDownData) > self.maxDataPoints:
            self.netDownData.pop(0)
        self.netUpCurve.setData(self.netUpData)
        self.netDownCurve.setData(self.netDownData)

        self.netLabel_Up.setText(f"Upload: {upSpeed:.1f} KB/s")
        self.netLabel_Down.setText(f"Download: {downSpeed:.1f} KB/s")
        self.netLabel_Sent.setText(f"Total Sent: {currentNet.bytes_sent/1_048_576:.1f} MB")
        self.netLabel_Recv.setText(f"Total Received: {currentNet.bytes_recv/1_048_576:.1f} MB")

        # 4) Disk
        currentDisk = psutil.disk_io_counters()
        readSpeed = (currentDisk.read_bytes - self.lastDisk.read_bytes) / 1024.0
        writeSpeed = (currentDisk.write_bytes - self.lastDisk.write_bytes) / 1024.0
        self.lastDisk = currentDisk

        self.diskReadData.append(readSpeed)
        self.diskWriteData.append(writeSpeed)
        if len(self.diskReadData) > self.maxDataPoints:
            self.diskReadData.pop(0)
        if len(self.diskWriteData) > self.maxDataPoints:
            self.diskWriteData.pop(0)
        self.diskReadCurve.setData(self.diskReadData)
        self.diskWriteCurve.setData(self.diskWriteData)

        self.diskLabel_Read.setText(f"Read: {readSpeed:.1f} KB/s")
        self.diskLabel_Write.setText(f"Write: {writeSpeed:.1f} KB/s")

        # If you want to show capacity for a specific disk (e.g., C: on Windows)
        try:
            usage = psutil.disk_usage("C:\\")
            total_gb = usage.total / (1024**3)
            used_gb = usage.used / (1024**3)
            self.diskLabel_Capacity.setText(f"Capacity: {used_gb:.1f}/{total_gb:.1f} GB")
        except Exception:
            pass

        # 5) GPU (placeholder)
        dummy_gpu = 5.0  # placeholder usage
        self.gpuData.append(dummy_gpu)
        if len(self.gpuData) > self.maxDataPoints:
            self.gpuData.pop(0)
        self.gpuCurve.setData(self.gpuData)
        self.gpuLabel_Usage.setText(f"Usage: {dummy_gpu:.1f}%")

    ############################################################################
    # 2.4. Process Termination (Context Menu)
    ############################################################################
    def openContextMenu(self, pos):
        index = self.tableView.indexAt(pos)
        if not index.isValid():
            return
        source_index = self.proxyModel.mapToSource(index)
        row = source_index.row()
        try:
            pid = int(self.processModel.processes[row][0])
        except (IndexError, ValueError):
            return

        menu = QMenu()
        killAction = menu.addAction("Terminate Process")
        action = menu.exec_(self.tableView.viewport().mapToGlobal(pos))
        if action == killAction:
            self.terminateProcess(pid)

    def terminateProcess(self, pid):
        try:
            psutil.Process(pid).terminate()
            QMessageBox.information(self, "Process Terminated",
                                    f"Process {pid} terminated successfully.")
        except Exception as e:
            QMessageBox.warning(self, "Error",
                                f"Failed to terminate process {pid}.\nError: {e}")
