from dta.dta_env import dta_env

env = dta_env(interval=60*60*5)
state = env.reset()
state = env.step(env.random_action())
