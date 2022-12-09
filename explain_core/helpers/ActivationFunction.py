class ActivationFunction:
  # specific model attributes
  SetPoint = 0.0
  Min = 0.0
  Max = 0.0
  Gain = 0.0
  TimeConstant = 0.0
  Output = 0.0
  UpdateInterval = 0.0

  # local parameters
  _activation = 0.0

  def __init__(self, set_point, min, max, gain, time_constant, update_interval) -> None:
    # set the parameters
    self.SetPoint = set_point
    self.Max = max
    self.Min = min
    self.Gain = gain
    self.TimeConstant = time_constant
    self.UpdateInterval = update_interval

  def Update(self, sensor_value):
    # calculate the sensor activity
    a = self.CalcActivation(sensor_value)

    # calculate the sensor output
    self._activation = self.UpdateInterval * ((1.0 / self.TimeConstant) * (-self._activation + a)) + self._activation
            
    # Apply the gain
    self.Output = self._activation * self.Gain
        
    #return the sensor output
    return self.Output

  def CalcActivation(self, value) -> float:
    a = 0.0
        
    if (value >= self.Max):
      a = self.Max - self.SetPoint
    else:
      if (value <= self.Min):
        a = self.Min - self.SetPoint
      else:
        a = value - self.SetPoint
        
    return a
