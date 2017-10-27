from minic_ast import *
from c_ast_to_minic import * 


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

