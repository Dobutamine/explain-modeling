from explain_core.helpers.ModelBaseClass import ModelBaseClass

class MechanicalVentilator(ModelBaseClass):
    # model specific attributes
    VentAir = {}
    TempSettings = {}
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

    # local parameters
    GasConstant = 62.36367
    _insp_timer = 0.0
    _exp_timer = 0.0
    

    # override the InitModel of the model base class as this model requires additional initialization
    def InitModel(self, modelEngine):
        # initialize the base class
        ModelBaseClass.InitModel(self, modelEngine)
        
        # initialize the gas compliances holding the ventilator air
        self.SetInspiredAir()

        # initialize the gas compliances holding the outside air
        self.SetOutsideAir()

        self.SetInspFlow(self.InspFlow)

        # close connection 
        self._modelEngine.Models["MOUTH_DS"].NoFlow = True
        # self._modelEngine.Models["VENTIN_YPIECE"].NoFlow = True
        # self._modelEngine.Models["YPIECE_VENTOUT"].NoFlow = True
        self._modelEngine.Models["Breathing"].IsEnabled = False

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
            # open the inspiration valve and close the expiration valve
            self._modelEngine.Models["VENTIN_YPIECE"].NoFlow = False
            self._modelEngine.Models["YPIECE_VENTOUT"].NoFlow = True

        # increase the timers
        if (self.Inspiration):
            self._insp_timer += self._t
            # guard the pressures
            if (self._modelEngine.Models["YPIECE"].Pres > self.PresAtm + self.Pip):
                # pressure exceeed so close the inspiration valve
                self._modelEngine.Models["VENTIN_YPIECE"].NoFlow = True
            else: 
                self._modelEngine.Models["VENTIN_YPIECE"].NoFlow = False

        if (self.Expiration):
            self._exp_timer += self._t

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


    def SetInspiredAir(self):
        # get a reference to the model which is going to hold the inspired air
        vent_in = self._modelEngine.Models["VENTIN"]

        vent_in.Temp = self.TempIn
        vent_in.TargetTemp = self.TempIn

        # set the atmospheric pressure 
        vent_in.Pres0 = self.PresAtm
 
        # calculate the pressure in the inspired air compliance, should be pAtm
        vent_in.StepModel()

        # calculate the concentration at this pressure and temperature in mmol/l !
        vent_in.CTotal = (vent_in.Pres / (self.GasConstant * (273.15 + vent_in.Temp))) * 1000.0

        # set the inspired air fractions
        vent_in.Fh2O = self.VentAirIn["Fh2O"]
        vent_in.Fo2 = self.VentAirIn["Fo2"]
        vent_in.Fco2 = self.VentAirIn["Fco2"]
        vent_in.Fn2 = self.VentAirIn["Fn2"]

        # calculate the inspired air concentrations
        vent_in.Ch2O = vent_in.Fh2O * vent_in.CTotal
        vent_in.Co2 = vent_in.Fo2 * vent_in.CTotal
        vent_in.Cco2 = vent_in.Fco2 * vent_in.CTotal
        vent_in.Cn2 = vent_in.Fn2 * vent_in.CTotal

        # calculate the inspired air partial pressures
        vent_in.Ph2O = vent_in.Fh2O * vent_in.Pres
        vent_in.Po2 = vent_in.Fo2 * vent_in.Pres
        vent_in.Pco2 = vent_in.Fco2 * vent_in.Pres
        vent_in.Pn2 = vent_in.Fn2 * vent_in.Pres


    