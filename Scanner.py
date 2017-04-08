# -*- coding: utf-8 -*-

# c and c++ only

import os, sys, time, random
from PIL import Image, ImageDraw, ImageFont

print(sys.argv)
result = {}

isCaseSensitive = False
fileSuffixList = ["c", "cpp", "cc", "h", "hpp"]
dirList = []

if len(sys.argv) > 1:
    argList = sys.argv[1:]
    argList.sort()
    if argList[-1] == "-":
        dirList.append(".")
else:
    argList = []
    dirList = ["."]

##### parse configure flags
for arg in argList:
    if arg[0] == "-":
        flags = arg[1:]
        for flag in flags:
            if flag == "s":
                isCaseSensitive = True
            elif flag == "h":
                print("------------------------------")
                print("Get include relationes in the given directories.\n")
                print("Usage:")
                print("    Scanner.py [option]... [dir]...")
                print("Default:")
                print("    Scanner.py .")
                print("Flags:")
                print("    -s: case sensitive search")
                print("    -h: display this message")
                sys.exit(0)
            else:
                print("error: Unknown flag(s).")
                sys.exit(1)
    else:
        dirList.append(arg)

##### scan given directories
for rootDir in dirList:
    fileList = {}
    sysHeaderWeight = {}
    projFileWeight = {}
    dirtyBit = {}

    ##### scan files
    print("scanning files...", end='')
    for (dirpath, dirnames, filenames) in os.walk(rootDir):
        for f in filenames:
            suffix = f.split(".")[-1]
            if not isCaseSensitive:
                suffix = suffix.lower()
            if suffix in fileSuffixList:
                relativePath = os.path.relpath(dirpath, rootDir)
                relativeFileName = os.path.join(relativePath, f)
                fileList[relativeFileName] = [1,]

    if len(fileList) == 0:
        print("error: no supported file.")
        sys.exit(2)
    print("done.")
    time.sleep(0.01)

    ##### scan include lines, and give them the basic weight
    print("scanning includes...", end='')
    for fileName in fileList.keys():
        file = open(os.path.join(rootDir, fileName), "r", encoding="utf8")
        dirtyBit[fileName] = [1,]
        if fileName not in projFileWeight:
            projFileWeight[fileName] = 0
        for line in file:
            line = line.rstrip("\n")
            if "#include" in line:
                includeFileName = line.split(" ")[-1][1:-1]
                includeFileName = includeFileName.replace("\\", os.sep)
                includeFileName = includeFileName.replace("/", os.sep)
                fileNotFound = True
                for findIncludeFile in fileList.keys():
                    if os.path.basename(findIncludeFile) == includeFileName:
                        fileNotFound = False
                        includeFileName = findIncludeFile
                        if findIncludeFile in projFileWeight:
                            projFileWeight[findIncludeFile] += 1
                        else:
                            projFileWeight[findIncludeFile] = 1
                        break
                if fileNotFound:
                    if includeFileName in sysHeaderWeight:
                        sysHeaderWeight[includeFileName] += 1
                    else:
                        sysHeaderWeight[includeFileName] = 1
                fileList[fileName].append(includeFileName)
                dirtyBit[fileName].append(0)
        file.close()
    print("done.")
    time.sleep(0.01)
    
    ##### calculate cumulated weight
    print("calculating cumulated weight...", end='')
    doneCalculate = False
    firstRun = True
    maxLevel = 0
    while(not doneCalculate):
        for fileName in fileList:
            listLength = len(fileList[fileName])
            if listLength < 1:
                print("error: fileList length should not be 0.")
                sys.exit(3)
            elif listLength > 1:
                for header in fileList[fileName][1:]:
                    if dirtyBit[fileName][fileList[fileName].index(header)] == 0:
                        if firstRun and header in sysHeaderWeight:
                            projFileWeight[fileName] += sysHeaderWeight[header]
                            dirtyBit[fileName][fileList[fileName].index(header)] = 1
                        elif header in projFileWeight:
                            if 0 not in dirtyBit[header]:
                                projFileWeight[fileName] += projFileWeight[header]
                                dirtyBit[fileName][fileList[fileName].index(header)] = 1
                                if fileList[fileName][0] <= fileList[header][0]:
                                    fileList[fileName][0] = fileList[header][0] + 1
                                if maxLevel <= fileList[fileName][0]:
                                    maxLevel = fileList[fileName][0] + 1
        doneCalculate = True
        for fileName in dirtyBit:
            if 0 in dirtyBit[fileName]:
                doneCalculate = False
                break
        firstRun = False
    print("done.")
    time.sleep(0.01)
    
    ##### create matrix for drawing
    print("creating matrix for drawing...", end='')
    levelCount = [0] * maxLevel
    for sysHeader in sysHeaderWeight:
        levelCount[0] += 1
    for fileName in fileList:
        levelCount[fileList[fileName][0]] += 1
    getMatrixLen = lambda x: 2*x-1
    maxNumPerLevel = max(max(levelCount), len(sysHeaderWeight))
    graphMatrix = []
    for i in range(maxLevel):
        graphMatrix.append([''] * getMatrixLen(maxNumPerLevel))
    
    index = 0
    currentRow = 0
    offset = maxNumPerLevel - len(sysHeaderWeight)
    for sysHeader in sorted(sysHeaderWeight, key=sysHeaderWeight.get):
        column = index + offset
        if index % 2 == 1:
            column = -index - offset
        if graphMatrix[currentRow][column] != '':
            print("error: graphMatrix " + str(currentRow) + " " + str(column) + " not empty.")
            sys.exit(4)
        graphMatrix[currentRow][column] = sysHeader
        index += 2
    
    index = 0
    for fileName in sorted(fileList, key=fileList.get):
        if currentRow < (fileList[fileName][0]):
            index = 0
            currentRow = (fileList[fileName][0])
            offset = maxNumPerLevel - levelCount[fileList[fileName][0]]
        column = index + offset
        if index % 2 == 1:
            column = -index - offset
        if graphMatrix[currentRow][column] != '':
            print("error: graphMatrix " + str(currentRow) + " " + str(column) + " not empty.")
            sys.exit(4)
        graphMatrix[currentRow][column] = fileName
        index += 2
    print("done.")
    time.sleep(0.01)
    
    ##### create image
    print("creating image...", end='')
    imgName = "testimg/projectGraph.jpg"
    white = (255, 255, 255)
    black = (0, 0, 0)
    gray = (50, 50, 50)
    blue = (0, 0, 255)
    red = (255, 0, 0)
    lightBlue = (0, 255, 255)
    font = ImageFont.truetype("arial.ttf", 50)
    txtRect = {}
    spacingX = 100
    spacingY = 400
    spacingTxt = 2
    diameterOffset = 40
    widthPerLevel = [spacingX * 2] * maxLevel
    maxHeightPerLevel = [spacingY] * maxLevel
    getMaxLenString = lambda stringList: max([(len(x), x) for x in stringList])
    for sysHeader in sysHeaderWeight:
        nouse, txt = getMaxLenString(sysHeader.split(os.sep))
        w , h = font.getsize(txt)
        h = (h + spacingTxt) * len(sysHeader.split(os.sep)) - spacingTxt
        txtRect[sysHeader] = (w, h)
        diameter = max(w,h)
        widthPerLevel[0] += diameter + spacingX
        if maxHeightPerLevel[0] < diameter:
            maxHeightPerLevel[0] = diameter + spacingY
    
    graphHeight = maxHeightPerLevel[0]
    currentLevel = 0
    for fileName in sorted(fileList, key=fileList.get):
        nouse, txt = getMaxLenString(fileName.split(os.sep))
        w , h = font.getsize(txt)
        h = (h + spacingTxt) * len(fileName.split(os.sep)) - spacingTxt
        txtRect[fileName] = (w, h)
        diameter = max(w, h)
        if currentLevel < fileList[fileName][0]:
            graphHeight += maxHeightPerLevel[currentLevel] + spacingY
            currentLevel = fileList[fileName][0]
        elif maxHeightPerLevel[currentLevel] < diameter:
            maxHeightPerLevel[currentLevel] = diameter
        widthPerLevel[currentLevel] += diameter + spacingX
    
    graphWidth = widthPerLevel[levelCount.index(max(levelCount))] + spacingX * 2
    graphHeight += maxHeightPerLevel[currentLevel] + spacingY
    graphMidX = graphWidth / 2
    image = Image.new("RGB", (graphWidth, graphHeight), white)
    draw = ImageDraw.Draw(image)
    print("done.")
    time.sleep(0.01)
    
    ##### drawing relation graph
    print("drawing relation graph...", end='')
    graphPoints = {}
    brushY = spacingY * 1.5
    for rowIndex in range(len(graphMatrix)):
        stepRight = (graphWidth - widthPerLevel[rowIndex]) / levelCount[rowIndex] + spacingX
        brushX = stepRight / 2
        if rowIndex > 0:
            brushY += maxHeightPerLevel[rowIndex - 1] + spacingY
        for columnIndex in range(len(graphMatrix[rowIndex])):
            txt = graphMatrix[rowIndex][columnIndex].replace(os.sep, os.sep + "\n")
            if txt != '':
                txtW, txtH = txtRect[graphMatrix[rowIndex][columnIndex]]
                diameter = max(txtW, txtH) + diameterOffset
                circleBrushY = brushY + maxHeightPerLevel[rowIndex]/2 - diameter/2
                graphPoints[graphMatrix[rowIndex][columnIndex]] = (brushX, circleBrushY)
                draw.ellipse((brushX, circleBrushY, brushX + diameter, circleBrushY + diameter), gray, gray)
                txtX = brushX + diameter/2 - txtW/2
                txtY = circleBrushY + diameter/2 - txtH/2
                draw.text((txtX, txtY), txt, lightBlue, font, spacingTxt, align="center")
                
                if rowIndex > 0:
                    randColor = (random.randint(0,240), random.randint(0,240), random.randint(0,240))
                    for header in fileList[graphMatrix[rowIndex][columnIndex]][1:]:
                        arrowTail = (brushX + diameter/2, circleBrushY)
                        arrowHeadX = graphPoints[header][0] + max(txtRect[header])/2 + diameterOffset/2
                        arrowHeadY = graphPoints[header][1] + max(txtRect[header]) + diameterOffset
                        
                        arrowHead = (arrowHeadX, arrowHeadY)
                        draw.line((arrowTail, arrowHead), randColor, 2)
                brushX += stepRight + txtW
    print("done.")
    
    image.save(imgName)
    