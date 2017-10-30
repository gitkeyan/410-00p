# example of how to run this script
# python wrapper.py /Users/abc/Desktop/project3inputs/p3_input3

from pycparser import parse_file
from pycparser.c_ast import *
sys.path.extend(['.', '..'])

from minic.minic_ast import *
from c_ast_to_minic import * 


class LHSPrinter(NodeVisitor):
    def __init__(self):
        self.varLst = set()  # all variables seen in the code
        self.lhsVar = set()  # variables that have values assigned to it
    
    def __str__(self):
        allVarStr = ""
        writtenVarLst = []
        for e in self.varLst:
            allVarStr += str(e)+ ", "
        for e in self.lhsVar:
            writtenVarLst.insert(0,e) 
        if (len(allVarStr) != 0):
            allVarStr = allVarStr[:-2]
        return "int* block_function(" + allVarStr +  ") " + "return" + str(writtenVarLst)

    def visit_Decl(self, decl):
        if decl.init is not None:
            self.lhsVar.add(decl.name)
            self.varLst.add(decl.name)
            self.visit(decl.init)
        else:
            if not isinstance(decl.type, FuncDecl):
                self.varLst.add(decl.name)

    def visit_Assignment(self, assignment):
        # get all left hand side variables as written variables
        
        if isinstance(assignment.lvalue, ID):
            varName = assignment.lvalue.name
            self.varLst.add(varName)
            self.lhsVar.add(varName) 
        
        # check if any right hand side variables have been written to
        rval = assignment.rvalue
        self.visit(rval)
        

    def visit_BinaryOp(self, binaryOp):
        self.visit(binaryOp.left)
        self.visit(binaryOp.right)
        
    def visit_ID(self, id):
        self.varLst.add(id.name)
        
    def visit_FuncCall(self, funcCall):
        for exprs, child in funcCall.args.children():
            self.visit(child)
                
        
    
    def get_AllVar(self):
        return self.varLst
        
        
    def get_LHSVar(self):
        return self.lhsVar
    
            
        

# wrap raw C code into a simple 
def makeDummyCFile(file):
    
    # read file
    f = open(file, 'r')
    input = f.read().split('\n')
    f.close()
    
    # add indentation
    newInput = "";
    for line in input:
        newInput += "    " + line + "\n"
    
    
    extensionInd = file.rfind('.')
    fileName = ""
    if extensionInd == -1:
        fileName = file + 'Dummy'
    else:
        fileName = file[:extensionInd] + 'Dummy' + file[extensionInd:]
    f = open(fileName, 'w')
    f.write("int* block_function(){\n" + newInput + "    return 0;\n}")
    f.close()
    
    return str(fileName)

inputFile = sys.argv[1]

#dummyName = inputFile
dummyName = makeDummyCFile(inputFile)

ast = parse_file(dummyName)
ast2 = transform(ast)
visitor = LHSPrinter()
visitor.visit(ast2)

print(visitor)

#print('Written Variables:')
#print(visitor.get_LHSVar())
#print('All Variables:')
#print(visitor.get_AllVar())
