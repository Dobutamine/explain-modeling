class BloodResistor:
    # class attributes
    Name = ""
    Description = ""
    ModelType = ""
    IsEnabled = False
    NoFlow = False
    NoBackFlow = False
    CompFrom = ""
    CompTo= ""
    RFor = 0
    RBack = 0
    Rk = 0

    # state variables
    Flow = 0
    Res = 0

    # local parameters
    _model = {}
    _comp_from = {}
    _comp_to = {}
    _t = 0.0005
    _is_initialized = False

    def __init__(self, **args):
        # initialize the super class
        super().__init__()

        # set the values of the independent properties with the values from the JSON configuration file
        for key, value in args.items():
            setattr(self, key, value)

    def InitModel(self, model):
        # store a reference to the model
        self._model = model

        # store the modeling stepsize for easy referencing
        self._t = model.ModelingStepsize

        # find the blood components which this resistors connects to
        self._comp_from = self._model.Models[self.CompFrom]
        self._comp_to = self._model.Models[self.CompTo]

        # signal that the component has been initialized
        self._is_initialized = True

    def StepModel(self):
        if (self.IsEnabled and self._is_initialized):
            self.CalcModel()

    def CalcModel(self):
        # get the pressures from the connected blood compliances
        p_u = self._comp_from.pres
        p_d = self._comp_to.pres

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

