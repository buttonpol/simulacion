﻿from SimPy.Simulation import *
import random
import numpy as np
import math

class G:
    boringCashRegisterQTY = 0
    awsmeCashRegisterQTY = 0

    
    awsmeCashRegisterManager = "Administrador de cajas de una sola cola" #vendria ser el cartel q le dice al cliente a q caja tiene q ir
    awsemCashWaitTime = Monitor('Tiempo de espera en cajas compartidas')
    awsemCashServiceTime = Monitor('Tiempo de servicio en cajas compartidas')

    boringCashWaitTime = Monitor('Tiempo de espera en cola cajas individuales')
    boringCashServiceTime = Monitor('Tiempo de servicio promedio en cajas individuales')
    boringCashRegister = [] # Cajas individuales con una cola por caja
    
    actMonBor = Monitor('Cantidad de clientes atendidos boring')
    actMonAws = Monitor('Cantidad de clientes atendidas awesome')
    
    ### MONITORES REPLICAS ###
    awsemCashWaitTimeRep = Monitor('Tiempo de espera en cajas compartidas')
    awsemCashServiceTimeRep = Monitor('Tiempo de servicio en cajas compartidas')

    boringCashWaitTimeRep = Monitor('Tiempo de espera en cola cajas individuales')
    boringCashServiceTimeRep = Monitor('Tiempo de servicio promedio en cajas individuales')
    
    actMonBorRep = Monitor('Cantidad de clientes atendidos boring')
    actMonAwsRep = Monitor('Cantidad de clientes atendidas awesome')
    
    waitMonBorRep = Monitor('Cantidad de clientes en cola boring')
    waitMonAwsRep = Monitor('Cantidad de clientes en cola awesome')

    #contadores de elementos en colas
class Arrivals(Process):
    
    def run(self,clientArrivalsRate,maxCartSize,boringServiceRate,awsmeServiceRate,clientsQTY):
        i = 0
        r = 0
        arrivals = clientArrivalsRate.keys()
        arrivals.sort()

        if(clientsQTY==0):
            while(True):    
            
                type = "smartClient"
                if (random.uniform(0,1) < 0.10):  # genera clientes tontos q no se fijan tamanio de la cola
                    type = "dummyClient"
                
                c = Client(str(i),type,50) 
                activate(c, c.run(boringServiceRate,awsmeServiceRate))

                if(r < len(arrivals) - 1):
                    if(i != 0 and arrivals[r + 1] <= now()):
                        r+=1
                        print "**********************************************"
                        print "* TASA DE ARRIBO: ",clientArrivalsRate[arrivals[r]],"                        *"
                        print "**********************************************"

                t = random.expovariate(1. / clientArrivalsRate[arrivals[r]])
                yield hold, self, t
                i+=1
        else:
            for n in range(clientsQTY):
                type = "smartClient"
                if (random.uniform(0,1) < 0.10):  # genera clientes tontos q no se fijan tamanio de la cola
                    type = "dummyClient"
                
                c = Client(str(n),type,random.uniform(1,maxCartSize)) 
                activate(c, c.run(boringServiceRate,awsmeServiceRate))

                if(r < len(arrivals) - 1):
                    if(i != 0 and arrivals[r + 1] <= now()):
                        r+=1
                        print "**********************************************"
                        print "* TASA DE ARRIBO: ",clientArrivalsRate[arrivals[r]],"                        *"
                        print "**********************************************"

                t = random.expovariate(1. / clientArrivalsRate[arrivals[r]])
                yield hold, self, t


class Client(Process):
    global  elementsInQueueBCR,elementsInQueueACR,elementsInQueueFCR,timesFreeBoringCR,timesFreeAwesomeCR
    def __init__(self, id, type, cartQty):
        Process.__init__(self)
        self.id = id
        self.type = type
        self.arrivalTime = now()
        self.cartQty = cartQty

       
    def run(self,boringServiceRate,awsmeServiceRate):

        print now(),"Arribo Cliente ",self.id

        if(self.type == "smartClient"): #Cliente inteligente

            if (G.awsmeCashRegisterQTY>0 and G.boringCashRegisterQTY>0):
                firstCheckBoring = random.uniform(0,1)
                if(firstCheckBoring < 0.50): #mira primero las cajas individuales si estan vacias

                    minBoringCashRegisterQQ = sys.maxint
                    boringCashRegisterIndex = 0
                    allBoringBussy = True
                    for i in range(len(G.boringCashRegister)):  # busca cajas individuales libres
                        bQQ = len(G.boringCashRegister[i].waitQ) + len(G.boringCashRegister[i].activeQ)
                        if(bQQ == 0):
                            print now(), ' Cliente ', self.id, " encontro caja ",G.boringCashRegister[i].name," vacia"
                            allBoringBussy = False
                            yield request,self,G.boringCashRegister[i]
                            G.boringCashWaitTime.observe(now() - self.arrivalTime)
                            print now(),"Cliente ",self.id, "espero ",now() - self.arrivalTime ," y entra en caja ",G.boringCashRegister[i].name
                            bt = random.uniform(0.1,boringServiceRate) * self.cartQty
                            G.boringCashServiceTime.observe(bt)
                            print now(),G.boringCashRegister[i].name,"atiende el Cliente ",self.id, " en un tiempo de ",bt
                            yield hold,self,bt
                            yield release,self,G.boringCashRegister[i]
                            G.actMonBor.observe(1)
                            print now(),"Fin Cliente",self.id
                            break
                        elif(bQQ < minBoringCashRegisterQQ):
                            minBoringCashRegisterQQ = bQQ       
                            boringCashRegisterIndex = i
                  
                    if(allBoringBussy): #SI TODAS LAS CAJAS INDIVIDUALES TIENEN CLIENTES COMPARO CONTRA PARALELA
                        paralels = (len(G.awsmeCashRegisterManager.waitQ) + len(G.awsmeCashRegisterManager.activeQ)) / G.awsmeCashRegisterQTY

                        if (minBoringCashRegisterQQ < paralels):#compara cual de los 2 tipos de cajas tienen menos clientes
                            print now(),"Cliente ",self.id, "llegado hace ",now() - self.arrivalTime ," hace cola en caja ",G.boringCashRegister[boringCashRegisterIndex].name
                            yield request,self,G.boringCashRegister[boringCashRegisterIndex]
                            G.boringCashWaitTime.observe(now() - self.arrivalTime)
                            print now(),"Cliente ",self.id, "espero ",now() - self.arrivalTime ," y entra en caja ",G.boringCashRegister[boringCashRegisterIndex].name
                            bt = random.uniform(0.1,boringServiceRate) * self.cartQty
                            G.boringCashServiceTime.observe(bt)
                            print now(),G.boringCashRegister[boringCashRegisterIndex].name,"atiende el Cliente ",self.id, " en un tiempo de ",bt
                            yield hold,self,bt       
                            yield release,self,G.boringCashRegister[boringCashRegisterIndex]
                            G.actMonBor.observe(1)
                            print now(),"Fin Cliente",self.id
                        else:
                            print now(), "Cliente ", self.id, "llegado hace ", now() - self.arrivalTime, "hace cola en caja ", G.awsmeCashRegisterManager.name
                            yield request,self,G.awsmeCashRegisterManager
                            print now(), "Cliente ", self.id, "espero -", now() - self.arrivalTime, "- y entra en caja ", G.awsmeCashRegisterManager.name
                            G.awsemCashWaitTime.observe(now() - self.arrivalTime)
                            at = random.uniform(0.1,awsmeServiceRate) * self.cartQty
                            G.awsemCashServiceTime.observe(at)
                            print now(),G.awsmeCashRegisterManager.name,"atiende el Cliente ",self.id, " en un tiempo de ",at
                            yield hold,self,at
                            yield release,self,G.awsmeCashRegisterManager
                            G.actMonAws.observe(1)
                            print now(),"Fin Cliente",self.id
                
                else: #mira primero la caja de una sola cola
                    paralels = (len(G.awsmeCashRegisterManager.waitQ) + len(G.awsmeCashRegisterManager.activeQ)) / G.awsmeCashRegisterQTY
                    if(paralels == 0):
                        print now(), "Cliente ", self.id, "llegado hace ", now() - self.arrivalTime, "hace cola en caja ", G.awsmeCashRegisterManager.name
                        yield request,self,G.awsmeCashRegisterManager
                        print now(), "Cliente ", self.id, "espero -", now() - self.arrivalTime, "- y entra en caja ", G.awsmeCashRegisterManager.name
                        G.awsemCashWaitTime.observe(now() - self.arrivalTime)
                        at = random.uniform(0.1,awsmeServiceRate) * self.cartQty
                        G.awsemCashServiceTime.observe(at)
                        print now(),G.awsmeCashRegisterManager.name,"atiende el Cliente ",self.id, " en un tiempo de ",at
                        yield hold,self,at
                        yield release,self,G.awsmeCashRegisterManager
                        G.actMonAws.observe(1)
                        print now(),"Fin Cliente",self.id
                    else:
                        minBoringCashRegisterQQ = sys.maxint
                        boringCashRegisterIndex = 0
                        for i in range(len(G.boringCashRegister)):  # busca cajas individuales libres
                            bQQ = len(G.boringCashRegister[i].waitQ) + len(G.boringCashRegister[i].activeQ)
                            if(bQQ == 0): #si hay una vacia entra
                                print now(), ' Cliente ', self.id, " encontro caja ",G.boringCashRegister[i].name," vacia"
                                yield request,self,G.boringCashRegister[i]
                                G.boringCashWaitTime.observe(now() - self.arrivalTime)
                                print now(),"Cliente ",self.id, "espero ",now() - self.arrivalTime ," y entra en caja ",G.boringCashRegister[i].name
                                bt = random.uniform(0.1,boringServiceRate) * self.cartQty
                                G.boringCashServiceTime.observe(bt)
                                print now(),G.boringCashRegister[i].name,"atiende el Cliente ",self.id, " en un tiempo de ",bt
                                yield hold,self,bt
                                yield release,self,G.boringCashRegister[i]
                                G.actMonBor.observe(1)
                                print now(),"Fin Cliente",self.id
                                break
                            elif(bQQ < minBoringCashRegisterQQ): #sino se guarda la de menor cola para comparar contra la paralela
                                minBoringCashRegisterQQ = bQQ       
                                boringCashRegisterIndex = i

                        if (minBoringCashRegisterQQ < paralels): #compara los dos tipos de caja
                            print now(),"Cliente ",self.id, "llegado hace ",now() - self.arrivalTime ," hace cola en caja ",G.boringCashRegister[boringCashRegisterIndex].name
                            yield request,self,G.boringCashRegister[boringCashRegisterIndex]
                            G.boringCashWaitTime.observe(now() - self.arrivalTime)
                            print now(),"Cliente ",self.id, "espero ",now() - self.arrivalTime ," y entra en caja ",G.boringCashRegister[boringCashRegisterIndex].name
                            bt = random.uniform(0.1,boringServiceRate) * self.cartQty
                            G.boringCashServiceTime.observe(bt)
                            print now(),G.boringCashRegister[boringCashRegisterIndex].name,"atiende el Cliente ",self.id, " en un tiempo de ",bt
                            yield hold,self,bt       
                            yield release,self,G.boringCashRegister[boringCashRegisterIndex]
                            G.actMonBor.observe(1)
                            print now(),"Fin Cliente",self.id
                        else:
                            print now(), "Cliente ", self.id, "llegado hace ", now() - self.arrivalTime, "hace cola en caja ", G.awsmeCashRegisterManager.name
                            yield request,self,G.awsmeCashRegisterManager
                            print now(), "Cliente ", self.id, "espero -", now() - self.arrivalTime, "- y entra en caja ", G.awsmeCashRegisterManager.name
                            G.awsemCashWaitTime.observe(now() - self.arrivalTime)
                            at = random.uniform(0.1,awsmeServiceRate) * self.cartQty
                            G.awsemCashServiceTime.observe(at)
                            print now(),G.awsmeCashRegisterManager.name,"atiende el Cliente ",self.id, " en un tiempo de ",at
                            yield hold,self,at
                            yield release,self,G.awsmeCashRegisterManager
                            G.actMonAws.observe(1)
                            print now(),"Fin Cliente",self.id

            elif(G.boringCashRegisterQTY>0 and G.awsmeCashRegisterQTY==0):
                minBoringCashRegisterQQ = sys.maxint
                boringCashRegisterIndex = 0
                allBoringBussy = True
                for i in range(len(G.boringCashRegister)):  # busca cajas individuales libres
                    bQQ = len(G.boringCashRegister[i].waitQ) + len(G.boringCashRegister[i].activeQ)
                    if(bQQ == 0):
                        print now(), ' Cliente ', self.id, " encontro caja ",G.boringCashRegister[i].name," vacia"
                        allBoringBussy = False
                        yield request,self,G.boringCashRegister[i]
                        G.boringCashWaitTime.observe(now() - self.arrivalTime)
                        print now(),"Cliente ",self.id, "espero ",now() - self.arrivalTime ," y entra en caja ",G.boringCashRegister[i].name
                        bt = random.uniform(0.1,boringServiceRate) * self.cartQty
                        G.boringCashServiceTime.observe(bt)
                        print now(),G.boringCashRegister[i].name,"atiende el Cliente ",self.id, " en un tiempo de ",bt
                        yield hold,self,bt
                        yield release,self,G.boringCashRegister[i]
                        G.actMonBor.observe(1)
                        print now(),"Fin Cliente",self.id
                        break
                    elif(bQQ < minBoringCashRegisterQQ):
                        minBoringCashRegisterQQ = bQQ       
                        boringCashRegisterIndex = i
                if(allBoringBussy):
                    print now(),"Cliente ",self.id, "llegado hace ",now() - self.arrivalTime ," hace cola en caja ",G.boringCashRegister[boringCashRegisterIndex].name
                    yield request,self,G.boringCashRegister[boringCashRegisterIndex]
                    G.boringCashWaitTime.observe(now() - self.arrivalTime)
                    print now(),"Cliente ",self.id, "espero ",now() - self.arrivalTime ," y entra en caja ",G.boringCashRegister[boringCashRegisterIndex].name
                    bt = random.uniform(0.1,boringServiceRate) * self.cartQty
                    G.boringCashServiceTime.observe(bt)
                    print now(),G.boringCashRegister[boringCashRegisterIndex].name,"atiende el Cliente ",self.id, " en un tiempo de ",bt
                    yield hold,self,bt       
                    yield release,self,G.boringCashRegister[boringCashRegisterIndex]
                    G.actMonBor.observe(1)
                    print now(),"Fin Cliente",self.id

            elif(G.boringCashRegisterQTY==0 and G.awsmeCashRegisterQTY>0):
                print now(), "Cliente ", self.id, "llegado hace ", now() - self.arrivalTime, "hace cola en caja ", G.awsmeCashRegisterManager.name
                yield request,self,G.awsmeCashRegisterManager
                print now(), "Cliente ", self.id, "espero -", now() - self.arrivalTime, "- y entra en caja ", G.awsmeCashRegisterManager.name
                G.awsemCashWaitTime.observe(now() - self.arrivalTime)
                at = random.uniform(0.1,awsmeServiceRate) * self.cartQty
                G.awsemCashServiceTime.observe(at)
                print now(),G.awsmeCashRegisterManager.name,"atiende el Cliente ",self.id, " en un tiempo de ",at
                yield hold,self,at
                yield release,self,G.awsmeCashRegisterManager
                G.actMonAws.observe(1)
                print now(),"Fin Cliente",self.id




        else: #cliente dummy
            if(G.awsmeCashRegisterQTY>0 and G.boringCashRegisterQTY>0):
                if (random.uniform(0,1) < 0.50): #entra aleatoriamente en una caja individual
                    selectedCashRegister = int(random.uniform(0,len(G.boringCashRegister) - 1))
                    yield request,self,G.boringCashRegister[selectedCashRegister]
                    G.boringCashWaitTime.observe(now() - self.arrivalTime)
                    print now(),"Cliente Dummy ",self.id, "espero ",now() - self.arrivalTime ," y entra en caja ",G.boringCashRegister[selectedCashRegister].name
                    bt = random.uniform(0.1,boringServiceRate) * self.cartQty
                    G.boringCashServiceTime.observe(bt)
                    print now(),G.boringCashRegister[selectedCashRegister].name,"atiende el Cliente Dummy ",self.id, " en un tiempo de ",bt
                    yield hold,self,bt
                    yield release,self,G.boringCashRegister[selectedCashRegister]
                    G.actMonBor.observe(1)
                    print now(),"Fin Cliente Dummy",self.id
                else:
                    #entra aleatoriamente en caja de una sola cola
                    print now(),"Cliente Dummy ",self.id, "espero ",now() - self.arrivalTime ," y entra en caja ",G.awsmeCashRegisterManager.name
                    yield request,self,G.awsmeCashRegisterManager
                    G.awsemCashWaitTime.observe(now() - self.arrivalTime)
                    at = random.uniform(0.1,awsmeServiceRate) * self.cartQty
                    G.awsemCashServiceTime.observe(at)
                    print now(),G.awsmeCashRegisterManager.name,"atiende el Cliente ",self.id, " en un tiempo de ",at
                    yield hold,self,at
                    yield release,self,G.awsmeCashRegisterManager
                    G.actMonAws.observe(1)
                    print now(),"Fin Cliente Dummy",self.id

            elif(G.boringCashRegisterQTY>0 and G.awsmeCashRegisterQTY==0):
                selectedCashRegister = int(random.uniform(0,len(G.boringCashRegister) - 1))
                yield request,self,G.boringCashRegister[selectedCashRegister]
                G.boringCashWaitTime.observe(now() - self.arrivalTime)
                print now(),"Cliente Dummy ",self.id, "espero ",now() - self.arrivalTime ," y entra en caja ",G.boringCashRegister[selectedCashRegister].name
                bt = random.uniform(0.1,boringServiceRate) * self.cartQty
                G.boringCashServiceTime.observe(bt)
                print now(),G.boringCashRegister[selectedCashRegister].name,"atiende el Cliente Dummy ",self.id, " en un tiempo de ",bt
                yield hold,self,bt
                yield release,self,G.boringCashRegister[selectedCashRegister]
                G.actMonBor.observe(1)
                print now(),"Fin Cliente Dummy",self.id

            elif(G.boringCashRegisterQTY==0 and G.awsmeCashRegisterQTY>0):
                #entra aleatoriamente en caja de una sola cola
                print now(),"Cliente Dummy ",self.id, "espero ",now() - self.arrivalTime ," y entra en caja ",G.awsmeCashRegisterManager.name
                yield request,self,G.awsmeCashRegisterManager
                G.awsemCashWaitTime.observe(now() - self.arrivalTime)
                at = random.uniform(0.1,awsmeServiceRate) * self.cartQty
                G.awsemCashServiceTime.observe(at)
                print now(),G.awsmeCashRegisterManager.name,"atiende el Cliente ",self.id, " en un tiempo de ",at
                yield hold,self,at
                yield release,self,G.awsmeCashRegisterManager
                G.actMonAws.observe(1)
                print now(),"Fin Cliente Dummy",self.id
                

def cashRegisterGenerator(boringCashRegisterQTY,awsmeCashRegisterQTY):

    G.awsmeCashRegisterManager = Resource(capacity=awsmeCashRegisterQTY, name="Unica Fila", monitored=True)

    for i in range(boringCashRegisterQTY):
            G.boringCashRegister.append(Resource(capacity=1,name='boringCR_' + str(i),monitored=True))

def resetMonitoresReplicas():
    
    G.awsemCashWaitTimeRep.reset()
    G.awsemCashServiceTimeRep.reset()

    G.boringCashWaitTimeRep.reset()
    G.boringCashServiceTimeRep.reset()
    
    G.actMonBorRep.reset()
    G.actMonAwsRep.reset()
    
def imprimirInfoReplicas(boringCashRegisterQTY,awsmeCashRegisterQTY):
    
        print "\n\n****** Estadisticas replicas *********" 
    
        if(boringCashRegisterQTY > 0):
            print "En boring el tiempo promedio de espera en cola: " , G.boringCashWaitTimeRep.mean()
            print "En boring el tiempo promedio de servicio: " ,G.boringCashServiceTimeRep.mean()            
            print'Cantidad de clientes promedio en cola boring: ', G.waitMonBorRep.mean()    
            print 'Cantidad de clientes atendidos en boring', G.actMonBorRep.mean()      

        if(awsmeCashRegisterQTY > 0):
            print "\nEn awesome el tiempo promedio de espera en cola: ", G.awsemCashWaitTimeRep.mean()
            print "En awesome el tiempo promedio de servicio: " ,G.awsemCashServiceTimeRep.mean()
            print'Cantidad de clientes promedio en cola awesome: ' , G.waitMonAwsRep.mean()        
            print 'Cantidad de clientes atendidos en awesome', G.actMonAwsRep.mean()


    
def model(maxtime,boringCashRegisterQTY,boringServiceRate,awsmeCashRegisterQTY,awsmeServiceRate,clientArrivalsRate,maxCartSize, replicas,clientsQTY):

    G.boringCashRegisterQTY = boringCashRegisterQTY
    G.awsmeCashRegisterQTY = awsmeCashRegisterQTY

    resetMonitoresReplicas()
    
    for r in range(replicas):
        initialize()
        # server definition
        G.awsmeCashRegisterQTY = awsmeCashRegisterQTY    
        cashRegisterGenerator(boringCashRegisterQTY,awsmeCashRegisterQTY)

        #  exectuion
        a = Arrivals()
        activate(a, a.run(clientArrivalsRate,maxCartSize,boringServiceRate,awsmeServiceRate,clientsQTY))
        simulate(until=maxtime)

        if(boringCashRegisterQTY > 0):        
            print "\n\nEn boring el tiempo promedio de espera en cola: " , G.boringCashWaitTime.mean()
            G.boringCashWaitTimeRep.observe(G.boringCashWaitTime.mean())
            print "En boring el tiempo promedio de servicio: " ,G.boringCashServiceTime.mean()
            G.boringCashServiceTimeRep.observe(G.boringCashServiceTime.mean())      
            G.boringCashServiceTime.reset()

            waitMonBorCashtAvg = Monitor('Cantidad de clientes promedio en cola boring') 
            for i in range(boringCashRegisterQTY):
                waitMonBorCashtAvg.observe(G.boringCashRegister[i].waitMon.timeAverage())
            
            print'Cantidad de clientes promedio en cola boring: ', waitMonBorCashtAvg.mean()
            G.waitMonBorRep.observe(waitMonBorCashtAvg.mean())
            waitMonBorCashtAvg.reset()
            print 'Cantidad de clientes atendidos en boring', G.actMonBor.total()
            G.actMonBorRep.observe(G.actMonBor.total())
            G.actMonBor.reset()

        if(awsmeCashRegisterQTY > 0): 
            print "\n\nEn awesome el tiempo promedio de espera en cola: ", G.awsemCashWaitTime.mean()
            G.awsemCashWaitTimeRep.observe(G.awsemCashWaitTime.mean())
            G.awsemCashWaitTime.reset()
            print "En awesome el tiempo promedio de servicio: " ,G.awsemCashServiceTime.mean()
            G.awsemCashServiceTimeRep.observe(G.awsemCashServiceTime.mean())
            G.awsemCashServiceTime.reset()
            print'Cantidad de clientes promedio en cola awesome: ' , G.awsmeCashRegisterManager.waitMon.timeAverage()  
            G.waitMonAwsRep.observe(G.awsmeCashRegisterManager.waitMon.timeAverage())           
            print 'Cantidad de clientes atendidos en awesome', G.actMonAws.total()       
            G.actMonAwsRep.observe(G.actMonAws.total())
            G.actMonAws.reset()
            

    imprimirInfoReplicas(boringCashRegisterQTY,awsmeCashRegisterQTY)


maxTimeSim = 840 # DE 8 AM A 22HS 14HS *60
bsr = 0.5
awsr = 0.5
maxCS = 50
cantReplicas = 5  # cantidad de replicas por simulacion

#clientArrivalsRate={0: 0.08, 240: 2, 360: 0.09, 720: 5} el super comienza su actividad 8 am,
#los tiempos son en minutos, desde las 8 am tiempo 0 comienza con una tasa baja
#de arribos hasta el medio dia luego de 240 minutos (4hs) es decir 12 am q
#comienza a incrmentar tasa de arribo LUEGO desp de las (360) 3pm baja
#nuevamente la tasa de arribos hasta las 8pm donde comienza otra ora pico
model(maxtime=maxTimeSim, boringCashRegisterQTY=4, boringServiceRate=bsr,awsmeCashRegisterQTY=4, awsmeServiceRate=awsr,
          clientArrivalsRate={0: 8, 240: 1, 360: 5, 720: 0.5}, maxCartSize=100, replicas=cantReplicas,clientsQTY=0)