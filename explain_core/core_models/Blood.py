from explain_core.core_models.ModelBaseClass import ModelBaseClass

class Blood(ModelBaseClass):
    # model specific attributes
    Solutes = {}

    # override the InitModel of the model base class as this model requires additional initialization
    def InitModel(self, modelEngine):
        # initialize the base class
        ModelBaseClass.InitModel(self, modelEngine)

        # find all blood compliances and blood time varying elastances and transfer the solutes
        for _, model in self._modelEngine.Models.items():
            if (model.ModelType == "BloodCompliance" or model.ModelType == "BloodTimeVaryingElastance"):
                model.Solutes = self.Solutes.copy()
