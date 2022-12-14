import math

# gas constant
_gas_constant = 62.36367

def SetAirComposition(comp, humidity, temperature, fo2_dry, fco2_dry, fn2_dry, fother_dry):
  # calculate the concentration at this pressure and temperature in mmol/l
  comp.Ctotal = (comp.Pres / (_gas_constant * (273.15 + temperature))) * 1000.0

  # calculate the water vapour pressure, concentration and fraction and this temperature and humidity (0 - 1)
  comp.Ph2o = (math.pow(math.e, 20.386 - 5132 / (temperature + 273))) * humidity
  comp.Fh2o = comp.Ph2o / comp.Pres
  comp.Ch2o = comp.Fh2o * comp.Ctotal

  # calculate the o2 partial pressure, fraction and concentration
  comp.Po2 = fo2_dry * (comp.Pres - comp.Ph2o)
  comp.Fo2 = comp.Po2 / comp.Pres
  comp.Co2 = comp.Fo2 * comp.Ctotal

  # calculate the co2 partial pressure, fraction and concentration
  comp.Pco2 = fco2_dry * (comp.Pres - comp.Ph2o)
  comp.Fco2 = comp.Pco2 / comp.Pres
  comp.Cco2 = comp.Fco2 * comp.Ctotal

  # calculate the n2 partial pressure, fraction and concentration
  comp.Pn2 = fn2_dry * (comp.Pres - comp.Ph2o)
  comp.Fn2 = comp.Pn2 / comp.Pres
  comp.Cn2 = comp.Fn2 * comp.Ctotal

  # calculate the other gas partial pressure, fraction and concentration
  comp.Pother = fother_dry * (comp.Pres - comp.Ph2o)
  comp.Fother = comp.Pother / comp.Pres
  comp.Cother = comp.Fother * comp.Ctotal



