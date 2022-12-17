import math

from explain_core.helpers.AirComposition import SetAirComposition
from explain_core.helpers.ModelBaseClass import ModelBaseClass

class MechanicalVentilator(ModelBaseClass):
    # model specific attributes
    VentInSettings = {}
    TubingSettings = {}
    YPieceSettings = {}
    VentOutSettings = {}
    
    # model independent parameters
    PresAtm = 760.0
    InspTime = 0.4
    Freq = 35
    Pip = 20.0
    Peep = 5.0
    InspFlow = 8.0
    ExpFlow = 3.0
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
    _tubing = {}
    _ypiece = {}
    _insp_valve = {}
    _exp_valve = {}
    _flow_sensor = {}
    _pressure_sensor = {}
    _etco2_sensor = {}

    ic = 1.0

    # override the InitModel of the model base class as this model requires additional initialization
    def InitModel(self, modelEngine):
        # initialize the base class
        ModelBaseClass.InitModel(self, modelEngine)

        # get a reference to all the gas compliances and gas resistors for easy access
        self._ventin = self._modelEngine.Models["VENTIN"]
        self._ventout = self._modelEngine.Models["VENTOUT"]
        self._tubing = self._modelEngine.Models["TUBING"]
        self._ypiece = self._modelEngine.Models["YPIECE"]
        self._insp_valve = self._modelEngine.Models["VENTIN_TUBING"]
        self._exp_valve = self._modelEngine.Models["TUBING_VENTOUT"]
        self._flow_sensor = self._modelEngine.Models["YPIECE_DS"]
        self._pressure_sensor = self._modelEngine.Models["TUBING"]
        self._etco2_sensor = self._modelEngine.Models["YPIECE"]

        self._insp_valve.IsEnabled = True
        self._exp_valve.IsEnabled = True
        self._modelEngine.Models["TUBING_YPIECE"].IsEnabled = True
        self._modelEngine.Models["YPIECE_DS"].IsEnabled = True

        # enable the ventilator and stop the spontaneous breathing for now
        self._modelEngine.Models["Breathing"].IsEnabled = False
        self._modelEngine.Models["MOUTH_DS"].NoFlow = True
        self._modelEngine.Models["MOUTH_DS"].IsEnabled = False

        # initialize the internal reservoir of the mechanical ventilator
        self.SetVentIn()
        
        # initialize the tubing
        self.SetTubing()
        self.SetYPiece()

        # set the expiratory reservoir
        self.SetVentOut()

        # set the inspiratory flow
        self.SetInspFlow(self.InspFlow)

       
        self.IsEnabled = True
        
    
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
        self._insp_valve.NoBackflow = True
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

        # calculate the pressure
        self._ventout.StepModel()

        # calculate the composition
        SetAirComposition(self._ventout, self.VentOutSettings["Humidity"], self.VentOutSettings["Temp"], self.VentOutSettings["Fo2Dry"], self.VentOutSettings["Fco2Dry"], self.VentOutSettings["Fn2Dry"], self.VentOutSettings["FotherDry"])

        # fix the composition as this compartment is continuously refreshed
        self._exp_valve.NoBackflow = True
        self._ventout.FixedComposition = True

    def SetTubing(self):
        # set the humidity, temperature and atmospheric pressure of the tubing
        self._tubing.Humidity = self.Humidity
        self._tubing.Temp = self.Temp
        self._tubing.TargetTemp = self.Temp
        self._tubing.Pres0 = self.PresAtm

        # calculate the volume and unstressed volume of the tubing
        self._tubing.Vol = math.pi * (math.pow(self.TubingSettings["InnerDiameter"], 2) / 4.0) * self.TubingSettings["Length"] * 1000.0
        self._tubing.UVol = self._tubing.Vol
        self._tubing.ElBase = self.TubingSettings["Elastance"]

        # calculate the pressures
        self._tubing.StepModel()

        # set the air composition
        SetAirComposition(self._tubing, self.Humidity, self.Temp, self.Fo2Dry, self.Fco2Dry, self.Fn2Dry, self.FotherDry)

    def CalcModel(self):
        # calculate the expiration time
        self.ExpTime = (60.0 / self.Freq) - self.InspTime

        # has the inspiration time elapsed?
        if (self._insp_timer >= self.InspTime):
            # reset inspiration timer
            self._insp_timer = 0.0
            # signal that the inspiration has ended and the expiration has started
            self.Inspiration = False
            self.ic = 1.0
            self.Expiration = True

            # report the vti
            self.Vt_insp = self._vt_insp_counter
            # reset the vti counter
            self._vt_insp_counter = 0.0
            
        
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
            # reset the volume counter
            self.Volume = 0.0
            

        # increase the timers
        if (self.Inspiration):
            # increase the timer
            self._insp_timer += self._t
            # increase the vti counter
            self._vt_insp_counter += self._flow_sensor.Flow * self._t

        if (self.Expiration):
            self._exp_timer += self._t
            # increase the vte counter
            self._vt_exp_counter += -self._flow_sensor.Flow * self._t


        # store etco2 signal
        self.EtCo2_signal = self._etco2_sensor.Pco2
        self.Flow = self._flow_sensor.Flow * 60.0                                           # convert to l/min
        self.Pressure = (self._modelEngine.Models["YPIECE"].Pres - self.PresAtm) * 1.35951  # convert to cmH2O relative to atmospheric pressure
        self.Volume += (self._flow_sensor.Flow * self._t) * 1000.0                          # convert to ml
        
        # control the in- and expiration valve
        self.InspirationValveControl()
        self.ExpirationValveControl()
        
    def BlowOffPressure(self):
        pres = self._tubingin.Pres
        target_pres = self.Pip + self.PresAtm
        # calculate the volume to lose
        dvol = (pres - target_pres) / self._tubingin.ElBase
        self._tubingin.VolumeOut(dvol)

    def InspirationValveControl(self):
        # if the expiration phase then the inspiration valve closed and we return
        if (self.Inspiration):
            # calculate the inspiratory flow
            res = self.SetInspFlow(self.InspFlow * self.ic)

            # close the expiration valve
            self._exp_valve.NoFlow = True

            # open the inspiration valve
            self._insp_valve.NoFlow = False

            # make sure no backflow can occur
            self._insp_valve.NoBackflow = True

            # # now we have to determine the resistance of the inspiration valve depending on the inspiratory flow setting
            delta = self._pressure_sensor.Pres - self.Pip + self.PresAtm
            
            self.ic = 1.0

            if (self._pressure_sensor.Pres > self.Pip + self.PresAtm):
                self._insp_valve.NoFlow = True

    def ExpirationValveControl(self):
        # if the inspiration phase is running then the expiration valve is closed and we return
        if (self.Expiration):
            # close the inspiration valve
            self._insp_valve.NoFlow = True

            # open the expiration valve
            self._exp_valve.NoFlow = False
            self._exp_valve.RFor = 10.0

            # make sure no backflow can occur
            self._exp_valve.NoBackflow = True

            if (self._pressure_sensor.Pres < self.Peep + self.PresAtm):
                self._exp_valve.NoFlow = True
 


    def SetInspFlow(self, flow):

        # we assume a large pressure difference between the ventilator and the atmospheric pressure
        delta_p = self._modelEngine.Models["VENTIN"].Pres - self._modelEngine.Models["VENTOUT"].Pres

        # flow = dp / R, R = dp / flow
        # calculate flow in l/s 
        flow_ls = flow / 60.0

        # calculate inspiratory valve resistance
        res = (delta_p / flow_ls) - self._exp_valve.RFor

        if (res > 0):
            # set inspiratory valve resistance
            self._insp_valve.RFor = res
            self._insp_valve.RBack = res

        return res








    