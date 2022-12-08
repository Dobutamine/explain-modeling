from explain_core.core_models.ModelBaseClass import ModelBaseClass

class BloodCompliance(ModelBaseClass):
    # model specific attributes
    Vol = 0
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
    Solutes = {}

    # override the base class CalcModel method
    def CalcModel(self):
        # calculate the pressure depending on the elastance
        self.Pres = self.ElBase * (1.0 + self.ElK * (self.Vol - self.UVol)) * (self.Vol - self.UVol) + self.Pres0 + self.PresExt + self.PresCc + self.PresMus

        # reset the external pressures as they have to be set every model cycle
        self.Pres0 = 0.0
        self.PresExt = 0.0
        self.PresCc = 0.0
        self.PresMus = 0.0


    def VolumeIn(self, dvol, compFrom):
        # increase the volume
        self.Vol += dvol

        # calculate the change in solute concentration 
        for solute, value in self.Solutes.items():
            dSol = (compFrom.Solutes[solute] - value) * dvol
            self.Solutes[solute] = ((value * self.Vol) + dSol) / self.Vol

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






