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
        self.declaredVar = set() # all declared variables
    

    def __str__(self):
        allVarTuple = ()
        writtenVarLst = []

        # use difference between all variables list and declared variable list 
        # to find all non-declared variables
        nonDeclaredVars = self.varLst.difference(self.declaredVar)
        for e in nonDeclaredVars:
            allVarTuple += (e,)

        for e in self.lhsVar:
            writtenVarLst.insert(0,e) 
        
        return "int* block_function" + str(allVarTuple).replace("'","") + " return " + str(writtenVarLst).replace("'","")

    def visit_Decl(self, decl):
        if decl.init is not None:
            self.lhsVar.add(decl.name)
            self.varLst.add(decl.name)
            self.declaredVar.add(decl.name)
            self.visit(decl.init)
        else:
            if not isinstance(decl.type, FuncDecl):
                self.varLst.add(decl.name)
                self.declaredVar.add(decl.name)

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
        
        
    def get_DeclaredVar(self):
        return self.declaredVar
    
            
        

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

inputFile =sys.argv[1]
dummyName = makeDummyCFile(inputFile)

ast = parse_file(dummyName)


ast1 = transform(ast)
visitor = LHSPrinter()
visitor.visit(ast1)

print(visitor)
