from copy import copy
from .node import Node

class WrongNodeTypeException(Exception):
   pass
   
class SeriesNode(Node):

   def __init__(self, upstreamLinks, downstreamLinks):
      if len(upstreamLinks) != 1 or len(downstreamLinks) != 1:
         raise WrongNodeTypeException
      Node.__init__(self, upstreamLinks, downstreamLinks)
   
   def calculateTransitionFlows(self, sendingFlow, receivingFlow, proportion, t=None):
      transitionFlows = dict()
      for inLink in self.upstreamLinks:
         transitionFlows[inLink] = dict()
        
      upLink = self.upstreamLinks[0]
      downLink = self.downstreamLinks[0]
     
      transitionFlows[upLink][downLink] = min(sendingFlow[upLink], receivingFlow[downLink])
      return transitionFlows
      
class RampMeterNode(SeriesNode):
   def __init__(self,upstreamLinks,downstreamLinks):
      super().__init__(upstreamLinks,downstreamLinks)
      self.flows = list()


   def calculateTransitionFlows(self,sendingFlow,receivingFlow,proportion, t=None):
      transitionFlows = dict()
      for inLink in self.upstreamLinks:
         transitionFlows[inLink] = dict()

      upLink = self.upstreamLinks[0]
      downLink = self.downstreamLinks[0]

      flow = min(self.vpts,sendingFlow[upLink],receivingFlow[downLink])
      transitionFlows[upLink][downLink] = flow
      self.flows.append(flow)

      # if (receivingFlow[downLink] < self.vpts and receivingFlow[downLink] < sendingFlow[upLink]):
      #    print("Backed up!")

      return transitionFlows
   
   def setParams(self,param):
      self.vpts = float(param)

class DivergeNode(Node):

   def __init__(self, upstreamLinks, downstreamLinks):
      if len(upstreamLinks) != 1 or len(downstreamLinks) < 1:
         raise WrongNodeTypeException
      Node.__init__(self, upstreamLinks, downstreamLinks)
   
   def calculateTransitionFlows(self, sendingFlow, receivingFlow, proportion, t=None):
      transitionFlows = dict()  
      for inLink in self.upstreamLinks:
         transitionFlows[inLink] = dict()
      
      inLink = self.upstreamLinks[0]
      
      movingFraction = 1
      for outLink in self.downstreamLinks:
         try:
            movingFraction = min(movingFraction, receivingFlow[outLink] / (sendingFlow[inLink] * proportion[inLink][outLink] ))
         except ZeroDivisionError:
            pass
            
      for outLink in self.downstreamLinks:
         transitionFlows[inLink][outLink] = movingFraction * proportion[inLink][outLink] * sendingFlow[inLink]            
      
      return transitionFlows
      
class OriginNode(Node):

   def __init__(self, upstreamLinks, downstreamLinks):
      if len(upstreamLinks) != 0:
         raise WrongNodeTypeException
      Node.__init__(self, upstreamLinks, downstreamLinks)
      self.isCentroid = True      

class DestinationNode(Node):
   
   def __init__(self, upstreamLinks, downstreamLinks):
      if len(downstreamLinks) != 0:
         raise WrongNodeTypeException
      Node.__init__(self, upstreamLinks, downstreamLinks)
      self.isCentroid = True
      self.isDestination = True
  
class MergeNode(Node):

   # For a merge node, also need to include the relative priority values for each node
   def __init__(self, upstreamLinks, downstreamLinks, priority):
      if len(upstreamLinks) < 1 or len(downstreamLinks) != 1:
         raise WrongNodeTypeException
      Node.__init__(self, upstreamLinks, downstreamLinks)
      self.priority = priority
      if min(priority.values()) <= 0:
         print("Merge nodes must have strictly positive priority values for incoming links.")
         raise WrongNodeTypeException
   
   def calculateTransitionFlows(self, sendingFlow, receivingFlow, proportion, t=None):
      transitionFlows = dict()   
      for inLink in self.upstreamLinks:
         transitionFlows[inLink] = dict()
      
      outLink = self.downstreamLinks[0]      
      
      for inLink in self.upstreamLinks:
         transitionFlows[inLink][outLink] = 0
         
      activeLinks = copy(self.upstreamLinks)
      while len(activeLinks) > 0 and receivingFlow[outLink] > 0:
         totalPriority = 0
         for inLink in activeLinks:
            totalPriority += self.priority[inLink]
         flowMovedThisIteration = 0
         inactivatedLinks = list()
         for inLink in activeLinks:
            additionalFlow = min(sendingFlow[inLink], self.priority[inLink] / float(totalPriority) * receivingFlow[outLink])
            transitionFlows[inLink][outLink] += additionalFlow
            flowMovedThisIteration += additionalFlow
            sendingFlow[inLink] -= additionalFlow
            if sendingFlow[inLink] == 0: 
               inactivatedLinks.append(inLink)
         receivingFlow[outLink] -= flowMovedThisIteration
         for inLink in inactivatedLinks:
            activeLinks.remove(inLink)
      
      return transitionFlows

class FullyProtectedIntersectionNode(Node):
   def __init__(self,upstreamLinks,downstreamLinks,barriers, permissivePhases):
      Node.__init__(self,upstreamLinks,downstreamLinks)
      self.barriers = barriers
      self.currentBarrier = None
      self.currentIdx = 0
      # self.currentBarrier.start(0)
      self.permissivePhases = permissivePhases

   def calculateTransitionFlows(self, sendingFlow, receivingFlow, proportion, t=None):
      activePhases = self.getActivePhases(t)
      transitionFlows = dict()

      for inLink in self.upstreamLinks:
         transitionFlows[inLink] = dict()
         for outLink in self.downstreamLinks:
            transitionFlows[inLink][outLink] = 0

      for (inLink, outLink) in activePhases:
         if inLink not in transitionFlows:
            transitionFlows[inLink] = dict()
         flow = min(sendingFlow[inLink], receivingFlow[outLink])
         transitionFlows[inLink][outLink] = flow
         receivingFlow[outLink] -= flow
      
      
      permissivePhases = self.getPermissivePhases(t)
      
      for (inLink, outLink) in permissivePhases:
         if inLink not in transitionFlows:
            transitionFlows[inLink] = dict()
         flow = min(receivingFlow[outLink], sendingFlow[inLink])
         transitionFlows[inLink][outLink] = flow
         receivingFlow[outLink] -= flow
      
      return transitionFlows

   def getActivePhases(self,t):
      barrier = self.getCurrentBarrier(t)
      return [ring.getActivePhase(t) for ring in barrier.getRings()]

   def getPermissivePhases(self,t):
      return self.permissivePhases
   
   def getCurrentBarrier(self,t):
      barrier = self.currentBarrier
      if barrier is None:
         barrier = self.barriers[0].copy()
         self.currentBarrier = barrier
         barrier.start(t)
      elif t - barrier.startTime > barrier.length:
         self.currentIdx = (self.currentIdx + 1) % len(self.barriers)
         barrier = self.barriers[self.currentIdx].copy()
         self.currentBarrier = barrier
         barrier.start(t)
      return barrier

   def setParams(self,params):
      if 'barrier 0' in params:
         self.barriers[0].length = max(0,params['barrier 0'])
      if 'barrier 1' in params:
         self.barriers[1].length = max(0,params['barrier 1'])

      if 'split 00' in params:
         self.barriers[0].rings[0].split = params['split 00']
      if 'split 01' in params:
         self.barriers[0].rings[1].split = params['split 01']
      if 'split 10' in params:
         self.barriers[1].rings[0].split = params['split 10']
      if 'split 11' in params:
         self.barriers[1].rings[1].split = params['split 11']

class Barrier:

   def __init__(self, rings, length):
      self.rings = [ring.copy(self) for ring in rings]
      self.length = length
      self.startTime = None
   
   def getRings(self):
      return self.rings

   def start(self,t):
      self.startTime = t
   
   def copy(self,length=None):
      if length is None:
         length = self.length
      return Barrier(self.rings,length)

class Ring:
   def __init__(self,phases,split):
      self.phases = phases
      self.split = split
   
   def copy(self,barrier):
      ring = Ring(self.phases,self.split)
      ring.barrier = barrier
      return ring

   def getActivePhase(self,t):
      transition = self.barrier.length*max(0.0,min(1.0,self.split))
      if transition < t - self.barrier.startTime:
         return self.phases[1]
      else:
         return self.phases[0]