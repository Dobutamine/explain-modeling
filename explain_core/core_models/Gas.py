from explain_core.helpers.ModelBaseClass import ModelBaseClass
from explain_core.helpers.AirComposition import SetAirComposition

class Gas(ModelBaseClass):
    # model specific attributes
    DryAir = {}
    HumiditySettings = {}
    TempSettings = {}
    PresAtm = 760.0

    # local parameters
    GasConstant = 62.36367

    def InitModel(self, modelEngine):
        # initialize the base class
        ModelBaseClass.InitModel(self, modelEngine)

        # set the temperatures
        self.SetTemperatures()

        # set the humidities
        self.SetHumidity()

        # initialize the gas compliances holding the inspired air
        self.SetInspiredAir()
        
    def SetTemperatures(self):
        # set the temperatures
        for model, temp in self.TempSettings.items():
            self._modelEngine.Models[model].Temp = temp
            self._modelEngine.Models[model].TargetTemp = temp

    def SetHumidity(self):
        for model, humidity in self.HumiditySettings.items():
            self._modelEngine.Models[model].Humidity = humidity

    def SetInspiredAir(self):
        # initialize the gas compliances holding the inspired air
        for name, model in self._modelEngine.Models.items():
            if (model.ModelType == "GasCompliance"):
                # set the atmospheric pressure
                model.Pres0 = self.PresAtm

                # first calculate the pressures
                model.StepModel()

                # set the inspired air composition to all gas compliances
                SetAirComposition(model, model.Humidity, model.Temp, self.DryAir["Fo2"], self.DryAir["Fco2"], self.DryAir["Fn2"], self.DryAir["Fother"])





