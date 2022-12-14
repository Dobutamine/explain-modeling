import math

from explain_core.core_models.GasCompliance import GasCompliance
from explain_core.core_models.GasResistor import GasResistor
from explain_core.helpers.AirComposition import SetAirComposition

from explain_core.helpers.ModelBaseClass import ModelBaseClass

class MechanicalVentilator(ModelBaseClass):
    # model specific attributes
    VentilatorInsp = {}
    VentilatorExp = {}
    TubingInsp = {}
    TubingExp = {}
    
    PresAtm = 760.0
    InspTime = 0.4
    ExpTime = 1.0
    Freq = 35
    Pip = 20.0
    Peep = 5.0
    InspFlow = 8.0
    ExpFlow = 8.0
    FiO2 = 0.21
    Temp = 37.0
    TidalVolume = 12.0
    TriggerVolume = 1.0
    Inspiration = True
    Expiration = False
    Vt_insp = 0.0
    Vt_exp = 0.0
    EtCo2_signal = 0.0
    EtCo2 = 0.0
    Humidity = 1.0

    # local parameters
    GasConstant = 62.36367
    _insp_timer = 0.0
    _exp_timer = 0.0
    _vt_insp_counter = 0.0
    _vt_exp_counter = 0.0
    _ventin = {}
    _out = {}
    _tubing = {}
    _insp_valve = {}
    _exp_valve = {}
    

    # override the InitModel of the model base class as this model requires additional initialization
    def InitModel(self, modelEngine):
        # initialize the base class
        ModelBaseClass.InitModel(self, modelEngine)

        # get a reference to all the gas compliances and gas resistors for easy access
        self._ventin = self._modelEngine.Models["VENTIN"]
        self._out = self._modelEngine.Models["OUT"]
        self._tubing = self._modelEngine.Models["TUBING"]
        self._insp_valve = self._modelEngine.Models["VENTIN_TUBING"]
        self._exp_valve = self._modelEngine.Models["TUBING_OUT"]

        # initialize the internal reservoir of the mechanical ventilator
        self.SetVentIn()
        
        # initialize the tubing
        self.SetTubing()

        self.SetInspFlow(self.InspFlow)

        #self.SetPeep()

        self.IsEnabled = True
        self._modelEngine.Models["Breathing"].IsEnabled = False
        self._modelEngine.Models["MOUTH_DS"].NoFlow = True
        self._modelEngine.Models["MOUTH_DS"].IsEnabled = False

    
    def SetVentIn(self):
        # set the humidity and temperature of the internal reservoir
        self._ventin.Humidity = self.Humidity
        self._ventin.Temp = self.Temp
        self._ventin.TargetTemp = self.Temp

        # calculate the volume of the internal reservoir
        self._ventin.Vol = (self.VentilatorInsp["InternalPressure"] / self._ventin.ElBase) + self._ventin.UVol

        # calculate the pressure
        self._ventin.StepModel()

        # calculate the composition
        SetAirComposition(self._ventin, self._ventin.Humidity, self._ventin.Temp, self.VentilatorInsp["Fo2Dry"], self.VentilatorInsp["Fco2Dry"], self.VentilatorInsp["Fn2Dry"], self.VentilatorInsp["FotherDry"])

        # fix the composition 
        self._ventin.FixedComposition = True

    def SetTubing(self):
        # set the humidity, temperature and atmospheric pressure of the tubing
        self._tubing.Humidity = self.Humidity
        self._tubing.Temp = self.Temp
        self._tubing.TargetTemp = self.Temp
        self._tubing.Pres0 = self.PresAtm

        # calculate the volume and unstressed volume of the tubing
        self._tubing.Vol = math.pi * (math.pow(self.Tubing["InnerDiameter"], 2) / 4.0) * self.Tubing["Length"] * 1000.0
        self._tubing.UVol = self._tubing.Vol

        # set the elastance of the tubing
        self._tubing.ElBase = self.Tubing["Elastance"]

        # calculate the pressures
        self._tubing.StepModel()

        # set the air composition
        SetAirComposition(self._tubing, self._tubing.Humidity, self._tubing.Temp, self.VentilatorInsp["Fo2Dry"], self.VentilatorInsp["Fco2Dry"], self.VentilatorInsp["Fn2Dry"], self.VentilatorInsp["FotherDry"])
  

    def CalcModel(self):
        # calculate the expiration time
        self.ExpTime = (60.0 / self.Freq) - self.InspTime

        # has the inspiration time elapsed?
        if (self._insp_timer > self.InspTime):
            # reset inspiration timer
            self._insp_timer = 0.0
            # signal that the inspiration has ended and the expiration has started
            self.Inspiration = False
            self.Expiration = True
            # report the vti
            self.Vt_insp = self._vt_insp_counter
            # reset the vti counter
            self._vt_insp_counter = 0.0
            # close the inspiration valve and open the expiration valve
            self._insp_valve.NoFlow = True
            self._exp_valve.NoFlow = False
        
        # has the expiration time elapsed
        if (self._exp_timer > self.ExpTime):
            # reset the expiration timer
            self._exp_timer = 0.0
            # signal that the expiration has ended and the inspiration has started
            self.Inspiration = True
            self.Expiration = False
            # report the vte
            self.Vt_exp = self._vt_exp_counter
             # report the end tidal co2
            self.EtCo2 = self._modelEngine.Models["DS"].Pco2
            # reset the vti counter
            self._vt_exp_counter = 0.0
            # open the inspiration valve and close the expiration valve
            self._insp_valve.NoFlow = False
            self._exp_valve.NoFlow = True

        # increase the timers
        if (self.Inspiration):
            # increase the timer
            self._insp_timer += self._t
            # increase the vti counter
            self._vt_insp_counter += self._modelEngine.Models["TUBING_DS"].Flow * self._t
            # guard the pressures
            if (self._modelEngine.Models["TUBING"].Pres > self.PresAtm + self.Pip):
                # pressure exceeed so close the inspiration valve
                self._insp_valve.NoFlow = True
            else: 
                self._insp_valve.NoFlow = False

        if (self.Expiration):
            self._exp_timer += self._t
            # increase the vte counter
            self._vt_exp_counter += self._modelEngine.Models["TUBING_DS"].Flow * self._t

        # store etco2 signal
        self.EtCo2_signal = self._modelEngine.Models["DS"].Pco2

    def SetInspFlow(self, flow):
        self.InspFlow = flow

        # we assume a large pressure difference between the ventilator and the atmospheric pressure
        delta_p = self._modelEngine.Models["VENTIN"].Pres - self._modelEngine.Models["OUT"].Pres

        # flow = dp / R, R = dp / flow
        # calculate flow in l/s 
        flow_ls = flow / 60.0

        # calculate inspiratory valve resistance
        res = delta_p / flow_ls

        # set inspiratory valve resistance
        self._insp_valve.RFor = res
        self._insp_valve.RBack = res


    def SetPeep(self, peep):
        self.Peep = peep
        self._modelEngine.Models["OUT"].Vol = (self.Peep / self._modelEngine.Models["OUT"].ElBase) + self._modelEngine.Models["OUT"].UVol













    