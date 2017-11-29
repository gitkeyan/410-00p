import sys, os
path = r'C:\Users\Meng\Desktop\Checkin6\410-00p'
os.chdir(path)


# example of how to run this script
# python checkin_test.py /Users/abc/Desktop/project3inputs/checkin3_input1

from pycparser import parse_file
from pycparser.c_ast import *
sys.path.extend(['.', '..'])

from pyminicMaster.minic.minic_ast import *
from pyminicMaster.c_ast_to_minic import * 
import os

import myfunctional_ast6 as my

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



# ------------------------ Checkin 3 starts here -------------------------------


# blockItemLst: list of statements to be read in the block
# returnLst:    list of availiable bindings

def minicToFunctional(ast, blockItemLst, returnLst, level = 0):

    if isinstance(ast, FileAST):
        statement = None
        blockItems = ast.ext[0].body.block_items

        statementCount = len(blockItems)
        for i in range(statementCount):
            statement = minicToFunctional(blockItems[i], blockItems[i+1:], [], level)
            if statement is not None:
                break
                  
        visitorF = LHSPrinter()
        visitorF.visit(ast)
        nonDeclaredVars = visitorF.varLst.difference(visitorF.declaredVar)
        lhsVar = [my.ID(var) for var in visitorF.get_LHSVar()]
        
        return my.FuncDef(nonDeclaredVars, statement, lhsVar)
    
    
    # filters and convert declaration statement to let ... = ... in ...
    if isinstance(ast, Decl):   
        if ast.init is not None:
            init = minicToFunctional(ast.init, [], returnLst, level + 1)
            if not blockItemLst:
                body = returnLst
            else:
                body = minicToFunctional(blockItemLst[0], blockItemLst[1:], returnLst + [ast.name], level + 1)
            
            return my.Let(ast.name, init, body, level)
        else:
            if not blockItemLst:
                return returnLst
            else:
                return minicToFunctional(blockItemLst[0], blockItemLst[1:], returnLst, level)
            
    # convert assignment statement to let ... = ... in ...
    if isinstance(ast, Assignment):
        identifier = minicToFunctional(ast.lvalue, [], returnLst)

        rv = minicToFunctional(ast.rvalue, [], returnLst, level + 1)

        if not blockItemLst:
            body = returnLst
        else:
            body = minicToFunctional(blockItemLst[0], blockItemLst[1:], returnLst + [identifier], level + 1)
        return my.Let(identifier, rv, body, level)
        
    if isinstance(ast, ID):
        return my.ID(ast.name, level)
        
    if isinstance(ast, Constant):
        return my.Constant(ast.value, level)

    if isinstance(ast, Return):
        return list(set(str(element) for element in returnLst))

    if isinstance(ast, BinaryOp):
        left = minicToFunctional(ast.left,[],returnLst)
        right = minicToFunctional(ast.right,[],returnLst)
        return my.BinaryOp(ast.op,left,right, level)
    
    if isinstance(ast, TernaryOp):
        iftrue = minicToFunctional(ast.iftrue,[],returnLst, level + 1)
        iffalse = minicToFunctional(ast.iffalse,[],returnLst, level + 1)
        cond = minicToFunctional(ast.cond,[],returnLst)
        return my.TernaryOp(cond, iftrue, iffalse, level)
    
    if isinstance(ast, FuncCall):
        args = []
        if ast.args is not None:
            for arg in ast.args.exprs:
                if isinstance(arg, Assignment):
                    args += [minicToFunctional(arg, [], [arg.lvalue.name])]
                else:
                    args += [minicToFunctional(arg, [], returnLst)]
        name = minicToFunctional(ast.name, blockItemLst, returnLst)
        return my.FuncCall(name, args, level)

    if isinstance(ast, ArrayRef):
        # for future reference      
        #if isinstance(ast.subscript, Assignment):
        #    subscript = minicToFunctional(ast.subscript, [], [ast.subscript.lvalue.name])
        #else:
        name = minicToFunctional(ast.name, [], returnLst)
        
        subscript = minicToFunctional(ast.subscript, [], returnLst)
        return my.ArrayRef(name, subscript, level);
        
    if isinstance(ast, UnaryOp):
        # for future reference 
        #if isinstance(ast.expr, Assignment):
        #    expr = minicToFunctional(ast.expr, [], [ast.expr.lvalue.name])
        #else:
        expr = minicToFunctional(ast.expr, [], returnLst)
        return my.UnaryOp(ast.op, expr, level)
    
    
    if isinstance(ast, ExprList):
        # convert something like a[1,2,b[1]] to functional programming
        exprs = [minicToFunctional(expr, [], returnLst) for expr in ast.exprs]
        return my.ExprList(exprs)
        
    # ---------------- Checkin 4 starts here -----------------------------------
    if isinstance(ast, If):
        # get all the written variables
        visitor1 = LHSPrinter()
        visitor1.visit(ast.iftrue)
        
        # determine all written variables in if and else
        if ast.iffalse is None:
            allLhs = list(visitor1.get_LHSVar())
        else:
            visitor2 = LHSPrinter()
            visitor2.visit(ast.iffalse)
            
            # add the variables together
            allLhs = list( visitor1.get_LHSVar().union(visitor2.get_LHSVar()) )
        
        iftrue = minicToFunctional(ast.iftrue,[],allLhs, level + 2)  # returnLst) 
        
        if ast.iffalse is None:
            iffalse = my.ReturnTuples(tuple(allLhs), level + 2)    # make the else statement when it doesn't exist
        else:
            # convert else statement to Let
            iffalse = minicToFunctional(ast.iffalse,[],allLhs, level + 2)  # returnLst)
        cond = minicToFunctional(ast.cond,[],[])   # returnLst)
        
        ternary = my.TernaryOp(cond, iftrue, iffalse, level + 1)
        

        if not blockItemLst:
            body = my.ReturnTuples(returnLst, level + 1) #returnLst
        else:
            body = minicToFunctional(blockItemLst[0], blockItemLst[1:], returnLst + allLhs, level + 1)
        
        letStatement = my.Let(tuple(allLhs), ternary, body, level)
        
        return letStatement
        #return my.TernaryOp(cond, ast.iftrue.block_items[0].lvalue.name, iffalse)
    if isinstance(ast, Block):
        statement = None
        blockItems = ast.block_items + [Return([])]

        statementCount = len(blockItems)
        for i in range(statementCount):
            statement = minicToFunctional(blockItems[i], blockItems[i+1:], returnLst, level)
            if statement is not None:
                break
        return statement
    
    
    # ------------------------ Checkin 6 starts here ---------------------------
    if isinstance(ast, For):
        block_items = [ast.stmt]
        
            
        if ast.cond is not None:
            pass
            #statement = my.TernaryOp(ast.cond, ast.stmt, returnLst, level)
            
        if ast.next is not None:
            print(ast.next)
            block_items[0].block_items = block_items[0].block_items + [ast.next] 
            

        if ast.init is not None:
            statement = minicToFunctional(ast.init, block_items, returnLst, level)

        #statement = minicToFunctional(ast.stmt, [], returnLst, level + 1)

        return statement
        
    if isinstance(ast, While):

        visitorF = LHSPrinter()
        visitorF.visit(ast)
        nonDeclaredVars = visitorF.varLst.difference(visitorF.declaredVar)
        lhsVar = tuple([var for var in visitorF.get_LHSVar()])
        
        assignedStatements = minicToFunctional(ast.stmt, [], [], level + 2)
        recursiveCall = my.LetrecCall('loop0', lhsVar, level + 2)        
        recursiveLet = my.Let(lhsVar, assignedStatements, recursiveCall, level + 1)        


        newReturnLst = returnLst + list(lhsVar)
        body = minicToFunctional(blockItemLst[0], blockItemLst[1:], newReturnLst, level + 1)
        statement = my.Letrec('loop0', lhsVar, recursiveLet, body, level)
        return statement
    
    if isinstance(ast, DoWhile):
        #print(ast.__slots__)
        # convert to statments + while with statements
        
        minicWhile = While(ast.cond, ast.stmt)
        newBlockItemLst = ast.stmt.block_items + [minicWhile] + blockItemLst
        return minicToFunctional(newBlockItemLst[0], newBlockItemLst[1:], returnLst, level)
        
        #newBlockItems = blockItemLst[1:]
    
    return None


inputFile = r'./project3inputs/checkin6_input1' #sys.argv[1]
dummyName = makeDummyCFile(inputFile)

ast = parse_file(dummyName)


ast1 = transform(ast)

visitor = LHSPrinter()
visitor.visit(ast1)

print("Input:\n")
f = open(dummyName, 'r')
input = f.read()
print(input)
f.close()


print("\n\n----- Output: -----\n")

ast2 = transform(ast)

functionalAST = minicToFunctional(ast2, [], [], 1)
print(functionalAST)
