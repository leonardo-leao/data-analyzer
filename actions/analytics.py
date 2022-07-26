import numpy as np
from scipy.fft import rfftfreq, rfft
from scipy.optimize import curve_fit
#from PyQt5 import QtCore

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

    def __init__(self, x, y) -> None:
        self.x = x
        self.y = y
        self.pointsToFit = 6

        # Fit parameters
        self.windows = int(len(y)/self.pointsToFit)
        self.steps = int(len(y)/self.windows)

        # Final Result of Fit
        self.fit = None

    def polynomial(self, x, a, b, c, d):
        return a*(x**3) + b*(x**2) + c*x + d

    # This fitting method is based on fitting small parts of the curve as a polynomial
    def standard(self):

        # Initial values of recursive calculation
        parameters = [1, 1, 1, 1]
        fit_x, fit_y = [], []

        # Fitting the small parts and adding to the final answer
        for i in range(self.windows):
            min = self.steps*i - 1 if i > 0 else 0
            max = min + 1 + self.steps if i < (self.windows - 1) else len(self.y)
            parameters, _ = curve_fit(self.polynomial, 
                                      self.x[min:max], 
                                      self.y[min:max], 
                                      parameters, 
                                      method="trf", loss="arctan")
            fit_x = fit_x + list(self.x[min:max])
            fit_y = fit_y + list(self.polynomial(self.x[min:max], *parameters))

        self.fit = {"x": fit_x, "y": fit_y}