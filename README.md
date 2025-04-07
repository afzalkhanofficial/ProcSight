# 🚀 ProcSight: Real-Time System & Process Monitoring Dashboard

**ProcSight** is a real-time system monitoring dashboard built using Python and PyQt5. It provides a dynamic graphical interface for monitoring system performance — including CPU, memory, disk, and network usage — and managing running processes with ease. Designed for system administrators and power users, it simplifies process management and visual system insights in one sleek UI.

---

## 🧠 Features

### 🖥️ Process Management
- Live view of all system processes
- Filter/search processes
- Terminate processes via GUI

### 📊 Performance Monitoring
- Real-time CPU usage graph
- Live memory, disk, and network usage visualization
- Smooth plots using `PyQtGraph`

### ⏱️ Live Data Updates
- Automatic updates using `QTimer`
- Uses `psutil` to fetch current system metrics

### 🔀 Modular Architecture
- Clean separation of GUI, data logic, and visualization components

---

## 🧩 Modules

| Module | Description |
|--------|-------------|
| `GUI` | Manages the sidebar, stacked widgets, and navigation |
| `Process Page` | Displays a table of all running processes with control options |
| `Performance Page` | Graphs CPU, memory, disk, and network stats in real time |
| `Data Acquisition` | Fetches metrics using `psutil` and sends data to the UI |

---

## 💻 Technologies Used

- **Programming Language:** `Python 3.11+`
- **GUI Framework:** `PyQt5`
- **Data Fetching:** `psutil`
- **Charting Library:** `PyQtGraph`
- **Version Control:** `Git` + `GitHub`

---

## 🚀 Getting Started

### 🔧 Prerequisites
```bash
pip install pyqt5 pyqtgraph psutil
```

### ▶️ Run the App
```bash
python ProcSight.py
```

---

## 📦 Folder Structure
```bash
ProcessPulse/
├── ProcSight.py
├── README.md
└── requirements.txt
```

## 📚 References
- [psutil Documentation](https://psutil.readthedocs.io/)
- [PyQt5 Documentation](https://doc.qt.io/qtforpython/)
- [PyQtGraph](http://www.pyqtgraph.org/)
- Similar Open Source Tool: [Glances](https://nicolargo.github.io/glances/)
