from abc import ABC, abstractmethod, abstractproperty

class TestClass:
    """
    The model class is the building block of Explain and at least 4 methods.
    
    The __init__ method takes a dictionary passing in the model parameters.

    The InitModel method initializes the ModelClass instance and has to be called after all models of explain are instantiated and 
    takes a reference the ModelEngine instance to access the other models of Explain.
    
    The StepModel method is called by the ModelEngine during every model step and determines whether or 
    not the ModelClass instance is enabled and properly initialized before calling the CalcModel method which 
    handles all the ModelClass instance specific calculations.
    
    All models (ModelClass instances) of explain must at least implement the methods (__init__, InitModel, StepModel and CalcModel).

    The ModelClass has at least 4 exposed parameters (Name, Description, ModelType and IsEnabled) which are initialized 
    by the constructor (__init__).

    The ModelClass also has three local parameters which are initialized by the constructor holding a reference 
    to the ModelEngine, ModelingStepsize and a boolean indicating whether the model class is initialized correctly.

    As Explain is translated into multiple programming languages the naming conventions of Python are not always used.
    """

    # common local parameters
    _modelEngine = {}
    _t = 0.0005
    _is_initialized = False

    # # constructor
    @abstractmethod
    def __init__(self, **args):
      pass

    # model initializer
    @abstractmethod
    def InitModel(self, modelEngine):
      pass

    # this method is called every model step by the Explain ModelEngine
    @abstractmethod
    def StepModel(self):
      pass

    # this method is responsible for the actual model calculations
    @abstractmethod
    def CalcModel(self):
      pass