from .link import Link
from .units import *

class NotYetAttemptedException(Exception):
   pass
   
DEFAULT = -1

class PointQueueLink(Link):

   def __init__(self, timestep, freeFlowSpeed, backwardWaveSpeed, jamDensity, length, downstreamCapacity, upstreamCapacity = DEFAULT, ID = None):
      # Create a generic link...
      Link.__init__(self, timestep, freeFlowSpeed, backwardWaveSpeed, jamDensity, length, downstreamCapacity, ID)
      # ... then allow point queues to have different upstream and downstream capacities
      self.downstreamCapacity = self.capacity 
      if (upstreamCapacity == DEFAULT):
         self.upstreamCapacity = self.downstreamCapacity
      else:
         self.upstreamCapacity = upstreamCapacity / HOURS * timestep
         
   def calculateSendingFlow(self, t):
      return min(self.upstreamCount(t + 1 - self.freeFlowTime) - self.downstreamCount(t), self.downstreamCapacity)

   def calculateReceivingFlow(self, t):
      return self.upstreamCapacity

class SpatialQueueLink(Link):

   def __init__(self, timestep, freeFlowSpeed, backwardWaveSpeed, jamDensity, length, downstreamCapacity, upstreamCapacity = DEFAULT, ID = None):
      # Create a generic link...
      Link.__init__(self, timestep, freeFlowSpeed, backwardWaveSpeed, jamDensity, length, downstreamCapacity, ID)
      # ... then allow spatial queues to have different upstream and downstream capacities
      self.downstreamCapacity = self.capacity
      if (upstreamCapacity == DEFAULT):
         self.upstreamCapacity = self.downstreamCapacity
      else:
         self.upstreamCapacity = upstreamCapacity / HOURS * timestep

   def calculateSendingFlow(self, t):
      return min(self.upstreamCount(t + 1 - self.freeFlowTime) - self.downstreamCount(t), self.downstreamCapacity)

   def calculateReceivingFlow(self, t):
      return max(0, min(self.maxVehicles - self.vehiclesOnLink(t), self.upstreamCapacity))

class Cell:
   
   def __init__(self, capacity, maxVehicles, delta):
      self.capacity = capacity
      self.maxVehicles = maxVehicles
      self.delta = delta
      self.vehicles = 0
            
   def calculateSendingFlow(self):
      return max(0,min(self.vehicles, self.capacity))

   def calculateReceivingFlow(self):
      return max(0,min(self.delta * (self.maxVehicles - self.vehicles), self.capacity))
      
   def removeVehicles(self, numVehicles):
      self.vehicles -= numVehicles
      
   def addVehicles(self, numVehicles):
      self.vehicles += numVehicles

class CellTransmissionModelLink(Link):

   def __init__(self, timestep, freeFlowSpeed, backwardWaveSpeed, jamDensity, length, capacity, ID = None):
      Link.__init__(self, timestep, freeFlowSpeed, backwardWaveSpeed, jamDensity, length, capacity, ID)
      # Create a cell for each timestep needed to traverse the link
      self.cells = list()
      for _ in range(self.freeFlowTime):
         newCell = Cell(self.capacity, self.jamDensity * self.length / self.freeFlowTime, self.backwardWaveSpeed / self.freeFlowSpeed)
         self.cells.append(newCell)
         
   def calculateSendingFlow(self, t):
      return self.cells[-1].calculateSendingFlow()

   def calculateReceivingFlow(self, t):
      return self.cells[0].calculateReceivingFlow()

   def linkUpdate(self, t):
      # Calculate sending/receiving flows based on initial values
      sendingFlow = self.calculateSendingFlow(t)
      receivingFlow = self.calculateReceivingFlow(t)

      # Now calculate flow moving between cells
      cellTransitionFlow = list()
      for c in range(0, self.freeFlowTime-1):
         cellSendingFlow = self.cells[c].calculateSendingFlow()
         cellReceivingFlow = self.cells[c+1].calculateReceivingFlow()
         cellTransitionFlow.append(min(cellSendingFlow, cellReceivingFlow))
      
      # Now propagate flow between cells
      for c in range(0, self.freeFlowTime-1):
         self.cells[c].removeVehicles(cellTransitionFlow[c])
         self.cells[c+1].addVehicles(cellTransitionFlow[c])
         
      return (sendingFlow, receivingFlow)

   def flowIn(self, pathFlows):
      Link.flowIn(self, pathFlows)
      totalIn = sum(pathFlows.values())
      self.cells[0].addVehicles(totalIn)
   
   def flowOut(self, pathFlows):   
      Link.flowOut(self, pathFlows)
      totalOut = sum(pathFlows.values())
      self.cells[len(self.cells)-1].removeVehicles(totalOut)

   def density(self):
      return sum(cell.vehicles for cell in self.cells)/self.length

class LinkTransmissionModelLink(Link):

   def calculateSendingFlow(self, t):
      return min(self.upstreamCount(t + 1 - self.freeFlowTime) - self.downstreamCount(t), self.capacity)

   def calculateReceivingFlow(self, t):
      return min(self.downstreamCount(t + 1 - self.backwardWaveTime) + self.maxVehicles - self.upstreamCount(t), self.capacity)
   
