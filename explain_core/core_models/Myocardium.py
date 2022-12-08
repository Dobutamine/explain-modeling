class Myocardium:
    # class attributes
    Name = ""
    Description = ""
    ModelType = ""
    IsEnabled = False

    # local parameters
    _model = {}
    _t = 0.0005
    _is_initialized = False

    def __init__(self, **args):
        # initialize the super class
        super().__init__()

        # set the values of the independent properties with the values from the JSON configuration file
        for key, value in args.items():
            setattr(self, key, value)

    def InitModel(self, model):
        # store a reference to the model
        self._model = model

        # store the modeling stepsize for easy referencing
        self._t = model.ModelingStepsize

        # signal that the component has been initialized
        self._is_initialized = True

    def StepModel(self):
        if (self.IsEnabled and self._is_initialized):
            self.CalcModel()

    def CalcModel(self):
        pass