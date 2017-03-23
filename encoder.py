import numpy as np
from scipy.optimize import brentq

__all__ = ['PolarBase', 'PolarCodeAWGN', 'PolarCodeBEC', 'PolarCodeBSC']


def theta(x):
    # approximation
    return np.where(
        x >= 10,
        np.sqrt(np.pi / x) * np.exp(-x/4) * (1 - 10 / 7 / x),
        np.exp(-0.4527 * x**0.86 + 0.0218)
    )

def theta1(x):
    # inverse function
    def _single_val(y):
        return brentq(lambda t: theta(t) - y, 1e-10, 1e10)
    return np.vectorize(_single_val)(x)


class PolarBase:
    def __init__(self, bhatt_param, N, K, kernel):
        if (np.log(N) / np.log(2)) % 1 != 0:
            raise ValueError('N is not a power of 2')

        self.N = N
        self.K = K
        self.kernel = kernel

        n = int(np.log(N) / np.log(2))
        values = np.array([bhatt_param])

        for level in range(n):
            values = values[:, np.newaxis]
            values = np.hstack((theta1(1 - (1 - theta(values))**2), 2 * values)).flatten()

        self.indices = np.argsort(values)[:K]
        self.indices = np.array(list(map(lambda x: int(bin(x)[2:].zfill(n)[::-1], 2), self.indices)))

        for i in range(n-1):
            self.kernel = np.kron(self.kernel, kernel)

    def encode(self, message):
        if message.shape[0] != self.K:
            raise ValueError('Message length should be {}'.format(self.K))

        message_extended = np.zeros(self.N)
        message_extended[self.indices] = message
        encoded = (self.kernel @ message_extended) % 2
        return encoded

class PolarCodeAWGN(PolarBase):
    def __init__(self, Ec, N0, N, K, kernel=np.array([[1, 1], [0, 1]])):
        bhatt_param = np.exp(-Ec / N0)
        super(PolarCodeAWGN, self).__init__(bhatt_param, N, K, kernel)

class PolarCodeBEC(PolarBase):
    def __init__(self, epsilon, N, K, kernel=np.array([[1, 1], [0, 1]])):
        super(PolarCodeBEC, self).__init__(epsilon, N, K, kernel)

class PolarCodeBSC(PolarBase):
    def __init__(self, p, N, K, kernel=np.array([[1, 1], [0, 1]])):
        bhatt_param = (p * (1 - p)) ** 0.5
        super(PolarCodeBSC, self).__init__(bhatt_param, N, K, kernel)