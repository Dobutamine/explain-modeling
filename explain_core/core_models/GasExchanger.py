from explain_core.core_models.ModelBaseClass import ModelBaseClass

class GasExchanger(ModelBaseClass):
    # model specific attributes
    CompBlood = "LL"
    CompGas = "ALL"
    DifO2 = 0.01
    DifCo2 = 0.01

    # local parameters


    def CalcModel(self):
        # we need to get the To2 and the Po2 of the blood and gas compartment
        to2_blood = self._modelEngine.Models[self.CompBlood].Solutes["To2"]
        tco2_blood = self._modelEngine.Models[self.CompBlood].Solutes["Tco2"]

        to2_gas = self._modelEngine.Models[self.CompGas].Co2
        tco2_gas = self._modelEngine.Models[self.CompGas].Cco2

        # calculate the po2 and pco2 of the blood compartment
        po2_blood = self._modelEngine.Models["Oxygenation"].calc_oxygenation(to2_blood).Po2
        pco2_blood = self._modelEngine.Models["AcidBase"].calc_acid_base(tco2_blood).Pco2



