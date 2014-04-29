import lexer

class DefaultGenerator:
    @staticmethod
    def index(components):
        return '_' + '_'.join(components)

class Compiler:
    def __init__(self, file, generator = DefaultGenerator):
        self.lexer = lexer.Lexer(file)
        self.heap = {}
        self.generator = generator
        # Init tokens
        self.token = self.lexer.read()
        self.nextToken = self.lexer.read()
        self.Instruction()

    def advance(self):
        self.token = self.nextToken
        self.nextToken = self.lexer.read()

    def match(self, tokenType):
        if self.token[0] == tokenType:
            self.advance()
        else:
            self.expected(tokenType)

    def read(self, tokenType):
        if self.token[0] == tokenType:
            ret = self.token[1]
            self.advance()
            return ret
        else:
            self.expected(tokenType)

    def expected(self, tokenType):
        raise SyntaxError("Expected {0}".format(tokenType))

    def readList(self, term):
        """
        <list> ::= (<integer> | <name>)*
        """
        ret = []
        while self.token[0] <> term:
            if self.token[0] == "integer" or self.token[0] == "name":
                ret.append(self.token[1])
                self.advance()
            else:
                self.expected("integer or string")
        return ret

    def Instruction(self):
        """
        <instruction> ::= <assignment> | <include> | <iter> | <formula>
        """
        if self.token[0] == 'local':
            self.readAssignment()
        elif self.token[0] == 'include':
            self.Include()
        elif self.nextToken[1] == "in":
            self.Iter()
        else:
            self.readFormula()

    def readAssignment(self):
        """
        <assignment> ::= <localName> ":=" <list>
        """
        local = self.read('local')
        self.match('assign')
        list = self.readList('newline')
        self.heap[local] = list

    def readExpression(self):
        """
        <expression> ::= <term> (<operator> <term>)*
        """
        compiled, all_iterators, all_identifiers = self.readTerm()
        all_terms = [compiled]

        while self.isTerm() or self.token[0] == 'operator':
            if self.token[0] == 'operator':
                all_terms.append(self.read('operator'))
            else:
                compiled, iterators, identifiers = self.readTerm()
                all_terms.append(compiled)
                all_iterators.update(iterators)
                all_identifiers.update(identifiers)

        return (' '.join(all_terms),
                all_iterators,
                all_identifiers)

    def isTerm(self):
        return self.token[0] == 'name' or self.token[0] == 'lparen' or self.token[0] == 'local' or self.token[0] == 'counter' or self.token[0] == 'real' or self.token[0] == 'integer'

    def readTerm(self):
        """
        <term> ::= <function> | <lparen> <expression> <rparen> | <local> | <counter> | <real> | <integer> | <identifier>
        """
        iterators = set()
        identifiers = None

        if self.token[0] == 'name' and self.nextToken[0] == 'lparen':
            compiled, iterators, identifiers = self.readFunction()
        elif self.token[0] == 'lparen':
            self.match('lparen')
            compiled, iterators, identifiers = self.readExpression()
            self.match('rparen')
        elif self.token[0] == 'local':
            compiled = self.read('local')
        elif self.token[0] == 'counter':
            compiled = self.read('counter')
            iterators.add(compiled[1:])
        elif self.token[0] == 'real':
            compiled = self.read('real')
        elif self.token[0] == 'integer':
            compiled = self.read('integer')
        else:
            compiled, iterators = self.readIdentifier()
            identifiers = set([compiled])

        return (compiled, iterators, identifiers)

    def readIdentifier(self):
        """
        <identifier> ::= (<name> | <placeholder>)+ [<index>] [<time>]
        """
        components = []
        iterators = set()

        if not self.token[0] in ['name', 'pipe']:
            self.expected('name or placeholder')

        while self.token[0] in ['name', 'pipe']:
            if self.token[0] == 'name':
                components.append(self.read('name'))
            elif self.token[0] == 'pipe':
                placeholder = self.readPlaceholder()
                components.append(placeholder[0])
                iterators.add(placeholder[1])

        if self.token[0] == 'lbracket':
            index, index_iterators = self.readIndex()
            components.append(index)
            iterators.update(index_iterators)

        if self.token[0] == 'lcurly':
            time = self.readTime()

        return (''.join(components), iterators)


    def readPlaceholder(self):
        """
        <placeholder> ::= <pipe> <name> <pipe>
        """
        self.match('pipe')
        name = self.read('name')
        self.match('pipe')
        return ("%({0})s".format(name), name)

    def readIndex(self):
        """
        <index> ::= <lbracket> (<name> | <integer>) (<comma> (<name> | <integer>))+ <rbracket>
        """
        components = []
        iterators = set()

        self.match('lbracket')

        if self.token[0] == 'name':
            name = self.read('name')
            components.append("%({0})s".format(name))
            iterators.add(name)
        elif self.token[0] == 'integer':
            components.append(self.read('integer'))
        else:
            self.expected('iterator name or integer')

        while self.token[0] == 'comma':
            self.match('comma')
            if self.token[0] == 'name':
                name = self.read('name')
                components.append("%({0})s".format(name))
                iterators.add(name)
            elif self.token[0] == 'integer':
                components.append(self.read('integer'))
            else:
                self.expected('iterator name or integer')

        self.match('rbracket')
        return (self.generator.index(components), iterators)

    def readFormula(self):
        """
        <formula> ::= <expression> <equal> <expression> [ (<iter>)* ]
        """
        lhs = self.readExpression()
        self.match('equal')
        rhs = self.readExpression()

        print lhs, rhs
