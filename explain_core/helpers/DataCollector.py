import math

class DataCollector:
  collected_data = []
  sample_interval = 0.005
  watch_list = []

  # common local parameters
  _modelEngine = {}
  _t = 0.0005
  _interval_counter = 0

  def __init__(self, modelEngine):
    # initialize the super class
    super().__init__()

    # store a reference to the model instance
    self._modelEngine = modelEngine

    # define the watch list
    self.watch_list = []

    # define the data sample interval
    self.sample_interval = 0.005
    self._interval_counter = 0

    # get the modeling stepsize from the model
    self._t = modelEngine.ModelingStepsize
    
    # try to add two always needed ecg properties to the watchlist
    try:
        self.ncc_ventricular = {'label': 'Heart.NccVentricular', 'model': self._modelEngine.Models['Heart'], 'prop': 'NccVentricular'}
        self.ncc_atrial = {'label': 'Heart.NccAtrial', 'model': self._modelEngine.Models['Heart'], 'prop': 'NccAtrial'}
    except:
        self.ncc_ventricular = {'label': '', 'model': None, 'prop': ''}
        self.ncc_atrial = {'label': '', 'model': None, 'prop': ''}

    # add the two always there
    self.watch_list.append(self.ncc_atrial)
    self.watch_list.append(self.ncc_ventricular)
        
    # define the data list
    self.collected_data = []

  def clear_data (self):
    self.collected_data = []

  def clear_watchlist(self):
    # first clear all data
    self.clear_data()

    # empty the watch list
    self.watch_list = []

    # add the two always there
    self.watch_list.append(self.ncc_atrial)
    self.watch_list.append(self.ncc_ventricular)

  def set_sample_interval(self, new_interval):
    self.sample_interval = new_interval

  def add_to_watchlist(self, property):
    # first clear all data
    self.clear_data()

    # add to the watchlist
    self.watch_list.append(property)

  def collect_data(self, model_clock):
    if (self._interval_counter >= self.sample_interval):
      self._interval_counter = 0
      data_object = { 'time': model_clock }
      for parameter in self.watch_list:
        label = parameter['label']
        prop = parameter['prop']
        weight = 1
        time = 1
        if prop == 'flow':
            weight = self._modelEngine.Weight
            time = 60
        if prop == 'vol':
            weight = self._modelEngine.Weight
        
        if parameter['model'] is not None:
            value = getattr(parameter['model'], parameter['prop'])
                
            data_object[label] = value / weight * time
            
      self.collected_data.append(data_object)
            
    
    self._interval_counter += self._t