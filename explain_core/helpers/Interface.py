class Interface:
    # local parameters
    _model = {}
    _t = 0.0005
    _is_initialized = False

    def __init__(self, model):
        # store a reference to the model
        self._model = model

        # store the modeling stepsize for easy referencing
        self._t = model.modeling_stepsize

        # signal that the component has been initialized
        self._is_initialized = True