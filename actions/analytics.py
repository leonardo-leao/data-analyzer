import numpy as np
from scipy.fft import rfftfreq, rfft
from scipy.optimize import curve_fit
from datetime import datetime
from PyQt5 import QtCore

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

    def __init__(self, x, y, pointsToFit) -> None:
        self.x = x
        self.y = y
        self.pointsToFit = pointsToFit
        print(self.pointsToFit)

        # Final Result of Fit
        self.fit = None

    def polynomial(self, x, a, b, c, d) -> float:
        x = np.array(x)
        return a*(x**3) + b*(x**2) + c*x + d

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

class Outliers(QtCore.QThread):

    """
        Indicated number os points to fit to each monitoring system:
        Concrete temperature: 12 points
        Hydrostatic leveling system: 300 points
    """

    def __init__(self, x, y, pv) -> None:
        self.x = np.array(x)
        self.y = np.array(y)

        if "HLS" in pv:
            self.pointsToFit = 300
        elif "Concrete" in pv and "Temp" in pv:
            self.pointsToFit = 12

        self.index_outliers = self.identify()

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