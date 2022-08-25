from PyQt5 import QtCore

import numpy as np
from time import sleep
from datetime import datetime
from actions.archiver import Request

class LivePlot(QtCore.QThread):

    def __init__(self, pvs: list[str], plotArea, parent=None) -> None:
        super(LivePlot, self).__init__(parent)
        self.pvs = pvs
        self.running = True
        self.plotArea = plotArea
        self.x = [[] for _ in range(len(pvs))]
        self.y = [[] for _ in range(len(pvs))]

    def run(self) -> None:
        while self.running:
            now = datetime.now()
            self.archiverRequest = Request(self.pvs, now, now, None, None)
            self.archiverRequest.start()
            self.archiverRequest.finished.connect(self.requestFinished)
            sleep(2)


    def requestFinished(self):
        i = 0
        for pv in self.archiverRequest.result.keys():
            self.x[i] += self.archiverRequest.result[pv]["datetimes"]
            self.y[i] += self.archiverRequest.result[pv]["values"]
            i += 1
        self.plotArea.plot(self.x, self.y, self.pvs)        
        self.archiverRequest.terminate()