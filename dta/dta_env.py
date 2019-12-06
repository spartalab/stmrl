from volumes import getVolumes
from initConfig import getInitConfig
from networkModel import NetworkModel
import numpy.random as random

class dta_env():
    """
    spec for DTA model environment that the RL algorithm will call
    """

    def __init__(self,interval,numIntervals=1,warmup=900):
        self.interval = interval
        self.numIntervals = numIntervals
        self.vols = getVolumes(1)
        self.cfg = getInitConfig(1)
        self.timeHorizon = warmup+(interval*numIntervals)
        self.warmup = warmup
        self.net = NetworkModel(self.timeHorizon)

        # # dimensionality of action and state space, as properties for the RL model
        self.action_space.dim = 20
        self.state_space.dim = 51
        self.action_space.mins = self.net.constraints()[0]
        self.action_space.maxs = self.net.constraints()[1]
        
        self.action_space.maxIncrements = {
            'split' : 0.05, #percent
            'barrier' : 10., #timesteps
            'ramp' : 25/3600     #people per timestep
        }
    
    def reset(self,seed=1831):
        """
        resets the state of the model to the beginning of the/a day
        """
        self.net.setConfig(self.cfg)

        rng = random.RandomState(seed)

        self.net.setDemand(self.vols,rng)
        self.net.finalizeODs()
        self.net.initializePathFlows()

        self.net.loadNetwork(range(self.warmup),True)
        self.net.calculateTravelTimes(range(self.warmup))
        self.curTime = self.warmup
        self.elapsedIntervals = 0
    
    def step(self, a=None):
        """
        In: what action (signal/ramp parameters) to use next
        Out: next state, what the reward was from the last state, whether or not the day is over
        """
        #process actions
        if a is not None:
            self.updateConfig(a)
            # self.net.setConfig(a)

        intv = range(self.curTime,self.curTime+self.interval)
        self.net.loadNetwork(intv,False)
        self.curTime += self.interval
        self.elapsedIntervals += 1

        self.net.calculateTravelTimes(intv)
        tstt = self.net.calculateTSTT(intv)
        tfft = self.net.calculateTFFT(intv)
        last_step_reward = tfft - tstt
        print(last_step_reward)

        done = self.elapsedIntervals == self.numIntervals

        next_state = (self.elapsedIntervals,self.net.getState(),self.cfg) # fetch state

        return next_state, last_step_reward, done

    def updateConfig(self,actions):

        deltas = self.getDeltas(actions)
        
        self.cfg['nb ramp'] += deltas['nb ramp']
        self.cfg['sb ramp'] += deltas['sb ramp']

        self.cfg['wx']['split 00'] += deltas['wx']['split 00']
        self.cfg['wx']['split 01'] += deltas['wx']['split 01']
        self.cfg['wx']['split 10'] += deltas['wx']['split 10']
        self.cfg['wx']['split 11'] += deltas['wx']['split 11']
        self.cfg['wx']['barrier 0'] += deltas['wx']['barrier 0']
        self.cfg['wx']['barrier 1'] += deltas['wx']['barrier 1']

        self.cfg['ex']['split 00'] += deltas['ex']['split 00']
        self.cfg['ex']['split 01'] += deltas['ex']['split 01']
        self.cfg['ex']['split 10'] += deltas['ex']['split 10']
        self.cfg['ex']['split 11'] += deltas['ex']['split 11']
        self.cfg['ex']['barrier 0'] += deltas['ex']['barrier 0']
        self.cfg['ex']['barrier 1'] += deltas['ex']['barrier 1']

        self.cfg['wrx']['split 00'] += deltas['wrx']['split 00']

        self.cfg['erx']['split 01'] += deltas['erx']['split 01']

        for key in self.cfg['wx']:
            self.cfg['wx'][key] = max(self.action_space.mins['wx'][key],
                                    min(self.action_space.maxs['wx'][key],self.cfg['wx'][key]))
        for key in self.cfg['ex']:
            self.cfg['ex'][key] = max(self.action_space.mins['ex'][key],
                                    min(self.action_space.maxs['ex'][key],self.cfg['ex'][key]))
        for key in self.cfg['erx']:
            self.cfg['erx'][key] = max(self.action_space.mins['erx'][key],
                                    min(self.action_space.maxs['erx'][key],self.cfg['erx'][key]))

        for key in self.cfg['wrx']:
            self.cfg['wrx'][key] = max(self.action_space.mins['wrx'][key],
                                    min(self.action_space.maxs['wrx'][key],self.cfg['wrx'][key]))

        self.cfg['nb ramp'] = max(self.action_space.mins['nb ramp'],
                                min(self.action_space.maxs['nb ramp'],
                                self.cfg['nb ramp']))
    
        self.cfg['sb ramp'] = max(self.action_space.mins['sb ramp'],
                                min(self.action_space.maxs['sb ramp'],
                                self.cfg['sb ramp']))
        
        self.net.setConfig(self.cfg)


    def random_action(self):
        """
        Generate a random action, to be used before RL model training has stabilized.
        """
        # TODO: complete
        raise NotImplementedError()

    def getDeltas(self,action):
        deltas = dict()
        incs = self.action_space.maxIncrements
        
        deltas['wx']['split 00'] = action['wx']['split 00'] * incs['split']
        deltas['wx']['split 01'] = action['wx']['split 01'] * incs['split']
        deltas['wx']['split 10'] = action['wx']['split 10'] * incs['split']
        deltas['wx']['split 11'] = action['wx']['split 11'] * incs['split']
        
        deltas['ex']['split 00'] = action['ex']['split 00'] * incs['split']
        deltas['ex']['split 01'] = action['ex']['split 01'] * incs['split']
        deltas['ex']['split 10'] = action['ex']['split 10'] * incs['split']
        deltas['ex']['split 11'] = action['ex']['split 11'] * incs['split']

        deltas['wrx']['split 00'] = action['wrx']['split 00'] * incs['split']
        deltas['erx']['split 01'] = action['erx']['split 01'] * incs['split']

        deltas['wx']['barrier 0'] = action['wx']['barrier 0'] * incs['barrier']
        deltas['wx']['barrier 1'] = action['wx']['barrier 1'] * incs['barrier']
        deltas['ex']['barrier 0'] = action['ex']['barrier 0'] * incs['barrier']
        deltas['ex']['barrier 1'] = action['ex']['barrier 1'] * incs['barrier']

        deltas['nb ramp'] = action['nb ramp'] * incs['ramp']
        deltas['sb ramp'] = action['sb ramp'] * incs['ramp']



        