import math

from explain_core.core_models.GasCompliance import GasCompliance
from explain_core.core_models.GasResistor import GasResistor
from explain_core.helpers.AirComposition import SetAirComposition

from explain_core.helpers.ModelBaseClass import ModelBaseClass

class MechanicalVentilator(ModelBaseClass):
    # model specific attributes
    VentInSettings = {}
    TubingInSettings = {}
    YPieceSettings = {}
    TubingOutSettings = {}
    VentOutSettings = {}
    
    # model independent parameters
    PresAtm = 760.0
    InspTime = 0.4
    Freq = 35
    Pip = 20.0
    Peep = 5.0
    InspFlow = 8.0
    Temp = 37.0
    Humidity = 1.0
    GasConstant = 62.36367

    # model dependent parameters
    Inspiration = True
    Expiration = False
    Vt_insp = 0.0
    Vt_exp = 0.0
    EtCo2_signal = 0.0
    EtCo2 = 0.0
    ExpTime = 1.0
    Flow = 0.0
    Pressure = 0.0
    Volume = 0.0
    Fo2Dry = 0.0
    Fco2Dry = 0.0
    Fn2Dry = 0.0
    FotherDry = 0.0
    
    # local parameters
    _insp_timer = 0.0
    _exp_timer = 0.0
    _vt_insp_counter = 0.0
    _vt_exp_counter = 0.0
    _ventin = {}
    _ventout = {}
    _tubingin = {}
    _ypiece = {}
    _tubingout = {}
    _insp_valve = {}
    _exp_valve = {}
    _flow_sensor = {}
    _pressure_sensor = {}
    _etco2_sensor = {}
    
    # override the InitModel of the model base class as this model requires additional initialization
    def InitModel(self, modelEngine):
        # initialize the base class
        ModelBaseClass.InitModel(self, modelEngine)

        # get a reference to all the gas compliances and gas resistors for easy access
        self._ventin = self._modelEngine.Models["VENTIN"]
        self._ventout = self._modelEngine.Models["VENTOUT"]
        self._tubingin = self._modelEngine.Models["TUBINGIN"]
        self._ypiece = self._modelEngine.Models["YPIECE"]
        self._tubingout = self._modelEngine.Models["TUBINGOUT"]
        self._insp_valve = self._modelEngine.Models["VENTIN_TUBINGIN"]
        self._exp_valve = self._modelEngine.Models["TUBINGOUT_VENTOUT"]
        self._flow_sensor = self._modelEngine.Models["YPIECE_DS"]
        self._pressure_sensor = self._modelEngine.Models["YPIECE"]
        self._etco2_sensor = self._modelEngine.Models["YPIECE"]

        # initialize the internal reservoir of the mechanical ventilator
        self.SetVentIn()
        
        # initialize the tubing
        self.SetTubingIn()
        self.SetYPiece()
        self.SetTubingOut()

        # set the expiratory reservoir
        self.SetVentOut()

        # calculate the insp valve resistance
        self.SetInspFlow()

        self.IsEnabled = True
        self._modelEngine.Models["Breathing"].IsEnabled = False
        self._modelEngine.Models["MOUTH_DS"].NoFlow = True
        self._modelEngine.Models["MOUTH_DS"].IsEnabled = False

    
    def SetYPiece(self):
        # set the humidity and temperature of the internal reservoir
        self._ypiece.Humidity = self.Humidity
        self._ypiece.Temp = self.Temp
        self._ypiece.TargetTemp = self.Temp
        self._ypiece.Pres0 = self.PresAtm
        
        # set the mechanical properties
        self._ypiece.Vol = self.YPieceSettings["Volume"]
        self._ypiece.UVol = self.YPieceSettings["Volume"]
        self._ypiece.ElBase = self.YPieceSettings["Elastance"]

        # calculate the pressure
        self._ypiece.StepModel()

        # calculate the composition
        SetAirComposition(self._ypiece, self.Humidity, self.Temp, self.Fo2Dry, self.Fco2Dry, self.Fn2Dry, self.FotherDry)


    def SetVentIn(self):
        # set the humidity and temperature of the internal reservoir
        self._ventin.Humidity = self.Humidity
        self._ventin.Temp = self.Temp
        self._ventin.TargetTemp = self.Temp
        self._ventin.Pres0 = self.PresAtm
        
        # set the mechanical properties
        self._ventin.UVol = self.VentInSettings["Volume"]
        self._ventin.ElBase = self.VentInSettings["Elastance"]

        # calculate the volume of the internal reservoir to reach the desired internal pressure
        self._ventin.Vol = (self.VentInSettings["InternalPressure"] / self._ventin.ElBase) + self._ventin.UVol

        # calculate the pressure
        self._ventin.StepModel()

        # calculate the composition
        SetAirComposition(self._ventin, self.Humidity, self.Temp, self.Fo2Dry, self.Fco2Dry, self.Fn2Dry, self.FotherDry)

        # fix the composition as this compartment is continuously refreshed
        self._ventin.FixedComposition = True

    def SetVentOut(self):
        # set the humidity and temperature of the internal reservoir
        self._ventout.Humidity = self.Humidity
        self._ventout.Temp = self.Temp
        self._ventout.TargetTemp = self.Temp
        self._ventout.Pres0 = self.PresAtm
        
        # set the mechanical properties
        self._ventout.Vol = self.VentOutSettings["Volume"]
        self._ventout.UVol = self.VentOutSettings["Volume"]
        self._ventout.ElBase = self.VentOutSettings["Elastance"]

        # calculate the volume of the internal reservoir to reach the desired internal pressure
        self._ventout.Vol = (self.Peep / self._ventout.ElBase) + self._ventout.UVol

        # calculate the pressure
        self._ventout.StepModel()

        # calculate the composition
        SetAirComposition(self._ventout, self.VentOutSettings["Humidity"], self.VentOutSettings["Temp"], self.VentOutSettings["Fo2Dry"], self.VentOutSettings["Fco2Dry"], self.VentOutSettings["Fn2Dry"], self.VentOutSettings["FotherDry"])

        # fix the composition as this compartment is continuously refreshed
        self._ventout.FixedComposition = True


    def SetTubingIn(self):
        # set the humidity, temperature and atmospheric pressure of the tubing
        self._tubingin.Humidity = self.Humidity
        self._tubingin.Temp = self.Temp
        self._tubingin.TargetTemp = self.Temp
        self._tubingin.Pres0 = self.PresAtm

        # calculate the volume and unstressed volume of the tubing
        self._tubingin.Vol = math.pi * (math.pow(self.TubingInSettings["InnerDiameter"], 2) / 4.0) * self.TubingInSettings["Length"] * 1000.0
        self._tubingin.UVol = self._tubingin.Vol
        self._tubingin.ElBase = self.TubingInSettings["Elastance"]

        # calculate the pressures
        self._tubingin.StepModel()

        # set the air composition
        SetAirComposition(self._tubingin, self.Humidity, self.Temp, self.Fo2Dry, self.Fco2Dry, self.Fn2Dry, self.FotherDry)
  
    def SetTubingOut(self):
        # set the humidity, temperature and atmospheric pressure of the tubing
        self._tubingout.Humidity = self.Humidity
        self._tubingout.Temp = self.Temp
        self._tubingout.TargetTemp = self.Temp
        self._tubingout.Pres0 = self.PresAtm

        # calculate the volume and unstressed volume of the tubing
        self._tubingout.Vol = math.pi * (math.pow(self.TubingOutSettings["InnerDiameter"], 2) / 4.0) * self.TubingOutSettings["Length"] * 1000.0
        self._tubingout.UVol = self._tubingout.Vol
        self._tubingout.ElBase = self.TubingOutSettings["Elastance"]

        # calculate the pressures
        self._tubingout.StepModel()

        # set the air composition
        SetAirComposition(self._tubingout, self.Humidity, self.Temp, self.Fo2Dry, self.Fco2Dry, self.Fn2Dry, self.FotherDry)

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
            self.EtCo2 = self._etco2_sensor.Pco2
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
            self._vt_insp_counter += self._flow_sensor.Flow * self._t
            # guard the pressures
            if (self._pressure_sensor.Pres > self.PresAtm + self.Pip):
                # pressure exceeed so close the inspiration valve
                self._insp_valve.NoFlow = True
            else: 
                self._insp_valve.NoFlow = False

        if (self.Expiration):
            self._exp_timer += self._t
            # increase the vte counter
            self._vt_exp_counter += -self._flow_sensor.Flow * self._t

        # store etco2 signal
        self.EtCo2_signal = self._etco2_sensor.Pco2
        self.Flow = self._flow_sensor.Flow
        self.Pressure = self._pressure_sensor.Pres
        self.Volume += self._flow_sensor.Flow

    def SetInspFlow(self):

        # we assume a large pressure difference between the ventilator and the atmospheric pressure
        delta_p = self._modelEngine.Models["VENTIN"].Pres - self._modelEngine.Models["VENTOUT"].Pres

        # flow = dp / R, R = dp / flow
        # calculate flow in l/s 
        flow_ls = self.InspFlow / 60.0

        # calculate inspiratory valve resistance
        res = (delta_p / flow_ls) - 2 * self._modelEngine.Models["YPIECE_DS"].RFor  - self._modelEngine.Models["TUBINGIN_YPIECE"].RFor - self._modelEngine.Models["YPIECE_TUBINGOUT"].RFor - self._modelEngine.Models["TUBINGOUT_VENTOUT"].RFor

        print(res)
        # set inspiratory valve resistance
        self._insp_valve.RFor = res
        self._insp_valve.RBack = res


    def SetPeep(self):
        # calculate the volume of the internal reservoir to reach the desired internal pressure
        self._ventout.Vol = ((self.Peep + self.PresAtm) / self._ventout.ElBase) + self._ventout.UVol

        # calculate the pressure
        self._ventout.StepModel()

        # calculate the composition
        SetAirComposition(self._ventout, self.VentOutSettings["Humidity"], self.VentOutSettings["Temp"], self.VentOutSettings["Fo2Dry"], self.VentOutSettings["Fco2Dry"], self.VentOutSettings["Fn2Dry"], self.VentOutSettings["FotherDry"])














    