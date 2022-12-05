import json, importlib
from explain_core.helpers.DataCollector import DataCollector
from explain_core.helpers.Interface import Interface

class ModelEngine:
    # define the model attributes
    name = ""
    description = ""
    initialized = False
    weight = 3.3
    model_time_total: float = 0.0
    modeling_stepsize = 0.0005

    # define an object holding all model components
    components = {}

    # define a datacollector
    datacollector = {}
    
    # define an interface
    interface = {}

    # define the constructor
    def __init__(self, model_definition: str):
        # initialize all model components with the parameters from the JSON file
        self.initialized = self.initialize_model(model_definition)

    def initialize_model(self, model_definition: str):
        # set the error counter = 0
        error_counter = 0

        # open the json file
        json_file = open(model_definition)

        # return a python dictionary object for processing
        model_definition = json.load(json_file)

        # initialize the model using the properties stored in the model definition file
        self.name = model_definition['Name']
        self.description = model_definition['Description']
        self.weight = model_definition['Weight']
        self.model_time_total = model_definition['ModelTimeTotal']
        self.modeling_stepsize = model_definition['ModelingStepsize']

        # initialize all model components and put a reference to them in the components list
        for key, component in model_definition['Components'].items():
            # try to find the desired model class from the core_models or custom_models folder
            try:
                # first find the model type of the component, so we can instantiate the correct model
                model_type = component["ModelType"]
                # try to import the module holding the model class from the core_models folder
                model_module = importlib.import_module('explain_core.core_models.' + model_type)
                # get the model class from the module
                model_class = getattr(model_module, model_type)
                # instantiate the model class with the properties stored in the model_definition file and a reference to the other components and add it to the components dictionary
                self.components[key] = model_class(**component)
            except:
                try:
                    # try to import the module holding the model class from the custom models folder
                    model_module = importlib.import_module('custom_models.' + model_type)
                    # get the model class from the module
                    model_class = getattr(model_module, model_type)
                    # instantiate the model class with the properties stored in the model_definition file and a reference to the other components and add it to the components dictionary
                    self.components[key] = model_class(**component)
                except:
                    # a module holding the desired model class is not found in the core_models or custom_models folder
                    print(f"{model_type} model not found in the core_models nor in the custom_models folder.")
                    error_counter += 1

        # initialize a datacollector
        self.datacollector =  DataCollector(self)

        # initialize a visualizer
        self.interface = Interface(self)

        if (error_counter == 0):
            # initialize all components
            for _, comp in self.components.items():
                comp.InitModel(self)

            print(f"{self.name} model loaded and initialized correctly.")
        else:
            print(f"{self.name} model failed to load correctly producing {error_counter} errors.")


    def start(self):
        # start the realtime model
        pass

    def stop(self):
        # stop the realtime model
        pass

    def calculate(self, time_to_calculate = 10.0):
        pass

    def model_step(self):
        pass

    def rt_model_step(self):
        pass

    def print_performance(self, perf):
        pass

