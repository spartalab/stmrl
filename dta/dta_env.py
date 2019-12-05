from .volumes import getVolumes
from .initConfig import getInitConfig
from .networkModel import NetworkModel
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
        # self.action_space.dim = # TODO
        # self.state_space.dim = # TODO
        # self.action_space.mins = # TODO
        # self.action_space.maxs = # TODO
        
    
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
        if 'nb ramp' in actions:
            self.cfg['nb ramp'] += actions['nb ramp']*25/3600
        if 'sb ramp' in actions:
            self.cfg['sb ramp'] += actions['sb ramp']*25/3600

        if 'wx' in actions:
            self.cfg['wx']['split 00'] += 0.05*actions['wx']['split 00']
            self.cfg['wx']['split 01'] += 0.05*actions['wx']['split 01']
            self.cfg['wx']['split 10'] += 0.05*actions['wx']['split 10']
            self.cfg['wx']['split 11'] += 0.05*actions['wx']['split 11']
            self.cfg['wx']['barrier 0'] += 5*actions['wx']['barrier 0']
            self.cfg['wx']['barrier 1'] += 5*actions['wx']['barrier 1']
        if 'ex' in actions:
            self.cfg['ex']['split 00'] += 0.05*actions['ex']['split 00']
            self.cfg['ex']['split 01'] += 0.05*actions['ex']['split 01']
            self.cfg['ex']['split 10'] += 0.05*actions['ex']['split 10']
            self.cfg['ex']['split 11'] += 0.05*actions['ex']['split 11']
            self.cfg['ex']['barrier 0'] += 5*actions['ex']['barrier 0']
            self.cfg['ex']['barrier 1'] += 5*actions['ex']['barrier 1']

        if 'wrx' in actions:
            self.cfg['wrx']['split 00'] += 0.05*actions['wrx']['split 00']
            self.cfg['wrx']['barrier 0'] += 5*actions['wrx']['barrier 0']
            self.cfg['wrx']['barrier 1'] += 5*actions['wrx']['barrier 1']

        if 'erx' in actions:
            self.cfg['erx']['split 01'] += 0.05*actions['erx']['split 01']
            self.cfg['erx']['barrier 0'] += 5*actions['erx']['barrier 0']
            self.cfg['erx']['barrier 1'] += 5*actions['erx']['barrier 1']

        self.net.setConfig(self.cfg)
        pass
    
    def random_action(self):
        """
        Generate a random action, to be used before RL model training has stabilized.
        """
        # TODO: complete
        raise NotImplementedError()