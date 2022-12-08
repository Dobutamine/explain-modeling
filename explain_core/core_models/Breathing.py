import math
from explain_core.core_models.ModelBaseClass import ModelBaseClass

class Breathing(ModelBaseClass):
    # model specific attributes
    BreathingEnabled = True
    RespRate = 40
    RefMinuteVolume = 0.63
    RefTidalVolume = 0.01547
    TargetMinuteVolume = 0.63
    TargetTidalVolume = 0.01547
    VtRrRatio = 0.00038
    IeRatio = 0.3
    RespMusclePressure = 0
    RmpGain = 9.0
    Targets = []

    # local parameters
    EMin4 = math.pow(math.e, -4)
    _insp_timer = 0.0
    _insp_running = False
    _exp_timer = 0.0
    _exp_running = False
    _ti = 0.0
    _te = 0.0
    _ncc_insp = 0
    _ncc_exp = 0
    _breath_timer = 0.0
    

    def CalcModel(self):
        # calculate the respiratory rate and target tidal volume from the target minute volume
        self.VtRrController()

        # calculate the inspiratory and expiratory time
        if (self.RespRate > 0):
            breath_interval = 60.0 / self.RespRate
            self._ti = self.IeRatio * breath_interval   # in seconds
            self._te = breath_interval - self._ti       # in seconds

        # is it time to start a breath?
        if (self._breath_timer > breath_interval):
            # reset the breath timer
            self._breath_timer = 0.0

            # signal that the inspiration is starting
            self._insp_running = True
            self._insp_timer = 0.0

            # reset the activation curve counter for the inspiration
            self._ncc_insp = 0.0

        # has the inspiration time elapsed?
        if (self._insp_timer > self._ti):
            # reset the inspiration timer
            self._insp_timer = 0.0
            
            # signal that the inspiration has stopped
            self._insp_running = False

            # signal that the expiration has started
            self._exp_running = True

            # reset the activation curve counter for the expiration
            self._ncc_exp = 0.0
        
        # has the expiration time elapsed?
        if (self._exp_timer > self._te):
            # reset the expiration timer
            self._exp_timer = 0.0

            # signal that the expiration has stopped
            self._exp_running = False

        # increase the timers
        self._breath_timer += self._t
        
        if (self._insp_running):
            self._insp_timer += self._t
            self._ncc_insp += 1.0

        if (self._exp_running):
            self._exp_timer += self._t
            self._ncc_exp += 1.0

        # calculate the respiratory muscle pressure
        self.CalcRespMusclePressure()

        # transfer muscle pressure to the targets
        for target in self.Targets:
            self._modelEngine.Models[target].PresExt = self.RespMusclePressure

    
    def CalcRespMusclePressure(self):
        # reset respiratory muscle pressure
        self.RespMusclePressure = 0

        # inspiration 
        if (self._insp_running):
            self.RespMusclePressure = (self._ncc_insp / (self._ti / self._t)) * self.RmpGain

        # expiration
        if (self._exp_running):
            self.RespMusclePressure = ((math.pow(math.e, -4.0 * (self._ncc_exp / (self._te / self._t))) - self.EMin4) / (1.0 - self.EMin4)) * self.RmpGain


    def VtRrController(self):
        # calculate the spontaneous resp rate depending on the target minute volume (from ANS) and the set vt-rr ratio
        self.RespRate = math.sqrt(self.TargetMinuteVolume / self.VtRrRatio)

        # calculate the target tidal volume depending on the target resp rate and target minute volume (from ANS)
        if (self.RespRate > 0):
            self.TargetTidalVolume = self.TargetMinuteVolume / self.RespRate