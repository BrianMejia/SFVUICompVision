import cv2
import numpy as np
import json
    
class FrameProcessor:
    def __init__(self, displayFrames):
        self.height = 1080
        self.width = 1920

        self.displayFrames = displayFrames

        with open('./cfg/Start1080p.json') as jsonFile:
            self.regions = json.load(jsonFile)
        
        self.sideDepKeys = [
            'hp1', 'hp2', 'hpg',
            'combo1', 'combo2', 'combo3',
            'ca', 'vt'
        ]

        self.frame = None
        self.overlay = None
        self.frameResized = None
        self.overlayResized = None
    
    def filterFrame(self):
        self.frameResized = cv2.resize(self.frame, (int(self.width/2), int(self.height/2)), interpolation=cv2.INTER_AREA)
        self.overlayResized = cv2.resize(self.overlay, (int(self.width/2), int(self.height/2)), interpolation=cv2.INTER_AREA)
        
        blackImg = np.full(self.frameResized.shape, (0,0,0), np.uint8)
        darkenedImg  = cv2.addWeighted(self.frameResized, 0.4, blackImg, 0.6, 0)

        cvFrame = cv2.add(cv2.cvtColor(darkenedImg, cv2.COLOR_BGR2BGRA), self.overlayResized)
        return cvFrame
    
    def maskOutputToBGRA(self, imgData):
        tmp = cv2.cvtColor(imgData, cv2.COLOR_BGR2GRAY)
        _, alpha = cv2.threshold(tmp, 0, 255, cv2.THRESH_BINARY)
        b, g, r = cv2.split(imgData)
        bgra = [b, g, r, alpha]

        return cv2.merge(bgra, 4)
    
    # Crops screen to fit within selected UI element
    # Finds color match of UI element within region, turns rest of cropped region transparent
    # Finds out if UI element is active on given frame
    def checkRegion(self, key):
        pos = self.regions[key]['boundPos']
        lower = np.array(self.regions[key]['boundBGR'][0], dtype = "uint8")
        upper = np.array(self.regions[key]['boundBGR'][1], dtype = "uint8")

        crop = self.frame[pos[0]:pos[0]+pos[1], pos[2]:pos[2]+pos[3]]
        mask = cv2.inRange(crop, lower, upper)

        output = None
        if self.displayFrames:
            output = self.maskOutputToBGRA(cv2.bitwise_and(crop, crop, mask = mask))

        percent = np.count_nonzero(mask) / mask.size
        
        res = {}
        res['active'] = (percent >= self.regions[key]['thres'])
        res['perc'] = percent
        res['fade'] = False
        if percent > 0.005 or (key in ['hp1', 'hp2', 'hpg'] and percent > 0.0005):
            res['fade'] = True
        
        return (res, output)
    
    def checkRegions(self, copyFrame, reqRegions):
        res = {}
        self.frame = copyFrame

        if self.displayFrames:
            self.overlay = np.zeros((self.height, self.width, 4), dtype=np.uint8)

        for key in reqRegions:
            (retMap, transCrop) = self.checkRegion(key)
            pos = self.regions[key]['boundPos']
            res[key] = retMap

            if self.displayFrames:
                self.overlay[pos[0]:pos[0]+pos[1], pos[2]:pos[2]+pos[3]] = transCrop

        return res
    
    def setSide(self, pSide):
        self.side = pSide
        boundPosStr = 'boundPos' + str(self.side)
        for key in self.sideDepKeys:
            self.regions[key]['boundPos'] = self.regions[key][boundPosStr]