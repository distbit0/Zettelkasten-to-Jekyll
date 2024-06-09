import json
import pysnooper
import utils


def findBlockQuoteConvos(md_string):
    blockquotes = []
    currentBlockquote = ""
    depths = []
    for line in md_string.split("\n"):
        if line.startswith(">"):
            currentBlockquote += line + "\n"
            depth = len([i for i in line.strip() if i == ">"])
            depths.append(depth)
        else:
            linesInBlockquote = len(currentBlockquote.strip().split("\n"))
            if linesInBlockquote > 5 and len(set(depths)) >= 1:
                blockquotes.append(currentBlockquote)
                currentBlockquote = ""
    return blockquotes


def invertBlockquoteConvos(md_string):
    blockquoteConvos = findBlockQuoteConvos(md_string)
    for blockquoteConvo in blockquoteConvos:
        md_string = md_string.replace(
            blockquoteConvo, invertBlockquoteConvo(blockquoteConvo)
        )

    return md_string


def invertBlockquoteConvo(string):
    convo = convertOriginalToConvo(string)
    string = convertConvoToInverted(convo)
    return string


def convertConvoToInverted(convo):
    def addMsgsToOutput(parent, msgs, depth, outputLines):
        for i in range(len(msgs)):
            message = msgs[i]
            if message["parent"] == parent:
                msgText = ">" * depth + message["message"].replace(
                    "\n", "\n" + ">" * depth
                )
                outputLines.append(msgText)
                outputLines = addMsgsToOutput(
                    message["message"], msgs[i + 1 :], depth + 1, outputLines
                )
        return outputLines

    outputLines = addMsgsToOutput("", convo, 1, [])
    outputText = "\n".join(outputLines) + "\n\n"

    return outputText


def removeBlockquotes(string):
    return string.replace(">", "").strip()


def convertOriginalToConvo(string):
    def getDepth(line):
        depth = 0
        for i in line.strip().split(" ")[0]:
            if i == ">":
                depth += 1
            else:
                break
        return depth

    convo = []
    message = []
    lines = string.split("\n")
    lastLineDepth = getDepth(lines[0])
    currentParentsAtDepths = {}
    for line in lines:
        lineDepth = getDepth(line)
        if lineDepth == lastLineDepth:
            message.append(line)
        else:
            message = removeBlockquotes("\n".join(message))
            for depth in list(currentParentsAtDepths):
                if depth <= lastLineDepth:
                    currentParentsAtDepths.pop(depth)

            lowestIndent = (
                min(currentParentsAtDepths.keys()) if currentParentsAtDepths else 0
            )
            parent = currentParentsAtDepths.get(lowestIndent, "")
            if "#draft" not in message and message:
                convo.append({"parent": parent, "message": message})
            currentParentsAtDepths[lastLineDepth] = message
            message = [line]

        lastLineDepth = lineDepth
    with open("convo.json", "w") as f:
        json.dump(convo, f, indent=4)
    return convo


if __name__ == "__main__":
    md_string = open(
        "/home/pimania/notes/Work/ProdTools/example blockquote convo.md"
    ).read()
    print(invertBlockquoteConvos(md_string))
