from copy import copy
from dta import node
from dta import nodeModel
from dta import link
from dta import linkModel
import sys
import traceback
from dta import utils
from dta import units
import numpy.random

INFINITY = 99999
NO_PATH = 'N/A'
EXIT_FAILURE = -1
IS_MISSING = -1

class OD:
	"""
	The OD class has four attributes: the origin node, the destination node,
	a list of the total demand between the origin and destination (with one element per
	time interval), and a list of paths which connect the origin and destination.
	This can either be an enumeration of all paths (which the Network class currently
	implements) or a subset of paths used for assignment.
	"""
	def __init__(self, origin, destination, demandRates):
		self.origin = origin
		self.destination = destination
		self.demandRates = list(demandRates)
		self.paths = list()
	
class StochasticOD(OD):
	def __init__(self,origin,destination,timeHorizon,rate,rng=numpy.random.RandomState()):
		demandRates = list(rng.poisson(rate,timeHorizon))
		#TODO generate demand rates stochastically
		super().__init__(origin,destination,demandRates)

class Network:
	"""
	The Network class has methods for reading a network, performing network loading, and
	performing dynamic traffic assignment.  It makes frequent calls to Link and Node
	methods.  Some important attributes of the Network class are the following:
	
		links ------------ a dictionary whose keys are a string identifier for a link (e.g., '(i,j)') and
								 whose values are Link objects
		nodes ------------ a list of Node objects
		ODs -------------- a list of OD objects
		forwardStar ------ a list with one element per node; each element of this list is a list of IDs for
								 links leaving this node.
		reverseStar ------ the same as forwardStar, but for links entering this node.
		pathFlows -------- a dictionary whose keys are paths (described as tuples of link IDs), and whose values are
								 lists of path flows at each time step.
		pathTravelTimes -- a dictionary whose keys are paths (described as tuples of link IDs), and whose values are
								 lists of path travel times for each possible departure time (one element per
								 time step).
						
	
	
	def __init__(self, networkFile):	
		
		#Set up a network by reading a network file, doing some basic validation, and initializing data structures.
		
		self.links = dict()
		self.nodes = list()
		self.ODs = list()
		self.pathFlows = dict() # Dictionary; keys are paths, values are a list of path flows (one per departure time)
		self.pathTravelTimes = dict() # Dictionary; keys are paths, values are a list of travel times (one per departure time)
		
		self.readNetworkFile(networkFile) # Read the network data
		self.validate() # Check for errors
		self.finalize() # Set up all remaining data structures
	"""
	#Special constructor for project network
	def __init__(self,vehsPerTimestep, seed = 1883,freeVol=3000,rampVol=600):
		rng = numpy.random.RandomState(seed)

		self.links = dict()
		self.ODs = list()
		self.pathFlows = dict()
		self.pathTravelTimes = dict()

		self.timestep = 1	#seconds
		self.simLength = 3600 #seconds
		self.timeHorizon = int(self.simLength/self.timestep)
		self.numLinks = 4
		self.numNodes = 5
		self.linkPriorities = dict()
		self.totalDemand = 0.0

		freeSpeed = 60 #mph
		freeBack = 30 #mph
		#freeVol = 3000 #veh/hr
		rampSpeed = 45 #mph
		rampBack = 30 #mph
		#rampVol = 600 #veh/hr

		freeIn = linkModel.CellTransmissionModelLink(self.timestep,freeSpeed,freeBack,200,5280*3/4,3200,'Freeway Upstream')
		freeOut = linkModel.CellTransmissionModelLink(self.timestep,freeSpeed,freeBack,200,5280,3200,'Freeway Downstream')
		rampIn = linkModel.PointQueueLink(self.timestep,rampSpeed,rampBack,200,5280,1600,ID='Ramp Upstream of Meter')
		rampOut = linkModel.CellTransmissionModelLink(self.timestep,rampSpeed+(freeSpeed-rampSpeed)/2,rampBack+(freeBack-rampBack)/2,200,900,1600,'Ramp Downstream of Meter')

		self.links['Freeway Upstream'] = freeIn
		self.links['Freeway Downstream'] = freeOut
		self.links['Ramp Upstream of Meter'] = rampIn
		self.links['Ramp Downstream of Meter'] = rampOut

		priorities = {freeIn:3,rampOut:1}

		freeStart = nodeModel.OriginNode([],[freeIn])
		rampStart = nodeModel.OriginNode([],[rampIn])
		rampMeter = nodeModel.RampMeterNode([rampIn],[rampOut])
		merge = nodeModel.MergeNode([freeIn,rampOut],[freeOut],priorities)
		freeEnd = nodeModel.DestinationNode([freeOut],[])
		self.nodes = [freeStart,rampStart,rampMeter,merge,freeEnd]

		freeIn.tail = 0
		freeIn.head = 3
		freeOut.tail = 3
		freeOut.head = 4
		rampIn.tail = 1
		rampIn.head = 2
		rampOut.tail = 2
		rampOut.head = 3

		freeOD = StochasticOD(0,4,self.timeHorizon,freeVol*self.timestep/3600,rng)
		self.ODs.append(freeOD)
		self.totalDemand += sum(freeOD.demandRates)

		rampOD = StochasticOD(1,4,self.timeHorizon,rampVol*self.timestep/3600,rng)
		self.ODs.append(rampOD)
		self.totalDemand += sum(rampOD.demandRates)

		self.finalizeLinks()
		self.finalizeODs()

	def updatePathFlows(self, targetPathFlows, stepSize):
		"""
		Updates the self.pathFlows dictionary to try to move closer to equilibrium.  In this assignment
		you will implement the convex combinations algorithm here, where the
		given stepSize is between 0 and 1, and the targetPathFlows matrix is given.
		
		You can refer to the number of vehicles departing on a particular path at a particular time
		with self.pathFlows[path][t] (for the current H matrix) or targetPathFlows[path][t] (for H*)
		"""
		for path in self.pathFlows: #for each path in the physical network
			for t in range(self.timeHorizon):	#for each time in the study period
				#set h = h*(s) + h(1-s), a convex combination of h* (from targetPathFlows) and the prior h value
				try:
					self.pathFlows[path][t] = (targetPathFlows[path][t]*stepSize) + (self.pathFlows[path][t]*(1-stepSize))
				except KeyError:	#if the path isn't listed in targetPathFlows, treat its target as 0
					self.pathFlows[path][t] = self.pathFlows[path][t]*(1-stepSize)
	
	def TDSP(self, origin, departureTime):
		"""
		Executes a one-to-all time-dependent shortest path algorithm to find the best paths from
		a given origin and departure time to all other nodes.  This method should return a tuple
		containing the cost and backlink labels for each node.  Each of these labels is expressed
		in a list with one element per node.
		"""
		##################
		# FIFO algorithm #
		##################
		# 1. Initialize by setting L_i = infinity for all nodes i except for the origin, where L_r = t_0
		cost = [INFINITY] * self.numNodes
		cost[origin] = departureTime
		# 2. Initialize the set of finalized nodes F = {} and the backnode vector q = -1
		finalized = set() #set of finalized nodes
		backlink = [NO_PATH] * self.numNodes

		# 6. While all reachable nodes have not been finalized
		while len(finalized) < self.numNodes:
			
			# 3. Choose an unfinalized node i with the lowest L_i value
			# (At the first iteration, this will be the origin r)
			"""
			Implementation note: this is a suboptimal way to find the min
			unfinalized node, but it's good enough to get through the assignment
			"""
			minL = INFINITY
			minN = None
			for node in range(self.numNodes):
				if node not in finalized and cost[node] < minL:
					minL = cost[node]
					minN = node
			if minN is None:	#If all reachable nodes have been finalized
				break			#terminate the procedure

			# 4. Finalize node i: F = F + i			
			finalized.add(minN)
			
			# 5. For each link (i,j) in outgoing(i) such that L_i + t_ij(L_i)
			# is within the time horizon, perform the following steps:
			
			for link in self.forwardStar[minN]:
				# a) Update L_j = min(L_j, L_i + t_ij(L_i))
				try:
					Lj = cost[minN] + self.links[link].travelTime[cost[minN]]
				except IndexError:
					Lj = INFINITY
				# b) if L_j changed in the previous step, update q_j = (i,j)		
				if Lj < cost[self.links[link].head]:
					cost[self.links[link].head] = Lj
					backlink[self.links[link].head] = link
  
		return (cost, backlink)
	
	def DTA(self, numIterations = 100, targetAEC = 0.1):
		"""
		Performs dynamic traffic assignment on the network, implementing the framework given
		in the textbook by iterating between network loading, time-dependent shortest path,
		and updating path flows.
		"""
		self.initializePathFlows()
		for self.iteration in range(0, numIterations):
			#print("Starting iteration %d ..." % (self.iteration + 1), end='')
			self.loadNetwork()
			self.calculateTravelTimes()
			targetPaths = self.findAllShortestPaths() # Returns h*
			AEC = self.averageExcessCost(recomputeSPTT = False) # No need to recompute SPTT since we just found them.
			#print("average excess cost is", AEC)
			if AEC < targetAEC: break
			self.updatePathFlows(targetPaths, 1.0 / (self.iteration + 2))

	def initializePathFlows(self):
		"""
		Gives an initial all-or-nothing assignment of demand to paths, based on current travel times.
		To avoid duplicating code, this is implemented by calling findAllShortestPaths and updatePathFlows
		with a step size of 1.
		"""
		for OD in self.ODs:
			for path in OD.paths:
				self.pathFlows[path] = [0 for t in range(0,self.timeHorizon)]
		self.updatePathFlows(self.findAllShortestPaths(), 1.0)
			  
	def loadNetwork(self,r=None,init=True):
		"""
		Implements the network loading algorithm described in Chapter 10 of the text, using calls
		to the Link and Node objects.
		"""
		if r is None:
			r = range(self.timeHorizon)

		# 1. Initialize; use dict's to store sending and receiving flows for each link
		if init:
			self.sendingFlow = dict()
			self.receivingFlow = dict()
			for ij in self.links: # Reset all counts
				self.links[ij].upstreamPathCount = list()
				self.links[ij].downstreamPathCount = list()
				self.links[ij].upstreamPathCount.append(dict())
				self.links[ij].downstreamPathCount.append(dict())
			
		for t in r:
			print(t)
			# 2. Calculate sending and receiving flows for all links
			for ij in self.links:
				self.sendingFlow[ij], self.receivingFlow[ij] = self.links[ij].linkUpdate(t)

			for i in range(self.numNodes):
				# Ignore centroids for now
				if hasattr(self.nodes[i], 'isCentroid'): continue

				# 3. Calculate transition flows for all nodes			
				self.nodes[i].proportion = self.nodes[i].calculateProportions(t)	
				transitionFlows =  self.nodes[i].calculateTransitionFlows( { self.links[ij] : self.sendingFlow[ij] for ij in self.reverseStar[i] },
																			{ self.links[ij] : self.receivingFlow[ij] for ij in self.forwardStar[i] },
																			self.nodes[i].proportion, t)
				# 4. Move flow
				self.nodes[i].moveFlow(transitionFlows, t)
				
			# 5. Load trips at origins
			self.loadTrips(t)
			
			# 6. Terminate trips at destinations
			self.terminateTrips(t)
			
	def loadTrips(self, t):
		"""
		Places flow at the upstream ends of paths.  Does NOT check to see if the link can accommodate these
		vehicles before adding... origin centroid connectors should have infinite density so this will not
		be a problem as long as your centroid connectors are coded correctly.
		"""
		inFlows = dict() # a two-key dictionary; first key is starting link, second key is path
		for ij in self.links:
			inFlows[ij] = dict()
			
		for OD in self.ODs:
			for path in OD.paths:
				if self.pathFlows[path][t] > 0:
					inFlows[path[0]][path] = self.pathFlows[path][t]
					
		for ij in self.links:
			if hasattr(self.nodes[self.links[ij].tail], 'isCentroid'):
				self.links[ij].flowIn(inFlows[ij])
	
	def terminateTrips(self, t):
		"""
		Removes flow from the network at the destination end of paths.
		"""
		for i in range(self.numNodes):
			if hasattr(self.nodes[i], 'isDestination'):
				self.nodes[i].calculateDisaggregateSendingFlows(t)
				for ij in self.reverseStar[i]:
					self.links[ij].flowOut(self.nodes[i].disaggregateSendingFlow[self.links[ij]])
	
	def calculateTravelTimes(self,rnge=None):
		"""
		Updates travel times of all links and paths in the network.
		"""
		if rnge is None:
			rnge = range(self.timeHorizon)
		self.calculateLinkTravelTimes(rnge)
		self.calculatePathTravelTimes(rnge)
		
	def calculateLinkTravelTimes(self,rnge, tolerance = 1e-5):
		"""
		Updates travel times for all links in the network, based on matching
		upstream/downstream counts.  tolerance argument is used to control numerical errors.
		"""
		for ij in self.links:
			for entryTime in rnge:
				n = self.links[ij].upstreamCount(entryTime)
				exitTime = entryTime + self.links[ij].freeFlowTime
				while exitTime < rnge[-1]:
					if self.links[ij].downstreamCount(exitTime) >= n - tolerance: break
					exitTime += 1
				self.links[ij].travelTime[entryTime] = exitTime - entryTime			 
		
	def calculatePathTravelTimes(self,rnge=None):
		"""
		Updates travel times for all paths in the network, by chaining together the
		time-dependent travel times of their constituent links.
		"""
		if rnge is None:
			rnge = range(self.timeHorizon)
		for OD in self.ODs:
			for path in OD.paths:
				if path not in self.pathTravelTimes:
					self.pathTravelTimes[path] = dict()
				for t in rnge:
					self.pathTravelTimes[path][t] = 0
				ptt = self.pathTravelTimes[path]
				pathArrivalTime = dict()
				for t in rnge:
					pathArrivalTime[t] = t
				for ij in path:
					for t in rnge:
						link = self.links[ij]
						try:
							ptt[t] += link.travelTime[pathArrivalTime[t]]
						except IndexError:
							ptt[t] += link.freeFlowTime
						try:
							pathArrivalTime[t] += self.links[ij].travelTime[pathArrivalTime[t]]
						except IndexError:
							pathArrivalTime[t] += self.links[ij].freeFlowTime
						pathArrivalTime[t] = min(pathArrivalTime[t], rnge[-1] - 1)
	
	def findAllShortestPaths(self):
		"""
		Finds shortest paths for all OD pairs in the network, using repeated calls to
		the TDSP method, and identify an all-or-nothing assignment which places all demand
		on these paths just found.  This method returns the targetPathFlows dictionary which
		contains this all-or-nothing assignment.
		"""
		self.SPTT = 0
		targetPathFlows = dict()
		for OD in self.ODs:
			for t in range(self.timeHorizon):
				if OD.demandRates[t] > 0:
					# Find shortest path...
					cost, backlink = self.TDSP(OD.origin, t)
					if backlink[OD.destination] == None:
						print("Unable to find a path from %d to %d within the time horizon, when departing at time %d." % (OD.origin, OD.destination, t))
						sys.exit(EXIT_FAILURE)
					# ...now reconstruct it from the labels...
					curNode = OD.destination
					tempPath = list()
					while curNode != OD.origin:
						tempPath.insert(0, backlink[curNode])
						curNode = self.links[backlink[curNode]].tail
					path = tuple(tempPath)
					# ...and add the relevant entry in the all-or-nothing assignment
					if path not in targetPathFlows:
						targetPathFlows[path] = [0] * self.timeHorizon
					targetPathFlows[path][t] = OD.demandRates[t]
					self.SPTT += OD.demandRates[t] * (cost[OD.destination] - t)
				
		return targetPathFlows	

	def calculateTSTT(self,r = None):
		"""
		Calculate total system travel time in the Network using the current path flows and travel times.
		"""
		if r is None:
			r = range(self.timeHorizon)
		TSTT = 0.0
		for link in self.links:
			for t in r:
				TSTT += self.links[link].vehiclesOnLink(t)
		return TSTT

	def calculateTFFT(self,r=None):
		if r is None:
			r = range(self.timeHorizon)
		TFFT = 0.0
		for path in self.pathFlows:
			for t in r:
				TFFT += self.pathFlows[path][t] * sum(self.links[link].freeFlowTime for link in path)
		return TFFT
			
	def averageExcessCost(self, recomputeSPTT = True):
		"""
		Calculate average excess cost.  Calculating shortest path travel time can be expensive, and often times we have already
		calculated it doing something else (like finding an all-or-nothing assignment).  Calling averageExcessCost with
		recomputeSPTT = False can save on some run time.  Just be sure that in your implementation, travel times haven't changed
		since the last call to findAllShortestPaths, or else you could get negative AEC or other nonsensical values.
		"""
		if recomputeSPTT == True: self.findAllShortestPaths()
		return (self.calculateTSTT() - self.SPTT) / self.totalDemand
	  
	def enumeratePaths(self, origin):
		"""
		Find literally all simple paths in the Network starting at a given origin.
		"""
		paths = list()
		activePaths = list()
		
		# Initialize with links from the origin
		for ij in self.forwardStar[origin]:
			paths.append((ij,))
			activePaths.append([ij])
				
		# Now iterate 
		while len(activePaths) > 0:
			newPaths = list()
			for path in activePaths: # Augment each active path
				i = self.links[path[-1]].head
				for ij in self.forwardStar[i]:
					if ij not in path:
						newPaths.append(tuple(list(path) + [ij,])) # Ugly data structure hacking
				activePaths.remove(path)	
			paths += newPaths
			activePaths += newPaths

		return paths
	  
	def readNetworkFile(self, networkFile):
		"""
		Read a given network file and set up Link and OD objects.
		"""
		linksRead = 0  
		self.timestep = IS_MISSING
		self.timeHorizon = IS_MISSING
		self.numLinks = IS_MISSING
		self.numNodes = IS_MISSING
		self.linkPriorities = dict()
		self.totalDemand = 0.0
				
		try:
			with open(networkFile, "r") as testFile:
				# Read test information
				fileLines = testFile.read().splitlines()
				for line in fileLines:
					# Ignore comments and blank lines
					if len(line.strip()) == 0 or line[0] == '#':
						continue
						 
					# Read network data
					if self.timestep == IS_MISSING:
						inputs = line.split(",")
						if len(inputs) != 4: raise utils.BadFileFormatException
						self.numLinks = int(inputs[0])
						self.numNodes = int(inputs[1])
						self.timestep = float(inputs[2])
						self.timeHorizon = int(inputs[3])
						continue
						
					# Read link data
					if (linksRead < self.numLinks):
						inputs = line.split(",")
						if len(inputs) != 10: 
							print("Error reading link data line %s" % inputs)
							raise utils.BadFileFormatException
						uf = float(inputs[3])
						w = float(inputs[4])
						kj = float(inputs[5])
						L = float(inputs[6])
						qmax = float(inputs[7])
						if	inputs[9] == 'PQ':  newLink = linkModel.PointQueueLink(self.timestep, uf, w, kj, L, qmax, qmax, inputs[0])
						elif inputs[9] == 'SQ':  newLink = linkModel.SpatialQueueLink(self.timestep, uf, w, kj, L, qmax, qmax, inputs[0])
						elif inputs[9] == 'CTM': newLink = linkModel.CellTransmissionModelLink(self.timestep, uf, w, kj, L, qmax, inputs[0])
						elif inputs[9] == 'LTM': newLink = linkModel.LinkTransmissionModelLink(self.timestep, uf, w, kj, L, qmax, inputs[0])
						else: 
							print("Link model %s is not implemented." % inputs[9])
							raise utils.BadFileFormatException
						newLink.tail = int(inputs[1]) - 1  # Convert from 1-based (input file) to 0-based (internal)
						newLink.head = int(inputs[2]) - 1  # Convert from 1-based (input file) to 0-based (internal)
						self.links[inputs[0]] = newLink
						self.linkPriorities[inputs[0]] = float(inputs[8])
						linksRead += 1
						continue
						
					# Read OD data
					inputs = line.split(",")
					if len(inputs) != 2 + self.timeHorizon:
						print("Wrong number of demand values for OD pair")
						raise utils.BadFileFormatException
					newOD = OD(int(inputs[0]) - 1, int(inputs[1]) - 1, [int(d) for d in inputs[2:]]) # Convert from 1-based (input file) to 0-based (internal)
					self.ODs.append(newOD)
					self.totalDemand += sum(newOD.demandRates)
					
		except IOError:
			print("\nError reading network file %s" % networkFile)
			traceback.print_exc(file=sys.stdout) 

	def validate(self):
		"""
		Perform basic input validation for the network.
		"""
		valid = True
		
		timeHorizonPositive = self.timeHorizon > 0
		if not timeHorizonPositive: print("Network validation failed: time horizon must be positive)", self.timeHorizon)
		timestepPositive = self.timestep > 0
		if not timestepPositive: print("Network validation failed: time step must be positive)", self.timestep)
		valid = valid and timeHorizonPositive and timestepPositive
		
		for ij in self.links:
			headInRange = self.links[ij].head > 0 and self.links[ij].head <= self.numNodes
			tailInRange = self.links[ij].head > 0 and self.links[ij].tail <= self.numNodes
			nonnegativeParameters = self.links[ij].freeFlowSpeed > 0 
			nonnegativeParameters = nonnegativeParameters and self.links[ij].backwardWaveSpeed > 0
			nonnegativeParameters = nonnegativeParameters and self.links[ij].jamDensity >= 0
			nonnegativeParameters = nonnegativeParameters and self.links[ij].length > 0			
			nonnegativeParameters = nonnegativeParameters and self.links[ij].capacity >= 0						
			nonnegativeParameters = nonnegativeParameters and self.linkPriorities[ij] >= 0						
			if not headInRange: print("Network validation failed: link %s head out of range" % ij)
			if not tailInRange: print("Network validation failed: link %s head out of range" % ij)
			if not nonnegativeParameters: print("Network validation failed: link %s has negative or zero parameters" % ij)
			valid = valid and headInRange and tailInRange and nonnegativeParameters
	  
		for OD in self.ODs:
			originInRange = OD.origin >= 0 and OD.origin < self.numNodes
			destinationInRange = OD.destination >= 0 and OD.destination < self.numNodes
			nonnegativeDemand = min(OD.demandRates) >= 0
			if not originInRange: print("Network validation failed: origin %d out of range" % (OD.origin + 1))
			if not destinationInRange: print("Network validation failed: destination %d out of range" % (OD.destination + 1))
			if not nonnegativeDemand: print("Network validation failed: negative demand value for OD pair %d -> %d" % (OD.origin + 1, OD.destination + 1))
			valid = valid and originInRange and destinationInRange and nonnegativeDemand
			
		if valid == False: raise utils.BadFileFormatException
			
	def finalizeLinks(self):
		"""
		Finish setting up the network, including Node objects (detecting the appropriate node type), 
		finding relevant paths, and  setting link and path travel times to free flow.
		"""
		
		# Set up links -- initialize travel times to free flow
		for ij in self.links:
			self.links[ij].travelTime = [self.links[ij].freeFlowTime for t in range(self.timeHorizon+900)]
			
		# Set up nodes -- identify links entering/leaving nodes, then initialize appropriately
		self.forwardStar = [[] for i in range(self.numNodes)]
		self.reverseStar = [[] for i in range(self.numNodes)]
		
		for ij in self.links:
			self.forwardStar[self.links[ij].tail].append(ij)	
			self.reverseStar[self.links[ij].head].append(ij)	
		"""	
		for i in range(self.numNodes):
			inLinks = [self.links[ij] for ij in self.reverseStar[i]]
			outLinks = [self.links[ij] for ij in self.forwardStar[i]]
			if len(inLinks) == 0:								  self.nodes.append(nodeModel.OriginNode(inLinks, outLinks))
			elif len(outLinks) == 0:							  self.nodes.append(nodeModel.DestinationNode(inLinks, outLinks))
			elif len(inLinks) == 1 and len(outLinks) == 1: self.nodes.append(nodeModel.SeriesNode(inLinks, outLinks))
			elif len(inLinks) == 1:								self.nodes.append(nodeModel.DivergeNode(inLinks, outLinks))
			elif len(outLinks) == 1:							  self.nodes.append(nodeModel.MergeNode(inLinks, outLinks,
																				{self.links[ij] : self.linkPriorities[ij] for ij in self.reverseStar[i]}))
			else:
				print("General intersections not yet implemented")
				raise utils.BadFileFormatException
		"""
	def finalizeODs(self):
		# Set up paths -- enumerate *all* network paths, then assign the appropriate ones to each OD pair
		# Warning: This approach will not scale if you give it a large network.  Use with caution.
		
		originPaths = list()
		for i in range(self.numNodes):
			originPaths.append(self.enumeratePaths(i))
			
		for OD in self.ODs:
			validOrigin = type(self.nodes[OD.origin]) is nodeModel.OriginNode
			validDestination = type(self.nodes[OD.destination]) is nodeModel.DestinationNode			
			if not validOrigin: print("Network validation failed: origin %d is not an OriginNode" % (OD.origin + 1))
			if not validDestination: print("Network validation failed: destination %d is not a DestinationNdode" % (OD.destination + 1))
			if not validOrigin or not validDestination: raise utils.BadFileFormatException
		
			OD.paths = [path for path in originPaths[OD.origin] if self.links[path[-1]].head == OD.destination]
			if len(OD.paths) == 0: 
				print("Network not connected: no paths from %d to %d" % (OD.origin, OD.destination))
				raise utils.BadFileFormatException
			
		self.calculatePathTravelTimes()

	"""
	Calculate the total entering demand between the start and end time segments
	"""
	def demand(self,start = 0, end = None):
		demand = 0.0
		for OD in self.ODs:
			demand += sum(OD.demandRates[start:end])
		return demand

	"""
	Calculate the TRTT from the difference in cumulative entrances and exits
	"""
	def rampTravelTime(self, start = 0, end = None):
		if end is None:
			end = self.timeHorizon

		rtt = 0.0
		inputProfile = self.ODs[1].demandRates
		outputProfile = self.nodes[2].flows

		flowToIgnore = sum(inputProfile[0:start])
		inputCursor = start

		outFlow = 0.0
		t = 0
		while outFlow + outputProfile[t] <= flowToIgnore:
			outFlow += outputProfile[t]
			t += 1
		sli = 0.0
		while inputCursor < end and t < self.timeHorizon:
			while sli < inputProfile[inputCursor] and t < self.timeHorizon:
				sli += outputProfile[t]
				rtt += outputProfile[t]*(t-inputCursor)
				t += 1
			oic = inputCursor
			inputCursor += 1
			while inputCursor < end and inputProfile[inputCursor] == 0:
				inputCursor += 1
			rtt -= (sli - inputProfile[oic])*(inputCursor-oic)
			sli = sli - inputProfile[oic]
			
		return rtt

	"""
	Calculate the total demand entering on the ramp between the start and end time
	"""
	def rampDemand(self,start = 0,end = None):
		if end is None:
			end = self.timeHorizon
		return sum(self.ODs[1].demandRates[start:end])