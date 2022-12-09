from explain_core.core_models.ModelBaseClass import ModelBaseClass

class Gas(ModelBaseClass):
    # model specific attributes
    InspiredAir = {}
    TempSettings = {}
    PresAtm = 760.0

    # local parameters
    GasConstant = 62.36367
    _inspAirModels = []


    def InitModel(self, modelEngine):
        # initialize the base class
        ModelBaseClass.InitModel(self, modelEngine)

        # set the temperatures
        self.SetTemperatures()

        # initialize the gas compliances holding the inspired air
        self.SetInspiredAir()
        
    def SetTemperatures(self):
        # set the temperatures
        for model, temp in self.TempSettings.items():
            self._modelEngine.Models[model].Temp = temp
            self._modelEngine.Models[model].TargetTemp = temp

    def SetInspiredAir(self):
        # initialize the gas compliances holding the inspired air
        for insp_model in self.InspiredAir["Models"]:
            # get a reference to the model which is going to hold the inspired air
            inspAirModel = self._modelEngine.Models[insp_model]

            # set the atmospheric pressure 
            inspAirModel.Pres0 = self.PresAtm

            # calculate the pressure in the inspired air compliance, should be pAtm
            inspAirModel.StepModel()

            # calculate the concentration at this pressure and temperature in mmol/l !
            inspAirModel.CTotal = (inspAirModel.Pres / (self.GasConstant * (273.15 + inspAirModel.Temp))) * 1000.0

            # set the inspired air fractions
            inspAirModel.Fh2O = self.InspiredAir["Fh2O"]
            inspAirModel.Fo2 = self.InspiredAir["Fo2"]
            inspAirModel.Fco2 = self.InspiredAir["Fco2"]
            inspAirModel.Fn2 = self.InspiredAir["Fn2"]

            # calculate the inspired air concentrations
            inspAirModel.Ch2O = inspAirModel.Fh2O * inspAirModel.CTotal
            inspAirModel.Co2 = inspAirModel.Fo2 * inspAirModel.CTotal
            inspAirModel.Cco2 = inspAirModel.Fco2 * inspAirModel.CTotal
            inspAirModel.Cn2 = inspAirModel.Fn2 * inspAirModel.CTotal

            # calculate the inspired air partial pressures
            inspAirModel.Ph2O = inspAirModel.Fh2O * inspAirModel.Pres
            inspAirModel.Po2 = inspAirModel.Fo2 * inspAirModel.Pres
            inspAirModel.Pco2 = inspAirModel.Fco2 * inspAirModel.Pres
            inspAirModel.Pn2 = inspAirModel.Fn2 * inspAirModel.Pres
        
            





