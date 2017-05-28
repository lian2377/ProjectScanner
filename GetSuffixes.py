# -*- coding: utf-8 -*-
"""
Created on Sun Mar 26 15:34:29 2017

@author: Lian
"""

import os, sys, argparse, chardet

fileSuffixList = ["c", "cpp", "cc", "h", "hpp"]

parser = argparse.ArgumentParser(description="Get include relationes in the given directories.")
parser.add_argument("-q", "--quiet", action="store_true", help="no output message")
parser.add_argument("-s", "--sensitive", action="store_true", help="case sensitive file name")
parser.add_argument("projectpath", nargs="+", help="project root path")
args = parser.parse_args()

isCaseSensitive = args.sensitive
isQuietScan = args.quiet

if not isQuietScan:
    if isCaseSensitive:
        print("case sensitive scan enabled.")

dirList = []
for arg in args.projectpath:
    temp = str(arg).replace("\\", os.sep)
    temp = temp.replace("/", os.sep)
    dirList.append(arg)

result = {}
for rootDir in dirList:
    for (dirpath, dirnames, filenames) in os.walk(rootDir):
        for f in filenames:
            if isCaseSensitive:
                fsplit = f.split(".")
            else:
                fsplit = f.lower().split(".")
            if len(fsplit) == 1:
                continue
            suf = fsplit[-1]
            if not isQuietScan:
                print(os.path.join(dirpath, f))
                print(suf)
                if suf in fileSuffixList:
                    print(chardet.detect(open(os.path.join(dirpath, f), "rb").read()))
            if suf in result:
                result[suf] += 1
            else:
                result[suf] = 1
print("get suffixes:")
keylist = list(result.keys())
keylist.sort()
for key in keylist:
    print(key + u" " + str(result[key]))