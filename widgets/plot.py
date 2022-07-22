from PyQt5.QtWidgets import *
from PyQt5.uic import loadUi
from PyQt5.QtGui import *
from PyQt5.QtCore import *

import numpy as np
from actions.analytics import FourierTransform
from actions.livePlot import LivePlot

class plot(QWidget):
    
    def __init__(self, data, pvs, options, parent=None):
        QWidget.__init__(self, parent)
        loadUi("./gui/plot.ui", self)

        self.data = data
        self.labels = pvs
        self.options = options
        self.livePlot = None

        if not self.options["livePlot"]:
            # Separates data between x and y axes
            self.X, self.Y = [], []
            for pv in self.labels:
                self.X.append(self.data[pv]["datetimes"])
                self.Y.append(np.array(self.data[pv]["values"]))

            self.plotedX = None
            self.plotedY = None
            self.plot()
        else:
            self.live()

        # Button actions
        self.button_plot_run.clicked.connect(self.plot)
        self.button_plot_expand.clicked.connect(self.expand)
        self.button_plot_remove.clicked.connect(self.remove)
        self.button_plot_options.clicked.connect(self.plotOptions)

        # Checkbox triggers
        self.checkbox_setDifference.clicked.connect(self.setDifference)

    #
    def remove(self):
        if self.livePlot != None:
            self.livePlot.terminate()
        self.close()

    #
    def expand(self):
        scaleFactor = 0.5 if self.minimumHeight() > 600 else 2
        self.frame.setMinimumHeight(int(self.minimumHeight()*scaleFactor))
        self.plotArea.resize(self.plotArea.width(), int(self.minimumHeight()*scaleFactor))
        self.setMinimumHeight(int(self.minimumHeight()*scaleFactor))
        self.plotArea.updateDraw()

    # Nao funciona
    def plotOptions(self):
        self.plotArea.layout.vertical_layout.itemAt(0).widget().hide()

    #
    def setDifference(self):
        if self.checkbox_setDifference.isChecked():
            for i in range(len(self.plotedY)):
                self.plotedY[i] = self.plotedY[i] - self.plotedY[i][0]
        else:
            self.plotedY = self.Y.copy()
        self.plotArea.updateY(self.plotedY)

    #
    def plot(self):

        if self.options["livePlot"]:
            self.live()
        else:
            self.plotedX = self.X.copy()
            self.plotedY = self.Y.copy()

            # Check if setDifference is checked and apply if true
            if self.options["setDifference"]:
                for i in range(len(self.plotedY)):
                    self.plotedY[i] = self.plotedY[i] - self.plotedY[i][0]

            if self.options["fft"]:
                for i in range(len(self.plotedX)):
                    fourierTransform = FourierTransform(self.plotedX[i], self.plotedY[i])
                    self.plotedX[i], self.plotedY[i] = fourierTransform.fft()

            self.plotArea.plot(self.plotedX, self.plotedY, self.labels)

    def live(self) -> None:
        self.livePlot = LivePlot(self.labels, self.plotArea, parent=self)
        self.livePlot.start()
    
