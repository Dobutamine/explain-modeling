from explain_core.core_models.ModelBaseClass import ModelBaseClass

class BloodTimeVaryingElastance(ModelBaseClass):
    # model specific attributes
    Vol = 0
    UVol = 0
    ElMin = 0
    ElMax = 0
    ElK = 0

    # state variables
    Pres = 0
    PresEd = 0
    PresEs = 0

    # external parameters
    Pres0 = 0
    PresMus = 0
    PresExt = 0
    PresCc = 0
    ActFactor = 0

    # override the base class CalcModel method
    def CalcModel(self):
         # calculate the end diastolic pressure
        self.PresEd = self.ElMin * (1.0 + self.ElK * (self.Vol - self.UVol)) * (self.Vol - self.UVol)

        # calculate the end systolic pressure
        self.PresEs = self.ElMax * (self.Vol - self.UVol)

        # calculate the pressure depending on the elastance
        self.Pres = self.ActFactor * (self.PresEs - self.PresEd) + self.PresEd + self.Pres0 + self.PresExt + self.PresCc + self.PresMus

        # reset the external pressures as they have to be set every model cycle
        self.Pres0 = 0.0
        self.PresExt = 0.0
        self.PresCc = 0.0
        self.PresMus = 0.0


    def VolumeIn(self, dvol, compFrom):
        # increase the volume
        self.Vol += dvol

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
