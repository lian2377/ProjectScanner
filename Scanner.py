# -*- coding: utf-8 -*-

# c and c++ only

import os, sys, time, json

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
        temp = str(arg).replace("\\", os.sep)
        temp = temp.replace("/", os.sep)
        dirList.append(arg)

##### scan given directories
for rootDir in dirList:
    fileList = {}
    sysHeaderWeight = {}
    projFileWeight = {}
    dirtyBit = {}
    projectName = rootDir.split(os.sep)[-1]
    if rootDir.split(os.sep)[-1] == "":
        projectName = rootDir.split(os.sep)[-2]

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
    
    ##### store into a json file
    outData = {}
    jsnFile = open(projectName + ".force.json", "w", encoding="utf8")
    
    outData["nodes"] = []
    outData["links"] = []
    for sysHeader in sysHeaderWeight.keys():
        outData["nodes"].append({"id":sysHeader, "group":0})
    for fileName in fileList.keys():
        outData["nodes"].append({"id":fileName, "group":fileList[fileName][0]})
        for includeFileName in fileList[fileName][1:]:
            value = 0
            if includeFileName in sysHeaderWeight:
                value = sysHeaderWeight[includeFileName]
            else:
                value = projFileWeight[includeFileName]
            outData["links"].append({"source":fileName, "target":includeFileName, "value":value})
    
    jsnFile.write(json.dumps(outData, indent=4, separators=(',', ': ')))
    jsnFile.close()
    
    outData.clear()
    outData = []
    jsnFile = open(projectName + ".bundling.json", "w", encoding="utf8")
    
    for sysHeader in sysHeaderWeight.keys():
        outData.append({"name":sysHeader, "size":sysHeaderWeight[sysHeader], "imports":[]})
    for fileName in fileList.keys():
        outData.append({"name":fileName, "size":projFileWeight[fileName], "imports":fileList[fileName][1:]})
    
    jsnFile.write(json.dumps(outData, indent=4, separators=(',', ': ')))
    jsnFile.close()
    