import math

from explain_core.helpers.ModelBaseClass import ModelBaseClass

class IntrathoracicPressure(ModelBaseClass):

  # common local parameters
    _modelEngine = {}
    _t = 0.0005
    _is_initialized = False

    def InitModel(self, modelEngine):
        # initialize the base class
        ModelBaseClass.InitModel(self, modelEngine)

    def CalcModel(self):
      pass