from .volumes import getVolumes
from .initConfig import getInitConfig
from .networkModel import NetworkModel
from .dta_env import dta_env

def main():
    interval = 5*60
    numIntervals = 3600//interval

    # interval = 3600
    # numIntervals = 1

    env = dta_env(interval,numIntervals)

    env.reset()

    for _ in range(numIntervals):
        env.step(None)

if __name__ == "__main__":
    main()