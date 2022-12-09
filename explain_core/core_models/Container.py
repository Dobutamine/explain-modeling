from explain_core.helpers.ModelBaseClass import ModelBaseClass

class Container(ModelBaseClass):
    # model specific attributes
    ContainedModels = []
    Vol = 0
    VolExt = 0
    UVol = 0
    ELBase = 0
    ElK = 0

    # state variables
    Pres = 0

    # external parameters
    Pres0 = 0
    PresMus = 0
    PresExt = 0
    PresCc = 0

    # local parameters
    _contained_models = {}

    # override the base class CalcModel method
    def CalcModel(self):
        # set the volume to the externally added volume
        self.Vol = self.VolExt

        # calculate the current volume of the container
        for model in self.ContainedModels:
            self.Vol += self._modelEngine.Models[model].Vol

        # calculate the pressure depending on the elastance
        self.Pres = self.ElBase * (1.0 + self.ElK * (self.Vol - self.UVol)) * (self.Vol - self.UVol) + self.Pres0 + self.PresExt + self.PresCc + self.PresMus

        # transfer the pressures to the models the container contains
        for model in self.ContainedModels:
            self._modelEngine.Models[model].PresExt += self.Pres

        # reset the external pressures as they have to be set every model cycle
        self.Pres0 = 0.0
        self.PresExt = 0.0
        self.PresCc = 0.0
        self.PresMus = 0.0