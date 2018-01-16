import cv2
import numpy as np
import copy
from sys import argv

drawing = False # true if mouse is pressed
ix,iy = 0,0
cx,cy = 0,0
boxList = []
seqBox = {} #marked box
outBox = {} #predicted box

def point_in_box(cx, cy, x1, y1, x2, y2):
    if (cx>min(x1,x2) and cx<max(x1,x2) and cy>min(y1,y2) and cy<max(y1,y2)):
        return True
    return False

# mouse callback function
def draw_box(event,x,y,flags,param):
    global ix,iy,drawing,res,resempty,boxList
    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        ix,iy = x,y
        #draw box in boxList
        res = np.copy(resempty)
        for cbox in boxList:
                cv2.rectangle(res, (cbox["x1"], cbox["y1"]), (cbox["x2"], cbox["y2"]), (0,255,0),2,0)
        cv2.imshow('origin', res)
    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing == True:
            #draw box in boxList
            res = np.copy(resempty)
            for cbox in boxList:
                cv2.rectangle(res, (cbox["x1"], cbox["y1"]), (cbox["x2"], cbox["y2"]), (0,255,0),2,0)
            cv2.rectangle(res,(ix,iy),(x,y),(0,255,0),2,0)
            cv2.imshow('origin', res)
    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        if (abs(ix-x)>10 and abs(iy-y)>10):
            #add rect to boxList
            boxDict = dict(x1=min(ix,x), y1=min(iy,y), x2=max(x,ix), y2=max(y,iy))
            boxList.append(boxDict)
        else:
            ix=iy=0
        #draw box in boxList
        res = np.copy(resempty)
        for cbox in boxList:
                cv2.rectangle(res, (cbox["x1"], cbox["y1"]), (cbox["x2"], cbox["y2"]), (0,255,0),2,0)        
        cv2.imshow('origin', res)
    elif event == cv2.EVENT_RBUTTONUP:
        #delete selected box in boxList
        for cbox in boxList:
            if (point_in_box(x,y, cbox["x1"], cbox["y1"], cbox["x2"], cbox["y2"])):
                boxList.remove(cbox)
                break
        #draw box in boxList
        res = np.copy(resempty)
        for cbox in boxList:
                cv2.rectangle(res, (cbox["x1"], cbox["y1"]), (cbox["x2"], cbox["y2"]), (0,255,0),2,0)
        cv2.imshow('origin', res)


def write_box_to_file(fileName):
    #print fileName
    f1 = open(fileName, 'w')
    f1.write("%s\n" % "frame, x1, y1, x2, y2")
    for boxidx in seqBox:
        f1.write("%03d, " % boxidx)
        for cbox in seqBox[boxidx]:
            f1.write("%03d, %03d, %03d, %03d, " % (cbox["x1"]*r, cbox["y1"]*r, cbox["x2"]*r, cbox["y2"]*r))
        f1.write("\n")
    f1.close()

def write_results_to_file(fileName):
    #print fileName
    f1 = open(fileName, 'w')
    f1.write("%s\n" % "frame, x1, y1, x2, y2")
    for boxidx in outBox:
        f1.write("%03d, " % boxidx)
        for cbox in outBox[boxidx]:
            f1.write("%03d, %03d, %03d, %03d, " % (cbox["x1"]*r, cbox["y1"]*r, cbox["x2"]*r, cbox["y2"]*r))
        f1.write("\n")
    f1.close()


def predict_box_in_all_frames():
    if len(seqBox)<=1:
        return
    markedFrames = seqBox.keys()
    markedFrames.sort()
    for i in range(markedFrames[0], markedFrames[-1]+1):
        outBox[i] = []        
    startIdx = markedFrames[0]
    startBoxLst = seqBox[startIdx]
    boxNumber = len(startBoxLst)
    for idx in markedFrames[1:]:
        endBoxLst = seqBox[idx]
        if (len(startBoxLst) != len(endBoxLst)):
            print "Box number error!"
            exit()

        #linear fitting for each box
        for i in range(boxNumber):
            x1s, y1s, x2s, y2s = startBoxLst[i]["x1"], startBoxLst[i]["y1"], startBoxLst[i]["x2"], startBoxLst[i]["y2"]
            x1e, y1e, x2e, y2e = endBoxLst[i]["x1"], endBoxLst[i]["y1"], endBoxLst[i]["x2"], endBoxLst[i]["y2"]

            for j in range(startIdx, idx):
                x1c = x1s + int((x1e-x1s)*(j-startIdx)/(idx-startIdx))
                y1c = y1s + int((y1e-y1s)*(j-startIdx)/(idx-startIdx))
                x2c = x2s + int((x2e-x2s)*(j-startIdx)/(idx-startIdx))
                y2c = y2s + int((y2e-y2s)*(j-startIdx)/(idx-startIdx))
                cboxDict = dict(x1=x1c, y1=y1c, x2=x2c, y2=y2c)
                outBox[j].append(cboxDict)

        #next predict
        startIdx = idx
        startBoxLst = seqBox[startIdx]
    #add last box to outBox
    outBox[idx] = copy.deepcopy(startBoxLst)


if __name__ == '__main__':
    if (len(argv)<3):
        print "usage: python markbox.py originFileName tamperFileName\n"
        exit()
    originFileName = argv[1] #"00001.mp4"
    tamperFileName = argv[2] #"00001_136-262.mp4"  
    #originFileName = "00001.mp4"
    #tamperFileName = "00001_136-262.mp4"            
    origin = cv2.VideoCapture(originFileName)
    tamper = cv2.VideoCapture(tamperFileName)

    fps = origin.get(cv2.CAP_PROP_FPS)
    size = (int(origin.get(cv2.CAP_PROP_FRAME_WIDTH)),
        int(origin.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    #print "fps %.2f, width %d, height %d" % (fps, size[0], size[1])
    #print "\npress ESC for quit\n"
    print originFileName
    print tamperFileName
    print "frame, x1, y1, x2, y2"

    cnt = 0
    w, h = size[0], size[1]
    r = 3
    cv2.namedWindow('origin', cv2.WINDOW_AUTOSIZE)
    cv2.namedWindow('tamper', cv2.WINDOW_AUTOSIZE)
    cv2.namedWindow('tamper-delta', cv2.WINDOW_AUTOSIZE)
    cv2.moveWindow('origin', 40, 40)
    cv2.moveWindow('tamper', w/r+80, 40)
    cv2.moveWindow('tamper-delta', 80, h/r+80)


    #skip bad frames at the begining
    if (not origin.isOpened()) or (not tamper.isOpened()):
        exit()
    ret1, frame = origin.read()
    ret2, framet = tamper.read()
    framepre = framet

    while (ret1==False or ret2==False):
        print "%d, skip one bad frame" % (cnt)
        cnt += 1
        framepre = framet
        ret1, frame = origin.read()
        ret2, framet = tamper.read()

    cv2.setMouseCallback('origin', draw_box)

    #process frame by frame
    while(ret1 and ret2):
        ix,iy = 0,0
        cx,cy = 0,0

        res=cv2.resize(frame, (w/r,h/r), interpolation=cv2.INTER_CUBIC)
        rest=cv2.resize(framet, (w/r,h/r), interpolation=cv2.INTER_CUBIC)

        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(rest, str(cnt), (10,50), font, 1, (0,0,255), 2)
        
        resempty = np.copy(res) #for backup

        #show box in boxList
        for cbox in boxList:
            p1 = (cbox["x1"], cbox["y1"])
            p2 = (cbox["x2"], cbox["y2"])
            cv2.rectangle(res, p1, p2, (0,0,255),2,0)

        cv2.imshow('origin', res)
        cv2.imshow('tamper', rest)
        
        resd = abs(framet-framepre)
        #resd = cv2.cvtColor(resd, cv2.COLOR_BGR2GRAY)
        resd = cv2.resize(resd, (w/r,h/r), interpolation=cv2.INTER_CUBIC)
        cv2.imshow('tamper-delta', resd)

        inputkey = cv2.waitKey(0)
        if inputkey & 0xFF == 27:
            break #ESC to exit
        elif inputkey  & 0xFF == ord('s'):
            #save boxList to seqList
            if len(boxList):
                seqBox[cnt] = copy.deepcopy(boxList)
            elif cnt in seqBox:
                seqBox.pop(cnt)

            #print box in boxList
            print "frame %03d, " % (cnt),
            for cbox in boxList:
                print "%d, %d, %d, %d, " % (cbox["x1"]*r, cbox["y1"]*r, cbox["x2"]*r, cbox["y2"]*r),
            print " "
        elif inputkey  & 0xFF == ord('r'):
            cnt = cnt - 2
            origin.set(cv2.CAP_PROP_POS_FRAMES, cnt)
            tamper.set(cv2.CAP_PROP_POS_FRAMES, cnt)
            #boxList = []

        cnt += 1
        if cnt in seqBox:
            boxList = copy.deepcopy(seqBox.get(cnt))

        framepre = framet
        ret1, frame = origin.read()
        ret2, framet = tamper.read()

    origin.release()
    tamper.release()
    cv2.destroyAllWindows()

    #write box in all video sequence to file
    write_box_to_file(originFileName.split('.')[0]+".txt")

    #predict box in all frames
    predict_box_in_all_frames()

    #write predict results in all video frames to file
    write_results_to_file(originFileName.split('.')[0]+"_predicted.txt")


