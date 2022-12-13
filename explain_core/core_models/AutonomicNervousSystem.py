from explain_core.helpers.ModelBaseClass import ModelBaseClass
from explain_core.helpers.ActivationFunction import ActivationFunction

class AutonomicNervousSystem(ModelBaseClass):
    # model specific attributes
    BaroreceptorLocation = "AA"
    ChemoreceptorLocation = "AA"
    UpdateInterval = 0.015
    
    SetBaro = 53
    MinBaro = 30
    MaxBaro = 76
    TcHpBaro = 2.0
    TcContBaro = 2.0
    TcResBaro = 2.0
    TcUvolBaro = 2.0
    GHpBaro = 0.0217
    GContBaro = 1.0
    GResBaro = 1.0
    GUvolBaro = 1.0
    
    SetPo2 = 80
    MinPo2 = 30
    MaxPo2 = 150
    TcVePo2 = 2.0
    GVePo2 = 0.0
    TcHpPo2 = 2.0
    GHpPo2 = 0.0
      
    SetPco2 = 40
    MinPco2 = 25
    MaxPco2 = 75
    TcVePco2 = 2.0
    GVePco2 = 0.02
    TcHpPco2 = 2.0
    GHpPco2 = 0.0
    
    SetPh = 7.4
    MinPh = 6.9
    MaxPh = 7.7
    TcVePh = 2.0
    GVePh = -2.0
    
    SetLungStretch = 53
    MinLungStretch = 53
    MaxLungStretch = 53
    TcVeLungStretch = 2.0
    GVeLungStretch = 0.0
    
    HeartModelName = "Heart"
    BreathingModelName = "Breathing"
    LungCompartments = ["ALL", "ALR"]
    SystemicResistors = []
    UnstressedVolumes = []

    # local parameters
    _baroreceptor = {}
    _chemoreceptor = {}
    _heart = {}
    _breathing = {}
    _systemic_resistors = {}
    _unstressed_volumes = {}
    _hpBaroActivationFunction = {}
    _hpPo2ActivationFunction = {}
    _hpPco2ActivationFunction = {}
    _vePo2ActivationFunction = {}
    _vePco2ActivationFunction = {}
    _vePhActivationFunction = {}
    _veLungStretchActivationFunction = {}
    _update_timer = 0.0

    def InitModel(self, modelEngine):
        # initialize the base class
        ModelBaseClass.InitModel(self, modelEngine)

        # find the input sites
        self._baroreceptor = self._modelEngine.Models[self.BaroreceptorLocation]
        self._chemoreceptor = self._modelEngine.Models[self.ChemoreceptorLocation]

        # initialize the controller which controls the heart period using the baro receptor
        self._hpBaroActivationFunction = ActivationFunction(self.SetBaro, self.MinBaro, self.MaxBaro, self.GHpBaro, self.TcHpBaro, self.UpdateInterval)

        # initialize the controller which controls the heart period using the po2
        self._hpPo2ActivationFunction = ActivationFunction(self.SetPo2, self.MinPo2, self.MaxPo2, self.GHpPo2, self.TcHpPo2, self.UpdateInterval)

        # initialize the controller which controls the heart period using the pco2
        self._hpPco2ActivationFunction = ActivationFunction(self.SetPco2, self.MinPco2, self.MaxPco2, self.GHpPco2, self.TcHpPco2, self.UpdateInterval)

        # initialize the controller which controls the exhaled minute volume by the pco2
        self._vePco2ActivationFunction = ActivationFunction(self.SetPco2, self.MinPco2, self.MaxPco2, self.GVePco2, self.TcVePco2, self.UpdateInterval)

        # initialize the controller which controls the exhaled minute volume by the po2
        self._vePo2ActivationFunction = ActivationFunction(self.SetPo2, self.MinPo2, self.MaxPo2, self.GVePo2, self.TcVePo2, self.UpdateInterval)

        # initialize the controller which controls the exhaled minute volume by the pco2
        self._vePco2ActivationFunction = ActivationFunction(self.SetPco2, self.MinPco2, self.MaxPco2, self.GVePco2, self.TcVePco2, self.UpdateInterval)

        # initialize the controller which controls the exhaled minute volume by the pH
        self._vePhActivationFunction = ActivationFunction(self.SetPh, self.MinPh, self.MaxPh, self.GVePh, self.TcVePh, self.UpdateInterval)

        # initialize the controller which controls the exhaled minute volume by the lung stretch receptor
        self._veLungStretchActivationFunction = ActivationFunction(self.SetLungStretch, self.MinLungStretch, self.MaxLungStretch, self.GVeLungStretch, self.TcVeLungStretch, self.UpdateInterval)

        # find the effector sites
        self._heart = self._modelEngine.Models[self.HeartModelName]
        self._breathing = self._modelEngine.Models[self.BreathingModelName]

    def CalcModel(self):
        # the autonomic nervous system updates slower for performance reasons
        if (self._update_timer > self.UpdateInterval):
            # reset the update timer
            self._update_timer = 0.0
            # do the calculations
            self.CalcAutonomicControl()
        
        # increase the update timer
        self._update_timer += self._t
    
    def CalcAutonomicControl(self):
        # calculate the acid base and oxygenation properties of chemoreceptor site
        ab = self._modelEngine.AcidBase.calc_acid_base(self._baroreceptor.Tco2)
        oxy = self._modelEngine.Oxygenation.calc_oxygenation(self._baroreceptor.To2)

        # store the results of the calculations
        if (not oxy.Error):
            self._chemoreceptor.Po2 = oxy.Po2
            self._chemoreceptor.So2 = oxy.So2
            
        if (not ab.Error):
            self._chemoreceptor.Pco2 = ab.Pco2
            self._chemoreceptor.Ph = ab.Ph

        # calculate the mean. In neonates the most accurate mean is given by MAP = DBP + (0.466 * (SBP-DBP))
        # map = _baroreceptor.PresMin  + 0.466 * (_baroreceptor.PresMax - _baroreceptor.PresMin);
        map = self._baroreceptor.Pres

        # get the lung volume for the lung stretch receptor
        lung_volume = 0.0
        for lc in self.LungCompartments:
            lung_volume += self._modelEngine.Models[lc].Vol

        # calculate the effect of the mean arterial pressure, po2, pco2 and pH on the heart period.
        self._heart.HeartPeriodChangeAns = self._hpBaroActivationFunction.Update(map) \
                                         + self._hpPo2ActivationFunction.Update(self._baroreceptor.Po2) \
                                         + self._hpPco2ActivationFunction.Update(self._baroreceptor.Pco2)

        # calculate the effect of the po2, pco2, pH and lung stretch on the exhaled minute volume
        self._breathing.TargetMinuteVolume = self._breathing.RefMinuteVolume \
                                           + self._vePhActivationFunction.Update(self._chemoreceptor.Ph) \
                                           + self._vePco2ActivationFunction.Update(self._chemoreceptor.Pco2) \
                                           + self._vePo2ActivationFunction.Update(self._chemoreceptor.Po2) \
                                           + self._veLungStretchActivationFunction.Update(lung_volume) 

        if (self._breathing.TargetMinuteVolume <= 0):
            self._breathing.TargetMinuteVolume = 0