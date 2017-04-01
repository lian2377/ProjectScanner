# -*- coding: utf-8 -*-

# c and c++ only

import os, sys

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
    for (dirpath, dirnames, filenames) in os.walk(rootDir):
        for f in filenames:
            suffix = f.split(".")[-1]
            if not isCaseSensitive:
                suffix = suffix.lower()
            for sfn in fileSuffixList:
                if suffix == sfn:
                    relativePath = os.path.relpath(dirpath, rootDir)
                    relativeFileName = os.path.join(relativePath, f)
                    fileList[relativeFileName] = [1,]
                    break

    ##### scan include lines, and give them the basic weight
    for fileName in fileList.keys():
        file = open(os.path.join(rootDir, fileName), "r", encoding="utf8")
        dirtyBit[fileName] = [1,]
        if fileName not in projFileWeight:
            projFileWeight[fileName] = 0
        for line in file:
            line = line.rstrip("\n")
            if "#include" in line:
                includeFileName = line.split(" ")[-1][1:-1]
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
    
    ##### calculate cumulated weight
    doneCalculate = False
    firstRun = True
    while(not doneCalculate):
        for fileName in fileList:
            listLength = len(fileList[fileName])
            if listLength < 1:
                print("error: fileList length should not be 0.")
                sys.exit(2)
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
        doneCalculate = True
        for fileName in dirtyBit:
            if 0 in dirtyBit[fileName]:
                doneCalculate = False
                break
        firstRun = False
    
    for fileName in sorted(fileList, key=fileList.get):
        print(fileName + " " + str(fileList[fileName]))
        
    for fileName in sorted(projFileWeight, key=projFileWeight.get):
        print(fileName + " " + str(projFileWeight[fileName]))
            
    for fileName in sysHeaderWeight:
        print(fileName + " " + str(sysHeaderWeight[fileName]))
    