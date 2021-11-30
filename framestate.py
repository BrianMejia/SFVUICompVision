import time

class FrameState:
    def __init__(self):
        self.keys = [
            'start1', 'start2', 'start3', 'fight',
            'ko1', 'ko2', 'whiteScreen', 'blackScreen',
            'end', 'hp1', 'hp2', 'hpg',
            'combo1', 'combo2', 'combo3',
            'ca', 'vt'
        ]

        self.states = {}
        for key in self.keys:
            self.states[key] = {}
            self.states[key]['active'] = False
            self.states[key]['perc'] = 0.0
            self.states[key]['fade'] = False
            self.states[key]['detected'] = False
        
        self.dmgCount = 0
        self.dmgTime = time.time()
        self.dmgCooldown = 1.75

        self.ocrFrames = []
        self.ocrChecked = False
    
    def getRegionsToCheck(self):
        toCheck = []

        if not self.states['start1']['detected'] and not self.states['end']['detected']:
            toCheck.extend(['start1', 'start2', 'start3'])
        if self.states['start1']['detected'] and not self.states['whiteScreen']['detected']:
            toCheck.append('whiteScreen')
        if (self.states['whiteScreen']['detected'] or self.states['blackScreen']['detected']) \
            and not self.states['fight']['detected']:
            toCheck.append('fight')
        if self.states['fight']['detected'] and not self.states['ko1']['detected']:
            toCheck.extend(['hp1', 'hp2', 'hpg', 'combo1', 'combo2', 'combo3', 'ko1', 'ko2'])
        if self.states['ko1']['detected'] and not self.states['end']['detected']:
            toCheck.extend(['ca', 'vt', 'blackScreen', 'end'])
        
        for key in self.states:
            # Fade helps visual clarity of Computer Vision window
            # as UI elements transition from active to non-active
            if self.states[key]['fade']:
                toCheck.append(key)
        
        return list(set(toCheck))
    
    # Most unique region of start screen is the show light 'VS' text
    # Checks three color ranges to see if 'VS' is on screen
    def checkStartDetected(self):
        darkPerc = self.states['start1']['perc']
        midPerc = self.states['start2']['perc']
        brightPerc = self.states['start3']['perc']

        regFilled = 0.9 <= (darkPerc + midPerc + brightPerc) <= 1.2
        regWithin1 = darkPerc-0.2 <= midPerc <= darkPerc+0.2
        regWithin2 = brightPerc-0.2 <= midPerc <= brightPerc+0.2

        res = regFilled and regWithin1 and regWithin2
        self.states['start1']['detected'], self.states['start2']['detected'], \
            self.states['start3']['detected'], = (res,)*3

        if res:
            print("Start Detected")

        return res
    
    # Adds time between checking for damage taken to stop combos from
    # activating the damage check every time a frame is processed
    #
    # There might be a way to determine if damage is taken
    # by the increasing/decreasing amount of red detected on
    # the healthbar, must look into that
    def checkDmgDetected(self):
        self.states['hp1']['detected'] = False
        elapsed = time.time() - self.dmgTime
        comboDet = self.states['combo1']['perc'] > 0.75 or self.states['combo2']['perc'] > 0.75 or self.states['combo3']['perc'] > 0.75
        if not comboDet and (elapsed >= self.dmgCooldown):
            self.dmgTime = time.time()
            self.states['hp1']['detected'] = True
            self.dmgCount += 1
            print("Damage {} Detected".format(self.dmgCount))
        elif comboDet:
            self.dmgTime = time.time() - 1.12
    
    # UI element activity is usually set to True and not
    # flipped back until another element is detected
    # Handler for this method of updating states of UI elements
    def setDetections(self, updatedStates):
        for key in updatedStates.keys():
            self.states[key]['active'] = updatedStates[key]['active']
            self.states[key]['perc'] = updatedStates[key]['perc']
            self.states[key]['fade'] = updatedStates[key]['fade']

        if self.states['start1']['active'] and not self.states['start1']['detected']:
            self.checkStartDetected()
        if self.states['whiteScreen']['active'] and not self.states['whiteScreen']['detected']:
            print("White Screen Detected")
            self.states['whiteScreen']['detected'] = True
        if self.states['fight']['active'] and not self.states['fight']['detected']:
            print("Fight Detected")
            self.states['fight']['detected'] = True
            self.states['blackScreen']['detected'] = False
        if self.states['ko1']['active'] and not self.states['ko1']['detected']:
            print("KO Detected")
            self.states['ko1']['detected'] = True
            for key in ['hp1', 'hp2', 'hpg']:
                self.states[key]['detected'] = False
        if self.states['blackScreen']['active'] and not self.states['blackScreen']['detected']:
            print("Black Screen Detected")
            self.states['blackScreen']['detected'] = True
            for key in ['fight', 'ko1', 'ca', 'vt']:
                self.states[key]['detected'] = False
        if self.states['ca']['active'] and not self.states['ca']['detected']:
            print("CA Detected")
            self.states['ca']['detected'] = True
        if self.states['vt']['active'] and not self.states['vt']['detected']:
            print("VT Detected")
            self.states['vt']['detected'] = True
        if self.states['end']['active'] and not self.states['end']['detected']:
            print("End Detected")
            self.states['end']['detected'] = True
            for key in ['start1', 'whiteScreen', 'ca', 'vt']:
                self.states[key]['detected'] = False
        
        damageActive = (self.states['hp1']['active'] or self.states['hp2']['active']) and not self.states['hpg']['active']
        if damageActive and not self.states['ko1']['detected']:
            self.checkDmgDetected()
        
        return (self.states['start1']['detected'], self.states['end']['detected'])