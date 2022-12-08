import math

from explain_core.core_models.ModelBaseClass import ModelBaseClass

class Heart(ModelBaseClass):
    # model specific attributes
    RightAtrium = ""
    LeftAtrium = ""
    RightVentricle = ""
    LeftVentricle = ""
    Coronaries = ""
    HeartRate = 120.0
    HeartRateRef = 120.0
    HeartRateUpperLimit = 300.0
    VenticularEscapeRate = 40.0
    RhythmType = 0
    PqTime = 0.1
    AvDelay = 0.02
    QrsTime = 0.075
    QtTime = 0.4
    CqtTime = 0.198

    # external properties
    NccAtrial = -1
    NccVentricular = -1
    Aaf = 0.0
    Vaf = 0.0
    HeartPeriodChangeAns = 0.0
    HeartPeriodChangeTemp = 0.0
    HeartPeriodChangeMyo = 0.0

    # local properties
    _kn = 0.579
    _ra = {}
    _la = {}
    _rv= {}
    _lv = {}
    _cor = {}
    _sa_node_period_limit = 0.2
    _sa_node_timer = 0.0
    _pq_running = False
    _pq_timer = 0.0
    _qrs_timer = 0.0
    _qrs_running = False
    _ventricle_is_refractory = False
    _qt_timer = 0.0
    _qt_running = False

    def InitModel(self, modelEngine):
        # initialize the base class
        ModelBaseClass.InitModel(self, modelEngine)

        # find the references to the atrial and ventricular models
        self._ra = self._modelEngine.Models[self.RightAtrium]
        self._la = self._modelEngine.Models[self.LeftAtrium]
        self._rv = self._modelEngine.Models[self.RightVentricle]
        self._lv = self._modelEngine.Models[self.LeftVentricle]
        self._cor = self._modelEngine.Models[self.Coronaries]
        
        # determine the maximal heartrate
        self._sa_node_period_limit = 60.0 / self.HeartRateUpperLimit


    def CalcModel(self):
        # calculate the qtc time depending on the heartrate
        self.CqtTime = self.Qtc()

        # calculate the sinus node interval in seconds depending on the heart rate
        sa_node_period = (60.0 / self.HeartRateRef) + self.HeartPeriodChangeAns + self.HeartPeriodChangeTemp + self.HeartPeriodChangeMyo

        # limit the heart period depending on the HeartRateUpperLimit property
        if (sa_node_period < self._sa_node_period_limit ):
            sa_node_period = self._sa_node_period_limit
        
        # calculate the current heartrate
        self.HeartRate = 60.0 / sa_node_period

        # has the sinus node period elapsed?
        if (self._sa_node_timer > sa_node_period):
            # reset the sinus node timer
            self._sa_node_timer = 0.0
            # signal that the pq-time starts running
            self._pq_running = True
            # reset the atrial activation curve counter
            self.NccAtrial = -1
        
        # has the pq time elapsed + the av delay time
        if (self._pq_timer > self.PqTime + self.AvDelay):
            # reset the pq timer
            self._pq_timer = 0.0
            # signal that the pq timer has stopped
            self._pq_running = False
            # check whether the ventricles are in a refractory state
            if (not self._ventricle_is_refractory):
                # signal that the qrs time starts running
                self._qrs_running = True
                # reset the ventricular activation curve
                self.NccVentricular = -1

        # has the qrs time elapsed?
        if (self._qrs_timer > self.QrsTime):
            # reset the qrs timer
            self._qrs_timer = 0.0
            # signal that the qrs timer has stopped
            self._qrs_running = False
            # signal that the qt time starts running
            self._qt_running = True
            # signal that the ventricles are now in a refractory state
            self._ventricle_is_refractory = True
        
        # has the qt time elapsed?
        if (self._qt_timer > self.CqtTime):
            # reset the qt timer
            self._qt_timer = 0.0
            # signal that the qt timer has stopped
            self._qt_running = False
            # signal that the ventricles are coming out of their refractory state
            self._ventricle_is_refractory = False

        # increase the timers with the modeling stepsize as set by the model base class
        self._sa_node_timer += self._t

        # increase the qt timer if their running
        if (self._pq_running):
            self._pq_timer += self._t
        
        if (self._qrs_running):
            self._qrs_timer += self._t
        
        if (self._qt_running):
            self._qt_timer += self._t

        # increase the heart activation function counters
        self.NccAtrial += 1
        self.NccVentricular += 1

        # calculate the varying elastance function
        atrial_duration = self.PqTime
        ventricular_duration = self.QrsTime + self.CqtTime

        # calculate the atrial activation function factor
        if (self.NccAtrial >= 0 and self.NccAtrial < self.PqTime / self._t):
            self.Aaf = math.sin(math.pi * (self.NccAtrial / (atrial_duration / self._t)))
        else:
            self.Aaf = 0.0

        # calculate the ventricular activation function factor
        if (self.NccVentricular >= 0 and self.NccVentricular < ventricular_duration / self._t):
            self.Vaf = self.NccVentricular / (self._kn * (ventricular_duration / self._t )) * math.sin(math.pi * (self.NccVentricular / (ventricular_duration / self._t)))
        else:
            self.Vaf = 0.0

        # transfer the varying elastance activation function factors to the heart models
        self._ra.ActFactor = self.Aaf
        self._la.ActFactor = self.Aaf
        self._rv.ActFactor = self.Vaf
        self._lv.ActFactor = self.Vaf
        self._cor.ActFactor = self.Vaf


    def Qtc(self) -> float:
        if (self.HeartRate > 10):
            return self.QtTime * math.sqrt(60.0 / self.HeartRate)
        else :
            return self.QtTime * math.sqrt(6.0)
