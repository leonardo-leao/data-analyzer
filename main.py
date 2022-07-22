from PyQt5.QtWidgets import *
from PyQt5.uic import loadUi
from PyQt5.QtGui import *
from PyQt5.QtCore import *
#from actions.archiver import Archiver

# Widgets and screens
from widgets.select2plot import Select2Plot
from widgets.searchpvs import SearchPVs
from actions.archiver import Request

class DataAnalyzer(QMainWindow):
    
    def __init__(self):
        QMainWindow.__init__(self)
        loadUi("./gui/main.ui", self)
        self.setWindowTitle("Data Analyzer")

        # Button actions
        self.button_addPlot.clicked.connect(self.addPlot)
        self.button_searchPV.clicked.connect(self.search_pv)
        self.button_request.clicked.connect(self.request)
        self.button_clearPVs.clicked.connect(self.clearPVs)
        self.button_clearPVsLoaded.clicked.connect(self.clearPVsLoaded)

        # Checkbox triggers
        self.cb_mean.clicked.connect(lambda: self.enableForm("mean"))
        self.cb_reference.clicked.connect(lambda: self.enableForm("reference"))

        # Plot Area
        self.plotArea.widget = QWidget()
        self.plotArea.vbox = QVBoxLayout()
        self.plotArea.widget.setLayout(self.plotArea.vbox)
        self.plotArea.setWidget(self.plotArea.widget)

        # Screens
        self.searchPVs = SearchPVs(self.logBox)
        self.select2Plot = Select2Plot(self.logBox)

        # ProgressBar
        self.progressBar.setMinimum(0)
        self.progressBar.setValue(0)

        # Attributes
        self.loaded = {}
        
    #
    def addPlot(self):
        pvs = self.searchPVs.pvs.copy()
        self.select2Plot.selectPvs(pvs, self.loaded, self.plotArea.vbox)
        self.select2Plot.show()

    #
    def enableForm(self, option):
        if option == "mean":
            self.form_mean.setEnabled(self.cb_mean.isChecked())
        elif option == "reference":
            self.form_reference.setEnabled(self.cb_reference.isChecked())

    #
    def search_pv(self):
        pvName = self.form_pvName.text()
        if pvName != "":
            self.searchPVs.selectPvs(pvName)
            self.searchPVs.show()
        else:
            self.logBox.append("Complete all the fields correctly...")

    #
    def request(self):
        if self.searchPVs.pvs != []:
            alreadyLoaded = self.loaded.keys()
            ini, end = self.getDatetimeRange()
            pvs = []
            
            # Check if some PV in list was not loaded
            for pv in self.searchPVs.pvs:
                if (pv not in alreadyLoaded) or ((ini, end) != self.loaded[pv]["request"]):
                    pvs.append(pv)
                else:
                    print("Warning: pv has already been loaded with this datetime range")
            
            # Request options
            mean, reference = None, None
            if self.cb_mean.isChecked():
                mean = self.form_mean.value()
            if self.cb_reference.isChecked():
                reference = self.form_reference.dateTime().toPyDateTime()

            # Create Request
            self.archiverRequest = Request(pvs, ini, end, mean, reference, progressBar=self.progressBar)
            self.archiverRequest.start()
            self.archiverRequest.finished.connect(self.requestFinished)
        else:
            self.logBox.append("<b style='color: orange'>Warning:</b> None PV selected")

    #
    def requestFinished(self):
        self.loaded.update(self.archiverRequest.result)
        self.archiverRequest.terminate()
        self.logBox.append("<b style='color: green'>Success:</b> PVs were loaded!")
     
    #
    def clearPVs(self):
        self.selectedPVs = []
        self.searchPVs.pvs = []
        self.logBox.clear()
        self.logBox.append("<b style='color: green'>Success:</b> Selected PVs were cleaned!")

    #
    def clearPVsLoaded(self):
        self.loaded = {}
        self.logBox.clear()
        self.logBox.append("<b style='color: green'>Success:</b> Loaded PVs were cleaned!")

    #
    def getDatetimeRange(self):
        ini = self.form_iniDatetime.dateTime().toPyDateTime()
        end = self.form_endDatetime.dateTime().toPyDateTime()
        return (ini, end)

app = QApplication([])
window = DataAnalyzer()
window.show()
app.exec_()