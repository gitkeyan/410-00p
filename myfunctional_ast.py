#-----------------------------------------------------------------
#
# Minic AST Node classes.
#
# Eli Bendersky [http://eli.thegreenplace.net]
# Victor Nicolet
# License: BSD
#-----------------------------------------------------------------


import sys

class Node(object):
    __slots__ = ()
    """ Abstract base class for AST nodes.
    """
    def children(self):
        """ A sequence of all children that are Nodes
        """
        pass

    def show(self, buf=sys.stdout, offset=0, attrnames=False, nodenames=False, showcoord=False, _my_node_name=None):
        """ Pretty print the Node and all its attributes and
            children (recursively) to a buffer.

            buf:
                Open IO buffer into which the Node is printed.

            offset:
                Initial offset (amount of leading spaces)

            attrnames:
                True if you want to see the attribute names in
                name=value pairs. False to only see the values.

            nodenames:
                True if you want to see the actual node names
                within their parents.

            showcoord:
                Do you want the coordinates of each Node to be
                displayed.
        """
        lead = ' ' * offset
        if nodenames and _my_node_name is not None:
            buf.write(lead + self.__class__.__name__+ ' <' + _my_node_name + '>: ')
        else:
            buf.write(lead + self.__class__.__name__+ ': ')

        if self.attr_names:
            if attrnames:
                nvlist = [(n, getattr(self,n)) for n in self.attr_names]
                attrstr = ', '.join('%s=%s' % nv for nv in nvlist)
            else:
                vlist = [getattr(self, n) for n in self.attr_names]
                attrstr = ', '.join('%s' % v for v in vlist)
            buf.write(attrstr)

        if showcoord:
            buf.write(' (at %s)' % self.coord)
        buf.write('\n')

        for (child_name, child) in self.children():
            child.show(
                buf,
                offset=offset + 2,
                attrnames=attrnames,
                nodenames=nodenames,
                showcoord=showcoord,
                _my_node_name=child_name)


class NodeVisitor(object):
    """ A base NodeVisitor class for visiting c_ast nodes.
        Subclass it and define your own visit_XXX methods, where
        XXX is the class name you want to visit with these
        methods.

        For example:

        class ConstantVisitor(NodeVisitor):
            def __init__(self):
                self.values = []

            def visit_Constant(self, node):
                self.values.append(node.value)

        Creates a list of values of all the bant nodes
        encountered below the given node. To use it:

        cv = ConstantVisitor()
        cv.visit(node)

        Notes:

        *   generic_visit() will be called for AST nodes for which
            no visit_XXX method was defined.
        *   The children of nodes for which a visit_XXX was
            defined will not be visited - if you need this, call
            generic_visit() on the node.
            You can use:
                NodeVisitor.generic_visit(self, node)
        *   Modeled after Python's own AST visiting facilities
            (the ast module of Python 3.0)
    """
    def visit(self, node):
        """ Visit a node.
        """
        method = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        """ Called if no explicit visitor function exists for a
            node. Implements preorder visiting of the node.
        """
        for c_name, c in node.children():
            self.visit(c)

class ArrayRef(Node):
    __slots__ = ('name', 'subscript', 'level', '__weakref__')
    def __init__(self, name, subscript, level = 0):
        self.name = name
        self.subscript = subscript
        self.level = level

    def __str__(self):
        return self.level * "    " + str(self.name) +"["+ str(self.subscript) + "]"
        
    def updateLevel(self, newLevel = 0):
        self.level = newLevel
        
    attr_names = ()


class BinaryOp(Node):
    __slots__ = ('op', 'left', 'right', 'level', '__weakref__')

    def __init__(self, op, left, right, level = 0):
        self.op = op
        self.left = left
        self.right = right
        self.level = level

    def __str__(self):
        return self.level * "    " + "(" + str(self.left) + " " + str(self.op) + " " +  str(self.right) + ")"
        
    def updateLevel(self, newLevel = 0):
        self.level = newLevel
    
    attr_names = ('op', )


class Constant(Node):
    __slots__ = ('value', 'level', '__weakref__')

    def __init__(self, value, level=0):
        self.value = value
        self.level = level

    def __str__(self):
        return self.level * "    " + str(self.value)
        
    def updateLevel(self, newLevel):
        self.level = newLevel
        
    attr_names = ('value', )


class ExprList(Node):
    __slots__ = ('exprs', 'coord', '__weakref__')

    def __init__(self, exprs, coord=None):
        self.exprs = exprs
        self.coord = coord

    def __str__(self):
        strLst = ""
        for expr in self.exprs:
            strLst += str(expr) + ", "
        return strLst[:-2] + ""
        
    def updateLevel(self, newLevel):
        pass
            
    attr_names = ()


class FuncCall(Node):
    __slots__ = ('name', 'args', 'level', '__weakref__')

    def __init__(self, name, args, level = 0):
        self.name = name
        self.args = args
        self.level = level
    
    def __str__(self):
        argString = ""
        for arg in self.args:
            argString += str(arg) + ", ";

        return self.level * "    " + str(self.name) + "(" + argString[:-2] + ")" 
    
    def updateLevel(self, newLevel):
        self.level = newLevel
        
    attr_names = ()

class FuncDef(Node):
    # The function prototype is defined as a struct using this class
    
    __slots__ = ('parameters', 'body', 'returns', 'level', '__weakref__')

    def __init__(self, parameters, body, returns, level=0):
        self.parameters = parameters   # list of variables undeclared in block provided
        self.body = body               # body of function 
        self.returns = returns         # list of written variables
        self.level = level

    def __str__(self):
        parameterStr = ""
        for parameter in self.parameters:
            parameterStr += str(parameter) + ", "
            
        returnStr = ""
        for returnVar in self.returns:
            returnStr += str(returnVar) + ", "    
        
        output = "func block_function(" +  parameterStr[:-2] + ") return (" 
        output += returnStr[:-2] + ") =\n" + str(self.body)
        return output

    attr_names = ()


class ID(Node):
    # class used to store variable name
    __slots__ = ('name', 'level', '__weakref__')

    def __init__(self, name, level = 0):
        self.name = name
        self.level = level

    def __str__(self):
        return self.level * "    " + str(self.name)
    
    def updateLevel(self, newLevel):
        self.level = newLevel

    attr_names = ('name', )


class TernaryOp(Node):
    __slots__ = ('cond', 'iftrue', 'iffalse', 'level', 'isExpression', '__weakref__')

    def __init__(self, cond, iftrue, iffalse, level = 0, isExpression = False):
        self.cond = cond            # if condition
        self.iftrue = iftrue        # statements to exectue if cond is true
        self.iffalse = iffalse      # statements to execute if cond is false
        self.level = level
        self.isExpression = isExpression   
        # isExpression = True means the expression is ternary
        # isExpression = False means the exprssion is if statment 
        
        # wrap the list of variables returned as a ReturnTuples object
        if isinstance(iffalse, tuple) or isinstance(iffalse, list):
            self.iffalse = ReturnTuples(iffalse, level + 1)
    
    def __str__(self):
        if not self.isExpression:
            output = self.level * "    " + "if " + str(self.cond) + "\n"
            output += self.level * "    " + "then\n"
            output +=  str(self.iftrue) + "\n"
            output += self.level * "    " + "else" + "\n"
            output += str(self.iffalse)
        else:
            output = self.level * "    " +"(" +  "if " + str(self.cond)
            output += " then " + str(self.iftrue).strip()
            output += " else " + str(self.iffalse).strip() + ")"

        return output

    def updateLevel(self, newLevel):
        self.level = newLevel
        if isinstance(self.iftrue, Node):
            self.iftrue.updateLevel(newLevel + 1)
        if isinstance(self.iffalse, Node):
            self.iffalse.updateLevel(newLevel + 1)
    
    attr_names = ()

class UnaryOp(Node):
    __slots__ = ('op', 'expr', 'level', '__weakref__')

    def __init__(self, op, expr, level = 0):
        self.op = op
        self.expr = expr
        self.level = level

    def __str__(self):
        return self.level * "    " + str(self.op) + "(" +str(self.expr) + ")"

    def updateLevel(self, newLevel):
        self.level = newLevel
        
    attr_names = ('op', )


class ReturnTuples(Node):
    # stores the list variables returned for the most inner let bindings
    
    __slots__ = ('exprs', 'level', '__weakref__')

    def __init__(self, exprs, level = 0):
        self.exprs = exprs
        self.level = level

    def __str__(self):
        output = ""
        if isinstance(self.exprs, tuple) or isinstance(self.exprs, list):
            if len(self.exprs) > 1:
                output = ""
                for i in self.exprs:
                    output += str(i) + ", "
                    
                output = "(" + output[:-2] + ")"
            else:
                output = str(self.exprs[0])
        return self.level * "    " + output
        
    def updateLevel(self, newLevel):
        self.level = newLevel
        
    attr_names = ()


class Let(Node):
    # The class used to store the let bindings 
    
    __slots__ = ('ident', 'assignedExpr', 'bodyExpr', 'level', '__weakref__')
    
    def __init__(self, ident, assignedExpr, bodyExpr, level = 0):
        self.ident = ident                  # identifier
        self.assignedExpr = assignedExpr    # expression
        self.bodyExpr = bodyExpr            # body expression (the expression after 'in')
        self.level = level
        
        
        # if the identifier is a list of one variable, make it just the variable 
        if isinstance(self.ident, list) or isinstance(self.ident, tuple):
            if len(self.ident) == 1:
                self.ident = self.ident[0]
            else: # otherwise make it into a list
                self.ident = list(self.ident)

        # properly wrap the returned tuples as ReturnTuples object of the body
        # expression
        if isinstance(self.bodyExpr, list) or isinstance(self.bodyExpr, tuple):
            self.bodyExpr = ReturnTuples(tuple(bodyExpr), level + 1)


    def __str__(self):
        # Output the string representation of Let
        '''
        Let ident = 
            assignedExpression
        in
            bodyExpression
        
        OR
        
        Let ident = assignedExpression
        in bodyExpression
        
        Depending on whether assignedExpression and bodyExpression can be
        represented in a single line
        '''

        if isinstance(self.ident, list) or isinstance(self.ident, tuple):
            identLst = ""
            for ident in self.ident:
                identLst += str(ident) + ", "
            identLst = identLst[:-2]
            output = self.level * "    " + "Let (" + identLst + ")" + " = "
        else:
            output = self.level * "    " + "Let " + str(self.ident) + " = " 
        
        assignedStr = str(self.assignedExpr)
        if len(assignedStr.split('\n')) > 1:
            output += "\n" + assignedStr
        else:
            output += assignedStr.strip()
        
        if isinstance(self.bodyExpr, list):
            if len(self.bodyExpr) > 1:
                returnLst = "("
                for exp in self.bodyExpr:
                    returnLst += str(exp) + ", "
                
                if returnLst[:-2] == "":
                    returnLst = "()"
                else:
                    returnLst = returnLst[:-2] + ")"
                
                output += "\n" + self.level * "    " + "in " + returnLst 
            else:
                output += "\n" + self.level * "    " + "in " + self.bodyExpr[0] 
            return output
            
        else:
            output += "\n" + self.level * "    " + "in "  
            
            bodyExprStr = str(self.bodyExpr)
            if len(bodyExprStr.split('\n')) > 1:
                output += "\n" + bodyExprStr
            else:
                output += bodyExprStr.strip()

            return output
        
    def updateLevel(self, newLevel):
        self.level = newLevel
        if isinstance(self.assignedExpr, Node):
            self.assignedExpr.updateLevel(newLevel + 1)
            
        if isinstance(self.bodyExpr, Node):
            self.bodyExpr.updateLevel(newLevel + 1)

    attr_names = ()

class Letrec(Node):
    # The class used to store the let rec bindings
    
    __slots__ = ('ident', 'args', 'assignedExpr', 'bodyExpr', 'level', '__weakref__')
    
    def __init__(self, ident, args, assignedExpr, bodyExpr, level = 0):
        self.ident = ident                    # identifier
        self.args = args                      # arglist
        self.assignedExpr = assignedExpr      # expression
        self.bodyExpr = bodyExpr              # body expression (the expression after 'in')
        self.level = level
        
        if isinstance(self.bodyExpr, list):
            self.bodyExpr = ReturnTuples(tuple(bodyExpr), level + 1)


    def __str__(self):
        argStr = ""
        for arg in self.args:
            argStr += " " + str(arg)
        argStr = argStr[1:]
        
        output = self.level * "    " + "let rec " + str(self.ident) + " " + argStr + " = \n"
        output += str(self.assignedExpr) + "\n"
        output += self.level * "    " + "in "
        
        lineCount = len(str(self.bodyExpr).split('\n'))
        if isinstance(self.bodyExpr, ReturnTuples) or (lineCount <= 1):
            output += str(self.bodyExpr).strip()
        else:
            output += "\n" + str(self.bodyExpr) 
        return output
        
    def updateLevel(self, newLevel):
        self.level = newLevel
        if isinstance(self.assignedExpr, Node):
            self.assignedExpr.updateLevel(newLevel + 1)
            
        if isinstance(self.bodyExpr, Node):
            self.bodyExpr.updateLevel(newLevel + 1)

class LetrecCall(Node):
    # An expression that calls a let rec binding 
    
    __slots__ = ('ident', 'args', 'level', '__weakref__')
    
    def __init__(self, ident, args, level = 0):
        self.ident = ident
        self.args = args
        self.level = level
        
    def __str__(self):
        output = self.level * "    " + str(self.ident)
        for arg in self.args:
            output += " " + str(arg)
        
        return output
        
    def updateLevel(self, newLevel):
        self.level = newLevel

