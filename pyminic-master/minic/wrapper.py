from pycparser import parse_file
from pycparser.c_ast import *
sys.path.extend(['.', '..'])

from minic.minic_ast import *
from c_ast_to_minic import * 


class LHSPrinter(NodeVisitor):
    def __init__(self):
        self.varLst = set()  # all variables seen in the code
        self.lhsVar = set()  # variables that have values assigned to it
      
    def visit_Decl(self, decl):
        if decl.init is not None:
            self.lhsVar.add(decl.name)
        
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
    f.write("int dummy(){\n" + newInput + "    return 0;\n}")
    f.close()
    
    return str(fileName)


# write path to file here
file = r'write path to file here'

dummyName = makeDummyCFile(file)

ast = parse_file(dummyName)
ast2 = transform(ast)
visitor = LHSPrinter()
visitor.visit(ast2)

print('Written Variables:')
print(visitor.get_LHSVar())
print('All Variables:')
print(visitor.get_AllVar())
