# -*- coding: utf-8 -*-

# c and c++ only

import os, sys, time, json, traceback, argparse
import ScanProjectStructure

fileSuffixList = ["c", "cpp", "cc", "h", "hpp"]

parser = argparse.ArgumentParser(description="Get include relationes in the given directories.")
parserGroup = parser.add_mutually_exclusive_group()
parserGroup.add_argument("-v", "--verbose", action="store_true", help="show verbose output")
parserGroup.add_argument("-q", "--quiet", action="store_true", help="no output message")
parserGroup.add_argument("--debug", action="store_true", help="show debug message")
parserGroup.add_argument("-st", "--scantree", action="store_true", help="scan and output project tree structure")
parserGroup.add_argument("-R", "--recursive", action="store_true", help="scan subdirectories recursively")
parser.add_argument("projectpath", nargs="+", help="project root path")
args = parser.parse_args()

isQuietScan = args.quiet
isVerbose = args.verbose
isDebugging = args.debug
isScanTree = args.scantree
isRecursive = args.recursive

if not isQuietScan:
    if isVerbose:
        print("show verbose message.")
    if isDebugging:
        print("show debug message")

dirList = []
for arg in args.projectpath:
    temp = str(arg).replace("\\", os.sep)
    temp = temp.replace("/", os.sep)
    dirList.append(temp)
    if isRecursive:
        for (dirpath, dirnames, filenames) in os.walk(arg):
            for d in dirnames:
                dirList.append(os.path.join(dirpath, d))

##### scan given directories
for rootDir in dirList:
    fileList = {}
    sysHeaderWeight = {}
    projFileWeight = {}
    dirtyBit = {}
    projectName = rootDir.strip('.').strip(os.sep).replace(os.sep, '.')

    ##### scan files
    if not isQuietScan:
        print("root directory: " + rootDir)
        ending = ""
        if isDebugging or isVerbose:
            ending = "\n"
        print("scanning files...", end='', flush=True)
    for (dirpath, dirnames, filenames) in os.walk(rootDir):
        for f in filenames:
            suffix = f.split(".")[-1]
            suffix = suffix.lower()
            if suffix in fileSuffixList:
                relativePath = os.path.relpath(dirpath, rootDir)
                relativeFileName = os.path.join(relativePath, f)
                if relativeFileName[0] == '.':
                    relativeFileName = os.sep.join(relativeFileName.split(os.sep)[1:])
                fileList[relativeFileName] = [1,]
                if not isQuietScan:
                    if isDebugging:
                        print("detect file {0}".format(relativeFileName))

    if len(fileList) == 0:
        print("error: no supported file.")
        if not isRecursive:
            sys.exit(2)
        else:
            continue
    if not isQuietScan:
        if isVerbose:
            print("fileList: {0}".format(fileList))
        print(str(len(fileList)) + " done.")
    time.sleep(0.01)

    ##### scan include lines, and give them the basic weight
    if not isQuietScan:
        print("scanning includes...", end='', flush=True)
    for fileName in fileList.keys():
        if isVerbose and not isQuietScan:
            print(os.path.join(rootDir, fileName))
        file = open(os.path.join(rootDir, fileName), "rb")
        dirtyBit[fileName] = [1,]
        if fileName not in projFileWeight:
            projFileWeight[fileName] = 0
        findBlockComment = False
        for line in file:
            line = line.rstrip(b"\n\r")
            try:
                line = line.decode("utf-8")
            except:
                import chardet
                detect = chardet.detect(line)
                line = line.decode(detect["encoding"])
            if line.find("*/") > -1:
                line = line[line.find("*/")+2:]
                findBlockComment = False
            if findBlockComment:
                continue
            if line.find("//") > -1:
                line = line[:line.find("//")]
            if line.find("/*") > -1:
                line = line[:line.find("/*")]
                findBlockComment = True
            if "#include" in line:
                includeFileName = line.split("#include")[1].strip(' ').rstrip(' ')
                if '\"' in includeFileName:
                    includeFileName = includeFileName.split('\"')[1]
                elif '<' in includeFileName:
                    includeFileName = includeFileName.split('>')[0][1:]
                else:
                    print(includeFileName)
                    sys.exit(4)
                includeFileName = includeFileName.replace("\\", os.sep)
                includeFileName = includeFileName.replace("/", os.sep)
                if includeFileName[0] == '.':
                    if includeFileName[1] == '.':
                        includeFileName = os.sep.join(fileName.split(os.sep)[:-2] + includeFileName.split(os.sep)[1:])
                    else:
                        includeFileName = os.sep.join(fileName.split(os.sep)[:-1] + includeFileName.split(os.sep)[1:])
                    
                if includeFileName in fileList:
                    if includeFileName in projFileWeight:
                        projFileWeight[includeFileName] += 1
                    else:
                        projFileWeight[includeFileName] = 1
                else:
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
        circularInclude = []
        while(not doneCalculate):
            nProgressedFile = 0
            for fileName in fileList.keys():
                listLength = len(fileList[fileName])
                if listLength < 1:
                    print("error: fileList length should not be 0.")
                    sys.exit(3)
                elif listLength > 1 and (0 in dirtyBit[fileName]):
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
                                    if header in circularInclude:
                                        headerIndex = circularInclude.index(header)
                                        if headerIndex + 1 == len(circularInclude):
                                            circularInclude.clear()
                                        else:
                                            circularInclude = circularInclude[headerIndex+1:]
                if 0 not in dirtyBit[fileName]:
                    nProgressedFile += 1

            if len(circularInclude) > 0 and 0 in dirtyBit[circularInclude[-1]]:
                headerIndex = dirtyBit[circularInclude[-1]].index(0)
                header = fileList[circularInclude[-1]][headerIndex]
                if 0 in dirtyBit[header]:
                    if header in circularInclude:
                        minWeight = projFileWeight[header]
                        lightestHeader = header
                        for circularHeader in circularInclude:
                            if minWeight > projFileWeight[circularHeader]:
                                minWeight = projFileWeight[circularHeader]
                                lightestHeader = circularHeader
                        for index in range(len(dirtyBit[lightestHeader])):
                            dirtyBit[lightestHeader][index] = 1

                        index = circularInclude.index(lightestHeader)
                        if index + 1 == len(circularInclude):
                            circularInclude.clear()
                        else:
                            circularInclude = circularInclude[index+1:]
                    else:
                        circularInclude.append(header)
            else:
                circularInclude = circularInclude[:-1]

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
                    if len(circularInclude) == 0:
                        circularInclude.append(fileName)
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
            if fileName in sysHeaderWeight:
                print(fileName + " ", end='')
                print(sysHeaderWeight[fileName])
            else:
                print(fileName + " ", end='')
                print(projFileWeight[fileName])
        traceback.print_exc()
        sys.exit(1)
    
    ##### store into a json file (force-directed)
    if not isQuietScan:
        print("saving force-directed graph json files...", end='', flush=True)
    outData = {}
    jsnFile = open(projectName + ".force-directed.json", "w", encoding="utf8")
    
    outData["nodes"] = []
    outData["links"] = []
    for sysHeader in sorted(sysHeaderWeight.keys()):
        outData["nodes"].append({"id":sysHeader, "group":0})
    for fileName in sorted(fileList.keys()):
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

    if not isQuietScan:
        print("done.")
        print("saving bundling graph json files...", end='', flush=True)
    
    ##### store into a json file (bundling)
    outData.clear()
    outData = []
    jsnFile = open(projectName + ".bundling.json", "w", encoding="utf8")
    
    for sysHeader in sorted(sysHeaderWeight.keys()):
        outData.append({"name":sysHeader, "size":sysHeaderWeight[sysHeader], "imports":[]})
    for fileName in sorted(fileList.keys()):
        outData.append({"name":fileName, "size":projFileWeight[fileName], "imports":fileList[fileName][1:]})
    
    jsnFile.write(json.dumps(outData, indent=4, separators=(',', ': ')))
    jsnFile.close()

    if not isQuietScan:
        print("done.")
        print("saving tree graph json files...", end='', flush=True)

    ##### store into a json file (tree)
    if isScanTree:
        ScanProjectStructure.scan(rootDir, True)
        ScanProjectStructure.scan(rootDir, True, fileSuffixList)

    if not isQuietScan:
        print("done.")
    print("Scan finished.")
