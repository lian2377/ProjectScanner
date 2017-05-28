# -*- coding: utf-8 -*-

# c and c++ only

import os, sys, time, json, traceback, argparse

fileSuffixList = ["c", "cpp", "cc", "h", "hpp"]

parser = argparse.ArgumentParser(description="Get include relationes in the given directories.")
parserGroup = parser.add_mutually_exclusive_group()
parserGroup.add_argument("-v", "--verbose", action="store_true", help="show verbose output")
parserGroup.add_argument("-q", "--quiet", action="store_true", help="no output message")
parser.add_argument("-s", "--sensitive", action="store_true", help="case sensitive file name")
parser.add_argument("projectpath", nargs="+", help="project root path")
args = parser.parse_args()

isCaseSensitive = args.sensitive
isQuietScan = args.quiet
isVerbose = args.verbose

if not isQuietScan:
    if isCaseSensitive:
        print("case sensitive scan enabled.")
    if isVerbose:
        print("show verbose message.")

dirList = []
for arg in args.projectpath:
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
    if not isQuietScan:
        print("scanning files...", end='', flush=True)
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
    if not isQuietScan:
        print(str(len(fileList)) + " done.")
    time.sleep(0.01)

    ##### scan include lines, and give them the basic weight
    if not isQuietScan:
        print("scanning includes...", end='', flush=True)
    for fileName in fileList.keys():
        if isVerbose and not isQuietScan:
            print(os.path.join(rootDir, fileName))
        file = open(os.path.join(rootDir, fileName), "r")
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
                if includeFileName not in fileList[fileName]:
                    fileList[fileName].append(includeFileName)
                    dirtyBit[fileName].append(0)
        file.close()
    if not isQuietScan:
        print("done.")
    time.sleep(0.01)
    
    try:
        ##### calculate cumulated weight
        if not isQuietScan:
            print("calculating cumulated weight...     ", end='', flush=True)
        doneCalculate = False
        firstRun = True
        maxLevel = 0
        while(not doneCalculate):
            nProgressedFile = 0
            for fileName in fileList.keys():
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
                if 0 not in dirtyBit[fileName]:
                    nProgressedFile += 1

            progress = 100.0 * nProgressedFile / len(fileList)
            if not isQuietScan:
                print("\b\b\b\b\b", end='', flush=True)
                if progress < 10:
                    print("{:.2f}%".format(progress), end='', flush=True)
                elif progress < 100:
                    print("{:.1f}%".format(progress), end='', flush=True)
                else:
                    print("{:.0f}%".format(progress), end='', flush=True)

            doneCalculate = True
            for fileName in dirtyBit:
                if 0 in dirtyBit[fileName]:
                    doneCalculate = False
                    break
            firstRun = False
        if not isQuietScan:
            print("done.")
        time.sleep(0.01)
    except:
        print()
        for fileName in fileList:
            print(fileName + " ", end='')
            print(fileList[fileName])
            print(fileName + " ", end='')
            print(dirtyBit[fileName])
        traceback.print_exc()
        sys.exit(1)
    
    ##### store into a json file
    if not isQuietScan:
        print("saving json files...", end='', flush=True)
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
    if not isQuietScan:
        print("done.")
    print("Scan finished.")
