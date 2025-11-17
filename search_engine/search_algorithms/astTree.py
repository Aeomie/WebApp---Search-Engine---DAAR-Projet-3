from typing import List
from enum import Enum

class Operation(Enum):
    DOT = 1
    ETOILE = 2
    PLUS = 3
    ALTERN = 4
    PARENTHESE_L = 5
    PARENTHESE_R = 6
    CONCAT = 7
    PROTECTION = 8

class RegExTree:
    def __init__(self, root: Operation, subTrees: List['RegExTree'] = []):
        self.root = root
        self.subTrees = subTrees
        self.id = ""

    def rootToString(self) -> str:
        if self.root == Operation.CONCAT:
            return "."
        elif self.root == Operation.ETOILE:
            return "*"
        elif self.root == Operation.PLUS:
            return "+"
        elif self.root == Operation.ALTERN:
            return "|"
        elif self.root == Operation.DOT:
            return "."
        else:
            return str(self.root)

    def __str__(self):
        if self.subTrees == []:
            return self.rootToString()
        result = self.rootToString() + "(" + self.subTrees[0].__str__()
        for i in range(1, len(self.subTrees)):
            result += "," + self.subTrees[i].__str__()
        return result + ")"




class RegEx:
    def __init__(self, regex : str):
        self.regex = regex

    def chartoRoot(self, c : str):
        if c == ".":
            return Operation.DOT
        elif c == "*":
            return Operation.ETOILE
        elif c == "+":
            return Operation.PLUS
        elif c == "|":
            return Operation.ALTERN
        elif c == "(":
            return Operation.PARENTHESE_L
        elif c == ")":
            return Operation.PARENTHESE_R
        else:
            return c

    """
    contain functions
    """

    def containParenthese(self, trees: List[RegExTree]) -> bool:
        return any(t.root in (Operation.PARENTHESE_L, Operation.PARENTHESE_R) for t in trees)

    def containEtoile(self, trees: List[RegExTree]) -> bool:
        return any(t.root == Operation.ETOILE and not t.subTrees for t in trees)

    def containConcat(self, trees: List[RegExTree]) -> bool:
        firstFound = False
        for t in trees:
            if t.root != Operation.ALTERN and not firstFound:
                firstFound = True
                continue
            if firstFound:
                if t.root != Operation.ALTERN:
                    return True
                else:
                    firstFound = False
        return False

    def containAltern(self, trees: List[RegExTree]) -> bool:
        return any(t.root == Operation.ALTERN and not t.subTrees for t in trees)

    def containPlus(self, trees: List[RegExTree]) -> bool:
        return any(t.root == Operation.PLUS and not t.subTrees for t in trees)
    """
    process functions
    """
    def processParenthese(self, trees: List[RegExTree]) -> List[RegExTree]:
        result = []
        found = False
        for t in trees:
            if not found and t.root == Operation.PARENTHESE_R:
                done = False
                content = []
                while not done and result:
                    last = result.pop()
                    if last.root == Operation.PARENTHESE_L:
                        done = True
                    else:
                        content.insert(0, last)
                if not done:
                    raise Exception("Mismatched parentheses")
                found = True
                subTrees = [self.parseList(content)]
                result.append(RegExTree(Operation.PROTECTION, subTrees))
            else:
                result.append(t)
        if not found:
            raise Exception("Closing parenthesis not found")
        return result


    def processEtoile(self, trees: List[RegExTree]) -> List[RegExTree]:
        result = []
        found = False
        for t in trees:
            if not found and t.root == Operation.ETOILE and not t.subTrees:
                if not result:
                    raise Exception("Etoile without preceding element")
                found = True
                last = result.pop()
                result.append(RegExTree(Operation.ETOILE, [last]))
            else:
                result.append(t)
        return result

    def processPlus(self, trees: List[RegExTree]) -> List[RegExTree]:
        result = []
        found = False
        for t in trees:
            if not found and t.root == Operation.PLUS and not t.subTrees:
                if not result:
                    raise Exception("Plus without preceding element")
                found = True
                last = result.pop()
                result.append(RegExTree(Operation.PLUS, [last]))
            else:
                result.append(t)
        return result

    def processConcat(self, trees: List[RegExTree]) -> List[RegExTree]:
        result = []
        found = False
        firstFound = False
        for t in trees:
            if not found and not firstFound and t.root != Operation.ALTERN:
                firstFound = True
                result.append(t)
                continue
            if not found and firstFound and t.root == Operation.ALTERN:
                firstFound = False
                result.append(t)
                continue
            if not found and firstFound and t.root != Operation.ALTERN:
                found = True
                last = result.pop()
                result.append(RegExTree(Operation.CONCAT, [last, t]))
            else:
                result.append(t)
        return result

    def processAltern(self, trees: List[RegExTree]) -> List[RegExTree]:
        result = []
        found = False
        gauche = None
        done = False
        for t in trees:
            if not found and t.root == Operation.ALTERN and not t.subTrees:
                if not result:
                    raise Exception("Altern without left element")
                found = True
                gauche = result.pop()
                continue
            if found and not done:
                if gauche is None:
                    raise Exception("Altern without left element")
                done = True
                result.append(RegExTree(Operation.ALTERN, [gauche, t]))
            else:
                result.append(t)
        return result

    """
     END PROCESS FUNCTIONS
    """

    def removeProtection(self, tree: RegExTree) -> RegExTree:
        if tree.root == Operation.PROTECTION and len(tree.subTrees) != 1:
            raise Exception("Protection node must have exactly one subtree")
        if not tree.subTrees:
            return tree
        if tree.root == Operation.PROTECTION:
            return self.removeProtection(tree.subTrees[0])
        subTrees = []
        for t in tree.subTrees:  # fixed
            subTrees.append(self.removeProtection(t))
        return RegExTree(tree.root, subTrees)

    # Parse list of RegExTree nodes
    def parseList(self, trees: List[RegExTree]) -> RegExTree:
        while self.containParenthese(trees):
            trees = self.processParenthese(trees)
        while self.containEtoile(trees):
            trees = self.processEtoile(trees)
        while self.containPlus(trees):
            trees = self.processPlus(trees)
        while self.containConcat(trees):
            trees = self.processConcat(trees)
        while self.containAltern(trees):
            trees = self.processAltern(trees)
        if len(trees) > 1:
            raise Exception("Parsing did not produce a single tree")
        return self.removeProtection(trees[0])

    def parse(self) -> RegExTree:
        trees = [RegExTree(self.chartoRoot(c)) for c in self.regex]
        return self.parseList(trees)
