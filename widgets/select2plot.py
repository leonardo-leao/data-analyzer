from PyQt5.QtWidgets import *
from PyQt5.uic import loadUi
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from numpy import minimum

from widgets.plot import plot

class Select2Plot(QMainWindow):

    def __init__(self, logBox):
        QMainWindow.__init__(self)
        loadUi("./gui/select2plot.ui", self)
        self.setWindowTitle("Plot Options")

        # Button actions
        self.pb_selectAll.clicked.connect(lambda: self.selectAllPvs(True))
        self.pb_deselectAll.clicked.connect(lambda: self.selectAllPvs(False))
        self.pb_load.clicked.connect(self.load)

        # Scroll List Area
        self.scrollArea.widget = QWidget()
        self.scrollArea.vbox = QVBoxLayout()
        self.scrollArea.widget.setLayout(self.scrollArea.vbox)
        self.scrollArea.setWidget(self.scrollArea.widget)

        self.logBox = logBox
        self.plotArea = None
        self.data = None

    # Search the PVs a show to user select which wants
    def selectPvs(self, pvs, data, plotArea):
        self.plotArea = plotArea
        self.data = data
        # Remove old PVs from list
        for i in reversed(range(self.scrollArea.vbox.count())): 
            self.scrollArea.vbox.itemAt(i).widget().setParent(None)
        self.addList(pvs)

    # Add searched PV to a list to user select which they want
    def addList(self, pvs):
        for pv in pvs:
            text = pv if pv not in self.data.keys() else pv + " ✔"
            self.scrollArea.vbox.addWidget(QCheckBox(text, minimumHeight=20))
        self.scrollArea.vbox.setAlignment(Qt.AlignTop)

    # Select all the PVs listed
    def selectAllPvs(self, op: bool):
        for i in range(self.scrollArea.vbox.count()):
            self.scrollArea.vbox.itemAt(i).widget().setChecked(op)

    # Get plot options
    def getPlotOptions(self):
        return {
            "setDifference": self.cb_setDiff.isChecked(),
            "removeOutliers": self.cb_removeOutliers.isChecked(),
            "fft": self.cb_fft.isChecked(),
            "livePlot": self.cb_livePlot.isChecked()
        }

    # Set a new list of PVs
    def load(self):
        pvs = []
        for i in range(self.scrollArea.vbox.count()):
            option = self.scrollArea.vbox.itemAt(i).widget()
            if option.isChecked() and option.text()[-1] == "✔":
                pvs.append(option.text()[:-2])
            elif option.isChecked() and self.cb_livePlot.isChecked():
                pvs.append(option.text())
            else:
                print("Warning: selected PV to plot is not load")
        if pvs != []:
            self.plotArea.addWidget(plot(self.data, pvs, self.getPlotOptions()))
        self.close()
