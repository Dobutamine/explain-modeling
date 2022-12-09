from explain_core.helpers.ModelBaseClass import ModelBaseClass

class Metabolism(ModelBaseClass):
    # model specific attributes
    Vo2 = 0.0
    RespQ = 0.0
    BodyTemp = 37.0
    MetabolicActiveModels = {}


    def CalcModel(self):
        # translate the VO2 in ml/kg/min to VO2 in mmol for this stepsize (assumption is 37 degrees and atmospheric pressure)
        vo2_step = ((0.039 * self.Vo2 * self._modelEngine.Weight) / 60.0) * self._t

        # do the metabolism for each active blood compliance
        for met_model, fvo2 in self.MetabolicActiveModels.items():
            # get the to2 from the blood compartment
            to2 = self._modelEngine.Models[met_model].To2
            
            # calculate the change in oxygen concentration in this step
            dto2 = vo2_step * fvo2

            # calculate the new oxygen concentration in blood
            new_to2 = (to2 * self._modelEngine.Models[met_model].Vol - dto2) / self._modelEngine.Models[met_model].Vol
            # guard against negative values
            if (new_to2 < 0):
                new_to2 = 0

            # get the tco2 from the blood compartment
            tco2 = self._modelEngine.Models[met_model].Tco2

            # calculate the change in co2 concentration in this step
            dtco2 = vo2_step * fvo2 * self.RespQ

            # calculate the new oxygen concentration in blood
            new_tco2 = (tco2 * self._modelEngine.Models[met_model].Vol + dtco2) / self._modelEngine.Models[met_model].Vol
            # guard against negative values
            if (new_tco2 < 0):
                new_tco2 = 0

            # store the new to2 and tco2
            self._modelEngine.Models[met_model].To2 = new_to2
            self._modelEngine.Models[met_model].Tco2 = new_tco2

