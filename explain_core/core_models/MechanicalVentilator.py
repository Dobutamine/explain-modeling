import math

from explain_core.core_models.GasCompliance import GasCompliance
from explain_core.core_models.GasResistor import GasResistor

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

    # local parameters
    GasConstant = 62.36367
    _insp_timer = 0.0
    _exp_timer = 0.0
    _vt_insp_counter = 0.0
    _vt_exp_counter = 0.0
    _ventin = {}
    _out = {}
    _tubinginsp = {}
    _tubingexp = {}
    

    # override the InitModel of the model base class as this model requires additional initialization
    def InitModel(self, modelEngine):
        # initialize the base class
        ModelBaseClass.InitModel(self, modelEngine)

        # get a reference to all the gas compliances and gas resistors for easy access
        self._ventin = self._modelEngine.Models["VENTIN"]
        self._out = self._modelEngine.Models["OUT"]
        self._tubinginsp = self._modelEngine.Models["TUBINGINSP"]
        self._tubingexp = self._modelEngine.Models["TUBINGEXP"]

        # initialize the internal reservoir of the mechanical ventilator
        self.SetVentIn()

        # initialize the tubing

        # initialize the outside air
    
    def SetVentIn(self):
        # calculate the desired volume in internal reservoir depending on the internal pressure parameter and reservoir a elastance of 1000 mmHg/l and a reservoir unstressed volume of 5 liters
        self._ventin.Vol = self.VentilatorInsp["InternalPressure"] / self._ventin.ElBase + self._ventin.UVol

        # set the Pres0 to the atmospheric pressure 
        self._ventin.Pres0 = self.PresAtm

        # set the temperatures
        self._ventin.Temp = self.VentilatorInsp["Temp"]
        self._ventin.TargetTemp = self.VentilatorInsp["Temp"]

        # calculate the pressure
        self._ventin.StepModel()

        # calculate the concentration at this pressure and temperature in mmol/l !
        self._ventin.CTotal = (self._ventin.Pres / (self.GasConstant * (273.15 + self._ventin.Temp))) * 1000.0

        # calculate the water vapour pressure fraction at this temperature when fully humidified
        fh2o = (self.VentilatorInsp["Humidity"] * self.CalcWaterVapourPressure(self._ventin.Temp)) / self._ventin.Pres

        # set the inspired air fractions
        # self._ventin.Fh2O = self.VentilatorInsp["Fh2O"]
        # self._ventin.Fo2 = self.VentilatorInsp["Fo2"]
        # self._ventin.Fco2 = self.VentilatorInsp["Fco2"]
        # self._ventin.Fn2 = self.VentilatorInsp["Fn2"]

        # # calculate the inspired air concentrations
        # self._ventin.Ch2O = self._ventin.Fh2O * self._ventin.CTotal
        # self._ventin.Co2 = self._ventin.Fo2 * self._ventin.CTotal
        # self._ventin.Cco2 = self._ventin.Fco2 * self._ventin.CTotal
        # self._ventin.Cn2 = self._ventin.Fn2 * self._ventin.CTotal

        # # calculate the inspired air partial pressures
        # self._ventin.Ph2O = self._ventin.Fh2O * self._ventin.Pres
        # self._ventin.Po2 = self._ventin.Fo2 * self._ventin.Pres
        # self._ventin.Pco2 = self._ventin.Fco2 * self._ventin.Pres
        # self._ventin.Pn2 = self._ventin.Fn2 * self._ventin.Pres



    def SetVentOut(self):
        pass

    def SetTubingInsp(self):
        pass

    def SetTubingExp(self):
        pass

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
            self._modelEngine.Models["VENTIN_YPIECE"].NoFlow = True
            self._modelEngine.Models["YPIECE_VENTOUT"].NoFlow = False
        
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
            self._modelEngine.Models["VENTIN_YPIECE"].NoFlow = False
            self._modelEngine.Models["YPIECE_VENTOUT"].NoFlow = True

        # increase the timers
        if (self.Inspiration):
            # increase the timer
            self._insp_timer += self._t
            # increase the vti counter
            self._vt_insp_counter += self._modelEngine.Models["VENTIN_YPIECE"].Flow * self._t
            # guard the pressures
            if (self._modelEngine.Models["YPIECE"].Pres > self.PresAtm + self.Pip):
                # pressure exceeed so close the inspiration valve
                self._modelEngine.Models["VENTIN_YPIECE"].NoFlow = True
            else: 
                self._modelEngine.Models["VENTIN_YPIECE"].NoFlow = False

        if (self.Expiration):
            self._exp_timer += self._t
            # increase the vte counter
            self._vt_exp_counter += self._modelEngine.Models["YPIECE_VENTOUT"].Flow * self._t

        # store etco2 signal
        self.EtCo2_signal = self._modelEngine.Models["DS"].Pco2

    def SetInspFlow(self, flow):
        self.InspFlow = flow

        # we assume a large pressure difference between the ventilator and the atmospheric pressure
        delta_p = self._modelEngine.Models["VENTIN"].Pres - self.PresAtm

        # flow = dp / R, R = dp / flow
        # calculate flow in l/s 
        flow_ls = flow / 60.0

        # calculate inspiratory valve resistance
        res = delta_p / flow_ls

        # set inspiratory valve resistance
        self._modelEngine.Models["VENTIN_YPIECE"].RFor = res
        self._modelEngine.Models["VENTIN_YPIECE"].RBack = res


    def SetPeep(self, peep):
        self.Peep = peep
        self._modelEngine.Models["VENTOUT"].Vol = (self.Peep / self._modelEngine.Models["VENTOUT"].ElBase) + self._modelEngine.Models["VENTOUT"].UVol

    def SetOutsideAir(self):
        # get a reference to the model which is going to hold the inspired air
        vent_out = self._modelEngine.Models["VENTOUT"]

        vent_out.Temp = self.TempOut
        vent_out.TargetTemp = self.TempOut

        # set the atmospheric pressure 
        vent_out.Pres0 = self.PresAtm

        # set PEEP
        self.SetPeep(self.Peep)
        
        # calculate the pressure in the inspired air compliance, should be pAtm
        vent_out.StepModel()

        # calculate the concentration at this pressure and temperature in mmol/l !
        vent_out.CTotal = (vent_out.Pres / (self.GasConstant * (273.15 + vent_out.Temp))) * 1000.0

        # set the inspired air fractions
        vent_out.Fh2O = self.VentAirOut["Fh2O"]
        vent_out.Fo2 = self.VentAirOut["Fo2"]
        vent_out.Fco2 = self.VentAirOut["Fco2"]
        vent_out.Fn2 = self.VentAirOut["Fn2"]

        # calculate the inspired air concentrations
        vent_out.Ch2O = vent_out.Fh2O * vent_out.CTotal
        vent_out.Co2 = vent_out.Fo2 * vent_out.CTotal
        vent_out.Cco2 = vent_out.Fco2 * vent_out.CTotal
        vent_out.Cn2 = vent_out.Fn2 * vent_out.CTotal

        # calculate the inspired air partial pressures
        vent_out.Ph2O = vent_out.Fh2O * vent_out.Pres
        vent_out.Po2 = vent_out.Fo2 * vent_out.Pres
        vent_out.Pco2 = vent_out.Fco2 * vent_out.Pres
        vent_out.Pn2 = vent_out.Fn2 * vent_out.Pres



    def CalcWaterVapourPressure(self, temp):
        # calculate the water vapour pressure in air depending on the temperature and 100% relative humidity
        return math.pow(math.e, 20.386 - 5132 / (temp + 273))


    