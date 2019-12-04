from network import Network
import scipy.stats
import numpy
import math
import threading

sem = threading.Semaphore()
"""
This method runs a base scenario featuring no ramp meter and seven scenarios
for ramp meter timings (ranging from 2.5 to 5.5 seconds), builds a confidence
interval for each on the total system travel time and total ramp travel time,
and, for the ramp meter scenarios, builds another confidence interval using
the ramp travel time as a control variate, then prints the results in CSV format.
"""
def main():
    print("Signal timing,Mean TSTT,Mean TRTT,TSTT CI,TRTT CI,Adj TSTT Mean,Adj TSTT CI")
    xi, yi, xci, yci, _, _ = runSims(0.000000000000001,False)
    print("{},{},{},{},--,--".format(xi,yi,xci,yci))
    print("--------------------------------------------------")
    for i in range(5,12):
        xi,yi,xci,yci,xa,xaci = runSims(i,True)
        print("{},{},{},{},{},{},{}".format(0.5*i,xi,yi,xci,yci,xa,xaci))

def runSims(i,useVars):
    #Statistical values
    n = 35
    alpha = 0.05
    za = scipy.stats.norm.ppf(1-alpha)
    zao2 = scipy.stats.norm.ppf(1-(alpha/2))
    seeds = [391,45843,28374,6932,34,2389,58724,56748,2857,3,
        8723,3621,4762,4720,372,553,774,192,29041,6643,
        78423,34834,6571,17289,12,47389,38212,219,535,765,
        1883,1831,2019,1993,35541]

    #Vehicle volume settings
    freeVol = 3000
    rampVol = 600
    
    #Measurement storage
    tstt = list()   #total system travel times
    astt = list()   #average vehicle travel times
    trtt = list()   #control variates (total ramp meter travel time)
    artt = list()   #average ramp travel time

    #Run n simulations in parallel
    thds = []
    for j in range(n):
        t = threading.Thread(target=indivSim, args=(i, seeds, j, freeVol, rampVol, trtt, tstt, astt, artt))
        thds.append(t)
        t.start()
    for t in thds:
        t.join()

    #Develop confidence intervals and begin constructing control variate
    tstm = numpy.mean(tstt) #Xbar
    trtm = numpy.mean(trtt) #Ybar
    sx2 = numpy.var(tstt,ddof=1)
    sy2 = numpy.var(trtt,ddof=1)    #sample variance of total ramp time
    sxy = numpy.cov(tstt,trtt)[0,1] #covariance
    lamhatn = sxy/sy2                 #lambda hat_n

    #Theoretical TRTT calculation
    arrRate = rampVol/3600
    svcRate = 1/(0.5*i)
    rho = arrRate/svcRate
    #meanQL = 0.5*rho**2/(1-rho)
    waitInQ = rho/(2*arrRate*(1-rho))
    waitInSys = waitInQ+0.5*i
    mu = (waitInSys+80)*rampVol/2
    
    #If this is a scenario with ramp meter,
    if useVars:
        #NBuild the confidence interval with the control variate
        W = list()
        for j in range(n):
            W.append(tstt[j]-lamhatn*(trtt[j]-mu))
        Wbar = numpy.mean(W)
        s2 = numpy.var(W,ddof=2)
        scv2 = s2*((1/n)+(1/(n+1)*(trtm-mu)/sy2))
        
        return  tstm, trtm, \
                zao2*math.sqrt(sx2)/math.sqrt(n), \
                zao2*math.sqrt(sy2)/math.sqrt(n), \
                Wbar,  \
                za*math.sqrt(scv2)
    else:   #Otherwise only build the standard confidence intervals
        return  tstm, trtm, \
                zao2*math.sqrt(sx2)/math.sqrt(n), \
                zao2*math.sqrt(sy2)/math.sqrt(n),\
                None, \
                None

def indivSim(i, seeds, j, freeVol, rampVol, trtt, tstt, astt, artt):
    #Initialize the network and load vehicles onto it
    net = Network(1/(0.5*i),seeds[j],freeVol,rampVol)
    net.initializePathFlows()
    net.loadNetwork()

    #Calculate simulation metrics
    net.calculateTravelTimes()
    t = net.calculateTSTT(range(900,2700))
    rtt = net.rampTravelTime(900,2700)
    td = net.demand(900,2700)
    rd = net.rampDemand(900,2700)

    #Store the metrics
    sem.acquire()
    trtt.append(rtt)
    tstt.append(t)
    astt.append(t/td)
    artt.append(rtt/rd)
    sem.release()

if __name__ == "__main__":
    main()