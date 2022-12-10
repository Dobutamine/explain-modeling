class DataCollector:
    LoggingInterval = 0.0005

    # local parameters
    _modelEngine = {}
    _t = 0.0005
    _is_initialized = False

    _watch_list = {}
    _model_data = []

    _logging_timer = 0.0

    def __init__(self, modelEngine):
        # store a reference to the model
        self._modelEngine = modelEngine

        # store the modeling stepsize for easy referencing
        self._t = modelEngine.ModelingStepsize

        # signal that the component has been initialized
        self._is_initialized = True

    def clear_watch_list(self):
        self._watch_list = {}

    def add_to_watch_list(self, model, prop):
        label = model + "." + prop
        self._watch_list[label] = (self._modelEngine.Models[model], prop)

    def remove_from_watchlist(self, model, prop):
        label = model + "." + prop
        del self._watch_list[label]
    
    def clear_model_data(self):
        # clear the model data list
        self._model_data = []

    def get_model_data(self):
        # create a copy of the model data
        md_cp = list(self._model_data)
        # clear the current model data list
        self._model_data = []
        # return the copy
        return md_cp

    def Update(self):
        if (self._logging_timer >= self.LoggingInterval):
            # reset the logging timer
            self._logging_timer = 0.0
            # store the data from the watchlist
            for label, wai in self._watch_list.items():
                self._model_data.append((self._modelEngine.ModelingTimeTotal,label, getattr(wai[0], wai[1])))
        
        # update the logging timer
        self._logging_timer += self._t