import math

from explain_core.helpers.BrentRootFinding import brent_root_finding

class Oxygenation:

    # class attributes
    Name = ""
    Description = ""
    ModelType = ""
    IsEnabled = False
    Hemoglobin = 0.0
    Dpg = 0.0

    # set the brent root finding properties
    _brent_accuracy = 1e-8
    _max_iterations = 100
    _left_o2 = 0.01
    _right_o2 = 100.0

    # set constants
    _mmol_to_ml = 22.2674
    _gas_constant = 62.36367

    # independent parameters
    _to2 = 0
    _ph = 0
    _temp = 0
    _be = 0

    # dependent parameters
    _so2 = 0
    _po2 = 0
    _pres = 760

    def __init__(self, **args):
        # initialize the super class
        super().__init__()

        # set the values of the independent properties with the values from the JSON configuration file
        for key, value in args.items():
            setattr(self, key, value)

    def InitModel(self, model):
        pass

    def StepModel(self):
        pass

    def CalcModel(self):
        pass

    def calc_oxygenation(self, to2: float, hb = 8.0, temp = 37.0, ph = 7.40,  dpg = 5, be = 0.0, pres = 760 ):

        # define a result object
        _result = OxyResult()

        # import the parameters
        self._to2 = to2
        self._hemoglobin = hb
        self._temp = temp
        self._ph = ph
        self._dpg = dpg
        self._be = be
        self._pres = pres

        # find the po2 and so2 and using a brent root finding procedure

        # the brent root finding returns a tuple (result: float, iterations: float, error: bool)
        r = brent_root_finding(self.oxygen_content, self._left_o2, self._right_o2, self._max_iterations, self._brent_accuracy)
        _result.Iterations = r[1]
        _result.Error = r[2]

        # if the brent root finding did not yield a value then return an error
        if (_result.Error):
            return _result

        # complete the result object and return it
        _result.Po2 = self._po2
        _result.So2 = self._so2

        return _result


    def oxygen_content(self, po2: float) -> float:
        # calculate the saturation from the current po2 from the current po2 estimate
        self._so2 = self.oxygen_dissociation_curve(po2)

        # store the current po2 estimate as mmHg
        self._po2 = po2 / 0.13333

        # calculate the to2 from the current po2 estimate
        # convert the hemoglobin unit from mmol/l to g/dL
        # convert the po2 from kPa to mmHg
        # convert to output from ml O2/dL blood to ml O2/l blood
        to2_new_estimate = (0.0031 * (po2 / 0.1333) + 1.36 * (self._hemoglobin / 0.6206) * self._so2) * 10.0

        # convert the ml O2/l to mmol/l with the gas law with (GasConstant * (273.15 + _temp)) / Pres) / to2 (mol/l)
        _mmolToMl = self._gas_constant * (273.15 + self._temp) / self._pres

        # calculate ml O2 / ml blood.
        to2_new_estimate = to2_new_estimate / self._mmol_to_ml

        # calculate the difference between the real to2 and the to2 based on the new po2 estimate and return it to the brent root finding function
        dto2 = self._to2 - to2_new_estimate

        # return the difference
        return dto2

    def oxygen_dissociation_curve(self, po2: float) -> float:
        # calculate the saturation from the po2 depending on the ph, be, temperature and dpg level.
        a = 1.04 * (7.4 - self._ph) + 0.005 * self._be + 0.07 * (self._dpg - 5.0)
        b = 0.055 * (self._temp + 273.15 - 310.15)
        y0 = 1.875
        x0 = 1.875 + a + b
        h0 = 3.5 + a
        k = 0.5343
        x = math.log(po2, math.e)
        y = x - x0 + h0 * math.tanh(k * (x - x0)) + y0
        return 1.0 / (math.pow(math.e, -y) + 1.0)


class OxyResult:
    Po2 = 0,
    So2 = 0,
    Error = True
    Iterations = 0