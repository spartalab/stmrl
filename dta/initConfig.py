def getInitConfig(timestep):
    cfg = { 'nb ramp' : 300*timestep/3600,
            'sb ramp' : 400*timestep/3600,
            
            'wx' :    
                {'split 00' : 0.3,
                'split 01' : 0.5,
                'split 10' : 0.7,
                'split 11' : 0.9,
                'barrier 0' : 60/timestep,
                'barrier 1' : 30/timestep},
            
            'ex' :
                {'split 00' : 0.8,
                'split 01' : 0.6,
                'split 10' : 0.4,
                'split 11' : 0.2,
                'barrier 0' : 50/timestep,
                'barrier 1' : 40/timestep},
            
            'wrx' :
                {'split 00' : 0.6,
                'barrier 0' : 40/timestep,
                'barrier 1' : 40/timestep},
            
            'erx' :
                {'split 01' : 0.4,
                'barrier 0' : 50/timestep,
                'barrier 1' : 50/timestep}
            }
    return cfg
        