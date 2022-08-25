import numpy as np
from scipy.fft import rfftfreq, rfft
from scipy.optimize import curve_fit
from datetime import datetime, timedelta
from PyQt5 import QtCore
from statistics import mode

class FourierTransform():

    def __init__(self, x, y) -> None:
        self.x = x
        self.y = y

        # Sample properties
        T, N = self.sampleProperties()
        self.period = T
        self.samples = N

    # Return the acquisition period and number of samples
    def sampleProperties(self) -> tuple:
        T = self.x[1] - self.x[0]   # Acquisition Period
        samples = len(self.x)       # Number of samples
        return (T.total_seconds(), samples)

    # Calculate the fast fourier transform
    def fft(self) -> tuple:

        # Creating frequency x axis data
        frequencies = rfftfreq(self.samples, self.period)

        # FFT
        magnitude = rfft(self.y)
        magnitude = np.abs(magnitude[1:])**2
        magnitude = 4/self.samples * magnitude
        period = 1/frequencies[1:]/60/60

        return (period, magnitude)

class NonlinearFit():

    def __init__(self, x, y, pointsToFit = None) -> None:
        self.x = x
        self.y = y
        self.pointsToFit = pointsToFit

        # Final Result of Fit
        self.fit = None

    def polynomial(self, x, a, b, c, d) -> float:
        x = np.array(x)
        return a*(x**3) + b*(x**2) + c*x + d

    def fourier(self, x, a, b, c, d, e, f, g, h, i, j, L) -> float:
        x = np.array(x)
        return a/2 + a*np.cos(np.pi*x/L) + b*np.sin(np.pi*x/L) + c*np.cos(2*np.pi*x/L) + d*np.sin(2*np.pi*x/L) + e*np.cos(3*np.pi*x/L) + f*np.sin(3*np.pi*x/L) + g*np.cos(4*np.pi*x/L) + h*np.sin(4*np.pi*x/L) + i*np.cos(5*np.pi*x/L) + j*np.sin(5*np.pi*x/L)

    # This fitting method is based on fitting small parts of the curve as a polynomial
    def standard(self) -> None:

        # Fit parameters
        self.windows = int(len(self.y)/self.pointsToFit)
        self.steps = int(len(self.y)/self.windows)

        # Initial values of recursive calculation
        advance = 1
        parameters = [1, 1, 1, 1]
        fit_x, fit_y = [], []

        try:
            # Fitting the small parts and adding to the final answer
            for i in range(self.windows):
                min = self.steps*i - advance if i > 0 else 0
                max = min + advance + self.steps if i < (self.windows - 1) else len(self.y)

                parameters, covariance = curve_fit(self.polynomial, 
                                        self.x[min:max], 
                                        self.y[min:max], 
                                        parameters, 
                                        method="trf", loss="arctan")

                max -= advance if i < self.windows-1 else 0
                max -= 1 if i == 0 else 0
                
                fit_x = fit_x + list(self.x[min:max])
                fit_y = fit_y + list(self.polynomial(self.x[min:max], *parameters))

            self.fit = {"x": np.array(fit_x), "y": np.array(fit_y)}
        except:
            print("Was not possible to fit with this number of points, we will increase in 50% and try again")
            self.pointsToFit = 1.5*self.pointsToFit
            self.standard()

    def fourierSeries(self) -> None:
        
        parameters = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        parameters, covariance = curve_fit(self.fourier, self.x, self.y, parameters, method="trf", loss="arctan")
        self.fit = {"x": self.x, "y": np.array(self.fourier(self.x, *parameters))}

class Outliers(QtCore.QThread):

    def __init__(self, x, y, pv, parent=None) -> None:
        super(Outliers, self).__init__(parent)
        self.x = np.array(x)
        self.y = np.array(y)

        if "HLS" in pv:
            self.pointsToFit = 300
        elif "Concrete" in pv and ("Temp" in pv or "Strain" in pv):
            self.pointsToFit = 12
        else:
            self.pointsToFit = 100

    def iqr(self, y):
        q1 = np.quantile(y, 0.25)
        q3 = np.quantile(y, 0.75)
        min = q1 - 1.5*(q3 - q1)
        max = q3 + 1.5*(q3 - q1)
        return (min, max)

    def identify(self):
        timestamps = np.array([datetime.timestamp(i) - datetime.timestamp(self.x[0]) for i in self.x])
        timestamps = timestamps/(timestamps[1] - timestamps[0])

        # Fitting data
        nonlinear = NonlinearFit(x=timestamps.copy(), y=self.y.copy(), pointsToFit=self.pointsToFit)
        nonlinear.standard()

        # Identify outliers based on IQR
        difference = self.y - nonlinear.fit["y"]
        min, max = self.iqr(difference)
        
        outliers = []
        for i in range(len(self.y)):
            if min > difference[i] or max < difference[i]:
                outliers.append(i)
        return outliers

    def remove(self):
        self.x = np.delete(self.x, self.index_outliers)
        self.y = np.delete(self.y, self.index_outliers)

    def run(self):
        self.index_outliers = self.identify()
        self.remove()

class Grouping():

    def __init__(self, x, y, ini, end, step: 'seconds'):
        self.x = x
        self.y = y
        self.ini = ini
        self.end = end
        self.step = timedelta(seconds=step)/2
        self.size = self.reconstruct()
    
    # FOH - first order holder
    def interpolate(self, x1, y1, x2, y2, x):
        return y1 + (x-x1)*(y2-y1)/(x2-x1)

    def reconstruct(self):

        avg = []
        for i in range(len(self.x)):

            # For the initial data is used a zero order holder (ZOH);
            while (self.x[i][0] - self.ini) >= self.step * 0.5:
                self.x[i].insert(0, self.x[i][0] - self.step)
                self.y[i].insert(0, self.y[i][0])

            # For middle data is used a first order holder (FOH) with linear interpolation
            inserted = 0
            for k in range(1, len(self.x[i])):
                j = k + inserted
                while (self.x[i][j] - self.x[i][j-1]) >= self.step * 1.1:
                    self.x[i].insert(j, self.x[i][j] - self.step)
                    self.y[i].insert(j, self.interpolate(
                        x1 = 0, 
                        y1 = self.y[i][j-1],
                        x2 = (self.x[i][j] - self.x[i][j-1]).total_seconds(),
                        y2 = self.y[i][j],
                        x = (self.x[i][j] - self.x[i][j-1] - self.step).total_seconds()
                    ))
                    inserted = inserted + 1

            # Number de acquisition in the time range
            acquisition = (self.end - self.ini)/self.step

            # For the initial data is used a zero order holder (ZOH);
            while len(self.x[i]) < acquisition:
                self.x[i].append(self.x[i][-1] + self.step)
                self.y[i].append(self.y[i][-1])

            avg.append(len(self.x[i]))

        return mode(avg)

    def average(self):
        avg = [0 for _ in range(self.size)]; cont = 0
        x = []
        for i in range(len(self.y)):
            if len(self.y[i]) == self.size:
                for j in range(self.size):
                    avg[j] += self.y[i][j]
                cont = cont + 1
                x = self.x[i]
        
        return x, [avg[i]/cont for i in range(len(avg))]

class Extra():

    @staticmethod
    def movingRMS(y, shift):
        y = [0] + y     # This implementation ignore the first valid input
        yc = np.cumsum(np.abs(y)**2)
        return np.sqrt((yc[shift:] - yc[:-shift]) / shift)
    
if __name__ == "__main__":
    from archiver import Request, Search
    import matplotlib.pyplot as plt
    s = Search("TU*S:SS*Concrete*N*Temp*")
    s.run()

    timeRange = datetime(2022, 8, 1), datetime(2022, 8, 19)
    r = Request(s.pvs, *timeRange)
    r.run()

    x, y = r.getXY()
    g = Grouping(*r.getXY(), *timeRange, 1800)

    x, y = g.average()

    

    plt.plot(x, y)
    movingrms = Extra.movingRMS(y, 50)
    plt.plot(x[(len(x)-len(movingrms))//2:(len(x)-len(movingrms))//2 + len(movingrms)], movingrms)
    
    plt.show()
