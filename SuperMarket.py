﻿from SimPy.Simulation import *
import random
import numpy as np
import math


#variables para mostrar resultados
resAvgWaitingBoringCR = 0
resAvgWaitingAwsCR = 0
resAvgWatingFastCR  = 0
resAvgServiceBoringCR = 0
resAvgServiceAwsCR = 0
resAvgServiceFastCR = 0



class G:
    boringCashRegister = [] # Cajas individuales con una cola por caja
    awsmeCashRegister = []  # Cajas con una cola para todas las cajas
    awsemCashRegisterManager = "Administrador de cajas de una sola cola" #vendria ser el cartel q le dice al cliente a q caja tiene q ir
    awsemCashWaitTime = Monitor('Tiempo de espera en cajas compartidas')
    boringCashWaitTime = Monitor('Tiempo de espera en cajas individuales')
    fastCashRegisterWaitTime = Monitor('Tiempo de espera en cajas rapidas')
    awsemCashServiceTime = Monitor('Tiempo de espera en cajas compartidas')
    boringCashServiceTime = Monitor('Tiempo de espera en cajas individuales')
    fastCashRegisterServiceTime = Monitor('Tiempo de espera en cajas rapidas')

class Arrivals(Process):
    
    def run(self,clientArrivalsRate,maxCartSize,boringServiceRate,awsmeServiceRate):
        i = 0
        r = 0
        arrivals = clientArrivalsRate.keys()
        while(True):    
            
            type = "smartClient"
            if (random.uniform(0,1) < 0.10):  # genera clientes tontos q no se fijan tamaño de la cola
                type = "dummyClient"
                
            c = Client(str(i),type,random.uniform(1,maxCartSize)) 
            activate(c, c.run(boringServiceRate,awsmeServiceRate))
            # calcula el tiempo del prox arribo...
            if(arrivals[r] >= i & i!=0):
                r+=1  #cambia la tasa de arribo para el tiempo especificado
                print "**********************************************"
                print "* TASA DE ARRIBO: ",clientArrivalsRate[r],"                        *"
                print "**********************************************"
            t = random.expovariate(1. / clientArrivalsRate[r])
            yield hold, self, t
            i+=1


class Client(Process):

    def __init__(self, id, type, cartQty):
        Process.__init__(self)
        self.id = id
        self.type = type
        self.arrivalTime = now()
        self.cartQty = cartQty

       
    def run(self,boringServiceRate,awsmeServiceRate):

        print now(),"Arribo Cliente ",self.id

        if(self.type == "smartClient"): #Cliente inteligente

            minBoringCashRegisterQQ = sys.maxint
            boringCashRegisterIndex = 0
            allBoringBussy = True
            for i in range(len(G.boringCashRegister)):  # busca cajas individuales libres
                bQQ = len(G.boringCashRegister[i].waitQ)
                if(bQQ == 0):
                    allBoringBussy = False
                    yield request,self,G.boringCashRegister[i]
                    print now(),"Cliente ",self.id, "entra en caja ",G.boringCashRegister[i].name
                    bt = random.uniform(1,boringServiceRate)
                    print now(),G.boringCashRegister[i].name,"atiende el Cliente ",self.id, " en un tiempo de ",bt
                    yield hold,self,bt
                    yield release,self,G.boringCashRegister[i]
                    print now(),"Fin Cliente",self.id
                    break
                elif(bQQ < minBoringCashRegisterQQ):
                    minBoringCashRegisterQQ = bQQ       
                    boringCashRegisterIndex = i
                  
            if(allBoringBussy):
                if(minBoringCashRegisterQQ < len(G.awsemCashRegisterManager.waitQ)):  ## compara cual de los 2 tipos tiene menos
                    yield request,self,G.boringCashRegister[boringCashRegisterIndex]         
                    print now(),"Cliente ",self.id, "entra en caja ",G.boringCashRegister[boringCashRegisterIndex].name       
                    bt = random.uniform(1,boringServiceRate)
                    print now(),G.boringCashRegister[boringCashRegisterIndex].name,"atiende el Cliente ",self.id, " en un tiempo de ",bt
                    yield hold,self,bt       
                    yield release,self,G.boringCashRegister[boringCashRegisterIndex]
                    print now(),"Fin Cliente",self.id
                else:
                    yield request,self,G.awsemCashRegisterManager
                    CRsbBussy = True
                    while (CRsbBussy):  # ADMINISTRADOR DE CAJAS busca cajas de una sola cola libre
                        for i in range(len(G.awsmeCashRegister)):
                            if(len(G.awsmeCashRegister[i].waitQ) == 0): # cuando encuentra una le asigna el turno al primer cliente de la cola
                                print now(),"Cliente ",self.id, "entra en caja ",G.awsmeCashRegister[i].name
                                CRsbBussy = False
                                yield release,self,G.awsemCashRegisterManager
                                yield request,self,G.awsmeCashRegister[i]
                                at = random.uniform(1,awsmeServiceRate)
                                print now(),G.awsmeCashRegister[i].name,"atiende el Cliente ",self.id, " en un tiempo de ",at
                                yield hold,self,at
                                yield release,self,G.awsmeCashRegister[i]
                                print now(),"Fin Cliente",self.id
                                break

        else: #cliente dummy
            
            if (random.uniform(0,1) < 0.50): #entra aleatoriamente en una caja individual
                selectedCashRegister = int(random.uniform(0,len(G.boringCashRegister)-1))
                yield request,self,G.boringCashRegister[selectedCashRegister]
                print now(),"Cliente Dummy ",self.id, "entra en caja ",G.boringCashRegister[selectedCashRegister].name
                bt = random.uniform(1,boringServiceRate)
                print now(),G.boringCashRegister[selectedCashRegister].name,"atiende el Cliente Dummy ",self.id, " en un tiempo de ",bt
                yield hold,self,bt
                yield release,self,G.boringCashRegister[selectedCashRegister]
                print now(),"Fin Cliente Dummy",self.id
            else:
                #entra aleatoriamente en caja de una sola cola
                yield request,self,G.awsemCashRegisterManager
                CRsbBussy = True
                while (CRsbBussy):  # ADMINISTRADOR DE CAJAS busca cajas de una sola cola libre
                        for i in range(len(G.awsmeCashRegister)):
                            if(len(G.awsmeCashRegister[i].waitQ) == 0): # cuando encuentra una le asigna el turno al primer cliente de la cola
                                print now(),"Cliente Dummy ",self.id, "entra en caja ",G.awsmeCashRegister[i].name
                                CRsbBussy = False
                                yield release,self,G.awsemCashRegisterManager
                                yield request,self,G.awsmeCashRegister[i]
                                at = random.uniform(1,awsmeServiceRate)
                                print now(),G.awsmeCashRegister[i].name,"atiende el Cliente Dummy ",self.id, " en un tiempo de ",at
                                yield hold,self,at
                                yield release,self,G.awsmeCashRegister[i]
                                print now(),"Fin Cliente Dummy",self.id
                                break
               
def resetMonitoresReplica():
    G.awsemCashRegisterManager.reset()
    G.awsemCashWaitTime.reset()
    G.boringCashWaitTime.reset()
    G.fastCashRegisterWaitTime.reset()
    G.awsemCashServiceTime.reset()
    G.boringCashServiceTime.reset()
    G.fastCashRegisterServiceTime.reset()

def resetMonitoresTotales():
    global resAvgWaitingBoringCR, resAvgWaitingAwsCR, resAvgServiceBoringCR, resAvgServiceAwsCR, resAvgServiceFastCR

    resAvgWaitingBoringCR = 0
    resAvgWaitingAwsCR = 0
    resAvgServiceBoringCR = 0
    resAvgServiceAwsCR = 0
    resAvgServiceFastCR = 0



def saveStatistics():
    global resAvgWaitingBoringCR, resAvgWaitingAwsCR, resAvgServiceBoringCR, resAvgServiceAwsCR, resAvgServiceFastCR, resAvgWatingFastCR

    resAvgWaitingBoringCR.observe(G.boringCashWaitTime.count())
    resAvgWaitingAwsCR.observe(G.awsemCashWaitTime.count())
    resAvgWatingFastCR.observe(G.fastCashRegisterWaitTime.count())
    resAvgServiceBoringCR.observe(G.boringCashServiceTime.count())
    resAvgServiceAwsCR.observe(G.awsemCashServiceTime.count())
    resAvgServiceFastCR.observe(G.fastCashRegisterServiceTime.count())


def cashRegisterGenerator(boringCashRegisterQTY,awsmeCashRegisterQTY):
    for i in range(awsmeCashRegisterQTY):
            G.awsmeCashRegister.append(Resource(capacity=1,name='awsmeCR_' + str(i),monitored=True))
    for i in range(boringCashRegisterQTY):
            G.boringCashRegister.append(Resource(capacity=1,name='boringCR_' + str(i),monitored=True))
    


def model(maxtime,boringCashRegisterQTY,boringServiceRate,awsmeCashRegisterQTY,awsmeServiceRate,clientArrivalsRate,maxCartSize, replicas):
    resetMonitoresTotales()
    for r in range(replicas):

        initialize()
        resetMonitoresReplica()
        # server definition
        cashRegisterGenerator(boringCashRegisterQTY,awsmeCashRegisterQTY)
        G.awsemCashRegisterManager = Resource(capacity=1,name="admin",monitored=True)
        
        #  exectuion
        a = Arrivals()
        activate(a, a.run(clientArrivalsRate,maxCartSize,boringServiceRate,awsmeServiceRate))
        simulate(until=maxtime)

        # statistics
        saveStatistics()





maxTimeSim = 10000
bsr = 15
awsr = 15
maxCS = 100
totalCashRegisters = 10
cantReplicas = 100 #cantidad de replicas por simulacion
fastCashRegister = 1 #cantidad de cajas rápidas

#Comparar las combinaciones de cantidad de cajas
for i in range(totalCashRegisters -1):
    model(maxtime=maxTimeSim, boringCashRegisterQTY=i, boringServiceRate=bsr,
          awsmeCashRegisterQTY=totalCashRegisters-i, awsmeServiceRate=awsr,
          clientArrivalsRate={0: 5, 200: 10, 300: 99}, maxCartSize=maxCS, replicas=cantReplicas)
