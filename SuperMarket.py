from SimPy.Simulation import *
import random
import numpy as np
import math



class Arrivals(Process):
    
    def run(self,clientArrivalsRate):
        i = 0
        while(True):    
            c = Client(str(i)) 
            activate(c, c.run())
            # calcula el tiempo del prox arribo...
            t = random.expovariate(1. / clientArrivalsRate)
            yield hold, self, t
            i+=1


class Client(Process):

    def __init__(self, id):
        Process.__init__(self)
        self.id = id
        self.arrivalTime = now()
   
    def weighted_choice(self,choices):
       total = sum(w for c, w in choices)
       r = random.uniform(0, total)
       upto = 0
       for c, w in choices:
          if upto + w >= r:
             return c
          upto += w
       
    def run(self):
        print now(),"Arribo Cliente ",self.id

def model(maxtime,clientArrivalsRate):   
        # inicializacion del motor de simulacion
        initialize()
        # definimos servers
        #  ejecucion
        a = Arrivals()
        activate(a, a.run())
        simulate(until=maxtime)