from explain_core.helpers.ModelBaseClass import ModelBaseClass

class MechanicalVentilator(ModelBaseClass):
    # model specific attributes
    InspTime = 0.4
    Freq = 35
    Pip = 20.0
    Peep = 5.0
    InspFlow = 8.0
    ExpFlow = 8.0
    FiO2 = 0.21
    Temp = 37.0
    Ph2O = 47.0
    TidalVolume = 12.0
    TriggerVolume = 1.0

    # local parameters
    _fco2 = 0.0
    _pco2 = 0.0
    _cco2 = 0.0

    _po2 = 0.0
    _co2 = 0.0
    
    

    # override the InitModel of the model base class as this model requires additional initialization
    def InitModel(self, modelEngine):
        # initialize the base class
        ModelBaseClass.InitModel(self, modelEngine)

    def CalcModel(self):
        pass


    