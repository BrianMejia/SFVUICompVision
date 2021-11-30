import cv2
import argparse
from threading import Thread
from queue import Queue, Empty
import time
import os
import psutil
import d3dshot

from frameprocessor import FrameProcessor
from framestate import FrameState
from charplayerocr import CharPlayerOCR

def run():
    p = psutil.Process(os.getpid())
    p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)

    # sideQueue is sent to separate OCR thread, communicates player side
    ocrFrames = []
    sideQueue = Queue()

    # Show Computer Vision on window if displayFrames is True
    fp = FrameProcessor(displayFrames)
    fs = FrameState()

    # Collect character/player names from match
    cpo = CharPlayerOCR()

    pSideReqSent = False
    pSideFound = False
    pSideCountdown = 5

    sideQueue = Queue()

    d = d3dshot.create(capture_output="numpy")
    d.capture(target_fps=targetFPS)
    time.sleep(2) # Let capture grab frames before processing them

    # cv2.namedWindow('CV Frame', cv2.WND_PROP_FULLSCREEN)
    # cv2.setWindowProperty('CV Frame', cv2.WND_PROP_FULLSCREEN,
    #                      cv2.WINDOW_FULLSCREEN)
    print("Starting Video...")
    try:
        while True:
            screenshot = cv2.cvtColor(d.get_latest_frame(), cv2.COLOR_RGB2BGR)

            # Determine which UI regions to check currently
            regionsToCheck = fs.getRegionsToCheck()

            # Return checked UI elements, which UI regions are active on screen
            detections = fp.checkRegions(screenshot, regionsToCheck)
            
            # UI that is active on screen determines other UI elements to check on next frame
            (startDet, endDet) = fs.setDetections(detections)

            if displayFrames:
                cvFrame = fp.filterFrame()
                cv2.imshow('CV Frame', cvFrame)
            
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    cv2.destroyAllWindows()
                    break

            if startDet and len(ocrFrames) < 15:
                # Start detection sometimes happens a little before
                # character/player names are clear enough to see,
                # gives script time before sending frames to process
                if pSideCountdown == 0:
                    ocrFrames.append(screenshot)
                else:
                    pSideCountdown -= 1
            if endDet and len(ocrFrames) > 0:
                ocrFrames = []
                pSideReqSent = False
                pSideFound = False

            if not pSideReqSent and len(ocrFrames) == 15:
                Thread(target=cpo.ocrStart, args=(ocrFrames, sideQueue,)).start()
                pSideReqSent = True
            
            if not pSideFound and pSideReqSent:
                try:
                    pSide = sideQueue.get(timeout=0.005)
                    fp.setSide(pSide)
                    pSideFound = True
                    pSideCountdown = 5
                except Empty:
                    pass
            
            # Reduce CPU usage by sleeping before processing next frame
            time.sleep(1/targetFPS)
    except KeyboardInterrupt:
        pass

    d.stop()
    exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A utility tool that detects which \
        UI elements are active during a Street Fighter V match.")
    parser.add_argument("-df", "--displayframes", help="flag that displays OpenCV2 window to \
        show UI element detection (more taxing on system)", action="store_true")

    argument = parser.parse_args()
    displayFrames = False
    targetFPS = 30

    if argument.displayframes:
        print("OpenCV2 will open a window to show which UI elements are detected to the user.")
        displayFrames = True

    run()
