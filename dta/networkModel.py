from dta import linkModel
from dta import nodeModel
from .network import Network, OD, StochasticOD



class NetworkModel(Network):
    def __init__(self, timeHorizon=3600, seed=1883):

        self.links = dict()
        self.ODs = list()
        self.pathFlows = dict()
        self.pathTravelTimes = dict()

        self.timestep = 1
        # self.numHours = 1
        # self.simLength = 3600*self.numHours
        # self.timeHorizon = int(self.simLength/self.timestep)
        self.timeHorizon = timeHorizon
        self.numLinks = 30
        self.numNodes = 26
        self.linkPriorities = dict()
        self.totalDemand = 0.0
        
        self.buildLinks()

        self.buildNodes()
        
        self.attachLinks()
        
    def buildLinks(self):
        freewaySpeed = 65
        freewayBack = 35
        rampSpeed = 45
        rampBack = 30
        crossSpeed = 45
        crossBack = 30
        minorSpeed = 35
        minorBack = 25

        # northbound freeway links
        self.links['FWY NB U'] = linkModel.CellTransmissionModelLink(self.timestep, freewaySpeed, freewayBack, 200, 1500, 3200, 'FWY NB U')
        self.links['FWY NB C'] = linkModel.CellTransmissionModelLink(self.timestep, freewaySpeed, freewayBack, 200, 5280, 3200, 'FWY NB C')
        self.links['FWY NB D'] = linkModel.CellTransmissionModelLink(self.timestep, freewaySpeed, freewayBack, 200, 1500, 3200, 'FWY NB D')

        # northbound freeway ramps
        self.links['FWY NB XR'] = linkModel.CellTransmissionModelLink(self.timestep, rampSpeed, rampBack, 200, 2640, 1600, 'FWY NB XR')
        self.links['FWY NB NRU'] = linkModel.CellTransmissionModelLink(self.timestep, rampSpeed, rampBack, 200, 1140, 1600,'FWY NB NRU')
        self.links['FWY NB NRD'] = linkModel.CellTransmissionModelLink(self.timestep, rampSpeed, rampBack, 200, 1500, 1600, 'FWY NB NRD')

        # southbound freeway links
        self.links['FWY SB U'] = linkModel.CellTransmissionModelLink(self.timestep, freewaySpeed, freewayBack, 200, 1500, 3200, 'FWY SB U')
        self.links['FWY SB C'] = linkModel.CellTransmissionModelLink(self.timestep, freewaySpeed, freewayBack, 200, 5280, 3200, 'FWY SB C')
        self.links['FWY SB D'] = linkModel.CellTransmissionModelLink(self.timestep, freewaySpeed, freewayBack, 200, 1500, 3200, 'FWY SB D')

        # southbound freeway ramps
        self.links['FWY SB XR'] = linkModel.CellTransmissionModelLink(self.timestep, rampSpeed, rampBack, 200, 2640, 1600, 'FWY SB XR')
        self.links['FWY SB NRU'] = linkModel.CellTransmissionModelLink(self.timestep, rampSpeed, rampBack, 200, 1140, 1600,'FWY SB NRU')
        self.links['FWY SB NRD'] = linkModel.CellTransmissionModelLink(self.timestep, rampSpeed, rampBack, 200, 1500, 1600,'FWY SB NRD')

        # eastbound cross street links
        self.links['XS EB I'] = linkModel.CellTransmissionModelLink(self.timestep, crossSpeed, crossBack, 200, 1500, 3200, 'XS EB I')
        self.links['XS EB A'] = linkModel.CellTransmissionModelLink(self.timestep, crossSpeed, crossBack, 200, 2000, 3200, 'XS EB A')
        self.links['XS EB C'] = linkModel.CellTransmissionModelLink(self.timestep, crossSpeed, crossBack, 200, 400, 3200, 'XS EB C')
        self.links['XS EB D'] = linkModel.CellTransmissionModelLink(self.timestep, crossSpeed, crossBack, 200, 2000, 3200, 'XS EB D')
        self.links['XS EB O'] = linkModel.CellTransmissionModelLink(self.timestep, crossSpeed, crossBack, 200, 1500, 3200, 'XS EB O')

        # westbound cross street links
        self.links['XS WB I'] = linkModel.CellTransmissionModelLink(self.timestep, crossSpeed, crossBack, 200, 1500, 3200, 'XS WB I')
        self.links['XS WB A'] = linkModel.CellTransmissionModelLink(self.timestep, crossSpeed, crossBack, 200, 2000, 3200, 'XS WB A')
        self.links['XS WB C'] = linkModel.CellTransmissionModelLink(self.timestep, crossSpeed, crossBack, 200, 400, 3200, 'XS WB C')
        self.links['XS WB D'] = linkModel.CellTransmissionModelLink(self.timestep, crossSpeed, crossBack, 200, 2000, 3200, 'XS WB D')
        self.links['XS WB O'] = linkModel.CellTransmissionModelLink(self.timestep, crossSpeed, crossBack, 200, 1500, 3200, 'XS WB O')

        # western collector links
        self.links['WC SB I'] = linkModel.CellTransmissionModelLink(self.timestep, minorSpeed, minorBack, 200, 2640, 1600, 'WC SB I')
        self.links['WC SB O'] = linkModel.CellTransmissionModelLink(self.timestep, minorSpeed, minorBack, 200, 2640, 1600, 'WC SB O')
        self.links['WC NB I'] = linkModel.CellTransmissionModelLink(self.timestep, minorSpeed, minorBack, 200, 2640, 1600, 'WC NB I')
        self.links['WC NB O'] = linkModel.CellTransmissionModelLink(self.timestep, minorSpeed, minorBack, 200, 2640, 1600, 'WC NB O')

        # eastern collector links
        self.links['EC SB I'] = linkModel.CellTransmissionModelLink(self.timestep, minorSpeed, minorBack, 200, 2640, 1600, 'EC SB I')
        self.links['EC SB O'] = linkModel.CellTransmissionModelLink(self.timestep, minorSpeed, minorBack, 200, 2640, 1600, 'EC SB O')
        self.links['EC NB I'] = linkModel.CellTransmissionModelLink(self.timestep, minorSpeed, minorBack, 200, 2640, 1600, 'EC NB I')
        self.links['EC NB O'] = linkModel.CellTransmissionModelLink(self.timestep, minorSpeed, minorBack, 200, 2640, 1600, 'EC NB O')

    def buildNodes(self):
        # generation nodes
        fwyNBstart = nodeModel.OriginNode([],[self.links['FWY NB U']])
        fwySBstart = nodeModel.OriginNode([],[self.links['FWY SB U']])
        xsEBstart = nodeModel.OriginNode([],[self.links['XS EB I']])
        xsWBstart = nodeModel.OriginNode([],[self.links['XS WB I']])
        wcNBstart = nodeModel.OriginNode([],[self.links['WC NB I']])
        wcSBstart = nodeModel.OriginNode([],[self.links['WC SB I']])
        ecNBstart = nodeModel.OriginNode([],[self.links['EC NB I']])
        ecSBstart = nodeModel.OriginNode([],[self.links['EC SB I']])

        # termination nodes
        fwyNBend = nodeModel.DestinationNode([self.links['FWY NB D']],[])
        fwySBend = nodeModel.DestinationNode([self.links['FWY SB D']],[])
        xsEBend = nodeModel.DestinationNode([self.links['XS EB O']],[])
        xsWBend = nodeModel.DestinationNode([self.links['XS WB O']],[])
        wcNBend = nodeModel.DestinationNode([self.links['WC NB O']],[])
        wcSBend = nodeModel.DestinationNode([self.links['WC SB O']],[])
        ecNBend = nodeModel.DestinationNode([self.links['EC NB O']],[])
        ecSBend = nodeModel.DestinationNode([self.links['EC SB O']],[])

        # ramp meters
        meterNB = nodeModel.RampMeterNode([self.links['FWY NB NRU']], [self.links['FWY NB NRD']])
        meterSB = nodeModel.RampMeterNode([self.links['FWY SB NRU']], [self.links['FWY SB NRD']])

        # merge nodes
        nbPriorities = {self.links['FWY NB NRD']:1, self.links['FWY NB C']:3}
        sbPriorities = {self.links['FWY SB NRD']:1, self.links['FWY SB C']:3}
        
        nbMerge = nodeModel.MergeNode([self.links['FWY NB C'], self.links['FWY NB NRD']], [self.links['FWY NB D']], nbPriorities)
        sbMerge = nodeModel.MergeNode([self.links['FWY SB C'], self.links['FWY SB NRD']], [self.links['FWY SB D']], sbPriorities)

        # diverge nodes
        nbDiv = nodeModel.DivergeNode([self.links['FWY NB U']],[self.links['FWY NB C'], self.links['FWY NB XR']])
        sbDiv = nodeModel.DivergeNode([self.links['FWY SB U']],[self.links['FWY SB C'], self.links['FWY SB XR']])








        # intersection nodes - Western intersection
        inLinks = [self.links['WC SB I'], self.links['WC NB I'], self.links['XS EB I'], self.links['XS WB D']]
        outLinks =[self.links['WC SB O'], self.links['WC NB O'], self.links['XS EB A'], self.links['XS WB O']]
        
        ring00 = nodeModel.Ring([(self.links['XS EB I'], self.links['XS EB A']),(self.links['XS WB D'], self.links['WC SB O'])],None)
        ring01 = nodeModel.Ring([(self.links['XS EB I'], self.links['WC NB O']),(self.links['XS WB D'], self.links['XS WB O'])],None)
        barrier0 = nodeModel.Barrier([ring00, ring01],None)
        ring00.barrier = barrier0
        ring01.barrier = barrier0

        ring10 = nodeModel.Ring([(self.links['WC NB I'], self.links['WC NB O']),(self.links['WC SB I'], self.links['XS EB A'])],None)
        ring11 = nodeModel.Ring([(self.links['WC NB I'], self.links['XS WB O']),(self.links['WC SB I'], self.links['WC SB O'])],None)
        barrier1 = nodeModel.Barrier([ring10,ring11],None)
        ring10.barrier = barrier1
        ring11.barrier = barrier1

        permissivePhases = [(self.links['XS EB I'], self.links['WC SB O']),
                            (self.links['XS WB D'], self.links['WC NB O']),
                            (self.links['WC SB I'], self.links['XS WB O']),
                            (self.links['WC NB I'], self.links['XS EB A'])]

        wx = nodeModel.FullyProtectedIntersectionNode(inLinks,outLinks,[barrier0,barrier1], permissivePhases)
        
        # Western ramp intersection
        inLinks = [self.links['XS EB A'],self.links['XS WB C'], self.links['FWY SB XR']]
        outLinks =[self.links['XS EB C'],self.links['XS WB D'], self.links['FWY SB NRU']]

        ring00 = nodeModel.Ring([(self.links['XS EB A'], self.links['XS EB C']),(self.links['XS WB C'], self.links['FWY SB NRU'])],None)
        ring01 = nodeModel.Ring([(self.links['XS WB C'], self.links['XS WB D']),(self.links['XS WB C'], self.links['XS WB D'])],1.0)
        barrier0 = nodeModel.Barrier([ring00,ring01],None)
        ring00.barrier = barrier0
        ring01.barrier = barrier0

        ring10 = nodeModel.Ring([(self.links['FWY SB XR'], self.links['XS EB C']),(self.links['FWY SB XR'], self.links['XS EB C'])],1.0)
        ring11 = nodeModel.Ring([(self.links['FWY SB XR'],self.links['FWY SB NRU']),(self.links['FWY SB XR'],self.links['FWY SB NRU'])],1.0)
        barrier1 = nodeModel.Barrier([ring10,ring11],None)

        permissivePhases = [(self.links['FWY SB XR'], self.links['XS WB D']),
                            (self.links['XS EB A'], self.links['FWY SB NRU'])]

        wrx = nodeModel.FullyProtectedIntersectionNode(inLinks, outLinks,[barrier0,barrier1], permissivePhases)

        # Eastern ramp intersection
        inLinks = [self.links['XS EB C'], self.links['XS WB A'], self.links['FWY NB XR']]
        outLinks =[self.links['XS EB D'], self.links['XS WB C'], self.links['FWY NB NRU']]

        ring00 = nodeModel.Ring([(self.links['XS EB C'], self.links['XS EB D']),(self.links['XS EB C'], self.links['XS EB D'])],1.0)
        ring01 = nodeModel.Ring([(self.links['XS EB C'], self.links['FWY NB NRU']),(self.links['XS WB A'], self.links['XS WB C'])],None)
        barrier0 = nodeModel.Barrier([ring00,ring01],None)
        ring00.barrier = barrier0
        ring01.barrier = barrier0

        ring10 = nodeModel.Ring([(self.links['FWY NB XR'], self.links['FWY NB NRU']),(self.links['FWY NB XR'], self.links['FWY NB NRU'])],1.0)
        ring11 = nodeModel.Ring([(self.links['FWY NB XR'], self.links['XS WB C']),(self.links['FWY NB XR'], self.links['XS WB C'])],1.0)
        barrier1 = nodeModel.Barrier([ring10,ring11],None)
        ring10.barrier = barrier1
        ring11.barrier = barrier1

        permissivePhases = [(self.links['FWY NB XR'],self.links['XS EB D']),
                            (self.links['XS WB A'],self.links['FWY NB NRU'])]
        erx = nodeModel.FullyProtectedIntersectionNode(inLinks,outLinks,[barrier0,barrier1],permissivePhases)

        # Eastern intersection
        inLinks = [self.links['XS EB D'], self.links['XS WB I'], self.links['EC NB I'], self.links['EC SB I']]
        outLinks =[self.links['XS EB O'], self.links['XS WB A'], self.links['EC NB O'], self.links['EC SB O']]

        ring00 = nodeModel.Ring([(self.links['XS EB D'], self.links['XS EB O']),(self.links['XS WB I'], self.links['EC SB O'])],None)
        ring01 = nodeModel.Ring([(self.links['XS EB D'], self.links['EC NB O']),(self.links['XS WB I'], self.links['XS WB A'])],None)
        barrier0 = nodeModel.Barrier([ring00,ring01],None)
        ring00.barrier = barrier0
        ring01.barrier = barrier0

        ring10 = nodeModel.Ring([(self.links['EC SB I'], self.links['EC SB O']),(self.links['EC NB I'], self.links['XS WB A'])],None)
        ring11 = nodeModel.Ring([(self.links['EC SB I'], self.links['XS EB O']),(self.links['EC NB I'], self.links['EC NB O'])],None)
        barrier1 = nodeModel.Barrier([ring10,ring11],None)
        ring10.barrier = barrier1
        ring11.barrier = barrier1

        permissivePhases = [(self.links['EC SB I'], self.links['XS WB A']),
                            (self.links['EC NB I'], self.links['XS EB O']),
                            (self.links['XS EB D'], self.links['EC SB O']),
                            (self.links['XS WB I'], self.links['EC NB O'])]

        ex = nodeModel.FullyProtectedIntersectionNode(inLinks,outLinks,[barrier0,barrier1],permissivePhases)

        self.nodes = [fwyNBstart,fwySBstart,
                        xsEBstart,xsWBstart,
                        ecNBstart,ecSBstart,
                        wcNBstart,wcSBstart,
                        
                        fwyNBend,fwySBend,
                        xsEBend,xsWBend,
                        ecNBend,ecSBend,
                        wcNBend,wcSBend,
                        
                        nbMerge,sbMerge,
                        nbDiv,sbDiv,
                        
                        meterNB,meterSB,
                        
                        ex,wx,
                        erx,wrx]

    
    #set intersection and ramp parameters
    def setConfig(self,config):
        self.nodes[20].setParams(config['nb ramp'])
        self.nodes[21].setParams(config['sb ramp'])
        self.nodes[23].setParams(config['wx'])
        self.nodes[25].setParams(config['wrx'])
        self.nodes[24].setParams(config['erx'])
        self.nodes[22].setParams(config['ex'])

    def attachLinks(self):
        #attach freeway links to nodes
        self.links['FWY NB U'].tail = 0
        self.links['FWY NB U'].head = 18
        self.links['FWY SB U'].tail = 1
        self.links['FWY SB U'].head = 19

        self.links['FWY NB C'].tail = 18
        self.links['FWY NB C'].head = 16
        self.links['FWY SB C'].tail = 19
        self.links['FWY SB C'].head = 17

        self.links['FWY NB D'].tail = 16
        self.links['FWY NB D'].head = 8
        self.links['FWY SB D'].tail = 17
        self.links['FWY SB D'].head = 9

        #attach ramp links to nodes
        self.links['FWY NB XR'].tail = 18
        self.links['FWY NB XR'].head = 24
        self.links['FWY SB XR'].tail = 19
        self.links['FWY SB XR'].head = 25

        self.links['FWY NB NRU'].tail = 24
        self.links['FWY NB NRU'].head = 20
        self.links['FWY SB NRU'].tail = 25
        self.links['FWY SB NRU'].head = 21

        self.links['FWY NB NRD'].tail = 20
        self.links['FWY NB NRD'].head = 16
        self.links['FWY SB NRD'].tail = 21
        self.links['FWY SB NRD'].head = 17

        #attach cross-street links to nodes
        self.links['XS EB I'].tail = 2
        self.links['XS EB I'].head = 23
        self.links['XS WB I'].tail = 3
        self.links['XS WB I'].head = 22

        self.links['XS EB A'].tail = 23
        self.links['XS EB A'].head = 25
        self.links['XS WB A'].tail = 22
        self.links['XS WB A'].head = 24

        self.links['XS EB C'].tail = 25
        self.links['XS EB C'].head = 24
        self.links['XS WB C'].tail = 24
        self.links['XS WB C'].head = 25

        self.links['XS EB D'].tail = 24
        self.links['XS EB D'].head = 22
        self.links['XS WB D'].tail = 25
        self.links['XS WB D'].head = 23

        self.links['XS EB O'].tail = 22
        self.links['XS EB O'].head = 10
        self.links['XS WB O'].tail = 23
        self.links['XS WB O'].head = 11

        #attach eastern collector
        self.links['EC NB I'].tail = 4
        self.links['EC NB I'].head = 22
        self.links['EC SB I'].tail = 5
        self.links['EC SB I'].head = 22

        self.links['EC NB O'].tail = 22
        self.links['EC NB O'].head = 12
        self.links['EC SB O'].tail = 22
        self.links['EC SB O'].head = 13

        #attach western collector
        self.links['WC NB I'].tail = 6
        self.links['WC NB I'].head = 23
        self.links['WC SB I'].tail = 7
        self.links['WC SB I'].head = 23

        self.links['WC NB O'].tail = 23
        self.links['WC NB O'].head = 14
        self.links['WC SB O'].tail = 23
        self.links['WC SB O'].head = 15

        self.finalizeLinks()

    def setDemand(self,volumes,rng):
                #OD demand

        #demand from north freeway
        nFwy = StochasticOD(0,8,self.timeHorizon,volumes['nFwy'],rng)
        self.ODs.append(nFwy)

        n2e = StochasticOD(0,10,self.timeHorizon,volumes['n2e'],rng)
        self.ODs.append(n2e)

        n2w = StochasticOD(0,11,self.timeHorizon,volumes['n2w'],rng)
        self.ODs.append(n2w)

        n2ne = StochasticOD(0,12,self.timeHorizon,volumes['n2ne'],rng)
        self.ODs.append(n2ne)

        n2nw = StochasticOD(0,14,self.timeHorizon,volumes['n2nw'],rng)
        self.ODs.append(n2nw)

        n2se = StochasticOD(0,13,self.timeHorizon,volumes['n2se'],rng)
        self.ODs.append(n2se)

        n2sw = StochasticOD(0,15,self.timeHorizon,volumes['n2sw'],rng)
        self.ODs.append(n2sw)

        #demand from south freeway
        sFwy = StochasticOD(1,9,self.timeHorizon,volumes['sFwy'],rng)
        self.ODs.append(sFwy)
        
        s2e = StochasticOD(1,10,self.timeHorizon,volumes['s2e'],rng)
        self.ODs.append(s2e)

        s2w = StochasticOD(1,11,self.timeHorizon,volumes['s2w'],rng)
        self.ODs.append(s2w)

        s2ne = StochasticOD(1,12,self.timeHorizon,volumes['s2ne'],rng)
        self.ODs.append(s2ne)

        s2nw = StochasticOD(1,14,self.timeHorizon,volumes['s2nw'],rng)
        self.ODs.append(s2nw)

        s2se = StochasticOD(1,13,self.timeHorizon,volumes['s2se'],rng)
        self.ODs.append(s2se)

        s2sw = StochasticOD(1,15,self.timeHorizon,volumes['s2sw'],rng)
        self.ODs.append(s2sw)

        #demand from WB XS
        e2w = StochasticOD(3,11,self.timeHorizon,volumes['e2w'],rng)
        self.ODs.append(e2w)
        
        e2n = StochasticOD(3,8,self.timeHorizon,volumes['e2n'],rng)
        self.ODs.append(e2n)
        
        e2s = StochasticOD(3,9,self.timeHorizon,volumes['e2s'],rng)
        self.ODs.append(e2s)
        
        e2ne = StochasticOD(3,12,self.timeHorizon,volumes['e2ne'],rng)
        self.ODs.append(e2ne)
        
        e2nw = StochasticOD(3,14,self.timeHorizon,volumes['e2nw'],rng)
        self.ODs.append(e2nw)
        
        e2se = StochasticOD(3,13,self.timeHorizon,volumes['e2se'],rng)
        self.ODs.append(e2se)
        
        e2sw = StochasticOD(3,15,self.timeHorizon,volumes['e2sw'],rng)
        self.ODs.append(e2sw)
        
        #demand from EB XS
        w2e = StochasticOD(2,10,self.timeHorizon,volumes['w2e'],rng)
        self.ODs.append(w2e)
        
        w2n = StochasticOD(2,8,self.timeHorizon,volumes['w2n'],rng)
        self.ODs.append(w2n)
        
        w2s = StochasticOD(2,9,self.timeHorizon,volumes['w2s'],rng)
        self.ODs.append(w2s)
        
        w2ne = StochasticOD(2,12,self.timeHorizon,volumes['w2ne'],rng)
        self.ODs.append(w2ne)
        
        w2nw = StochasticOD(2,14,self.timeHorizon,volumes['w2nw'],rng)
        self.ODs.append(w2nw)
        
        w2se = StochasticOD(2,13,self.timeHorizon,volumes['w2se'],rng)
        self.ODs.append(w2se)
        
        w2sw = StochasticOD(2,15,self.timeHorizon,volumes['w2sw'],rng)
        self.ODs.append(w2sw)
        
        #demand from NE collector
        ne2n = StochasticOD(5,8,self.timeHorizon,volumes['ne2n'],rng)
        self.ODs.append(ne2n)
        
        ne2s = StochasticOD(5,9,self.timeHorizon,volumes['ne2s'],rng)
        self.ODs.append(ne2s)
        
        ne2e = StochasticOD(5,10,self.timeHorizon,volumes['ne2e'],rng)
        self.ODs.append(ne2e)
        
        ne2w = StochasticOD(5,11,self.timeHorizon,volumes['ne2w'],rng)
        self.ODs.append(ne2w)
        
        ne2nw = StochasticOD(5,14,self.timeHorizon,volumes['ne2nw'],rng)
        self.ODs.append(ne2nw)
        
        ne2se = StochasticOD(5,13,self.timeHorizon,volumes['ne2se'],rng)
        self.ODs.append(ne2se)
        
        ne2sw = StochasticOD(5,15,self.timeHorizon,volumes['ne2sw'],rng)
        self.ODs.append(ne2sw)
        

        #demand from NW collector
        nw2n = StochasticOD(7,8,self.timeHorizon,volumes['nw2n'],rng)
        self.ODs.append(nw2n)
        
        nw2s = StochasticOD(7,9,self.timeHorizon,volumes['nw2s'],rng)
        self.ODs.append(nw2s)
        
        nw2e = StochasticOD(7,10,self.timeHorizon,volumes['nw2e'],rng)
        self.ODs.append(nw2e)
        
        nw2w = StochasticOD(7,11,self.timeHorizon,volumes['nw2w'],rng)
        self.ODs.append(nw2w)
        
        nw2ne = StochasticOD(7,12,self.timeHorizon,volumes['nw2ne'],rng)
        self.ODs.append(nw2ne)
        
        nw2se = StochasticOD(7,13,self.timeHorizon,volumes['nw2se'],rng)
        self.ODs.append(nw2se)
        
        nw2sw = StochasticOD(7,15,self.timeHorizon,volumes['nw2sw'],rng)
        self.ODs.append(nw2sw)
        

        #demand from SE collector
        se2n = StochasticOD(4,8,self.timeHorizon,volumes['se2n'],rng)
        self.ODs.append(se2n)
        
        se2s = StochasticOD(4,9,self.timeHorizon,volumes['se2s'],rng)
        self.ODs.append(se2s)
        
        se2e = StochasticOD(4,10,self.timeHorizon,volumes['se2e'],rng)
        self.ODs.append(se2e)
        
        se2w = StochasticOD(4,11,self.timeHorizon,volumes['se2w'],rng)
        self.ODs.append(se2w)
        
        se2ne = StochasticOD(4,12,self.timeHorizon,volumes['se2ne'],rng)
        self.ODs.append(se2ne)
        
        se2nw = StochasticOD(4,14,self.timeHorizon,volumes['se2nw'],rng)
        self.ODs.append(se2nw)
        
        se2sw = StochasticOD(4,15,self.timeHorizon,volumes['se2sw'],rng)
        self.ODs.append(se2sw)
        

        #demand from SW collector
        sw2n = StochasticOD(6,8,self.timeHorizon,volumes['sw2n'],rng)
        self.ODs.append(sw2n)
        
        sw2s = StochasticOD(6,9,self.timeHorizon,volumes['sw2s'],rng)
        self.ODs.append(sw2s)
        
        sw2e = StochasticOD(6,10,self.timeHorizon,volumes['sw2e'],rng)
        self.ODs.append(sw2e)
        
        sw2w = StochasticOD(6,11,self.timeHorizon,volumes['sw2w'],rng)
        self.ODs.append(sw2w)
        
        sw2ne = StochasticOD(6,12,self.timeHorizon,volumes['sw2ne'],rng)
        self.ODs.append(sw2ne)
        
        sw2nw = StochasticOD(6,14,self.timeHorizon,volumes['sw2nw'],rng)
        self.ODs.append(sw2nw)
        
        sw2se = StochasticOD(6,13,self.timeHorizon,volumes['sw2se'],rng)
        self.ODs.append(sw2se)



        for od in self.ODs:
            self.totalDemand += sum(od.demandRates)
        

    def getState(self):
        ret = dict()
        for link in self.links:
            ret[link] = self.links[link].density()
        return ret
