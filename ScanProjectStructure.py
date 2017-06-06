import os, json

def scan(projectPath, fileOutput = False, suffixList = None):
    rootDir = str(projectPath).replace("\\", os.sep)
    rootDir = rootDir.replace("/", os.sep)
    projectName = rootDir.rstrip(os.sep).split(os.sep)[-1]
    getSuffix = lambda s:s.split('.')[-1]
    fileList = []
    for (dirpath, dirnames, filenames) in os.walk(rootDir):
        for f in filenames:
            if suffixList is not None and getSuffix(f) not in suffixList:
                continue
            relativePath = os.path.relpath(dirpath, rootDir)
            relativeFileName = os.path.join(relativePath, f)
            if relativeFileName[0] == '.':
                relativeFileName = os.sep.join(relativeFileName.split(os.sep)[1:])
            fileList.append(relativeFileName)
    treeRoot = {"name": projectName, "children": []}
    for fileName in fileList:
        target = treeRoot
        targetPath = []
        newNodeList = fileName.split(os.sep)
        firstNode = newNodeList[0]
        checkList = []
        for node in treeRoot["children"]:
            checkList.append(node)
        findFirstPos = False
        while not findFirstPos:
            tmpList = []
            for node in checkList:
                if node["name"] == firstNode:
                    findFirstPos = True
                    target = node
                    targetPath.append(target["name"])
                    if "children" in node:
                        lastExistNode = node
                        for newNodeName in newNodeList[1:]:
                            findNextPos = False
                            nextNode = node
                            for node2 in lastExistNode["children"]:
                                if node2["name"] == newNodeName:
                                    findNextPos = True
                                    nextNode = node2
                                    break
                            if findNextPos:
                                lastExistNode = nextNode
                                target = lastExistNode
                                if "children" not in nextNode:
                                    break
                                targetPath.append(target["name"])
                            else:
                                break
                    break
                elif "children" in node:
                    for node2 in node["children"]:
                        tmpList.append(node2)
            if not findFirstPos:
                if len(tmpList) == 0:
                    target = treeRoot
                    findFirstPos = True
                checkList = tmpList

        if target != treeRoot:
            for node in targetPath:
                newNodeList.pop(0)

        i = 0
        for newNodeName in newNodeList:
            if i == len(newNodeList)-1:
                target["children"].append({"name": newNodeName})
            else:
                target["children"].append({"name": newNodeName, "children": []})
                target = target["children"][-1]
            i += 1

    unsortList = []
    treeRoot["children"] = sorted(treeRoot["children"], key=lambda x: x["name"])
    unsortList.append(treeRoot["children"])
    while True:
        if len(unsortList) == 0:
            break
        for item in unsortList[0]:
            if "children" in item:
                item["children"] = sorted(item["children"], key=lambda x: x["name"])
                unsortList.append(item["children"])
        unsortList.pop(0)

    if fileOutput:
        jsnFileName = projectName
        if suffixList is None:
            jsnFileName += ".all"
        jsnFile = open(jsnFileName + ".tree.json", "w", encoding="utf8")
        jsnFile.write(json.dumps(treeRoot, indent=4, separators=(',', ': ')))
        jsnFile.close()
    return treeRoot
