import math

from explain_core.core_models.ModelBaseClass import ModelBaseClass
from explain_core.helpers.BrentRootFinding import Brent

class AcidBase(ModelBaseClass):
    # class attributes
    AlphaCo2P = 0.03067

    # set the brent root finding properties
    _brent_accuracy = 1e-8
    _max_iterations = 100
    _left_hp = math.pow(10.0, -7.8) * 1000.0
    _right_hp = math.pow(10.0, -6.8) * 1000.0

    # set acid base constants
    _kw = math.pow(10.0, -13.6) * 1000.0
    _kc = math.pow(10.0, -6.1) * 1000.0
    _kd = math.pow(10.0, -10.22) * 1000.0

    # blood gas
    _tco2 = 0
    _sid = 0
    _albumin = 0
    _phosphates = 0
    _uma = 0
    _ph = 0
    _pco2 = 0
    _hco3 = 0
    _cco2 = 0
    _cco3 = 0
    _oh = 0

    def calc_acid_base(self, tco2, sid = 35.9, alb = 25.0, pi = 1.64, u = 0.0):
        # declare a new blood gas instance
        _result = BloodGas()

        # store the parameters
        self._tco2 = tco2
        self._sid = sid
        self._phosphates = pi
        self._albumin = alb
        self._uma = u

        # find the hp concentration
        r = Brent(self.net_charge_plasma, self._left_hp, self._right_hp, self._max_iterations, self._brent_accuracy)
        _result.Iterations = r[1]
        _result.Error = r[2]

        # if the brent root finding did not yield a value then return an error
        if (_result.Error):
            return _result

        # complete the result object and return it
        _result.Ph = self._ph
        _result.Pco2 = self._pco2
        _result.Hco3 = self._hco3

        return _result


    def net_charge_plasma(self, h):
        # calculate the plasma co2 concentration based on the total co2 in the plasma, hydrogen concentration and the constants Kc and Kd
        self._cco2 = self._tco2 / (1.0 + (self._kc / h) + (self._kc * self._kd) / (math.pow(h, 2.0)))
        # calculate the plasma hco3(-) concentration (bicarbonate)
        self._hco3 = (self._kc * self._cco2) / h # Eq.3
        # calculate the plasma co3(2-) concentration (carbonate)
        self._cco3 = (self._kd * self._hco3) / h # Eq.4
        # calculate the plasma OH(-) concentration (water dissociation)
        self._oh = self._kw / h # Eq.7
        # calculate the pco2 of the plasma
        self._pco2 = self._cco2 / self.AlphaCo2P # Eq.13
        # calculate the pH
        self._ph = -math.log10(h / 1000.0) # Eq. 9
        # calculate the weak acids (albumin and phosphates)
        a = self._albumin * (0.123 * self._ph - 0.631) + self._phosphates * (0.309 * self._ph - 0.469)  #Eq.8
        ac = h - self._hco3 - a - self._oh - (2.0 * self._cco3) # Eq.10
        # calculate the net charge of the plasma. If the netcharge is zero than the current hp_estimate is the correct one.
        nc = ac + self._sid - self._uma # Eq. 12
        # return the net charge
        return nc

class BloodGas:
    Ph = 0
    Pco2 = 0
    Hco3 = 0
    Be = 0
    Iterations = 0
    Error = True

