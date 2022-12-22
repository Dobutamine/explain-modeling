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
    VtSet = 0.015
    Pip = 20.0
    PipMax = 30.0
    Peep = 5.0
    InspFlow = 8.0
    ExpFlow = 3.0
    Temp = 37.0
    Humidity = 1.0
    GasConstant = 62.36367
    VolumeGuaranteed = False

    # model dependent parameters
    Inspiration = True
    Expiration = False
    VtInsp = 0.0
    VtExp = 0.0
    EtCo2_signal = 0.0
    EtCo2 = 0.0
    ExpTime = 1.0
    Flow = 0.0
    Pres = 0.0
    Vol = 0.0
    Fo2Dry = 0.0
    Fco2Dry = 0.0
    Fn2Dry = 0.0
    FotherDry = 0.0
    EtRes = 37.9

    # local parameters
    _insp_timer = 0.0
    _exp_timer = 0.0
    _vt_insp_counter = 0.0
    _vt_exp_counter = 0.0
    _ventin = {}
    _ventout = {}
    _tubingin = {}
    _tubingout = {}
    _ypiece = {}
    _insp_valve = {}
    _exp_valve = {}
    _flow_sensor = {}
    _pressure_sensor = {}
    _internal_pressure_sensor = {}
    _internal_volume_counter = 0
    _etco2_sensor = {}
    _insp_valve_flow_reduction = 1.0


    # override the InitModel of the model base class as this model requires additional initialization
    def InitModel(self, modelEngine):
        # initialize the base class
        ModelBaseClass.InitModel(self, modelEngine)

        # get a reference to all the gas compliances and gas resistors for easy access
        self._ventin = self._modelEngine.Models["VENTIN"]
        self._ventout = self._modelEngine.Models["VENTOUT"]
        self._tubingin = self._modelEngine.Models["TUBINGIN"]
        self._tubingout = self._modelEngine.Models["TUBINGOUT"]
        self._ypiece = self._modelEngine.Models["YPIECE"]
        self._insp_valve = self._modelEngine.Models["VENTIN_TUBINGIN"]
        self._exp_valve = self._modelEngine.Models["TUBINGOUT_VENTOUT"]
        self._flow_sensor = self._modelEngine.Models["YPIECE_DS"]
        self._pressure_sensor = self._modelEngine.Models["YPIECE"]
        self._internal_pressure_sensor = self._modelEngine.Models["TUBINGIN"]
        self._internal_flow_sensor = self._modelEngine.Models["VENTIN_TUBINGIN"]
        self._etco2_sensor = self._modelEngine.Models["DS"]

        # initialize the internal reservoir of the mechanical ventilator
        self.SetVentIn()
        
        # initialize the tubing 
        self.SetTubing()

        # initialize the Y-piece
        self.SetYPiece()

        # set the expiratory reservoir
        self.SetVentOut()

        # set the initial state of the in- and expiratory valves
        self.PressureLimited()
    
    def SwitchVentilator(self, state):
        # turn on or turn off the ventilator
        if state:
            self.IsEnabled = True
            self._modelEngine.Models["YPIECE_DS"].IsEnabled = True
            self._modelEngine.Models["YPIECE_DS"].NoFlow = False
        else:
            self.IsEnabled = False
            self._modelEngine.Models["YPIECE_DS"].IsEnabled = False
            self._modelEngine.Models["YPIECE_DS"].NoFlow = True


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
        self._tubingin.Humidity = self.Humidity
        self._tubingin.Temp = self.Temp
        self._tubingin.TargetTemp = self.Temp
        self._tubingin.Pres0 = self.PresAtm

        # calculate the volume and unstressed volume of the tubing
        self._tubingin.Vol = math.pi * (math.pow(self.TubingSettings["InnerDiameter"], 2) / 4.0) * self.TubingSettings["Length"] * 1000.0
        self._tubingin.UVol = self._tubingin.Vol
        self._tubingin.ElBase = self.TubingSettings["Elastance"]

        # calculate the pressures
        self._tubingin.StepModel()

        # set the air composition
        SetAirComposition(self._tubingin, self.Humidity, self.Temp, self.Fo2Dry, self.Fco2Dry, self.Fn2Dry, self.FotherDry)

        # set the humidity, temperature and atmospheric pressure of the tubing
        self._tubingout.Humidity = self.Humidity
        self._tubingout.Temp = self.Temp
        self._tubingout.TargetTemp = self.Temp
        self._tubingout.Pres0 = self.PresAtm

        # calculate the volume and unstressed volume of the tubing
        self._tubingout.Vol = math.pi * (math.pow(self.TubingSettings["InnerDiameter"], 2) / 4.0) * self.TubingSettings["Length"] * 1000.0
        self._tubingout.UVol = self._tubingout.Vol
        self._tubingout.ElBase = self.TubingSettings["Elastance"]

        # calculate the pressures
        self._tubingout.StepModel()

        # set the air composition
        SetAirComposition(self._tubingout, self.Humidity, self.Temp, self.Fo2Dry, self.Fco2Dry, self.Fn2Dry, self.FotherDry)

    def CalcModel(self):
        # calculate the expiration time
        self.ExpTime = (60.0 / self.Freq) - self.InspTime

        # has the inspiration time elapsed?
        if (self._insp_timer >= self.InspTime):
            # reset inspiration timer
            self._insp_timer = 0.0
            # signal that the inspiration has ended and the expiration has started
            self.Inspiration = False
            self.Expiration = True
            # report the vti
            self.VtInsp = self._vt_insp_counter
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
            self.VtExp = self._vt_exp_counter
            # change pip when in prvc mode
            if (self.VolumeGuaranteed):
                self.PressureRegulatedVolumeControl()
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
        self.Pres = (self._pressure_sensor.Pres - self.PresAtm) * 1.35951  # convert to cmH2O relative to atmospheric pressure
        self.Vol += (self._flow_sensor.Flow * self._t) * 1000.0                          # convert to ml
        
        # calculate the endotracheal tube resistance
        self.EtTubeResistance(self.Flow)
 
        self.PressureLimited()
        
    def EtTubeResistance(self, flow):
        res5 = 37.9
        res10 = 57.3

        a = (10.0 - 5.0) / ((res10 - res5) * 0.735559)
        b = res5 * 0.735559 - a * 5.0

        if abs(flow) < 0.5:
            flow = 0.5

        self.EtRes = abs(flow) * a + b

        self._modelEngine.Models["YPIECE_DS"].RFor = self.EtRes
        self._modelEngine.Models["YPIECE_DS"].RBack = self.EtRes

    def PressureRegulatedVolumeControl(self):
        # is the tidal volume reached
        if (self.VtExp > self.VtSet + 0.001):
            # decrease pip 
            self.Pip -= 1.0
            # guard against too low pip
            if ((self.Pip - self.Peep) < 4.0):
                self.Pip = self.Peep + 4.0
        if (self.VtExp < self.VtSet - 0.001):
            # increase pip
            self.Pip += 1.0
            # guard against too high pip
            if (self.Pip > self.PipMax):
                self.Pip = self.PipMax
    
    def VolumeControl(self):
        pass

    def HFOV(self):
        pass
    
    def PressureLimited(self):
        if self.Inspiration:
            # calculate the inspiratory valve resistance to achieve the desired inspiratory flow

            # pressure gradient over the respiratory system
            delta_p = self._modelEngine.Models["VENTIN"].Pres - self._modelEngine.Models["VENTOUT"].Pres
            
            # calculate the resistance of the inspiratory valve
            if (self._insp_valve_flow_reduction <= 0.0):
                res = 100000000000
            else:
                res = (delta_p / (self.InspFlow / 60.0)) - self._exp_valve.RFor - 50.0

            # set the inspiratory valve resistance
            self._insp_valve.RFor = res

            # make sure the valve is open and make sure no backflow can occur
            self._insp_valve.NoFlow = False
            self._insp_valve.NoBackflow = True

            # close the expiratory valve
            self._exp_valve.NoFlow = True

            threshold = self.Pip + self.PresAtm + 1.0
            if (self._internal_pressure_sensor.Pres >= threshold):
                self._insp_valve.NoFlow = True


        if self.Expiration:
            # calculate the inspiratory valve resistance to achieve the desired expiratory bias flow

            # pressure gradient over the respiratory system
            delta_p = self._modelEngine.Models["VENTIN"].Pres - self._modelEngine.Models["VENTOUT"].Pres

            # calculate the resistance of the inspiratory valve
            res = (delta_p / (self.ExpFlow / 60.0)) - self._exp_valve.RFor - 50.0

            # set the inspiratory valve resistance
            self._insp_valve.RFor = res

            # make sure the valve is open and make sure no backflow can occur
            self._insp_valve.NoFlow = False
            self._insp_valve.NoBackflow = True

            # make sure the expiratory valve is open and make sure no backflow can occur
            self._exp_valve.RFor = 25.0
            self._exp_valve.NoFlow = False
            self._exp_valve.NoBackflow = True

            # guard the positive end expiratory pressure
            if (self._pressure_sensor.Pres < self.Peep + self.PresAtm):
                # close the expiration valve when the pressure falls below the positive end expiratory pressure
                self._exp_valve.NoFlow = True

    def SetInspTime(self, time):
        self.InspTime = time

    def SetFreq(self, freq):
        self.Freq = freq

    def SetInspFlow(self, flow):
        self.InspFlow = flow

    def SetExpFlow(self, flow):
        self.ExpFlow = flow

    def SetFiO2(self, fio2):
        self.Fo2Dry = fio2
    
    def SetPip(self, pip):
        self.Pip = pip / 1.35951
    
    def SetPeep(self, peep):
        self.Peep = peep / 1.35951

    def SetTemp(self, temp):
        self.Temp = temp

    def SetHumidity(self, humidity):
        self.Humidity = humidity

    def SetTargetVt(self, vt):
        self.VtSet = vt / 1000.0
    
    def SetMode(self, mode):
        if (mode == "PC"):
            self.VolumeGuaranteed = False

        if (mode == "PRVC"):
            self.VolumeGuaranteed = True
 
    def SetTubingDiameter(self, diameter):
        self.TubingSettings["InnerDiameter"] = diameter / 1000.0

    def SetTubingLength(self, length):
        self.TubingSettings["Length"] = length

    def SetTubingCompliance(self, comp):
        self.TubingSettings["Elastance"] = 1.0 / comp

    def SetTubeSize(self, tube_size):
        pass




    