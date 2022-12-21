import math, os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path

import warnings
warnings.filterwarnings("ignore")


class Interface:
    def __init__(self, modelEngine):
        # initialize the super class
        super().__init__()

        # store a reference to the model instance
        self._modelEngine = modelEngine

        # get the modeling stepsize from the model
        self.t = modelEngine.ModelingStepsize

        # plot line colors
        self.lines = ['r-', 'b-', 'g-', 'c-', 'm-', 'y-', 'k-', 'w-']

        # define a list holding the prop changes
        self.propChanges = []
        self.prop_update_interval = 0.015
        self.prop_update_counter = 0
        
        self.output_path = str(os.path.join(Path().absolute())) + r'/'
    
    def calculate(self, time_to_calculate = 10):
        self._modelEngine.Calculate(time_to_calculate)

    # property setters and getters
    def process_prop_changes(self):
        # process the propchanges
        if (self.prop_update_counter >= self.prop_update_interval):
            self.prop_update_counter = 0
            for change in self.propChanges:
                change.update()
                if change.completed:
                    self.propChanges.remove(change)

        self.prop_update_counter += self.t
        
    def set_property(self, prop, new_value, in_time = 0, at_time = 0):
        prop = self.find_model_prop(prop)
        if (prop != None):
            # check whether the type of new_value is the same as the model type
            if type(new_value) == type(getattr(prop['model'], prop['prop'])):
                new_prop_change = propChange(prop, new_value, in_time, at_time)
                self.propChanges.append(new_prop_change)
                print(f"{prop['label']} is scheduled to change from {new_prop_change.initial_value} to {new_value} in {in_time} sec. at {at_time} sec. during next model run.")
            else:
                current_value_type = type(getattr(prop['model'], prop['prop']))
                new_value_type = type(new_value)
                print(f'property type mismatch. model property type = {current_value_type}, new value type = {new_value_type}')
        else:
            print("property not found in model")

        print(self.propChanges)
    
    def get_property(self, prop):
        prop = self.find_model_prop(prop)
        if (prop != None):
            value = getattr(prop['model'], prop['prop'])
        return value

    def find_model_prop(self, prop):
        # split the model from the prop
        t  = prop.split(sep=".")
        if (len(t) == 2):
          # try to find the parameter in the model
          if t[0] in self._modelEngine.Models:
            if (hasattr(self._modelEngine.Models[t[0]], t[1])):
              return { 'label': prop, 'model': self._modelEngine.Models[t[0]], 'prop': t[1]}

        return None    
    
     # getters
    def get_vitals(self, aorta = "AA", right_atrium = "RA", pulmonary_artery = "PA"):
        vitals = {
            "heartrate": self._modelEngine.Models['Heart'].HeartRate,
            "spo2": self._modelEngine.Models[aorta].So2,
            "abp_systole": self._modelEngine.Models[aorta].PresMax,
            "abp_diastole": self._modelEngine.Models[aorta].PresMin,
            "pap_systole": self._modelEngine.Models[pulmonary_artery].PresMax,
            "pap_diastole": self._modelEngine.Models[pulmonary_artery].PresMin,
            "cvp": (2 * self._modelEngine.Models[right_atrium].PresMax + self._modelEngine.Models[right_atrium].PresMin) / 3,
            "resp_rate": self._modelEngine.Models['Breathing'].RespRate
        }
        
        return vitals
    
    def get_gas_flows(self, time_to_calculate = 10):
        self._modelEngine.DataCollector.clear_watchlist()

        properties = []
        for component in self._modelEngine.Models:
            component_type = self._modelEngine.Models[component].ModelType

            if (component_type == "GasResistor"):
                properties.append(component + ".Flow")

        self.analyze(properties, time_to_calculate)
        
    def get_blood_flows(self, time_to_calculate = 10):
        self._modelEngine.DataCollector.clear_watchlist()

        properties = []
        for component in self._modelEngine.Models:
            component_type = self._modelEngine.Models[component].ModelType

            if (component_type == "BloodResistor"):
                properties.append(component + ".Flow")

        self.analyze(properties, time_to_calculate, sampleinterval=0.0005)

    def get_blood_gas(self, component = 'AA'):
        # define a dictionary which is going to hold the bloodgas
        bg={}
        
        # find the component type as we only can calculate the bloodgas in a blood or time-varying elastance component
        component_type = self._modelEngine.Models[component].ModelType
                        
        # check whether the desired component is of an appropriate type and contains blood.
        if (component_type == "BloodCompliance" or component_type == "TimeVaryingElastance"):
            # calculate the acidbase and oxygenation
            ab = self._modelEngine.AcidBase.calc_acid_base(self._modelEngine.Models[component].Tco2)
            oxy = self._modelEngine.Oxygenation.calc_oxygenation(self._modelEngine.Models[component].To2)
            
        if (not ab.Error):
            bg["Ph"] = ab.Ph
            bg["Pco2"] = ab.Pco2
            bg["Hco3"] = ab.Hco3
        
        if (not oxy.Error):
            bg["Po2"] = oxy.Po2
            bg["So2"] = oxy.So2

        return bg
    
    def get_blood_pressures(self, time_to_calculate = 10):
        self._modelEngine.DataCollector.clear_watchlist()

        properties = []
        for component in self._modelEngine.Models:
            component_type = self._modelEngine.Models[component].ModelType
            if (component_type == "BloodCompliance" or component_type == "TimeVaryingElastance"):
                properties.append(component + ".Pres")

        self.analyze(properties, time_to_calculate)
            
    def get_total_blood_volume(self):
        total_volume = 0
        pulm_blood_volume = 0
        pulm_cap_volume = 0
        syst_blood_volume = 0
        heart_volume = 0
        cap_volume = 0
        ven_volume = 0
        art_volume = 0
        upper_body = 0
        lower_body = 0
        
        for component in self._modelEngine.Models:
            component_type = self._modelEngine.Models[component].ModelType
                
            if (component_type == "BloodCompliance" or component_type == "TimeVaryingElastance"):
                total_volume += self._modelEngine.Models[component].Vol

            if component == 'PA' or component == 'PV':
                pulm_blood_volume += self._modelEngine.Models[component].Vol
            if component == 'LL' or component == 'RL':
                pulm_blood_volume += self._modelEngine.Models[component].Vol
                pulm_cap_volume += self._modelEngine.Models[component].Vol
            
            # heart
            if component == 'RA' or component == 'RV' or component == 'LA' or component == 'LV' or component == 'COR' :
                heart_volume += self._modelEngine.Models[component].Vol
            # capillaries
            if component == 'RLB' or component == 'RUB' or component == 'BR' or component == 'INT' or component == 'LS' or component == 'KID':
                cap_volume += self._modelEngine.Models[component].Vol
            # venous
            if component == 'IVCI' or component == 'IVCE' or component == 'SVC' :
                ven_volume += self._modelEngine.Models[component].Vol
            if component == 'AA' or component == 'AAR' or component == 'AD':
                art_volume += self._modelEngine.Models[component].Vol
            if component == 'RUB' or component == 'BR' or component == 'SVC':
                upper_body += self._modelEngine.Models[component].Vol
            if component == 'RLB' or component == 'AAR' or component == 'AA' or component == 'AD' or component == 'IVCI' or component == 'IVCE' or component == 'INT' or component == 'LS' or component == 'KID':
                lower_body+= self._modelEngine.Models[component].Vol
                
            
                
        syst_blood_volume = total_volume - pulm_blood_volume
        
        print (f"Total blood volume: {total_volume * 1000 / self._modelEngine.weight} ml/kg = {total_volume / total_volume * 100}%")
        print (f"Systemic blood volume: {syst_blood_volume * 1000 / self._modelEngine.weight} ml/kg = {syst_blood_volume / total_volume * 100}%")
        print (f"Pulmonary total blood volume: {pulm_blood_volume * 1000 / self._modelEngine.weight} ml/kg = {pulm_blood_volume / total_volume * 100}%")
        print (f"Pulmonary capillary blood volume: {pulm_cap_volume * 1000 / self._modelEngine.weight} ml/kg = {pulm_cap_volume / pulm_blood_volume * 100}% of total pulmonary blood volume")
        print (f"Heart blood volume: {heart_volume * 1000 / self._modelEngine.weight} ml/kg = {heart_volume / total_volume * 100}%")
        print (f"Capillary blood volume: {cap_volume * 1000 / self._modelEngine.weight} ml/kg = {cap_volume / total_volume * 100}%")
        print (f"Venous blood volume: {ven_volume * 1000 / self._modelEngine.weight} ml/kg = {ven_volume / total_volume * 100}%")
        print (f"Arterial blood volume: {art_volume * 1000 / self._modelEngine.weight} ml/kg = {art_volume / total_volume * 100}%")
        print (f"Upper body blood volume: {upper_body * 1000 / self._modelEngine.weight} ml/kg = {upper_body / total_volume * 100}%")
        print (f"Lower body blood volume: {lower_body * 1000 / self._modelEngine.weight} ml/kg = {lower_body / total_volume * 100}%")
        
        return total_volume
                      
    def get_blood_volumes(self, time_to_calculate = 10):
        self._modelEngine.DataCollector.clear_watchlist()

        properties = []
        for component in self._modelEngine.Models:
            component_type = self._modelEngine.Models[component].ModelType
            if (component_type == "BloodCompliance" or component_type == "TimeVaryingElastance"):
                properties.append(component + ".Vol")

        self.analyze(properties, time_to_calculate)

    def get_gas_pressures(self, time_to_calculate = 10):
        self._modelEngine.DataCollector.clear_watchlist()

        properties = []
        for component in self._modelEngine.Models:
            component_type = self._modelEngine.Models[component].ModelType

            if (component_type == "GasCompliance"):
                properties.append(component + ".Pres")

        self.analyze(properties, time_to_calculate)

    def get_gas_volumes(self, time_to_calculate = 10):
        self._modelEngine.DataCollector.clear_watchlist()

        properties = []
        for component in self._modelEngine.Models:
            if (self._modelEngine.Models[component].ModelType == "GasCompliance"):
                properties.append(component + ".Vol")

        self.analyze(properties, time_to_calculate)
    
    # inspectors
    def inspect_model(self):
        model = {}
        for component_name, component in self._modelEngine.Models.items():
            model[component_name]= component.Description
            
        return model
    
    def inspect_model_component(self, component):
        content = {}
        for attribute in dir(self._modelEngine.Models[component]):
            if not attribute.startswith('__'):
                attr_type = type(getattr(self._modelEngine.Models[component],attribute))
                if (attr_type is str) or (attr_type is float) or (attr_type is bool) or (attr_type is int):
                    content[attribute] = getattr(self._modelEngine.Models[component], attribute)
        return content
        
    def analyze(self, properties, time_to_calculate = 10, sampleinterval = 0.005, calculate=True):
        if calculate:
            # first clear the watchllist and this also clears all data
            self._modelEngine.DataCollector.clear_watchlist()

            # set the sample interval
            self._modelEngine.DataCollector.set_sample_interval(sampleinterval)

            # add the property to the watchlist
            if (isinstance(properties, str)):
              properties = [properties]

            # add the properties to the watch_list
            for prop in properties:
              prop_reference = self.find_model_prop(prop)
              if (prop_reference != None):
                self._modelEngine.DataCollector.add_to_watchlist(prop_reference)

            # calculate the model steps
            self._modelEngine.Calculate(time_to_calculate)

        print("")

        parameters = []
        no_parameters = 0
        # get the watch list of the datacollector
        for watched_parameter in self._modelEngine.DataCollector.watch_list:
          parameters.append(watched_parameter['label'])

        no_dp = len(self._modelEngine.DataCollector.collected_data)
        x = np.zeros(no_dp)
        y = []
        heartbeats = 0

        for parameter in enumerate(parameters):
          y.append(np.zeros(no_dp))
          no_parameters += 1

        for index,t in enumerate(self._modelEngine.DataCollector.collected_data):
          x[index] = t['time']

          for idx, parameter in enumerate(parameters):
            y[idx][index] = t[parameter]

        for idx, parameter in enumerate(parameters):
          prop_category  = parameter.split(sep=".")

          if prop_category[1] == "pres":
            data = np.array(y[idx])
            max = round(np.amax(data), 5)
            min = round(np.amin(data), 5)

            print("{:<16}: max {:10}, min {:10} mmHg". format(parameter, max, min))
            continue

          if prop_category[1] == "vol":
            data = np.array(y[idx])
            max = round(np.amax(data) * 1000, 5)
            min = round(np.amin(data) * 1000, 5)

            print("{:<16}: max {:10}, min {:10} ml/kg". format(parameter, max, min))
            continue
            
          if prop_category[1] == "NccVentricular":
            data = np.array(y[idx])
            heartbeats = np.count_nonzero(data == 1)
            continue
            
          if prop_category[1] == "flow":
            data = np.array(y[idx])
            data_forward = np.where(data > 0, data, 0)
            data_backward = np.where(data < 0, data, 0)
            
            t_start = x[0]
            t_end = x[-1]
            
            sum = np.sum(data)
            sum_forward = np.sum(data_forward)
            sum_backward = np.sum(data_backward)
            
            flow = (sum * sampleinterval / (t_end - t_start))
            flow = round(flow * 1000, 5)
            flow_forward = 0
            flow_backward = 0
            
            if (flow != 0.0):
                flow_forward = (sum_forward / sum) * flow
                flow_forward = round(flow_forward, 5)

                flow_backward = (sum_backward / sum) * flow
                flow_backward = round(flow_backward, 5)
            
            bpm = (heartbeats / (t_end - t_start)) * 60
            if (sampleinterval != self._modelEngine.modeling_stepsize):
                print(f"Stroke volume calculation might be inaccurate. Try using a sampleinterval of {self._modelEngine.modeling_stepsize}")
                bpm = self._modelEngine.Models['Heart'].heart_rate
            sv = round(flow / bpm, 5)
            print("{:16}: net {:10}, forward {:10}, backward {:10} ml/kg/min, stroke volume: {:10} ml/kg, ". format(parameter, flow, flow_forward, flow_backward, sv))

            continue

          if prop_category[1] == "NccAtrial":
            continue
            
          data = np.array(y[idx])
          max = round(np.amax(data), 5)
          min = round(np.amin(data), 5)
          print("{:<16}: max {:10} min {:10}". format(parameter, max, min))

    # plotters    
    def plot_time_graph (self, properties, time_to_calculate = 10,  combined = True, sharey = True, ylabel = '',  autoscale=True, ylowerlim = 0, yupperlim = 100, fill=True, fill_between=False, zeroline=False, sampleinterval = 0.005, analyze=True):
        # first clear the watchllist and this also clears all data
        self._modelEngine.DataCollector.clear_watchlist()

        # set the sample interval
        self._modelEngine.DataCollector.set_sample_interval(sampleinterval)

        # add the property to the watchlist
        if (isinstance(properties, str)):
          properties = [properties]

        # add the properties to the watch_list
        for prop in properties:
          prop_reference = self.find_model_prop(prop)
          if (prop_reference != None):
            self._modelEngine.DataCollector.add_to_watchlist(prop_reference)

        # calculate the model steps
        self._modelEngine.Calculate(time_to_calculate)

        # plot the properties
        self.draw_time_graph(sharey, combined, ylabel, autoscale, ylowerlim, yupperlim, fill, fill_between, zeroline)
        
        # analyze
        if analyze:
            self.analyze(properties, time_to_calculate, sampleinterval, calculate=False)

    def plot_xy_graph(self, property_x, property_y, time_to_calculate = 2, sampleinterval = 0.0005):
        # first clear the watchllist and this also clears all data
        self._modelEngine.DataCollector.clear_watchlist()

         # set the sample interval
        self._modelEngine.DataCollector.set_sample_interval(sampleinterval)

        prop_reference_x = self.find_model_prop(property_x)
        if (prop_reference_x != None):
          self._modelEngine.DataCollector.add_to_watchlist(prop_reference_x)

        prop_reference_y = self.find_model_prop(property_y)
        if (prop_reference_y != None):
          self._modelEngine.DataCollector.add_to_watchlist(prop_reference_y)

        # calculate the model steps
        self._modelEngine.Calculate(time_to_calculate)

        self.draw_xy_graph(property_x, property_y)
    
      # plotters
    def plot_vitals(self, time = 10, aorta = "AA", heart = "Heart", breathing = "Breathing"):
        self.plot_time_graph([  aorta + ".PresMax", aorta + ".PresMin", heart + ".HeartRate",  breathing +".RespRate", "AA.so2"], time_to_calculate=time, combined=True, sharey=False, autoscale=False, ylowerlim=0, yupperlim=200, fill=False, fill_between=True)
    
    # lung plotters
    def plot_lung_pressures(self, time=10, dead_space = "DS", left_lung = "ALL", right_lung= "ALR", combined=True, sharey=True, autoscale=True, ylowerlim=0, yupperlim=100, fill=False, analyze=False):
        self.plot_time_graph([ dead_space + ".Pres",left_lung + ".Pres", right_lung + ".Pres"], time_to_calculate=time, autoscale=True, combined=combined, sharey=sharey, sampleinterval = 0.0005, ylowerlim=ylowerlim, yupperlim=yupperlim, fill=fill, fill_between=False,analyze=analyze)
    
    def plot_lung_volumes(self, time=10, left_lung = "ALL", right_lung= "ALR", combined=True, sharey=True, autoscale=True, ylowerlim=0, yupperlim=100, fill=False, analyze=False):
        self.plot_time_graph([left_lung + ".Vol", right_lung + ".Vol"], time_to_calculate=time, autoscale=True, combined=combined, sharey=sharey, sampleinterval = 0.0005, ylowerlim=ylowerlim, yupperlim=yupperlim, fill=fill, fill_between=False, analyze=analyze)
    
    def plot_lung_flows(self, time=10, mouth = "MOUTH_DS", left_lung = "DS_ALL", right_lung = "DS_ALR", combined=True, sharey=True, autoscale=True, ylowerlim=0, yupperlim=100, fill=False, analyze=False):
        self.plot_time_graph([ mouth + ".Flow", left_lung + ".Flow", right_lung +".Flow"], time_to_calculate=time, autoscale=True, combined=combined, sharey=sharey, sampleinterval = 0.0005, ylowerlim=ylowerlim, yupperlim=yupperlim, fill=fill, fill_between=False, analyze=analyze)

    # heart plotters
    def plot_heart_pressures(self, time=2, lv = "LV", rv = "RV", la = "LA", ra = "RA", aorta = "AA", pulm_artery = "PA", combined=True, sharey=True, autoscale=True, ylowerlim=0, yupperlim=100, fill=True, fill_between=False, analyze=False):
        self.plot_time_graph([ lv + ".Pres", rv +".Pres", la + ".Pres", ra + ".Pres", aorta + ".Pres", pulm_artery + ".Pres"], time_to_calculate=time, autoscale=True, combined=combined, sharey=sharey, sampleinterval = 0.0005, ylowerlim=ylowerlim, yupperlim=yupperlim, fill=fill, fill_between=False, analyze=analyze)
        
    def plot_heart_volumes(self, time=2, lv = "LV", rv = "RV", la = "LA", ra = "RA", combined=True, sharey=True, autoscale=True, ylowerlim=0, yupperlim=100, fill=True, analyze=False):
        self.plot_time_graph([ lv + ".Vol", rv + ".Vol", la + ".Vol", ra + ".Vol"], time_to_calculate=time, autoscale=True, combined=combined, sharey=sharey, sampleinterval = 0.0005, ylowerlim=ylowerlim, yupperlim=yupperlim, fill=fill, fill_between=False, analyze=analyze)
    
    def plot_heart_flows(self, time=2, la_lv = "LA_LV", lv_aorta = "LV_AA", ra_rv = "RA_RV", rv_pulm_artery = "RV_PA", combined=True, sharey=True, autoscale=True, ylowerlim=0, yupperlim=100, fill=True, analyze=False):
        self.plot_time_graph([ la_lv + ".Flow", lv_aorta + ".Flow", ra_rv + ".Flow", rv_pulm_artery + ".Flow"], time_to_calculate=time, autoscale=True, combined=combined, sharey=sharey, sampleinterval = 0.0005, ylowerlim=ylowerlim, yupperlim=yupperlim, fill=fill, fill_between=False, analyze=analyze)
        
    def plot_heart_pressures_left(self, time=2, la = "LA", lv = "LV", aorta = "AA",  combined=True, sharey=True, autoscale=True, ylowerlim=0, yupperlim=100, fill=True, analyze=False):
        self.plot_time_graph([lv + ".Pres", la + ".Pres", aorta + ".Pres"], time_to_calculate=time, autoscale=True, combined=combined, sharey=sharey, sampleinterval = 0.0005, ylowerlim=ylowerlim, yupperlim=yupperlim, fill=fill, fill_between=False, analyze=analyze)
        
    def plot_heart_flows_left(self, time=2,la_lv="LA_LV", lv_aorta="LV_AA", combined=True, sharey=True, autoscale=True, ylowerlim=0, yupperlim=100, fill=True, analyze=False):
        self.plot_time_graph([la_lv+".Flow", lv_aorta+".Flow"],time_to_calculate=time, autoscale=True, combined=combined, sharey=sharey, sampleinterval = 0.0005, ylowerlim=ylowerlim, yupperlim=yupperlim, fill=fill, fill_between=False, analyze=analyze)
    
    def plot_heart_volumes_left(self, time=2, la="LA", lv="LV", combined=True, sharey=True, autoscale=True, ylowerlim=0, yupperlim=100, fill=True, analyze=False):
        self.plot_time_graph([la+".Vol", lv+".Vol"], time_to_calculate=time, autoscale=True, combined=combined, sharey=sharey, sampleinterval = 0.0005, ylowerlim=ylowerlim, yupperlim=yupperlim, fill=fill, fill_between=False, analyze=analyze)
    
    def plot_heart_flows_right(self, time=2, ra_rv="RA_RV", rv_pulm_artery="RV_PA", combined=True, sharey=True, autoscale=True, ylowerlim=0, yupperlim=100, fill=True, analyze=False):
        self.plot_time_graph([ra_rv + ".Flow", rv_pulm_artery +".Flow"], time_to_calculate=time, autoscale=True, combined=combined, sharey=sharey, sampleinterval = 0.0005, ylowerlim=ylowerlim, yupperlim=yupperlim, fill=fill, fill_between=False, analyze=analyze)
    
    def plot_heart_volumes_right(self, time=2, ra="RA", rv="RV", combined=True, sharey=True, autoscale=True, ylowerlim=0, yupperlim=100, fill=True, analyze=False):
        self.plot_time_graph([ra + ".Vol", rv + ".Vol"], time_to_calculate=time, autoscale=True, combined=combined, sharey=sharey, sampleinterval = 0.0005, ylowerlim=ylowerlim, yupperlim=yupperlim, fill=fill, fill_between=False, analyze=analyze)
        
    def plot_heart_pressures_right(self,time=2, ra="RA", rv="RV", pulm_artery="PA", combined=True, sharey=True, autoscale=True, ylowerlim=0, yupperlim=100, fill=True, analyze=False):
        self.plot_time_graph([ rv + ".Pres", ra + ".Pres", pulm_artery + ".Pres"], time_to_calculate=time, autoscale=True, combined=combined, sharey=sharey, sampleinterval = 0.0005, ylowerlim=ylowerlim, yupperlim=yupperlim, fill=fill, fill_between=False, analyze=analyze)
    
    def plot_heart_left(self, time=2, la="LA", lv="LV",la_lv="LA_LV",lv_aorta="LV_AA", combined=True, sharey=True, autoscale=True, ylowerlim=0, yupperlim=100, fill=True, analyze=False):
        self.plot_time_graph([la + ".Pres", lv + ".Pres", la_lv + ".Flow", lv_aorta + ".Flow"], time_to_calculate=time, autoscale=True, combined=combined, sharey=sharey, sampleinterval = 0.0005, ylowerlim=ylowerlim, yupperlim=yupperlim, fill=fill, fill_between=False, analyze=analyze)
        
    def plot_heart_right(self, time=2, ra="RA", rv="RV", ra_rv="RA_RV", rv_pulm_artery="RV_PA", combined=True, sharey=True, autoscale=True, ylowerlim=0, yupperlim=100, fill=True, analyze=False):
        self.plot_time_graph([ra + ".Pres", rv + ".Pres", ra_rv + ".Flow", rv_pulm_artery + ".Flow"], time_to_calculate=time, autoscale=True, combined=combined, sharey=sharey, sampleinterval = 0.0005, ylowerlim=ylowerlim, yupperlim=yupperlim, fill=fill, fill_between=False, analyze=analyze)

    def plot_pda(self, time=2, pda = "DA", combined=True, sharey=True, autoscale=True, ylowerlim=0, yupperlim=100, fill=True, analyze=False):
        self.plot_time_graph([pda + ".Flow"], time_to_calculate=time, autoscale=True, combined=combined, sharey=sharey, sampleinterval = 0.0005, ylowerlim=ylowerlim, yupperlim=yupperlim, fill=fill, fill_between=False, analyze=analyze)
        
    def plot_ofo(self, time=2, ofo = "FO", combined=True, sharey=True, autoscale=True, ylowerlim=0, yupperlim=100, fill=True, analyze=False):
        self.plot_time_graph([ofo +".Flow"], time_to_calculate=time, autoscale=True, combined=combined, sharey=sharey, sampleinterval = 0.0005, ylowerlim=ylowerlim, yupperlim=yupperlim, fill=fill, fill_between=False, analyze=analyze)
        
    def plot_shunts(self, time=2, pda = "DA", ofo = "FO", vsd = "VSD", combined=True, sharey=True, autoscale=True, ylowerlim=0, yupperlim=100, fill=True, analyze=False):
        self.plot_time_graph([pda + ".Flow", ofo + ".Flow", vsd + ".Flow"], time_to_calculate=time, autoscale=True, combined=combined, sharey=sharey, sampleinterval = 0.0005, ylowerlim=ylowerlim, yupperlim=yupperlim, fill=fill, fill_between=False, analyze=analyze)
        

    def plot_ventilator_curves(self, time=10, ventilator = "MechanicalVentilator", combined=False, sharey=False, autoscale=True, ylowerlim=0, yupperlim=100, fill=False, analyze=True):
        self.plot_time_graph([ ventilator + ".Pressure", ventilator + ".Flow", ventilator + ".Volume"], time_to_calculate=time, autoscale=True, combined=combined, sharey=sharey, sampleinterval = 0.0005, ylowerlim=ylowerlim, yupperlim=yupperlim, fill=fill, fill_between=False, analyze=analyze)
    
    def write_to_excel (self, properties, filename='data', time_to_calculate = 10, sampleinterval = 0.005, calculate=True):
        self.analyze(properties, time_to_calculate = time_to_calculate, sampleinterval = sampleinterval, calculate=calculate)
        # build a parameter list
        parameters = ['time']
        no_parameters = 0
        # get the watch list of the datacollector
        for watched_parameter in self._modelEngine.DataCollector.watch_list:
            if (watched_parameter['label'] != "Heart.NccVentricular" and watched_parameter['label'] != "Heart.NccAtrial"):
                parameters.append(watched_parameter['label'])

        data = []
        for index,t in enumerate(self._modelEngine.DataCollector.collected_data):
            dataline = []
            for idx, parameter in enumerate(parameters):
                dataline.append(t[parameter])
            data.append(dataline)
            
        df = pd.DataFrame(data, columns=parameters)
        path = self.output_path + filename + '.xlsx'
        df.to_excel(path)        
    
    def draw_xy_graph(self, property_x, property_y):
        no_dp = len(self._modelEngine.DataCollector.collected_data)
        x = np.zeros(no_dp)
        y = np.zeros(no_dp)

        for index,t in enumerate(self._modelEngine.DataCollector.collected_data):
          x[index] = t[property_x]
          y[index] = t[property_y]

        plt.figure( figsize=(3, 3), dpi=300)
        # Subplot of figure 1 with id 211 the data (red line r-, first legend = parameter)
        plt.plot(x, y, self.lines[0], linewidth=1)
        plt.xlabel(property_x, fontsize=6)
        plt.ylabel(property_y, fontsize=6)
        plt.xticks(fontsize=6)
        plt.yticks(fontsize=6)

        plt.show()

    def draw_time_graph(self, sharey = False, combined = True, ylabel = '', autoscale=True, ylowerlim = 0, yupperlim = 100, fill=True, fill_between=False, zeroline=False):
        parameters = []
        no_parameters = 0
        # get the watch list of the datacollector
        for watched_parameter in self._modelEngine.DataCollector.watch_list:
          if (watched_parameter['label'] != "Heart.NccVentricular" and watched_parameter['label'] != "Heart.NccAtrial"):
            parameters.append(watched_parameter['label'])

        no_dp = len(self._modelEngine.DataCollector.collected_data)
        x = np.zeros(no_dp)
        y = []

        for parameter in enumerate(parameters):
          y.append(np.zeros(no_dp))
          no_parameters += 1

        for index,t in enumerate(self._modelEngine.DataCollector.collected_data):
          x[index] = t['time']

          for idx, parameter in enumerate(parameters):
            y[idx][index] = t[parameter]


        # determine number of needed plots
        if (no_parameters == 1):
            combined = True
            
        if (combined == False):
          
          fig, axs = plt.subplots(nrows=no_parameters, ncols=1, figsize=(18, 3 * no_parameters), sharex=True, sharey=sharey, constrained_layout=True)
          if (no_parameters > 1):
            for i, ax in enumerate(axs):
              ax.plot(x, y[i], self.lines[i], linewidth=1)
              ax.set_title(parameters[i], fontsize=10)
              ax.set_xlabel('time (s)', fontsize=8)
              ax.set_ylabel(ylabel, fontsize=8) 
              if not autoscale:
                 ax.set_ylim([ylowerlim, yupperlim])
              if zeroline:
                  ax.hlines(0, np.amin(x),np.amax(x), linestyles='dashed')
              if fill:
                  ax.fill_between(x, y[i], color='blue', alpha=0.3)
          else:
              axs.plot(x, y[0], self.lines[0], linewidth=1)
              axs.set_title(parameters[0], fontsize=10)
              axs.set_xlabel('time (s)', fontsize=8)
              axs.set_ylabel(ylabel, fontsize=8)

              if not autoscale:
                 axs.set_ylim([ylowerlim, yupperlim])
              if zeroline:
                  ax.hlines(0, np.amin(x),np.amax(x), linestyles='dashed')
              if fill:
                  axs.fill_between(x, y[0], color='blue', alpha=0.3)

        if (combined):
          plt.figure( figsize=(18, 3), dpi=300)
          if not autoscale:
                plt.ylim([ylowerlim, yupperlim])
          for index, parameter in enumerate(parameters):
            # Subplot of figure 1 with id 211 the data (red line r-, first legend = parameter)
            plt.plot(x, y[index], self.lines[index], linewidth=1, label = parameter)
            if fill:
                plt.fill_between(x, y[index], color='blue', alpha=0.3)
          if zeroline:
            plt.hlines(0, np.amin(x),np.amax(x), linestyles='dashed')
          plt.xlabel('time (s)', fontsize=8)
          plt.ylabel(ylabel, fontsize=8)
          plt.xticks(fontsize=8)
          plt.yticks(fontsize=8)
          # Add a legend
          plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.22), ncol=6, fontsize=8)
          if fill_between:
                plt.fill_between(x, y[0], y[1], color='blue', alpha=0.1)

        plt.show()
        

    
class propChange:
  def __init__(self, prop, new_value, in_time, at_time = 0, update_interval = 0.015):

    self.prop = prop
    self.current_value = getattr(prop['model'], prop['prop'])
    self.initial_value = self.current_value
    self.target_value = new_value
    self.at_time = at_time
    self.in_time = in_time

    if (in_time > 0):
      self.step_size = ((self.target_value - self.current_value) / self.in_time) * update_interval
    else:
      self.step_size = 0

    
    self.update_interval = update_interval
    self.running = False
    self.completed = False
    self.running_time = 0
  
  def update (self):
    if self.completed == False:
      # check whether the property should start changing (if the at_time has passed)
      if self.running_time >= self.at_time:
        if (self.running == False):
          print(f"- {self.prop['label']} change started at {self.running_time}. Inital value: {self.initial_value}")
        self.running = True
      else:
        self.running = False

      self.running_time += self.update_interval

      if (self.running):
        self.current_value += self.step_size
        if abs(self.current_value - self.target_value) < abs(self.step_size):
          self.current_value = self.target_value
          self.step_size = 0
          self.running = False
          self.completed = True
          
        if (self.step_size == 0):
          self.current_value = self.target_value
          self.completed = True
          print(f"- {self.prop['label']} change stopped at {self.running_time}. New value: {self.current_value}")

        setattr(self.prop['model'], self.prop['prop'], self.current_value)

  def cancel (self):
    self.step_size = 0
    self.current_value = self.initial_value
    self.completed = True
    setattr(self.prop['model'], self.prop['prop'], self.current_value)

  def complete (self):
    self.step_size = 0
    self.current_value = self.target_value
    self.completed = True
    setattr(self.prop['model'], self.prop['prop'], self.current_value)