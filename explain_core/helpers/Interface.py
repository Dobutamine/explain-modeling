class Interface:
    # local parameters
    _modelEngine = {}
    _t = 0.0005
    _is_initialized = False

    def __init__(self, modelEngine):
        # store a reference to the model
        self._modelEngine = modelEngine

        # store the modeling stepsize for easy referencing
        self._t = modelEngine.ModelingStepsize

        # signal that the component has been initialized
        self._is_initialized = True