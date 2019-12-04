class dta_env():
    """
    spec for DTA model environment that the RL algorithm will call
    """

    def __init__():
        pass
    
    def reset():
        """
        resets the state of the model to the beginning of the/a day
        """
        
        return initial_state
    
    def step(self, a):
        """
        In: what action (signal/ramp parameters) to use next
        Out: next state, what the reward was from the last state, whether or not the day is over
        """

        return next_state, last_step_reward, done
