# example of how to run this script
# python checkin_test.py /Users/abc/Desktop/project3inputs/checkin3_input1

from pycparser import parse_file
from pycparser.c_ast import *
sys.path.extend(['.', '..'])

from pyminicMaster.minic.minic_ast import *
from pyminicMaster.c_ast_to_minic import * 
import os


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
        
        #return "func block_function" + str(tuple(nonDeclaredVars)) + " return " + str(list(self.lhsVar))
        return 'func block_function' +'(' + ','.join(map(str, nonDeclaredVars)) + ')' + " return " + '[' + ','.join(map(str, self.lhsVar)) + ']'

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
            
        if isinstance(assignment.lvalue, ArrayRef):
            arrayRef = assignment.lvalue
            # set getArrayName to True to indicate that we want to add array into
            # the write set
            if isinstance(arrayRef.name, ID):
                self.visit_ID(arrayRef.name, True)
            elif isinstance(arrayRef.name, ArrayRef):
                self.visit_ArrayRef(arrayRef.name, True) 
            else:
                self.visit(arrayRef.name)
            self.visit(arrayRef.subscript)
            
        
        # check if any right hand side variables have been written to
        rval = assignment.rvalue
        self.visit(rval)
        
        

    def visit_BinaryOp(self, binaryOp):
        self.visit(binaryOp.left)
        self.visit(binaryOp.right)
        
    def visit_ID(self, id, getArrayName = False):
        if getArrayName:
            self.lhsVar.add(id.name)
        self.varLst.add(id.name)
        
    def visit_FuncCall(self, funcCall):
        if funcCall.args is not None:
            for exprs, child in funcCall.args.children():
                self.visit(child)
                
    def visit_ArrayRef(self, arrayRef, getArrayName = False):
        # call the right visit to help add array modified into the write set
        if isinstance(arrayRef.name, ID):
            self.visit_ID(arrayRef.name, getArrayName)
        elif isinstance(arrayRef.name, ArrayRef):
            self.visit_ArrayRef(arrayRef.name, getArrayName)
        else:
            self.visit(arrayRef.name)
        self.visit(arrayRef.subscript)
    
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
        
    fileName, file_extension = os.path.splitext(file)  
    fileName +=  'Dummy' + file_extension
        
    f = open(fileName, 'w')
    f.write("int* block_function(){\n" + newInput + "    return 0;\n}")
    f.close()
    
    return str(fileName)


inputFile = sys.argv[1]
dummyName = makeDummyCFile(inputFile)

ast = parse_file(dummyName)


ast1 = transform(ast)
visitor = LHSPrinter()
visitor.visit(ast1)

print(visitor)

# ------------------------ Checkin 3 starts here -------------------------------


import myfunctional_ast4 as my

# blockItemLst: list of statements to be read in the block
# returnLst:    list of availiable bindings

def minicToFunctional(ast, blockItemLst, returnLst):

    if isinstance(ast, FileAST):
        statement = None
        
        blockItems = ast.ext[0].body.block_items

        statementCount = len(blockItems)
        for i in range(statementCount):
            statement = minicToFunctional(blockItems[i], blockItems[i+1:], [])
            if statement is not None:
                break
        return statement
    
    
    # filters and convert declaration statement to let ... = ... in ...
    if isinstance(ast, Decl):   
        if ast.init is not None:
            init = minicToFunctional(ast.init, [], returnLst)
            if not blockItemLst:
                body = returnLst
            else:
                body = minicToFunctional(blockItemLst[0], blockItemLst[1:], returnLst + [ast.name])
            
            return my.Let(ast.name, init, body)
        else:
            if not blockItemLst:
                return returnLst
            else:
                return minicToFunctional(blockItemLst[0], blockItemLst[1:], returnLst)
            
    # convert assignment statement to let ... = ... in ...
    if isinstance(ast, Assignment):
        identifier = minicToFunctional(ast.lvalue, [], returnLst)
        #identifier = ast.lvalue.name  # get name of left hand side variable


        # for future reference 
        #if isinstance(ast.rvalue, Assignment):
        #    rv = minicToFunctional(ast.rvalue, [], [ast.rvalue.lvalue.name])
        #else:
        rv = minicToFunctional(ast.rvalue, [], returnLst)

        
        if not blockItemLst:
            body = returnLst
        else:
            body = minicToFunctional(blockItemLst[0], blockItemLst[1:], returnLst + [identifier])
        return my.Let(identifier, rv, body)
        
    if isinstance(ast, ID):
        return my.ID(ast.name)
        
    if isinstance(ast, Constant):
        return my.Constant(ast.value)

    if isinstance(ast, Return):
        return list(set(str(element) for element in returnLst))

    if isinstance(ast, BinaryOp):
        left = minicToFunctional(ast.left,[],returnLst)
        right = minicToFunctional(ast.right,[],returnLst)
        return my.BinaryOp(ast.op,left,right)
    
    if isinstance(ast, TernaryOp):
        iftrue = minicToFunctional(ast.iftrue,[],returnLst)
        iffalse = minicToFunctional(ast.iffalse,[],returnLst)
        cond = minicToFunctional(ast.cond,[],returnLst)
        return my.TernaryOp(cond, iftrue, iffalse)
    
    if isinstance(ast, FuncCall):
        args = []
        if ast.args is not None:
            for arg in ast.args.exprs:
                if isinstance(arg, Assignment):
                    args += [minicToFunctional(arg, [], [arg.lvalue.name])]
                else:
                    args += [minicToFunctional(arg, [], returnLst)]
        name = minicToFunctional(ast.name, blockItemLst, returnLst)
        return my.FuncCall(name, args)

    if isinstance(ast, ArrayRef):
        # for future reference      
        #if isinstance(ast.subscript, Assignment):
        #    subscript = minicToFunctional(ast.subscript, [], [ast.subscript.lvalue.name])
        #else:
        name = minicToFunctional(ast.name, [], returnLst)
        
        subscript = minicToFunctional(ast.subscript, [], returnLst)
        return my.ArrayRef(name, subscript);
    if isinstance(ast, UnaryOp):
        # for future reference 
        #if isinstance(ast.expr, Assignment):
        #    expr = minicToFunctional(ast.expr, [], [ast.expr.lvalue.name])
        #else:
        expr = minicToFunctional(ast.expr, [], returnLst)
        return my.UnaryOp(ast.op, expr)
    
    
    if isinstance(ast, ExprList):
        # convert something like a[1,2,b[1]] to functional programming
        exprs = [minicToFunctional(expr, [], returnLst) for expr in ast.exprs]
        return my.ExprList(exprs)
        
    # ---------------- Checkin 4 starts here -----------------------------------
    if isinstance(ast, If):
        # ast.iftrue is Compound
        
        
        # else:
        # ast.iffalse is Compound
        
        # else if:
        # ast.iffalse is a new If object
        
        # items = ast.ext[0].body.block_items
        #items[0].iftrue.block_items
        return None
    
    
    return None

ast2 = transform(ast)

functionalAST = minicToFunctional(ast2, [], [])
print(functionalAST)
