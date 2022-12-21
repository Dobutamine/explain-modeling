from explain_core.helpers.ModelBaseClass import ModelBaseClass

class Container(ModelBaseClass):
    # model specific attributes
    ContainedModels = []
    VolExt = 0
    UVol = 0
    ELBase = 0
    ElK = 0

    # state variables
    Pres = 0
    PresMax = 0.0
    PresMin = 0.0
    Vol = 0
    VolMax = 0.0
    VolMin = 0.0

    # external parameters
    Pres0 = 0
    PresMus = 0
    PresExt = 0
    PresCc = 0

     # local parameter
    _temp_max_pres = -1000.0
    _temp_min_pres = 1000.0
    _temp_max_vol = -1000.0
    _temp_min_vol = 1000.0
    _update_counter = 0.0
    _update_interval = 1.0


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

        # find the min and max values of the last update interval
        if (self.Pres > self._temp_max_pres):
            self._temp_max_pres = self.Pres
        if (self.Pres < self._temp_min_pres):
            self._temp_min_pres = self.Pres

        if (self.Vol > self._temp_max_vol):
            self._temp_max_vol = self.Vol
        if (self.Vol < self._temp_min_vol):
            self._temp_min_vol = self.Vol

        if (self._update_counter > self._update_interval):
            self._update_counter = 0.0
            self.PresMax = self._temp_max_pres
            self.PresMin = self._temp_min_pres
            self._temp_max_pres = -1000.0
            self._temp_min_pres = 1000.0

            self.VolMax = self._temp_max_vol
            self.VolMin = self._temp_min_vol
            self._temp_max_vol = -1000.0
            self._temp_min_vol = 1000.0
            
        self._update_counter += self._t