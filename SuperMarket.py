from SimPy.Simulation import *
import random
import numpy as np
import math

class G:
    boringCashRegister = [] # Cajas individuales con una cola por caja
    awsmeCashRegister = []  # Cajas con una cola para todas las cajas
class Arrivals(Process):
    
    def run(self,clientArrivalsRate,maxCartSize):
        i = 0
        r = 0
        arrivals = clientArrivalsRate.keys()
        while(True):    
            c = Client(str(i),random.uniform(1,maxCartSize)) 
            activate(c, c.run())
            # calcula el tiempo del prox arribo...
            if(arrivals[r] >= i & i != 0):
                r+=1  #cambia la tasa de arribo para el tiempo especificado
            t = random.expovariate(1. / clientArrivalsRate[r])
            yield hold, self, t
            i+=1


class Client(Process):

    def __init__(self, id,cartQty):
        Process.__init__(self)
        self.id = id
        self.arrivalTime = now()
        self.cartQty = cartQty

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

        minBoringCashRegisterQQ = sys.maxint
        boringCashRegisterIndex = 0
        for i in range(len(G.boringCashRegister)):  # busca cajas individuales libres
            bQQ = len(G.boringCashRegister[i].waitQ)
            if(bQQ == 0):
                print now(),"Cliente ",self.id, "entra en caja ",G.boringCashRegister[i].name
                yield request,self,G.boringCashRegister[i]
            elif(bQQ < minBoringCashRegisterQQ):
                minBoringCashRegisterQQ = bQQ       
                boringCashRegisterIndex = i
                  
        minAwsmeCashRegisterQQ = sys.maxint
        awsmeCashRegisterIndex = 0
        for i in range(len(G.awsmeCashRegister)):  # busca cajas de una sola cola libres
            aQQ = len(G.awsmeCashRegister[i].waitQ)
            if(aQQ == 0):
                print now(),"Cliente ",self.id, "entra en caja ",G.boringCashRegister[i].name
                yield request,self,G.awsmeCashRegister[i]
            elif(aQQ < minAwsmeCashRegisterQQ):
                minAwsmeCashRegisterQQ = aQQ  
                awsmeCashRegisterIndex = i       

        if(minBoringCashRegisterQQ < minAwsmeCashRegisterQQ):  ## compara cual de los 2 tipos tiene menos
            print now(),"Cliente ",self.id, "entra en caja ",G.boringCashRegister[boringCashRegisterIndex].name
            yield request,self,G.boringCashRegister[boringCashRegisterIndex]           
        else:
            print now(),"Cliente ",self.id, "entra en caja ",G.boringCashRegister[awsmeCashRegisterIndex].name
            yield request,self,G.awsmeCashRegister[awsmeCashRegisterIndex]


def cashRegisterGenerator(boringCashRegisterQTY,awsmeCashRegisterQTY):
    for i in range(awsmeCashRegisterQTY):
            G.awsmeCashRegister.append(Resource(capacity=1,name='awsmeCR_' + str(i),monitored=True))
    for i in range(boringCashRegisterQTY):
            G.boringCashRegister.append(Resource(capacity=1,name='boringCR_' + str(i),monitored=True))
    


def model(maxtime,boringCashRegisterQTY,awsmeCashRegisterQTY,clientArrivalsRate,maxCartSize):  

        initialize()

        # server definition
        cashRegisterGenerator(boringCashRegisterQTY,awsmeCashRegisterQTY)
        
        #  exectuion
        a = Arrivals()
        activate(a, a.run(clientArrivalsRate,maxCartSize))
        simulate(until=maxtime)


model(2000,8,2,{0: 0.9, 1000: 0.7, 3000: 0.5},50)