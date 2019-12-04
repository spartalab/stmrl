from units import *

class Node:

   def __init__(self, upstreamLinks, downstreamLinks):
      self.upstreamLinks = list(upstreamLinks)
      self.downstreamLinks = list(downstreamLinks)
   
   def updateNode(self, t):
      """
      updateNode performs all the computations needed for a node during network loading: calculating sending/receiving
      flows for adjacent links, calculating proportions, transition flows, and finally moving flow.
      """
      sendingFlow = dict()
      receivingFlow = dict()
      for inLink in self.upstreamLinks:               
         sendingFlow[inLink] = inLink.calculateSendingFlow(t)
      for outLink in self.downstreamLinks:
         receivingFlow[outLink] = outLink.calculateReceivingFlow(t)
      self.proportion = self.calculateProportions(t)   
      self.transitionFlows = self.calculateTransitionFlows(sendingFlow, receivingFlow, self.proportion)
      self.moveFlow(t, self.transitionFlows)
         
   def calculateTransitionFlows(self, sendingFlow, receivingFlow, proportion, t=None):
      """
      transitionFlow is a dictionary of dictionaries whose keys are a pair of incoming and outgoing links, and whose
      values are the number of vehicles which can move between these pair of links during a time interval.  This
      method must be overridden for each node type.
      """
      pass
   
   def moveFlow(self, transitionFlows, t):
      """
      This method actually takes care of moving flow from incoming links to outgoing links.  transitionFlows is a dictionary
      of dictionaries; the two keys are the incoming and outgoing links, and the values indicate how many vehicles should move
      between that pair of links during time interval t.  To do this while ensuring FIFO, we need to use the disaggregated
      version of the sending flows calculated earlier.
      """
      linkInflow = dict()
      for outLink in self.downstreamLinks:
         linkInflow[outLink] = dict()

      for inLink in self.upstreamLinks:
         sendingFlow = inLink.calculateSendingFlow(t)
         linkOutflow = dict()
         for path in self.disaggregateSendingFlow[inLink]:
            for outLink in self.downstreamLinks:
               if outLink.ID in path and sendingFlow * self.proportion[inLink][outLink] > 0:
                  pathMovingFlow = self.disaggregateSendingFlow[inLink][path] * transitionFlows[inLink][outLink] / (sendingFlow * self.proportion[inLink][outLink])
                  linkOutflow[path] = pathMovingFlow
                  linkInflow[outLink][path] = linkInflow[outLink].setdefault(path, 0) + pathMovingFlow
         inLink.flowOut(linkOutflow)
         
      for outLink in self.downstreamLinks:
         outLink.flowIn(linkInflow[outLink])

   
   def calculateDisaggregateSendingFlows(self, t):
      """
      This method calculates the sending flow for a link, then uses getFlowComposition to see what paths are used by these vehicles.
      Due to discretization, the sending flow vehicles generally do not align exactly with time interval boundaries, so this method
      scales/normalizes these values so that the total number of vehicles in the disaggregateSendingFlow is correct, while the proportions
      match those given by getFlowComposition (which is based on a superset of the time intervals in the sending flow).
      """
      self.disaggregateSendingFlow = dict()
      for inLink in self.upstreamLinks:
         sendingFlow = inLink.calculateSendingFlow(t)
        
         # Get raw disaggregate sending flows...
         if sendingFlow > 0:
            self.disaggregateSendingFlow[inLink] = inLink.getFlowComposition(inLink.getEntryTime(inLink.downstreamCount(t),False), inLink.getEntryTime(inLink.downstreamCount(t) + sendingFlow, True))
         else:
            self.disaggregateSendingFlow[inLink] = dict()

         # Now scale them so they add up to the proper values.
         if self.disaggregateSendingFlow[inLink] != None and sum(self.disaggregateSendingFlow[inLink].values()) > 0:
            scaleFactor = sendingFlow / sum(self.disaggregateSendingFlow[inLink].values())
            for path in self.disaggregateSendingFlow[inLink]:
               self.disaggregateSendingFlow[inLink][path] *= scaleFactor
            

   # Each path is a tuple of links that includes each link at most once                     
   def calculateProportions(self, t): 
      """
      calculateProportions uses the disaggregateSendingFlows from incoming links to calculate the proportion of the sending flow
      headed for each outgoing link.  It returns a dictionary of dictionaries (proportion) whose keys are the incoming and outgoing
      links, and whose values are the proportion of the sending flow from the incoming link which wants to turn onto the outgoing
      link.
      """
      self.calculateDisaggregateSendingFlows(t)
      proportion = dict()
      for inLink in self.upstreamLinks:
         proportion[inLink] = dict()
         outFlow = dict()
         for path in self.disaggregateSendingFlow[inLink]:
            for outLink in self.downstreamLinks:
               if outLink.ID in path:
                  proportion[inLink][outLink] = proportion[inLink].setdefault(outLink, 0) + self.disaggregateSendingFlow[inLink][path]
                  continue
         totalFlow = float(sum(proportion[inLink].values()))
         if (totalFlow > 0):
            for outLink in self.downstreamLinks:
               proportion[inLink][outLink] = proportion[inLink].setdefault(outLink, 0) / totalFlow
         else:
            for outLink in self.downstreamLinks:
               proportion[inLink][outLink] = 1.0 / (len(self.downstreamLinks))
      return proportion
            

      

