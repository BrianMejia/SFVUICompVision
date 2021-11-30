import cv2
import numpy as np
import pytesseract
import psutil
import os

# OCR processing modified, taken from
# https://github.com/Techyuvi/OCR
#
# This class detects player side based on a player name!
# Please change self.pName to match your own
class CharPlayerOCR:
    def __init__(self):
        self.image = None

        self.charLower = np.array([242, 241, 230])
        self.charUpper = np.array([255, 255, 255])
        self.nameLower = np.array([115, 115, 200])
        self.nameUpper = np.array([255, 255, 255])

        self.P1CharBound = (635, 60, 84, 441)
        self.P2CharBound = (635, 60, 1390, 452)
        self.P1NameBound = (810, 33, 128, 270)
        self.P2NameBound = (810, 33, 1313, 270)

        self.P1 = []
        self.P2 = []
        self.pSide = 0
        self.pName = 'Mejican'

        p = psutil.Process(os.getpid())
        p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
        
    def process_players(self, images):
        imgCount = 1
        for image in images:
            print("Checking Image {}".format(imgCount))
            self.P1 = []
            self.P2 = []
            self.pSide = 0

            self.process_player(image, True)
            self.process_player(image, False)

            if len(self.P1) > 0 and len(self.P2) > 0:
                self.pSide = self.get_player_side()
                if self.pSide != -1:
                    self.write_opponent_char()
                    return
            
            print("Data Not Found for Image {}".format(imgCount))
            imgCount += 1
    
    def get_player_side(self):
        p1LenGood = len(self.P1[0]) > 0 and self.P1[0][0] is not None
        p2LenGood = len(self.P2[0]) > 0 and self.P2[0][0] is not None

        if p1LenGood and p2LenGood:
            print(self.P1)
            print(self.P2)
            if self.P1[0][0] == self.pName:
                return 1
            if self.P2[0][0] == self.pName:
                return 2
        return -1
    
    def process_player(self, image, isP1):
        charBound = self.P1CharBound if isP1 else self.P2CharBound
        nameBound = self.P1NameBound if isP1 else self.P2NameBound

        bgrBounds = ((self.nameLower, self.nameUpper), (self.charLower, self.charUpper))
        for idx, bound in enumerate([nameBound, charBound]):
            crop = image[bound[0]:bound[0]+bound[1], bound[2]:bound[2]+bound[3]]
            thresholds_image = self.pre_processing(crop, bgrBounds[idx][0], bgrBounds[idx][1])
            parsed_data = self.parse_text(thresholds_image)
            arranged_text = self.format_text(parsed_data)

            if isP1:
                self.P1.append(arranged_text)
            else:
                self.P2.append(arranged_text)

    def pre_processing(self, image, lower, upper):      
        mask = cv2.inRange(image, lower, upper)
        colorThres = cv2.bitwise_not(image, image, mask=mask)
        colorThres[mask==0] = (255,255,255)

        return colorThres

    def parse_text(self, threshold_img):
        tesseract_config = r'--oem 3 --psm 6'
        details = pytesseract.image_to_data(threshold_img, output_type=pytesseract.Output.DICT,
                                            config=tesseract_config, lang='eng')
        return details

    def format_text(self, details):
        parse_text = []
        word_list = []
        last_word = ''
        for word in details['text']:
            if word != '':
                word_list.append(word)
                last_word = word
            if (last_word != '' and word == '') or (word == details['text'][-1]):
                parse_text.append(word_list)
                word_list = []
        
        return parse_text[0]
    
    def write_opponent_char(self):
        charList = self.P1 if self.pSide == 2 else self.P2
        opp_char = 'SAKURA'

        if any ('F.A.N.G' in string for string in charList):
            opp_char = 'FANG'
        else:
            with open('cfg/SFVChars.txt', 'r') as f:
                char_names = f.readlines()
                for char in char_names:
                    if any(char.strip() in string for string in charList):
                        opp_char = char.strip()
                        break
        
        print(opp_char)
    
    def ocrStart(self, frames, sideQueue):
        self.process_players(frames)
        sideQueue.put(self.pSide)
        exit(0)