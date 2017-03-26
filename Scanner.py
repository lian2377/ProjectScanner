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
    dirList = ["."]

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
                print("    -s: case sensitive")
                print("    -h: display this message")
                sys.exit(0)
            else:
                print("Unknown flag error")
                sys.exit(1)
    else:
        dirList.append(arg)

fileList = {}
for rootDir in dirList:
    for (dirpath, dirnames, filenames) in os.walk(rootDir):
        for f in filenames:
            suffix = f.split(".")[-1]
            if not isCaseSensitive:
                suffix = suffix.lower()
            for sfn in fileSuffixList:
                if suffix == sfn:
                    relativePath = os.path.relpath(dirpath, rootDir)
                    str1 = os.path.join(relativePath, f)
                    fileList[str1] = []
                    break

for fileName in fileList:
    file = open(os.path.join(rootDir, fileName), "r", encoding="utf8")
    for line in file:
        line = line.rstrip("\n")
        if "#include" in line:
            fileList[fileName].append(line.split(" ")[-1][1:-1])
    file.close()

for fileName in fileList:
    print(fileName + " " + str(fileList[fileName]))
    