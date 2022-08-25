import ast
import requests

from datetime import datetime, timedelta
from PyQt5 import QtCore

class Search(QtCore.QThread):

    url  = "http://ais-eng-srv-ta.cnpem.br/retrieval/bpl/getMatchingPVs"

    # Constructor method
    def __init__(self, search: str, limit: int = 500, parent=None) -> None:
        super(Search, self).__init__(parent)
        self.search = search         # String to process variable search
        self.limit = limit          # Limit of PVs returned
        self.pvs = []               # List of PVs after search

    def run(self) -> None:
        query = {"pv": self.search, "limit": self.limit}
        response = requests.get(Search.url, params=query)
        self.pvs = ast.literal_eval(response.text)

class Request(QtCore.QThread):

    url = "http://ais-eng-srv-ta.cnpem.br/retrieval/data/getData.json"

    def __init__(self, pvs: list, ini: datetime, end: datetime, mean: int = None, reference: datetime = None, progressBar = None, parent = None) -> None:
        super(Request, self).__init__(parent)
        self.pvs = pvs
        self.ini = ini
        self.end = end
        self.progressBar = progressBar
        self.mean = mean
        self.reference = reference
        self.result = None

        # ProgressBar 
        if self.progressBar != None:
            self.progressBar.setMaximum(len(pvs)-1)

    def datetime2Str(self, datetime: datetime) -> str:
        return datetime.strftime("%Y-%m-%dT%H:%M:%SZ")

    def getXY(self) -> list[list]:
        x, y = [], []
        for pv in self.result.keys():
            x.append(self.result[pv]["datetimes"].copy())
            y.append(self.result[pv]["values"].copy())
        return [x, y]

    def run(self) -> None:

        self.result = {}

        for i in range(len(self.pvs)):
            pv = self.pvs[i]
            meanPV = f"({pv})" if self.mean == None else f"mean_{self.mean}({pv})"
            
            if None not in [self.ini, self.end]:
                ini = self.datetime2Str(self.ini - timedelta(minutes=30))
                end = self.datetime2Str(self.end + timedelta(minutes=30))
                query = {"pv": meanPV, "from": ini, "to": end}
            else:
                query = {"pv": meanPV}

            try:
                response = requests.get(Request.url, params=query)
                json = response.json()
                metadata = json[0]["meta"]
                data = json[0]["data"]

                datetimes, values = [], []
                for i in range(len(data)):
                    time = datetime.fromtimestamp(data[i]["secs"])
                    if self.ini <= time <= self.end:
                        datetimes.append(time)
                        values.append(data[i]["val"])

                if [] not in [datetimes, values]:
                    self.result[pv] = {
                        "datetimes": datetimes, 
                        "values": values,
                        "unit": metadata["EGU"],
                        "request": (self.ini, self.end)
                    }

            except Exception as e:
                self.result[pv] = "Failed"
                print("[ARCHIVER] Error - message:", e)

            if self.progressBar != None:
                self.progressBar.setValue(i)
            