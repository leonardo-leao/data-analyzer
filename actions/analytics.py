import numpy as np
from scipy.fft import rfftfreq, rfft

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


