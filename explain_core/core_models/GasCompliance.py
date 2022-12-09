import math

from explain_core.helpers.ModelBaseClass import ModelBaseClass

class GasCompliance(ModelBaseClass):
     # model specific attributes
    Vol = 0
    UVol = 0
    ELBase = 0
    ElK = 0

    # state variables
    Pres = 0
    CTotal = 0
    Co2 = 0
    Cco2 = 0
    Cn2 = 0
    Ch2o = 0
    Po2 = 0
    Pco2 = 0
    Pn2 = 0
    Ph2o = 0
    Fo2 = 0
    Fco2 = 0
    Fn2 = 0
    Fh2o = 0
    Temp = 20.0
    TargetTemp = 37.0

    # external parameters
    Pres0 = 0
    PresMus = 0
    PresExt = 0
    PresCc = 0

    # local parameters
    GasConstant = 62.36367

    def CalcModel(self):
        # add heat to the gas 
        self.AddHeat()

        # add water vapour to the gas
        self.AddWaterVapour()

        # calculate the pressure depending on the elastance
        self.Pres = self.ElBase * (1.0 + self.ElK * (self.Vol - self.UVol)) * (self.Vol - self.UVol) + self.Pres0 + self.PresExt + self.PresCc + self.PresMus

        # reset the external pressures as they have to be set every model cycle except for Pres0
        self.PresExt = 0.0
        self.PresCc = 0.0
        self.PresMus = 0.0

        # calculate the new gas composition
        self.CalcgasComposition()

    def AddHeat(self):
        # calculate a temperature change depending on the target temperature and the current temperature
        dT = (self.TargetTemp - self.Temp) * 0.0005
        self.Temp += dT
            
        # change the volume as the temperature changes
        if (self.Pres != 0):
            # as CTotal is in mmol/l we have convert it as the gas constant is in mol
            dV = (self.CTotal * self.Vol * self.GasConstant * dT) / self.Pres
            self.Vol += (dV / 1000.0)
                
            # guard against negative volumes
            if (self.Vol < 0):
                self.Vol = 0

    def AddWaterVapour(self):       
        # Calculate water vapour pressure at compliance temperature
        pH2Ot = self.CalcWaterVapourPressure(self.Temp)
        
        # do the diffusion from water vapour depending on the tissue water vapour and gas water vapour pressure
        dH2O = 0.00001 * (pH2Ot - self.Ph2o) * self._t
        if (self.Vol != 0):
            self.Ch2o = ((self.Ch2o * self.Vol) + dH2O) / self.Vol
        
        # as the water vapour also takes volume this is added to the compliance
        if (self.Pres != 0):
        # as dH2O is in mmol/l we have convert it as the gas constant is in mol
            self.Vol += (((self.GasConstant * (273.15 + self.Temp)) / self.Pres) * (dH2O / 1000.0))
    

    def CalcgasComposition(self):
        # calculate CTotal sum of all concentrations
        self.CTotal = self.Ch2o + self.Co2 + self.Cco2 + self.Cn2
        
        # protect against division by zero
        if self.CTotal == 0: return
        
        # calculate the partial pressures
        self.Ph2o = (self.Ch2o / self.CTotal) * self.Pres
        self.Po2 = (self.Co2 / self.CTotal) * self.Pres
        self.Pco2 = (self.Cco2 / self.CTotal) * self.Pres
        self.Pn2 = (self.Cn2 / self.CTotal) * self.Pres

    def CalcWaterVapourPressure(self, temp):
        # calculate the water vapour pressure in air depending on the temperature
        return math.pow(math.e, 20.386 - 5132 / (temp + 273))

    def VolumeIn(self, dvol, modelFrom):
        # increase the volume
        self.Vol += dvol

        # change the gas concentrations
        dCo2 = (modelFrom.Co2 - self.Co2) * dvol
        self.Co2 = ((self.Co2 * self.Vol) + dCo2) / self.Vol

        dCco2 = (modelFrom.Cco2 - self.Cco2) * dvol
        self.Cco2 = ((self.Cco2 * self.Vol) + dCco2) / self.Vol

        dCn2 = (modelFrom.Cn2 - self.Cn2) * dvol
        self.Cn2 = ((self.Cn2 * self.Vol) + dCn2) / self.Vol

        dCh2o = (modelFrom.Ch2o - self.Ch2o) * dvol
        self.Ch2o = ((self.Ch2o * self.Vol) + dCh2o) / self.Vol

        # change temperature due to influx of gas
        dTemp = (modelFrom.Temp - self.Temp) * dvol
        self.Temp = ((self.Temp * self.Vol) + dTemp) / self.Vol

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
