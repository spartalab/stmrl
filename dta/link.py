from .units import *

class Link:

   def __init__(self, timestep, freeFlowSpeed, backwardWaveSpeed, jamDensity, length, capacity, ID = None):
      """
      Sets up a link, adjusting units in the following way:
         INPUTS:
         freeFlowSpeed and backwardWaveSpeed arguments must be provided in mi/hr
         jamDensity must be in veh/mi
         length must be provided in feet
         timestep must be in seconds
         capacity argument must be provided in veh/hr
         
         ATTRIBUTES:
         freeFlowSpeed and backwardWaveSpeed will be in *ft/sec*
         jamDensity will be in *veh/ft*
         length will be in *ft*
         freeFlowTime and backwardWaveTime will be integer numbers of *timesteps*
         capacity will be in vehicles per *timestep*         
      """ 
      self.ID = ID
      self.capacity = capacity / HOURS * timestep
      self.freeFlowSpeed = freeFlowSpeed * MILES / HOURS
      self.backwardWaveSpeed = backwardWaveSpeed * MILES / HOURS
      self.jamDensity = jamDensity / MILES
      self.length = length * FEET
      self.maxVehicles = self.length * self.jamDensity
      
      # freeFlowTime and backwardWaveTime are in units of TIMESTEPs
      self.freeFlowTime = int((self.length/self.freeFlowSpeed + timestep - 1) / timestep) 
      self.backwardWaveTime = int((self.length/self.backwardWaveSpeed + timestep - 1) / timestep) 

      # initialize dictionaries and counts
      self.upstreamPathCount = list()
      self.downstreamPathCount = list()
      self.upstreamPathCount.append(dict())
      self.downstreamPathCount.append(dict())

   def calculateSendingFlow(self, t):
      pass

   def calculateReceivingFlow(self, t):
      pass

   def linkUpdate(self, t):
      """
      linkUpdate performs any internal calculations needed for a link at time t, and returns a tuple (S,R) with the sending and receiving flows
      By default, it only returns this tuple; if more is needed you need to override this method.
      """
      return (self.calculateSendingFlow(t), self.calculateReceivingFlow(t))

   def upstreamCount(self, t):
      """
      Return the cumulative entries to a link up through time t
      """
      if t < 0:
         return 0
      count = 0
      for path in self.upstreamPathCount[t].keys():
         count += self.upstreamPathCount[t][path]
      return count

   def downstreamCount(self, t):
      """
      Return the cumulative exits from a link up through time t
      """
      if t < 0:
         return 0
      count = 0
      for path in self.downstreamPathCount[t].keys():
         count += self.downstreamPathCount[t][path]
      return count

   def vehiclesOnLink(self, t):
      """
      Return the number of vehicles currently on a link at time t
      """
      return self.upstreamCount(t) - self.downstreamCount(t)

   def flowIn(self, pathFlows):
      """
      Adds flow to the upstream end of a link; based on pathFlows.  Tracks inflows disaggregated by path.  Extends upstream array. 
      """
      self.upstreamPathCount.append(dict())
      # First copy previous flows
      for path in self.upstreamPathCount[-2].keys():
         self.upstreamPathCount[-1][path] = self.upstreamPathCount[-2][path]

      # Then add new inflows
      for path in pathFlows or []:
         self.upstreamPathCount[-1][path] = pathFlows[path] + self.upstreamPathCount[-1].setdefault(path, 0)

   def flowOut(self, pathFlows):
      """
      Removes flow from the downstream end of a link; based on pathFlows.  Tracks outflows disaggregated by path. Extends downstream array.
      """
      self.downstreamPathCount.append(dict())
      
      # First copy previous flows
      for path in self.downstreamPathCount[-2].keys():
         self.downstreamPathCount[-1][path] = self.downstreamPathCount[-2][path]

      # Then add new outflows
      for path in pathFlows or []:
         self.downstreamPathCount[-1][path] = pathFlows[path] + self.downstreamPathCount[-1].setdefault(path, 0)

   def getFlowComposition(self, startTime, endTime):
      """
      Returns the total number of vehicles entering a link between startTime and endTime (inclusive), disaggregated by path.
      These values are returned in a dictionary with paths as keys.
      """
      startTime = int(startTime)
      endTime = min(int(endTime), startTime + 1)
            
      pathCounts = dict()
      totalFlow = 0
     
      for path in set(self.upstreamPathCount[startTime].keys()) | set(self.upstreamPathCount[endTime].keys()):
         pathCounts[path] = self.upstreamPathCount[endTime].setdefault(path, 0) - self.upstreamPathCount[startTime].setdefault(path, 0)

      return pathCounts
      
   def getEntryTime(self, vehicle, roundUp = False, tolerance = 0.01):
      """
      Returns the time interval during which a given vehicle entered the link.  The roundUp argument indicates whether we should round up (to
      the next multiple of the timestep) or round down (to the previous multiple of the timestep) for this entry time.  In dynamic network
      loading, we should round down when getting the first time interval (startTime in getFlowComposition), and round up when getting the
      second time interval (endTime in getFlowComposition).  This will ensure startTime and endTime are different (or else getFlowComposition
      will simply return all zeroes, which is not useful for getting turning proportions.)
      
      The tolerance argument is used to control for numerical/floating point errors, and can be adjusted as necessary.
      """   
      # round down when getting first time; round up when getting second time
      if roundUp == True:
         t = 0
         while self.upstreamCount(t) <= vehicle - tolerance:
            t += 1
            if t == len(self.upstreamPathCount): return len(self.upstreamPathCount)
      else:
         t = len(self.upstreamPathCount) - 1
         while self.upstreamCount(t) >= vehicle + tolerance:
            t -= 1
            if t == 0: return 0
      return t
      
   def calculateTravelTime(self, t):
      pass

   def density(self,t):
      return (self.upstreamCount(t) - self.downstreamCount(t))/self.length

   def averageSpeed(self,timeRange):
      cumulativeSpeed = 0
      for t in timeRange:
         density = self.density(t)
         if density == 0:
            cumulativeSpeed += self.freeFlowSpeed
         else:
            cumulativeSpeed += (0.5*(self.upstreamCount(t)-self.upstreamCount(t-1)) + 0.5*(self.downstreamCount(t)-self.downstreamCount(t-1)))/density

      return cumulativeSpeed/len(timeRange)

   def enteredDuring(self,timeRange):
      cumulativeVehicles = 0
      for t in timeRange:
         cumulativeVehicles += self.upstreamCount(t) - self.upstreamCount(t-1)
      return cumulativeVehicles

   def exitedDuring(self,timeRange):
      cumulativeVehicles = 0
      for t in timeRange:
         cumulativeVehicles += self.downstreamCount(t) - self.downstreamCount(t-1)
      return cumulativeVehicles

   def __hash__(self):
      return hash(self.ID)
