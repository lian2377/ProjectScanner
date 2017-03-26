# -*- coding: utf-8 -*-
"""
Created on Sun Mar 26 15:34:29 2017

@author: Lian
"""

import os, sys

print(sys.argv)
result = {}

isCaseSensitive = False

if len(sys.argv) > 1:
    argList = sys.argv[1:]
    argList.sort()
    if argList[len(argList)-1][0] == "-":
        argList.append(".")
else:
    argList = ["."]

for arg in argList:
    if arg[0] == "-":
        flags = arg[1:]
        for flag in flags:
            if flag == "s":
                isCaseSensitive = True
            elif flag == "h":
                print("------------------------------")
                print("Scans all suffixes in the given directories.\n")
                print("Usage:")
                print("    Getsuffixes.py [option]... [dir]...")
                print("Default:")
                print("    Getsuffixes.py .")
                print("Flags:")
                print("    -s: case sensitive")
                print("    -h: display this message")
                sys.exit(0)
            else:
                print("Unknown flag error")
                sys.exit(1)
    else:
        for (dirpath, dirnames, filenames) in os.walk(arg):
            for f in filenames:
                if isCaseSensitive:
                    fsplit = f.split(".")
                else:
                    fsplit = f.lower().split(".")
                if len(fsplit) == 1:
                    continue
                print(os.path.join(dirpath, f).encode("utf8").decode("utf8"))
                suf = fsplit[len(fsplit)-1]
                print(suf)
                if suf in result:
                    result[suf] += 1
                else:
                    result[suf] = 1
print("get suffixes:")
keylist = list(result.keys())
keylist.sort()
for key in keylist:
    print(key + u" " + str(result[key]))