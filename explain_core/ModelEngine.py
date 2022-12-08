# import the python dependencies
import json, importlib

# import the helper classes
from explain_core.helpers.DataCollector import DataCollector
from explain_core.helpers.Interface import Interface

class ModelEngine:
    """
    The ModelEngine class is the most important class of Explain. 
    It is responisble for loading, initializing and running all models.
    
    When the ModelEngine class is instantiated it needs a JSON string holding the model parameters as an argument. 
    It processes the JSON string and loads, initantiates and initializes all the models.

    The other methods of the class are used to run the model in a realtime mode (Start, Stop) 
    or to calculate a number of seconds (Calculate) which takes the number of seconds as an argument. 
    
    The ModelStep method is used to calculate 1 model step by iterating over the components dictionary and 
    calling the StepModel method of these components.

    As Explain is translated into multiple programming languages the naming conventions of Python are not always used.
    """
    # define the model attributes with default values
    Name = ""
    Description = ""
    Weight = 3.3
    ModelingTimeTotal = 0.0
    ModelingStepsize = 0.0005

    # define a boolean to indicate if the model engine initialized correctly.
    Initialized = False

    # define an object holding all modelengine models
    Models = {}

    # define a datacollector
    DataCollector = {}
    
    # define an interface
    Interface = {}

    # local parameters
    _logging = False

    # this routine is called to initialize the model and takes a explain model definition in the form of a JSON string as parameter
    def __init__(self, explain_definition: str, logging = True):
        # initialize the super class
        super().__init__()

        # set the error counter = 0
        error_counter = 0

        # enable of disable the logger
        self._logging = logging
        self._verbose = False

        # open the json file
        json_file = open(explain_definition)

        # convert the JSON string explain model definition to a dictionary
        explain_definition = json.load(json_file)

        # initialize the model using the properties stored in the explain model definition
        self.Name = explain_definition['Name']
        self.Description = explain_definition['Description']
        self.Weight = explain_definition['Weight']
        self.ModelingTimeTotal = explain_definition['ModelTimeTotal']
        self.ModelingStepsize = explain_definition['ModelingStepsize']

        # load and instantiate all models from the explain model definition and put a reference to them in the models dictionary.
        for model_name, model_definition in explain_definition['Models'].items():
            # try to find the desired model class from the core_models or custom_models folder
            try:
                # first find the type of the model, so we can instantiate the correct model
                model_type = model_definition["ModelType"]

                # try to import the module holding the model class from the core_models folder
                model_module = importlib.import_module('explain_core.core_models.' + model_type)
                
                # get the model class from the module
                model_class = getattr(model_module, model_type)
                
                # instantiate the model class with the properties stored in the model_definition  and put a reference to it in the models dictionary.
                self.Models[model_name] = model_class(**model_definition)

            except:
                # if the above fails then search for the model class in the custom models folder
                try:
                    # try to import the module holding the model class from the custom models folder
                    model_module = importlib.import_module('custom_models.' + model_type)
                    
                    # get the model class from the module
                    model_class = getattr(model_module, model_type)
                    
                    # instantiate the model class with the properties stored in the model_definition and put a reference to it in the models dictionary
                    self.Models[model_name] = model_class(**model_definition)
                except:
                    # a module holding the desired model class is not found in the core_models or custom_models folder
                    self.Logger(f"{model_type} error or the model was not found in core_models nor custom_models folder.", True)
                    error_counter += 1

        # initialize a datacollector
        self.DataCollector =  DataCollector(self)

        # initialize an model interface
        self.Interface = Interface(self)

        # if there are no errors then call the InitModel method on the models to initialize them.
        if (error_counter == 0):
            # determine initialization error counter
            init_error = 0
            # initialize all models by calling the InitModel method which all models should expose.
            for name, model in self.Models.items():
                try:
                    model.InitModel(self)
                    # self.Logger(f"{name} loaded and initialized.")
                except:
                    self.Logger(f"{name} initialization error.", True)
                    init_error += 1
            # check whether any errors occured during the initialization phase
            if (init_error == 0):
                self.Initialized = True
                self.Logger(f"All models of {self.Name} loaded and initialized correctly. Have fun!", True)
            else:
                self.Logger(f"{self.Name}: initialization error.", True)
        else:
            self.Logger(f"{self.Name}: loading error.", True)


    def Start(self):
        # start the realtime model
        pass

    def Stop(self):
        # stop the realtime model
        pass

    def Calculate(self, time_to_calculate = 10.0):
        # calculate the number of model steps needed
        no_steps = int(time_to_calculate / self.ModelingStepsize)

        # do the calculations
        for i in range(no_steps):
            # iterate over all the models and call the StepModel method of each model 
            for _, model in self.Models.items():
                model.StepModel()
            
            # update the datacollector
            self.DataCollector.Update()
            
    def Logger(self, log_message, always_print = False):
        if (self._logging):
            if (self._verbose or always_print):
                print(log_message)
