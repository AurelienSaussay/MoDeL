from pyparsing import *

from elements import *

def tokensAsList(kls, tokens):
    return kls(tokens.asList())

def tokensAsArguments(kls, tokens):
    return kls(*tokens.asList())

def setParseClass(self, kls, unpack = False):
    self.setParseAction(partial(tokensAsArguments if unpack else tokensAsList, kls))
    return self

ParserElement.setParseClass = setParseClass

openParenSuppr = Suppress('(')
closeParenSuppr = Suppress(')')

integer = Combine(Optional('-') + Word(nums)).setParseAction(lambda toks: Integer(int(toks[0])))

real =  Combine(Optional('-') + Word(nums) + '.' + Word(nums)).setParseAction(lambda toks: Real(float(toks[0])))

variableName = Word(alphas + '_%$@', alphanums + '_').setParseClass(VariableName, True)

placeholder = (Suppress('|') + variableName + Suppress('|')).setParseClass(Placeholder, True)

identifier = ( (variableName | placeholder) + ZeroOrMore(variableName | placeholder) ).setParseClass(Identifier)

expression = Forward()
index = (Suppress('[') + delimitedList(expression) + Suppress(']')).setParseClass(Index)

timeOffset = (openParenSuppr + (integer | variableName) + closeParenSuppr).setParseClass(TimeOffset, True)

array = (identifier + index + Group(Optional(timeOffset))).setParseClass(Array, True)

operand = array | identifier | real | integer

unaryOperator = oneOf('+ -').setParseClass(Operator, True)

operator = oneOf('+ - * / ^').setParseClass(Operator, True)

comparisonOperator = oneOf('<> < <= > >= ==').setParseClass(ComparisonOperator, True)

booleanOperator = oneOf('and or xor').setParseClass(BooleanOperator, True)

func = (variableName + openParenSuppr + Group(delimitedList(expression)) + closeParenSuppr).setParseClass(Func, True)

formula = Forward()
sumFunc = (Suppress('sum') + openParenSuppr + formula + closeParenSuppr).setParseClass(SumFunc, True)

openParen = Literal('(').setParseClass(BaseElement, True)
closeParen = Literal(')').setParseClass(BaseElement, True)

atom =  sumFunc | func | openParen + expression + closeParen | operand
expression << Optional(unaryOperator) + atom + ZeroOrMore((operator | comparisonOperator | booleanOperator) + atom)
expression = expression.setParseClass(Expression)

equation = (expression + Suppress('=') + expression).setParseClass(Equation, True)

condition = (Suppress(Keyword('if')) + expression).setParseClass(Condition, True)

lstRaw  = OneOrMore(Word(alphanums))
lst = (Group(lstRaw) + Group(Optional(Suppress('\\') + lstRaw))).setParseClass(Lst, True)

def grouped(elem):
    return Group(elem | openParenSuppr + delimitedList(elem) + closeParenSuppr).setParseClass(Grouped, True)

iter = (grouped(variableName) + Suppress(Keyword('in')) + (grouped(lst) | variableName)).setParseClass(Iter, True)

options = oneOf('!pv !p !Pv !P').setParseAction(lambda toks: toks[0])

formula << (Group(Optional(options)) +
            (equation | expression) +
            Group(Optional(condition)) +
            Group(Optional(Suppress(',') + delimitedList(iter)))).setParseClass(Formula, True)
