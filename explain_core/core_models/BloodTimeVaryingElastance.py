from explain_core.helpers.ModelBaseClass import ModelBaseClass

class BloodTimeVaryingElastance(ModelBaseClass):
    # state variables pressure
    Vol = 0
    VolMax = 0
    VolMin = 0
    UVol = 0

    #state variables elastance
    ElMin = 0
    ElMax = 0
    ElK = 0
    ActFactor = 0

    # state variables pressure
    Pres = 0
    Pres0 = 0
    PresEd = 0
    PresEs = 0
    PresMus = 0
    PresExt = 0
    PresCc = 0
    PresMax = 0
    PresMin = 0

    # state variables oxygenation
    To2 = 0
    Po2 = 0
    So2 = 0

    # state variables acid base
    Tco2 = 0
    Ph = 0
    Pco2 = 0
    Hco3 = 0
    Be = 0
    Sid = 0
    Uma = 0

    # list holding all solutes
    Solutes = []

    # local parameters
    _temp_pres_max = -1000
    _temp_pres_min = 1000
    _temp_vol_max = -1000
    _temp_vol_min = 1000
    _eval_timer = 0
    _eval_time = 1.0

    def CalcModel(self):
        # calculate the end diastolic pressure
        self.PresEd = self.ElMin * (1.0 + self.ElK * (self.Vol - self.UVol)) * (self.Vol - self.UVol)

        # calculate the end systolic pressure
        self.PresEs = self.ElMax * (self.Vol - self.UVol)

        # calculate the pressure depending on the elastance
        self.Pres = self.ActFactor * (self.PresEs - self.PresEd) + self.PresEd + self.Pres0 + self.PresExt + self.PresCc + self.PresMus

        # reset the external pressures
        self.Pres0 = 0.0
        self.PresExt = 0.0
        self.PresCc = 0.0
        self.PresMus = 0.0

        # determine the maximal and minimal pressures and volumes
        self.CalcMinMax()

    def VolumeIn(self, dvol, compFrom):
        # increase the volume
        self.Vol += dvol

        # calculate the change in solute concentration

    def VolumeOut(self, dvol):
        # declare a volume deficit
        vol_deficit = 0.0

        # decrease the volume
        self.Vol -= dvol

        # guard against negative volumes and a mass balance disturbance
        if (self.Vol < 0):
            vol_deficit = -self.Vol
            self.Vol = 0.0

        # return the volume deficit
        return vol_deficit

    def CalcMinMax(self):
        if (self.Pres > self._temp_pres_max):
            self._temp_pres_max = self.Pres
        if (self.Pres < self._temp_pres_min):
            self._temp_pres_min = self.Pres
        if (self.Vol > self._temp_vol_max):
            self._temp_vol_max = self.Vol
        if (self.Vol < self._temp_vol_min):
            self._temp_vol_min = self.Vol

        # evaluate
        if (self._eval_timer > self._eval_time):
            self.vol_max = self._temp_vol_max
            self.vol_min = self._temp_vol_min
            self.pres_max = self._temp_pres_max
            self.pres_min = self._temp_pres_min

            self._temp_pres_min = 1000
            self._temp_pres_max = -1000
            self._temp_vol_min = 1000
            self._temp_vol_max = -1000

            self._eval_timer = 0

        # increase the evaluation timer
        self._eval_timer += self._t






