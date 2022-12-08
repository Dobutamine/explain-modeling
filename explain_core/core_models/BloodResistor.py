from explain_core.core_models.ModelBaseClass import ModelBaseClass

class BloodResistor(ModelBaseClass):
    # model specific attributes
    NoFlow = False
    NoBackFlow = False
    CompFrom = ""
    CompTo = ""
    RFor = 1
    RBack = 1
    Rk = 0

    # state variables
    Flow = 0
    Res = 0

    # local parameters
    _comp_from = {}
    _comp_to = {}

    # override the InitModel of the model base class as this model requires additional initialization
    def InitModel(self, modelEngine):
        # initialize the base class
        ModelBaseClass.InitModel(self, modelEngine)

        # find the blood components which this resistors connects to
        self._comp_from = self._modelEngine.Models[self.CompFrom]
        self._comp_to = self._modelEngine.Models[self.CompTo]

    def CalcModel(self):
        # get the pressures from the connected blood compliances
        p_u = self._comp_from.Pres
        p_d = self._comp_to.Pres

        # calculate the flow in l/s
        if (p_u > p_d):
            self.Res = (self.RFor * (1.0 + self.Rk * self.Flow))
            self.Flow = (p_u - p_d) / self.Res
        else:
            if (not self.NoBackFlow):
                self.Res = (self.RBack * (1.0 + self.Rk * self.Flow))
                self.Flow = (p_u - p_d) / self.Res
            else:
                self.Flow = 0

        if (self.NoFlow):
            self.Flow = 0

        # calculate the absolute flow in the model step
        dvol = self.Flow * self._t

        # change the volumes of the connected compliances
        if (dvol > 0):
            mb_pos = self._comp_from.VolumeOut(dvol)
            self._comp_to.VolumeIn(dvol - mb_pos, self._comp_from)
        else:
            mb_neg = self._comp_to.VolumeOut(-dvol)
            self._comp_from.VolumeIn(-(dvol - mb_neg), self._comp_to)

