'''
This program reads a C code block (populated with assignment statements) stored in the input file provided
and wraps the C code block inside a C function. 
The dummy file that stores this C function is then generated under the same path as the input file.
For this project we uses pycpaser, and minic to help determine the corresponding AST for the c code block.
With AST of the C code, we convert the C code's AST into its functional programming equivalent AST and output
the functional programming language version of the C code.

This code first print the C function
Then print the functional programming equivalent of the C code
Then print the simplified functional programming equivalent of the C code 
'''
# example of how to run this script
# python project3.py /Users/abc/Desktop/project3inputs/checkin3_input1

from pycparser import parse_file
from pycparser.c_ast import *
sys.path.extend(['.', '..'])

from pyminicMaster.minic.minic_ast import *
from pyminicMaster.c_ast_to_minic import * 
import os

import myfunctional_ast as my


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
        # add variable to the list of all variables
        if getArrayName:  
            # add variable to the set of modified variables
            # if other statements says it is on the left hand side
            self.lhsVar.add(id.name)
        self.varLst.add(id.name)
        
    def visit_FuncCall(self, funcCall):
        # visit each of the argument in the function
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
                
# wrap raw C code into a simple c function
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
        lhsVar = [var for var in visitorF.get_LHSVar()]
        
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
            var = identifier
            while isinstance(var, my.ArrayRef):
                var = var.name
                
            body = minicToFunctional(blockItemLst[0], blockItemLst[1:], returnLst + [var], level + 1)
        return my.Let(identifier, rv, body, level)
        
    if isinstance(ast, ID):
        # structure used to store name of variable
        return my.ID(ast.name, level)
        
    if isinstance(ast, Constant):
        # structure used to store int, string, boolean value of a variable
        return my.Constant(ast.value, level)

    if isinstance(ast, Return):
        # C code's block end here.
        # return the list of modified variables in the code block
        return list(set(str(element) for element in returnLst))

    if isinstance(ast, BinaryOp):
        # convert a binary expression to functional programming
        left = minicToFunctional(ast.left,[],returnLst)
        right = minicToFunctional(ast.right,[],returnLst)
        return my.BinaryOp(ast.op,left,right, level)
    
    if isinstance(ast, TernaryOp):
        # compute the functional programming equivalent for the expression on the
        # left and the expression on the right, and the expression for the condition for ternary expressions and if statements
        
        iftrue = minicToFunctional(ast.iftrue,[],returnLst, level + 1)
        iffalse = minicToFunctional(ast.iffalse,[],returnLst, level + 1)
        cond = minicToFunctional(ast.cond,[],returnLst)
        return my.TernaryOp(cond, iftrue, iffalse, level, True)
    
    if isinstance(ast, FuncCall):
        # get the functional programming equivalent expression for each argument
        # and build the function call expression in terms of myfunctional_ast
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
        # convert the variable and its subscripts to functional programming format
        # so they can be printed
        name = minicToFunctional(ast.name, [], returnLst)
        
        subscript = minicToFunctional(ast.subscript, [], returnLst)
        return my.ArrayRef(name, subscript, level);
        
    if isinstance(ast, UnaryOp):
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
        
        iftrue = minicToFunctional(ast.iftrue,[],allLhs, level + 2) 
        
        if ast.iffalse is None:
            iffalse = my.ReturnTuples(tuple(allLhs), level + 2)    # make the else statement when it doesn't exist
        else:
            # convert else statement to Let
            iffalse = minicToFunctional(ast.iffalse,[],allLhs, level + 2)  
            
        cond = minicToFunctional(ast.cond,[],[])
        
        ternary = my.TernaryOp(cond, iftrue, iffalse, level + 1)
        

        if not blockItemLst:
            body = my.ReturnTuples(returnLst, level + 1)
        else:
            body = minicToFunctional(blockItemLst[0], blockItemLst[1:], returnLst + allLhs, level + 1)
        
        letStatement = my.Let(tuple(allLhs), ternary, body, level)
        
        return letStatement

    if isinstance(ast, Block):
        # handles compound statements for iftrue and iffalse
        # iterate through each statement until the first none empty line come up
        # Convert the build the let bindings for that statement and the statements
        # that follows
        
        statement = None
        blockItems = ast.block_items + [Return([])]

        statementCount = len(blockItems)
        for i in range(statementCount):
            statement = minicToFunctional(blockItems[i], blockItems[i+1:], returnLst, level)
            if statement is not None:
                break
        return statement
    
    
    # ------------------------ Checkin 6 starts here ---------------------------
    if isinstance(ast, my.LetrecCall):
        return ast
            
    if isinstance(ast, While):
        # Find all the modified variables in the loop using the visitor 
        # implmented above
        visitorF = LHSPrinter()
        visitorF.visit(ast)
        nonDeclaredVars = visitorF.varLst.difference(visitorF.declaredVar)
        lhsVar = tuple([var for var in visitorF.get_LHSVar()])
        
        # make the recusive call object for let rec and add it to the end of 
        # the list of statements to be executed within the loop 
        recursiveCall = my.LetrecCall('loop', lhsVar, level + 3)     
        newStmt = Block(ast.stmt.block_items + [recursiveCall])
        loopStatements = minicToFunctional(newStmt, [], [], level + 3)
        
        # make the ternary operation that determines if the statements in the
        # loop should be executed
        cond = minicToFunctional(ast.cond, [], [])
        ifStatement = my.TernaryOp(cond, loopStatements, lhsVar, level + 2)
        
        # recursive let
        recursiveLet = my.Letrec('loop', lhsVar, ifStatement, recursiveCall, level + 1)
        
        # add the variables written within the loop into the return list and
        # make the let binding for the variables returned from let rec
        newReturnLst = returnLst + list(lhsVar) 
        body = minicToFunctional(blockItemLst[0], blockItemLst[1:], newReturnLst, level + 1)
        statement = my.Let(lhsVar, recursiveLet, body, level)
        
        return statement
    
    if isinstance(ast, DoWhile):
        # convert Dowhile to statments + while with statements
        
        minicWhile = While(ast.cond, ast.stmt)
        newBlockItemLst = ast.stmt.block_items + [minicWhile] + blockItemLst
        return minicToFunctional(newBlockItemLst[0], newBlockItemLst[1:], returnLst, level)
        
    
    if isinstance(ast, For):
        # convert for loop to init + while with (statements + next)
        
        newStmt = Block(ast.stmt.block_items + [ast.next])
        minicWhile = While(ast.cond, newStmt)
        newBlockItemLst = [ast.init, minicWhile] + blockItemLst
        
        return minicToFunctional(newBlockItemLst[0], newBlockItemLst[1:], returnLst, level)
    
    return None



import copy

#------------------------ Let binding simplification algorithm -----------------
'''
Simplification rule:
If the variable in let is a constant, attempt to simplify it by changing each
place where the variable occured on the right hand side with its value.
If the variable is modified in a loop (let rec), then undo the simplification
for this variable.

Then do the simplification for the body expression as well.
'''

def simplify(ast):
    newAst = copy.deepcopy(ast)
    
    if isinstance(newAst, my.FuncDef):
        # prototype don't need simplification, but its body does
        newAst.body = simplify(newAst.body)
        
        # call on updateLevel to make the bindings line up
        if isinstance(newAst.body, my.Node):
            newAst.body.updateLevel(1);
        return newAst
        
    if isinstance(newAst, my.Let):        
        # simplify variables that are assigned to constant
        if isinstance(newAst.ident, my.ID) and isinstance(newAst.assignedExpr, my.Constant):
            
            varName = str(newAst.ident).strip()
            
            val = newAst.assignedExpr
            newAst = replaceVar(newAst.bodyExpr, varName, val)
            
            # if variable should not be modified, make a copy of the original
            # ast again and simplify body expression
            if newAst is None:
                newAst = copy.deepcopy(ast)
                newAst.bodyExpr = simplify(newAst.bodyExpr)
            else:
                newAst = simplify(newAst);
            return newAst
            
        # simplify body expression for array ref
        if isinstance(newAst.ident, my.ArrayRef):  
            newAst.bodyExpr = simplify(newAst.bodyExpr)
            return newAst

        # ast is a let made for if statement
        # simplify both assgined Expression as well as the body expression
        newAst.assignedExpr = simplify(newAst.assignedExpr)
        newAst.bodyExpr = simplify(newAst.bodyExpr)

        return newAst
        
    if isinstance(newAst, my.TernaryOp):
        newAst.iftrue = simplify(newAst.iftrue) 
        newAst.iffalse = simplify(newAst.iffalse)
        
        return newAst
        
    if isinstance(newAst, my.Letrec):
        # simplify both the assgined Expression as well as the body expression
        newAst.assignedExpr = simplify(newAst.assignedExpr)
        newAst.bodyExpr = simplify(newAst.bodyExpr)
    
    return newAst

#------------------------ variable replacement algorithm -----------------------
'''
Replace variable with name of varName with its value val instead.
This function is used to help eliminate variables assigned to constants

Replacement rule:
Replace every variable with same string name as varName with val
Recursively calls on itself to also do the replacement in the let's body expression

If the identifier to a let binding have the same name as varName, then replacement
ends after variable is replaced on the right-hand side.

If the variable to be replace is modified in a let rec, return None.
If replacement results in a None to be returned, return None immediately.

The AST or None returned helps determine if a simplification step can be taken

'''

def replaceVar(ast, varName, val):
    
    if isinstance(ast, my.FuncDef):
        newAst = copy.deepcopy(ast)
        newAst.body = replaceVar(newAst.body, varName, val) 

        # Check if variable to be replace exist in a loop
        if newAst.body is None:
            return None
        else:
            return newAst
    
    if isinstance(ast, my.Let):
        newAst = copy.deepcopy(ast)
        if isinstance(newAst.ident, str):
            newAst.ident = my.ID(newAst.ident.strip(), 0)
        
        if isinstance(newAst.ident, my.ID) or isinstance(newAst.ident, my.ArrayRef):
            
            if isinstance(newAst.ident, my.ArrayRef):
                newAst.ident = replaceVar(newAst.ident, varName, val)
                
                # Check if variable to be replace exist in a loop
                if newAst.ident is None:
                    return None
            
            newAst.assignedExpr = replaceVar(newAst.assignedExpr, varName, val)
            if newAst.assignedExpr is None:
                return None

            
            # if the name of variable is not the one that need to be replaced,
            # check if 
            if (str(newAst.ident).strip() != varName):
                newAst.bodyExpr = replaceVar(newAst.bodyExpr, varName, val) 
                
                if newAst.bodyExpr is None:
                    return None
                
            return newAst
        
        # Do replace of variable for if statements        
        if isinstance(newAst.ident, list) or isinstance(newAst.ident, tuple):
            newAst.assignedExpr = replaceVar(newAst.assignedExpr, varName, val)
        
            if newAst.assignedExpr is None:
                return None
                
            newAst.bodyExpr = replaceVar(newAst.bodyExpr, varName, val) 
            
            if newAst.bodyExpr is None:
                return None    
                
        return newAst
        
    if isinstance(ast, my.ID):
        newAst = copy.deepcopy(ast)
        # replace variable if the name are the same
        if str(ast).strip() == varName:
            newAst = copy.deepcopy(val)
            newAst.level = ast.level 
        return newAst

        
    if isinstance(ast, my.ReturnTuples):
        
        # Replace the variable named as varName with the value val in the return
        # tuple
        newAst = copy.deepcopy(ast)
        
        if isinstance(newAst.exprs, tuple):
            newAst.exprs = list(newAst.exprs)
        
        for i in range(len(ast.exprs)):
            
            if isinstance(newAst.exprs[i], str) and (newAst.exprs[i] == str(varName).strip()):                
                newAst.exprs[i] = copy.deepcopy(val)
                newAst.exprs[i].level = 0 
            if str(newAst.exprs[i]).strip() == str(varName).strip():
                newAst.exprs[i] = copy.deepcopy(val)
                newAst.exprs[i].level = 0 
        return newAst
        
        
    if isinstance(ast, my.BinaryOp):
        # Do replacement for the expression on the left and the expression on the right
        newAst = copy.deepcopy(ast)
        
        newAst.left = replaceVar(newAst.left, varName, val)
        
        if newAst.left is None:
            return None
        
        newAst.right = replaceVar(newAst.right, varName, val)
        
        if newAst.right is None:
            return None
        return newAst
        
    if isinstance(ast, my.TernaryOp):
        # Do replacement in the condition, iftrue, and iffalse
        newAst = copy.deepcopy(ast)
        newAst.cond = replaceVar(newAst.cond, varName, val)
        newAst.iftrue = replaceVar(newAst.iftrue, varName, val)
        
        if newAst.iftrue is None:  # variable to be replaced is modified in let rec
            return None
        
        newAst.iffalse = replaceVar(newAst.iffalse, varName, val)
        
        if newAst.iffalse is None: # variable to be replaced is modified in let rec
            return None
        
        return newAst
        
    if isinstance(ast, my.FuncCall):
        # look up each argument of the function and replace variable if name is varName
        newAst = copy.deepcopy(ast)
        for i in range(len(newAst.args)):
            if isinstance(newAst.args[i], str) and (newAst.args[i] == str(varName).strip()):
                newAst.args[i] = copy.deepcopy(val)
                newAst.args[i].level = 0
                
            else:
                newAst.args[i] = replaceVar(newAst.args[i], varName, val)
        
        return newAst

    if isinstance(ast, my.ArrayRef):
        # look up each subscript and replace variable if name is varName
        newAst = copy.deepcopy(ast)
        if not isinstance(newAst.name, my.ID):
            newAst.name = replaceVar(newAst.name, varName, val)
        
        newAst.subscript = replaceVar(newAst.subscript, varName, val)
        return newAst

    if isinstance(ast, my.UnaryOp):
        # Do replacement for the expressiono in the unary expression
        newAst = copy.deepcopy(ast)
        newAst.expr = replaceVar(newAst.expr, varName, val)
        return newAst

    if isinstance(ast, my.ExprList):
        # Do replacement for each of the expression in expression list
        newAst = copy.deepcopy(ast)
        for i in range(len(newAst.exprs)):
            if isinstance(newAst.exprs[i], str) and (newAst.exprs[i] == str(varName).strip()):
                newAst.exprs[i] = copy.deepcopy(val)
                newAst.exprs[i].level = 0
                
            else:
                newAst.exprs[i] = replaceVar(newAst.exprs[i], varName, val)

        return newAst
        
    if isinstance(ast, my.Letrec):
        
        # return back a None to indicated that the variable should not be simplified because it is used in a loop
        if varName in ast.args:
            return None
        else:
            # Replace variable in let rec since variable is not modified in let rec
            newAst = copy.deepcopy(ast)
            newAst.assignedExpr = replaceVar(newAst.assignedExpr, varName, val)
            if newAst.assignedExpr is None:
                return None
            
            # Do the variable replacement to the body of let rec
            newAst.bodyExpr = replaceVar(newAst.bodyExpr, varName, val)
            
            if newAst.bodyExpr is None:
                return None
            return newAst
        
    if isinstance(ast, my.LetrecCall):
        # Do replacement for each of the argument in argument list
        newAst = copy.deepcopy(ast)
        
        if isinstance(newAst.args, tuple):
            newAst.args = list(newAst.args)
        for i in range(len(newAst.args)):
            if isinstance(newAst.args[i], str) and (newAst.args[i] == str(varName).strip()):
                newAst.args[i] = copy.deepcopy(val)
                newAst.args[i].level = 0
                
            else:
                newAst.args[i] = replaceVar(newAst.args[i], varName, val)

        return newAst
        
   
    return ast
#------------------------ variable replacement algorithm End -------------------

inputFile = sys.argv[1]
dummyName = makeDummyCFile(inputFile)

ast = parse_file(dummyName)    # pycparser to minic_ast  ast
ast1 = transform(ast)          # minic_ast to myfunctional_ast

print("Input:\n")
f = open(dummyName, 'r')
input = f.read()
print(input)
f.close()


print("\n\n----- Output: -----\n")

ast2 = transform(ast)

functionalAST = minicToFunctional(ast2, [], [], 1)
print(functionalAST)

print('\n\n --------- Simplified ----------\n')
simplifiedAST = simplify(functionalAST)
print(str(simplifiedAST))
