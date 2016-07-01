from SimPy.Simulation import *
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
    
    awsmeCashRegisterManager = "Administrador de cajas de una sola cola" #vendria ser el cartel q le dice al cliente a q caja tiene q ir
    awsemCashWaitTime = Monitor('Tiempo de espera en cajas compartidas')
    awsemCashServiceTime = Monitor('Tiempo de servicio en cajas compartidas')

    boringCashWaitTime = Monitor('Tiempo de espera en cola cajas individuales')
    boringCashServiceTime = Monitor('Tiempo de servicio promedio en cajas individuales')
    boringCashRegister = [] # Cajas individuales con una cola por caja
    
    actMonBor = Monitor('Cantidad de clientes atendidos boring')
    actMonAws = Monitor('Cantidad de clientes atendidas awesome')
    
    ### MONITORES REPLICAS ###
    
    awsmeCashRegisterManagerRep = "Administrador de cajas de una sola cola" #vendria ser el cartel q le dice al cliente a q caja tiene q ir
    awsemCashWaitTimeRep = Monitor('Tiempo de espera en cajas compartidas')
    awsemCashServiceTimeRep = Monitor('Tiempo de servicio en cajas compartidas')

    boringCashWaitTimeRep = Monitor('Tiempo de espera en cola cajas individuales')
    boringCashServiceTimeRep = Monitor('Tiempo de servicio promedio en cajas individuales')
    
    actMonBorRep = Monitor('Cantidad de clientes atendidos boring')
    actMonAwsRep = Monitor('Cantidad de clientes atendidas awesome')
    
    waitMonBorRep = Monitor('Cantidad de clientes en cola boring')
    waitMonAwsRep = Monitor('Cantidad de clientes en cola awesome')

    #contadores de elementos en colas

    elementsInQueueBCR = [] # contador de elementos en la cola de las cajas individuales
    elementsInQueueACR = 0 # contador de elementos en la cola de las cajas individuales
    elementsInQueueFCR = 0 # contador de elementos en la cola de las cajas individuales
    timesFreeBoringCR = 0
    timesFreeAwesomeCR=0


class Arrivals(Process):
    
    def run(self,clientArrivalsRate,maxCartSize,boringServiceRate,awsmeServiceRate):
        i = 0
        r = 0
        lastRateVisited = False
        arrivals = clientArrivalsRate.keys()
        while(True):    
            
            type = "smartClient"
            if (random.uniform(0,1) < 0.10):  # genera clientes tontos q no se fijan tamanio de la cola
                type = "dummyClient"
                
            c = Client(str(i),type,random.uniform(1,maxCartSize)) 
            activate(c, c.run(boringServiceRate,awsmeServiceRate))
            # calcula el tiempo del prox arribo...
            if(i != 0 and arrivals[r] <= int(now()) and lastRateVisited == False):
                r+=1  #cambia la tasa de arribo para el tiempo especificado
                if(r < len(arrivals)):
                    print "**********************************************"
                    print "* TASA DE ARRIBO: ",clientArrivalsRate[arrivals[r]],"                        *"
                    print "**********************************************"
                else:
                    r-=1
                    lastRateVisited = True
            t = random.expovariate(1. / clientArrivalsRate[arrivals[r]])
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
                #bQQ = len(G.boringCashRegister[i].waitQ) + len(G.boringCashRegister[i].activeQ )
                bQQ = G.elementsInQueueBCR[i]+ len(G.boringCashRegister[i].activeQ )
                if(bQQ == 0):
                    print now(), ' Cliente ', self.id, " encontro caja ",G.boringCashRegister[i].name," vacia"
                    allBoringBussy = False
                    yield request,self,G.boringCashRegister[i]
                    G.boringCashWaitTime.observe(now() - self.arrivalTime)
                    G.elementsInQueueBCR[i] = G.elementsInQueueBCR[i] + self.cartQty
                    print now(),"Cliente ",self.id, "espero ",now()-self.arrivalTime ," y entra en caja ",G.boringCashRegister[i].name
                    
                    bt = random.uniform(1,boringServiceRate)*self.cartQty
                    G.boringCashServiceTime.observe(bt)
                    print now(),G.boringCashRegister[i].name,"atiende el Cliente ",self.id, " en un tiempo de ",bt
                    yield hold,self,bt
                    yield release,self,G.boringCashRegister[i]
                    G.actMonBor.observe(1)
                    G.elementsInQueueBCR[i] = G.elementsInQueueBCR[i] - self.cartQty
                    print now(),"Fin Cliente",self.id
                    break
                elif(bQQ < minBoringCashRegisterQQ):
                    minBoringCashRegisterQQ = bQQ       
                    boringCashRegisterIndex = i
                  
            if(allBoringBussy):
                individuals = (np.sum(G.elementsInQueueBCR) + G.elementsInQueueFCR) / len(G.boringCashRegister)
                paralels = (len(G.awsmeCashRegisterManager.activeQ) + G.elementsInQueueACR) / G.awsmeCashRegisterQTY
                print 'len(G.awsmeCashRegisterManager.activeQ)', len(G.awsmeCashRegisterManager.activeQ), ' ; G.elementsInQueueACR', G.elementsInQueueACR, '; G.awsmeCashRegisterQTY ',  G.awsmeCashRegisterQTY
                if (individuals < paralels):
            #if(minBoringCashRegisterQQ < int(len(G.awsmeCashRegisterManager.waitQ)/G.awsmeCashRegisterQTY)):  ## compara cual de los 2 tipos tiene menos
                    print now(),"Cliente ",self.id, "llegado hace ",now()-self.arrivalTime ," hace cola en caja ",G.boringCashRegister[boringCashRegisterIndex].name
                    yield request,self,G.boringCashRegister[boringCashRegisterIndex]
                    G.boringCashWaitTime.observe(now()-self.arrivalTime)
                    G.elementsInQueueACR = G.elementsInQueueACR + self.cartQty
                    print now(),"Cliente ",self.id, "espero ",now()-self.arrivalTime ," y entra en caja ",G.boringCashRegister[boringCashRegisterIndex].name
                    bt = random.uniform(1,boringServiceRate)*self.cartQty
                    G.boringCashServiceTime.observe(bt)
                    print now(),G.boringCashRegister[boringCashRegisterIndex].name,"atiende el Cliente ",self.id, " en un tiempo de ",bt
                    yield hold,self,bt       
                    yield release,self,G.boringCashRegister[boringCashRegisterIndex]
                    G.actMonBor.observe(1)
                    G.elementsInQueueACR = G.elementsInQueueACR - self.cartQty
                    print now(),"Fin Cliente",self.id
                else:
                    print now(), "Cliente ", self.id, "llegado hace ", now() - self.arrivalTime, "hace cola en caja ", G.awsmeCashRegisterManager.name
                    yield request,self,G.awsmeCashRegisterManager
                    print now(), "Cliente ", self.id, "espero -", now() - self.arrivalTime, "- y entra en caja ", G.awsmeCashRegisterManager.name
                    G.awsemCashWaitTime.observe(now()-self.arrivalTime)
                    at = random.uniform(1,awsmeServiceRate)*self.cartQty
                    G.awsemCashServiceTime.observe(at)
                    print now(),G.awsmeCashRegisterManager.name,"atiende el Cliente ",self.id, " en un tiempo de ",at
                    yield hold,self,at
                    yield release,self,G.awsmeCashRegisterManager
                    G.actMonAws.observe(1)
                    print now(),"Fin Cliente",self.id
        else: #cliente dummy
            
            if (random.uniform(0,1) < 0.50): #entra aleatoriamente en una caja individual
                selectedCashRegister = int(random.uniform(0,len(G.boringCashRegister)-1))
                yield request,self,G.boringCashRegister[selectedCashRegister]
                G.boringCashWaitTime.observe(now()-self.arrivalTime)
                print now(),"Cliente Dummy ",self.id, "espero ",now()-self.arrivalTime ," y entra en caja ",G.boringCashRegister[selectedCashRegister].name
                bt = random.uniform(1,boringServiceRate)*self.cartQty
                G.boringCashServiceTime.observe(bt)
                print now(),G.boringCashRegister[selectedCashRegister].name,"atiende el Cliente Dummy ",self.id, " en un tiempo de ",bt
                yield hold,self,bt
                yield release,self,G.boringCashRegister[selectedCashRegister]
                G.actMonBor.observe(1)
                print now(),"Fin Cliente Dummy",self.id
            else:
                #entra aleatoriamente en caja de una sola cola
                print now(),"Cliente Dummy ",self.id, "espero ",now()-self.arrivalTime ," y entra en caja ",G.awsmeCashRegisterManager.name
                yield request,self,G.awsmeCashRegisterManager
                G.awsemCashWaitTime.observe(now()-self.arrivalTime)
                at = random.uniform(1,awsmeServiceRate)*self.cartQty
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
            G.elementsInQueueBCR.append(0)

def resetMonitoresReplicas():
    
    G.awsemCashWaitTimeRep.reset()
    G.awsemCashServiceTimeRep.reset()

    G.boringCashWaitTimeRep.reset()
    G.boringCashServiceTimeRep.reset()
    
    G.actMonBorRep.reset()
    G.actMonAwsRep.reset()
    
def imprimirInfoReplicas():
    
        print "\n\n Estadisticas replicas" 
    
        print "En boring el tiempo promedio de espera en cola: " , G.boringCashWaitTimeRep.mean()
        
        print "En awesome el tiempo promedio de espera en cola: ", G.awsemCashWaitTimeRep.mean()
        
        print "En boring el tiempo promedio de servicio: " ,G.boringCashServiceTimeRep.mean()
        
        print "En awesome el tiempo promedio de servicio: " ,G.awsemCashServiceTimeRep.mean()
        
            
        print'Cantidad de clientes promedio en cola boring: ', G.waitMonBorRep.mean()
    
    
        print'Cantidad de clientes promedio en cola awesome: ' , G.waitMonAwsRep.mean()
    
        print 'Cantidad de clientes atendidos en boring', G.actMonBorRep.mean()
        
        print 'Cantidad de clientes atendidos en awesome', G.actMonAwsRep.mean()

        print 'cantidad de veces que se encontro una fila vacia ', G.timesFreeBoringCR
    
    

def model(maxtime,boringCashRegisterQTY,boringServiceRate,awsmeCashRegisterQTY,awsmeServiceRate,clientArrivalsRate,maxCartSize, replicas):
  #  resetMonitoresTotales()
    resetMonitoresReplicas()
    
    for r in range(replicas):
        initialize()
        # server definition
        G.awsmeCashRegisterQTY = awsmeCashRegisterQTY
            
        cashRegisterGenerator(boringCashRegisterQTY,awsmeCashRegisterQTY)
         #    resetMonitoresReplica()
        
        #  exectuion
        a = Arrivals()
        activate(a, a.run(clientArrivalsRate,maxCartSize,boringServiceRate,awsmeServiceRate))
        simulate(until=maxtime)
        
        print "\n\nEn boring el tiempo promedio de espera en cola: " , G.boringCashWaitTime.mean()
        G.boringCashWaitTimeRep.observe(G.boringCashWaitTime.mean())
        
        print "En awesome el tiempo promedio de espera en cola: ", G.awsemCashWaitTime.mean()
        G.awsemCashWaitTimeRep.observe(G.awsemCashWaitTime.mean())
        
        print "En boring el tiempo promedio de servicio: " ,G.boringCashServiceTime.mean()
        G.boringCashServiceTimeRep.observe(G.boringCashServiceTime.mean())
        
        print "En awesome el tiempo promedio de servicio: " ,G.awsemCashServiceTime.mean()
        G.awsemCashServiceTimeRep.observe(G.awsemCashServiceTime.mean())
        
        waitMonBorCashtAvg = Monitor('Cantidad de clientes promedio en cola boring') 
        
        for i in range(boringCashRegisterQTY):
            waitMonBorCashtAvg.observe(G.boringCashRegister[i].waitMon.timeAverage())
            
        print'Cantidad de clientes promedio en cola boring: ', waitMonBorCashtAvg.mean()
        G.waitMonBorRep.observe(waitMonBorCashtAvg.mean())
    
    
        print'Cantidad de clientes promedio en cola awesome: ' , G.awsmeCashRegisterManager.waitMon.timeAverage()  
        G.waitMonAwsRep.observe(G.awsmeCashRegisterManager.waitMon.timeAverage()) 
    
        print 'Cantidad de clientes atendidos en boring', G.actMonBor.total()
        G.actMonBorRep.observe(G.actMonBor.total())
        
        print 'Cantidad de clientes atendidos en awesome', G.actMonAws.total()
        G.actMonAwsRep.observe(G.actMonAws.total())
    imprimirInfoReplicas()


maxTimeSim = 10000
bsr = 1.5
awsr = 1.5
maxCS = 50
totalCashRegisters = 10
cantReplicas = 1  # cantidad de replicas por simulacion
fastCashRegister = 1  # cantidad de cajas rpidas

model(maxtime=1100, boringCashRegisterQTY=4, boringServiceRate=2,
          awsmeCashRegisterQTY=4, awsmeServiceRate=2,
          clientArrivalsRate={0: 1, 500: 2, 800: 5}, maxCartSize=100, replicas=cantReplicas)

#model(maxtime=maxTimeSim, boringCashRegisterQTY=4, boringServiceRate=bsr,
#          awsmeCashRegisterQTY=4, awsmeServiceRate=awsr,
#          clientArrivalsRate={0: 5, 200: 10, 300: 99}, maxCartSize=maxCS, replicas=cantReplicas)