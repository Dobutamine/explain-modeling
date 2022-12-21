import math

from explain_core.helpers.ModelBaseClass import ModelBaseClass

class Pda(ModelBaseClass):
    # independent parameters
    Length = 10.0
    Diameter = 5.1
    Viscosity = 3.5
    Model = {}
    Flow = 0.0
    Velocity = 0.0
    Velocity10 = 0.0

    # local parameters
    _pda = {}
    _res = 1.0
    
    # override the InitModel of the model base class as this model requires additional initialization
    def InitModel(self, modelEngine):
        # initialize the base class
        ModelBaseClass.InitModel(self, modelEngine)

        # reference the blood resister
        self._pda = self._modelEngine.Models[self.Model]

    
    def CalcModel(self):
        # calculate the resistance of the ductus arteriousus where
        # the duct is modeled as a perfect tube with a diameter and a length in millimeters
        # the viscosity is in centiPoise
        
        # resistance is calculated using Poiseuille's Law : R = (8 * n * L) / (PI * r^4)
        
        # we have to watch the units carefully where we have to make sure that the units in the formula are 
        # resistance is in mmHg * s / l
        # L = length in meters from millimeters
        # r = radius in meters from millimeters
        # n = viscosity in mmHg * s from centiPoise
        
        # convert viscosity from centiPoise to mmHg * s
        n_mmhgs = self.Viscosity * 0.001 * 0.00750062
        
        # convert the length to meters
        length_meters = self.Length / 1000.0
        
        # calculate the radius in meters
        radius_meters = (self.Diameter / 2) / 1000.0

        # calculate the resistance using Poiseuille's Law, the resistance is now in mmHg * s/mm^3
        self._res = (8.0 * n_mmhgs * length_meters) / (math.pi * math.pow(radius_meters, 4))
        
        # convert resistance of mmHg * s / mm^3 to mmHg *s / l
        self._res = self._res / 1000.0
        
        # transfer the resistance to the ductus arteriosus blood connector and enable flow
        self._pda.IsEnabled = self.IsEnabled
        self._pda.NoFlow = not self.IsEnabled
        self._pda.RFor = self._res
        self._pda.RBack = self._res
        
        # store the pda flow in l / s
        self.Flow = self._pda.Flow
        
        # calculate the velocity in m/s, for that we have to convert the flow to mm^3/sec
        # velocity = flow_rate (in mm^3/s) / (pi * radius^2)     in m/s
        self.Velocity = (self._pda.Flow / 1000.0) / (math.pi * math.pow(radius_meters, 2.0))
        self.Velocity10 = self.Velocity * 10.0


