from explain_core.helpers.ModelBaseClass import ModelBaseClass

class Blood(ModelBaseClass):
    # model specific attributes
    Solutes = {}
    To2 = 0.0
    Tco2 = 0.0

    # override the InitModel of the model base class as this model requires additional initialization
    def InitModel(self, modelEngine):
        # initialize the base class
        ModelBaseClass.InitModel(self, modelEngine)

        # find all blood compliances and blood time varying elastances and transfer the solutes to the compartments
        self.SetSolutes()

        # set pCO2 and pO2 in lung compliances
        for n, m in self._modelEngine.Models.items():
            if (n == "LL"):
                m.Po2 = 100.0
                m.Pco2 = 45.0
            if (n == "LR"):
                m.Po2 = 100.0
                m.Pco2 = 45.0


    def SetSolutes(self):
        # find all blood compliances and blood time varying elastances and transfer the solutes to the compartments
        for _, model in self._modelEngine.Models.items():
            if (model.ModelType == "BloodCompliance" or model.ModelType == "BloodTimeVaryingElastance"):
                model.Solutes = self.Solutes.copy()
                model.To2 = self.To2
                model.Tco2 = self.Tco2

