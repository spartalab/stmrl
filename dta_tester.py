from dta.dta_env import dta_env

env = dta_env(interval=60*60*5)
for i in range(30):
    with open(""+str(i)+".txt",'w') as outfile:
        ni = 60//5
        env = dta_env(interval=60*5, numIntervals=ni)
        state = env.reset()
        for _ in range(ni):
            _, rew, _ = env.step()
            outfile.write(str(rew)+"\n")