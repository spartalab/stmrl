def getVolumes(timestep):
    #volumes in vehicles per hour
    vols = {'nFwy' : 3000,
            'n2e' : 400,
            'n2w' : 400,
            'n2ne' : 100,
            'n2nw' : 100,
            'n2se' : 100,
            'n2sw' : 100,
            
            'sFwy' : 3000,
            's2e' : 400,
            's2w' : 400,
            's2ne' : 100,
            's2nw' : 100,
            's2se' : 100,
            's2sw' : 100,
            
            'e2w' : 1000,
            'e2n' : 400,
            'e2s' : 400,
            'e2ne' : 100,
            'e2nw' : 100,
            'e2se' : 100,
            'e2sw' : 100,
            
            'w2e' : 1000,
            'w2n' : 400,
            'w2s' : 400,
            'w2ne' : 100,
            'w2nw' : 100,
            'w2se' : 100,
            'w2sw' : 100,
            
            'ne2n' : 50,
            'ne2s' : 50,
            'ne2e' : 30,
            'ne2w' : 30,
            'ne2nw' : 10,
            'ne2se' : 10,
            'ne2sw' : 10,
            
            'nw2n' : 50,
            'nw2s' : 50,
            'nw2e' : 30,
            'nw2w' : 30,
            'nw2ne' : 10,
            'nw2se' : 10,
            'nw2sw' : 10,
            
            'se2n' : 50,
            'se2s' : 50,
            'se2e' : 30,
            'se2w' : 30,
            'se2ne' : 10,
            'se2nw' : 10,
            'se2sw' : 10,
            
            'sw2n' : 50,
            'sw2s' : 50,
            'sw2e' : 30,
            'sw2w' : 30,
            'sw2ne' : 10,
            'sw2nw' : 10,
            'sw2se' : 10
            }
    for key in vols:
        vols[key] = vols[key]*timestep/3600

    return vols