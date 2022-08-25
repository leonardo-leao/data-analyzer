from operator import truediv
from PyQt5.QtWidgets import *
from PyQt5.uic import loadUi
from PyQt5.QtGui import *
from PyQt5.QtCore import *

import numpy as np
from actions.analytics import FourierTransform, Outliers, Extra
from actions.livePlot import LivePlot

class plot(QWidget):
    
    def __init__(self, data, pvs, options, parent=None):
        QWidget.__init__(self, parent)
        loadUi("./gui/plot.ui", self)

        self.data = data
        self.labels = pvs
        self.options = options
        self.livePlot = None
        self.outliers = []

        if not self.options["livePlot"]:
            # Separates data between x and y axes
            self.X, self.Y, outliers = [], [], []
            for pv in self.labels:
                self.X.append(self.data[pv]["datetimes"])
                self.Y.append(np.array(self.data[pv]["values"]))
                self.outliers.append(Outliers(self.data[pv]["datetimes"], self.data[pv]["values"], pv))
                self.outliers[-1].start()
            self.outliers[-1].finished.connect(self.enableOutlier)

            self.plotedX = None
            self.plotedY = None
            self.plotedXrms = []
            self.plotedYrms = []
            self.plot()
        else:
            self.live()

        # Button actions
        self.button_plot_run.clicked.connect(self.plot)
        self.button_plot_expand.clicked.connect(self.expand)
        self.button_plot_remove.clicked.connect(self.remove)
        self.button_plot_options.clicked.connect(self.plotOptions)

        # Checkbox triggers
        self.checkbox_setDifference.clicked.connect(self.update)
        self.checkbox_removeOutliers.clicked.connect(self.update)
        self.checkbox_rmsValue.clicked.connect(self.update)

        # Input triggers
        self.spin_rms.valueChanged.connect(self.update)

        # Auxiliar parameters
        self.diffWasChecked = False
 
    #
    def remove(self):
        if self.livePlot != None:
            self.livePlot.terminate()
        self.close()

    #
    def enableOutlier(self):
        self.checkbox_removeOutliers.setEnabled(True)

    #
    def update(self):
        self.setDifference()
        self.removeOutliers()
        self.rmsValue()
        self.plotArea.update(self.plotedX + self.plotedXrms, self.plotedY + self.plotedYrms, self.labels)

    #
    def rmsValue(self):
        if self.checkbox_rmsValue.isChecked():
            spin = self.spin_rms.value()
            for i in range(len(self.labels) - len(self.plotedXrms)):
                movingRMS = Extra.movingRMS(self.plotedY[i].copy(), spin)
                ini = (len(self.plotedX[i])-len(movingRMS))//2
                end = ini + len(movingRMS)
                if len(self.plotedXrms) != len(self.plotedX):
                    self.plotedXrms.append(self.plotedX[i][ini:end])
                    self.plotedYrms.append(movingRMS)
                    self.labels.append(self.labels[i] + "_RMS")
                else:
                    self.plotedXrms[i] = self.plotedX[i][ini:end]
                    self.plotedYrms[i] = movingRMS
        else:
            self.plotedXrms = []
            self.plotedYrms = []
            newLabels = []
            for i in range(len(self.labels)):
                if "RMS" not in self.labels[i]:
                    newLabels.append(self.labels[i])
            self.labels = newLabels

    #
    def removeOutliers(self):
        if self.checkbox_removeOutliers.isChecked():
            for i in range(len(self.outliers)):
                self.plotedX[i] = self.outliers[i].x.copy()
                self.plotedY[i] = self.outliers[i].y.copy()
        else:
            self.plotedX = self.X.copy()
            self.plotedY = self.Y.copy()
        self.setDifference()

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
            self.diffWasChecked = True
        elif self.diffWasChecked == True:
            for i in range(len(self.plotedY)):
                self.plotedY[i] = self.plotedY[i] + self.Y[i][0]
            self.diffWasChecked = False

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
                    fourierTransform = FourierTransform(self.plotedX[i].copy(), self.plotedY[i].copy())
                    self.plotedX[i], self.plotedY[i] = fourierTransform.fft()

            self.plotArea.plot(self.plotedX, self.plotedY, self.labels)

    def live(self) -> None:
        self.livePlot = LivePlot(self.labels, self.plotArea, parent=self)
        self.livePlot.start()
    
