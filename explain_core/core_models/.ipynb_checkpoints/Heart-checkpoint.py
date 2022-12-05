class Heart:
    # class attributes
    Name = ""
    Description = ""
    ModelType = ""
    IsEnabled = False
    HeartRate = 0.0
    HeartRateRef = 0.0
    HeartPeriodChangeAns = 0.0
    HeartPeriodChangeMyo = 0.0
    RhythmType = 0
    PqTime = 0.0
    QrsTime = 0.0
    QtTime = 0.0
    CqtTime = 0.0
    NccVentricular = 0.0
    NccAtrial = 0.0
    EcgSignal = 0.0
    Aaf = 0.0
    Vaf = 0.0
    Kn = 0.579
    NoOfBeats = 5


    # local parameters
    _model = {}
    _t = 0.0005
    _is_initialized = False
    _heart_period = 0.0
    _sa_node_period = 0.0
    _sa_node_timer = 0.0
    _pq_timer = 0.0
    _pq_running = False
    _qrs_timer = 0.0
    _qrs_running = False
    _ventricle_is_refractory = False
    _qt_timer = 0.0
    _qt_running = False
    _measured_qrs_counter = 0.0
    _measured_qrs_timer = 0.0



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
        self._t = model.modeling_stepsize

        # signal that the component has been initialized
        self._is_initialized = True

    def StepModel(self):
        if (self.IsEnabled and self._is_initialized):
            self.CalcModel()

    def CalcModel(self):
        pass