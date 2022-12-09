from explain_core.helpers.ModelBaseClass import ModelBaseClass

class GasExchanger(ModelBaseClass):
    # model specific attributes
    CompBlood = "LL"
    CompGas = "ALL"
    DifO2 = 0.01
    DifCo2 = 0.01

    # local parameters
    _flux_o2 = 0.0
    _flux_co2 = 0.0

    def CalcModel(self):
        # get the total oxygen and carbon dioxide content from the blood components
        to2_blood = self._modelEngine.Models[self.CompBlood].To2
        tco2_blood = self._modelEngine.Models[self.CompBlood].Tco2

        # calculate the partial pressures of oxygen and carbon dioxide from the total content
        po2_blood = self._modelEngine.Oxygenation.calc_oxygenation(to2_blood).Po2
        pco2_blood = self._modelEngine.AcidBase.calc_acid_base(tco2_blood).Pco2

        # get the partial pressures from the gas components
        co2_gas = self._modelEngine.Models[self.CompGas].Co2
        cco2_gas = self._modelEngine.Models[self.CompGas].Cco2
        po2_gas = self._modelEngine.Models[self.CompGas].Po2
        pco2_gas = self._modelEngine.Models[self.CompGas].Pco2

        # calculate the O2 flux from the blood to the gas compartment
        self._flux_o2 = (po2_blood - po2_gas) * self.DifO2 * self._t

        # calculate the CO2 flux from the blood to the gas compartment
        self._flux_co2 = (pco2_blood - pco2_gas) * self.DifCo2 * self._t

        # calculate the new O2 concentrations of the gas and blood compartments
        new_to2_blood = (to2_blood * self._modelEngine.Models[self.CompBlood].Vol - self._flux_o2) / self._modelEngine.Models[self.CompBlood].Vol
        if (new_to2_blood < 0):
            new_to2_blood = 0

        new_co2_gas = (co2_gas * self._modelEngine.Models[self.CompGas].Vol + self._flux_o2) / self._modelEngine.Models[self.CompGas].Vol
        if (new_co2_gas < 0):
            new_co2_gas = 0

        # calculate the new Co2 concentrations of the gas and blood compartments
        new_tco2_blood = (tco2_blood * self._modelEngine.Models[self.CompBlood].Vol - self._flux_co2) / self._modelEngine.Models[self.CompBlood].Vol
        if (new_tco2_blood < 0):
            new_tco2_blood = 0

        new_cco2_gas = (cco2_gas * self._modelEngine.Models[self.CompGas].Vol + self._flux_co2) / self._modelEngine.Models[self.CompGas].Vol
        if (new_cco2_gas < 0):
            new_cco2_gas = 0

        # transfer the new concentrations
        self._modelEngine.Models[self.CompBlood].To2 = new_to2_blood
        self._modelEngine.Models[self.CompBlood].Tco2 = new_tco2_blood
        self._modelEngine.Models[self.CompGas].Co2 = new_co2_gas
        self._modelEngine.Models[self.CompGas].Cco2 = new_cco2_gas
