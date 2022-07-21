from PyQt5.QtWidgets import *
from PyQt5.uic import loadUi
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from actions.archiver import Search
from widgets.plot import plot

class SearchPVs(QMainWindow):

    def __init__(self, logBox):
        QMainWindow.__init__(self)
        loadUi("./gui/searchpvs.ui", self)
        self.setWindowTitle("Select PVs")

        # Button actions
        self.pb_selectAll.clicked.connect(lambda: self.selectAllPvs(True))
        self.pb_deselectAll.clicked.connect(lambda: self.selectAllPvs(False))
        self.pb_load.clicked.connect(self.load)

        self.logBox = logBox
        self.pvs = []

    # Search the PVs a show to user select which wants
    def selectPvs(self, pvName):
        self.search = Search(pvName)
        self.search.start()
        self.search.finished.connect(self.addList)

        # Remove old PVs from list
        for i in reversed(range(self.list.count())): 
            self.list.itemAt(i).widget().setParent(None)

    # Add searched PV to a list to user select which they want
    def addList(self):
        pvs = self.search.pvs
        for i in range(len(pvs)):
            self.list.addWidget(QCheckBox(pvs[i], checked=(pvs[i] in self.pvs)))
        self.list.setAlignment(Qt.AlignTop)
        self.search.terminate()

    # Select all the PVs listed
    def selectAllPvs(self, op: bool):
        for i in range(self.list.count()):
            self.list.itemAt(i).widget().setChecked(op)

    # Set a new list of PVs
    def load(self):
        pvs = self.pvs
        for i in range(self.list.count()):
            option = self.list.itemAt(i).widget()
            if option.isChecked() and option.text() not in pvs:
                pvs.append(option.text())
        self.logBox.clear()
        self.logBox.append(str(pvs))
        self.pvs = pvs
        self.close()