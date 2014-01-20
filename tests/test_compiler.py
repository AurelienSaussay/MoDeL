from .. import grammar
from .. import traversal
import csv

# class TestCompiler(object):
#     @classmethod
#     def setup_class(cls):
#         with open('../tmp_all_vars.csv', 'rb') as csvfile:
#             rows = list(csv.reader(csvfile))
#             cls.heap = dict(zip(rows[0],
#                                 [float(e) if e != 'NA' else
#                                  None for e in rows[2]]))

#     def test_compiles_VariableName_Price_Volume(self):
#         res = grammar.variableName.parseString("M")[0]
#         assert res.compile({}, {}, '!pv') == 'PM * M'



#     def test_compiles_Identifier_Price_Volume(self):
#         res = grammar.identifier.parseString("test|V|_energy|O|")[0]
#         assert res.compile({grammar.VariableName('V'): 'Q', grammar.VariableName('O'): 'M'}, {}, '!pv') == "PtestQ_energyM * testQ_energyM"





#     def test_compiles_Array_Price_Volume(self):
#         res = grammar.array.parseString("arrayName8[com, 5, sec]")[0]
#         assert res.compile({grammar.VariableName('com'): '24', grammar.VariableName('sec'): '2403'}, {}, '!pv') == "ParrayName8_24_5_2403 * arrayName8_24_5_2403"




#     def test_evaluates_Expression(self):
#         res = grammar.expression.parseString("2 * Q[com, sec] + 4 * X[com, sec]")[0]
#         assert res.evaluate({grammar.VariableName('com'): '24', grammar.VariableName('sec'): '2403'},
#                             {'Q_24_2403': 1, 'X_24_2403': 10}) == 42
#         res = grammar.expression.parseString("2 * Q[com, sec] - X[com, sec] ^ 2 < 0")[0]
#         assert res.evaluate({grammar.VariableName('com'): '24', grammar.VariableName('sec'): '2403'},
#                             {'Q_24_2403': 1, 'X_24_2403': 10}) == True


#     def test_compiles_Equation(self):
#         res = grammar.equation.parseString("energy[com] = log(B[3])")[0]
#         assert res.compile({grammar.VariableName('com'): '24'}, {}, '') == "energy_24 = log(B_3)"
#         res = grammar.equation.parseString("energy[com] = B[3]")[0]
#         assert res.compile({grammar.VariableName('com'): '24'}, {}, '!pv') == "Penergy_24 * energy_24 = PB_3 * B_3\nenergy_24 = B_3"


#     def test_compiles_SumFunc(self):
#         res = grammar.sumFunc.parseString("sum(Q[c, s] if Q[c, s] <> 0, c in 01 02 03)")[0]
#         assert res.compile({grammar.VariableName('s'): '10'}, {'Q_01_10': 15, 'Q_02_10': 0, 'Q_03_10': 20}, '') == "0 + Q_01_10 + Q_03_10"


class TestParser(object):

    def _expected(self, res, nodetype, children_count, *children_types):
        assert res.nodetype == nodetype
        assert len(res.children) == children_count
        for i, t in enumerate(children_types):
            if t is None:
                assert res.children[i] is None
            elif t == traversal.ASTNone:
                assert res.children[i] == traversal.ASTNone
            else:
                assert res.children[i].nodetype == t

    def test_parses_integer(self):
        res = grammar.integer.parseString("42")[0]
        assert res.nodetype == "integer"
        assert res.immediate == 42
        res = grammar.integer.parseString("-42")[0]
        assert res.nodetype == "integer"
        assert res.immediate == -42

    def test_parses_real(self):
        res = grammar.real.parseString("3.14159")[0]
        assert res.nodetype == "real"
        assert res.immediate == 3.14159
        res = grammar.real.parseString("-3.14159")[0]
        assert res.nodetype == "real"
        assert res.immediate == -3.14159

    def test_parses_variableName(self):
        res = grammar.variableName.parseString("testVariable")[0]
        assert res.nodetype == "variableName"
        assert res.immediate == "testVariable"
        res = grammar.variableName.parseString("_test9_Variable")[0]
        assert res.nodetype == "variableName"
        assert res.immediate == "_test9_Variable"

    def test_parses_placeholder(self):
        res = grammar.placeholder.parseString("|X|")[0]
        self._expected(res, "placeholder", 1, "variableName")

    def test_parses_identifier(self):
        res = grammar.identifier.parseString("test|X|_energy|O|")[0]
        self._expected(res, "identifier", 4, "variableName", "placeholder", "variableName", "placeholder")
        res = grammar.identifier.parseString("testVar")[0]
        self._expected(res, "identifier", 1, "variableName")

    def test_parses_timeOffset(self):
        res = grammar.timeOffset.parseString("(-1)")[0]
        self._expected(res, "timeOffset", 1, "integer")
        res = grammar.timeOffset.parseString("(outOfTimeMan)")[0]
        self._expected(res, "timeOffset", 1, "variableName")

    def test_parses_index(self):
        res = grammar.index.parseString("[com, sec]")[0]
        self._expected(res, "index", 2, "expression", "expression")

    def test_parses_array(self):
        res = grammar.array.parseString("|X|tes|M|_arrayName8[com, 5, sec]")[0]
        self._expected(res, "array", 3, "identifier", "index", traversal.ASTNone)
        res = grammar.array.parseString("timeAry[5](-1)")[0]
        self._expected(res, "array", 3, "identifier", "index", "timeOffset")

    def test_parses_function(self):
        res = grammar.func.parseString("d(log(test))")[0]
        self._expected(res, "function", 2, "variableName", "formula")
        assert res.children[1].children[1].nodetype == "expression"
        res = grammar.func.parseString("@elem(PK[s], %baseyear)")[0]
        self._expected(res, "function", 3, "variableName", "expression", "expression")
        assert res.children[0].immediate == '@elem'
        res = grammar.func.parseString("multiple(c, s, 42)")[0]
        self._expected(res, "function", 4, "variableName", "expression", "expression", "expression")

    def test_parses_expression(self):
        res = grammar.expression.parseString("D|O|[com, sec] + d(log(Q[com, sec])) - A / B")[0]
        self._expected(res, "expression", 7, "array", "operator", "function", "operator", "identifier", "operator", "identifier")
        res = grammar.expression.parseString("( (CH[c]>0) * CH[c] + (CH[c]<=0) * 1 )")[0]
        self._expected(res, "expression", 3, "literal", "expression", "literal")
        res = grammar.expression.parseString("-ES_KLEM($s, 1) * d(log(CK[s]) - log(CL[s]))")[0]
        self._expected(res, "expression", 4, "operator", "function", "operator", "function")

    def test_parses_equation(self):
        res = grammar.equation.parseString("energy|O|[com] + _test|X||M|[sec] = log(B[j])")[0]
        self._expected(res, "equation", 2, "expression", "expression")

    def test_parses_condition(self):
        res = grammar.condition.parseString("if energy[com, sec] > 0")[0]
        self._expected(res, "condition", 1, "expression")

    def test_parses_listBase(self):
        res = grammar.lstBase.parseString("01 02 03 04 05 06 07")[0]
        self._expected(res, "listBase", 7, "string", "string", "string", "string", "string", "string", "string")

    def test_parses_list(self):
        res = grammar.lst.parseString("01 02 03 04 05 06 07")[0]
        self._expected(res, "list", 2, "listBase", traversal.ASTNone)
        assert res.children[0].children[3].immediate == "04"
        res = grammar.lst.parseString("01 02 03 04 05 06 07 \ 04 06")[0]
        self._expected(res, "list", 2, "listBase", "listBase")
        assert res.children[0].children[3].immediate == "04"
        assert res.children[1].children[1].immediate == "06"

    def test_parses_iterator(self):
        res = grammar.iter.parseString("com in 01 02 03 04 05 06 07")[0]
        self._expected(res, "iterator", 2, "variableName", "list")
        res = grammar.iter.parseString("(c, s) in (01 02 03, 04 05 06)")[0]
        self._expected(res, "iterator", 4, "variableName", "variableName", "list", "list")

    def test_parses_formula(self):
        res = grammar.formula.parseString("|V|[com] = |V|D[com] + |V|M[com], V in Q CH G I DS, com in 01 02 03 04 05 06 07 08 09")[0]
        self._expected(res, "formula", 5, None, "equation", None, "iterator", "iterator")
        res = grammar.formula.parseString("Q = QD + QM")[0]
        self._expected(res, "formula", 4, None, "equation", None, None)
        res = grammar.formula.parseString("|V|[com] = |V|D[com] + |V|M[com] if |V|[com] > 0, V in Q CH I, com in 01 02 07 08 09")[0]
        self._expected(res, "formula", 5, None, "equation", "condition", "iterator", "iterator")
        res = grammar.formula.parseString("Q[s] = sum(Q[c, s] if Q[c, s] <> 0, c in 01 02 03), s in 10 11 12")[0]
        self._expected(res, "formula", 4, None, "equation", None, "iterator")
        self._expected(res.children[1].children[1], 'expression', 1, "function")


class TestCompiler(object):
    def test_compiles_integer(self):
        ast = grammar.integer.parseString("42")[0]
        assert traversal.compile_ast(ast).compiled == 42

    def test_compiles_real(self):
        ast = grammar.real.parseString("3.14159")[0]
        assert traversal.compile_ast(ast).compiled == 3.14159

    def test_compiles_variableName(self):
        ast = grammar.variableName.parseString("_test9_Variable")[0]
        assert traversal.compile_ast(ast).compiled == "_test9_Variable"

    def test_compiles_list(self):
        ast = grammar.lst.parseString("01 02 03 04 05 06 07")[0]
        assert traversal.compile_ast(ast).compiled == ['01', '02', '03', '04', '05', '06', '07']
        ast = grammar.lst.parseString("01 02 03 04 05 06 07 \ 04 06")[0]
        assert traversal.compile_ast(ast).compiled == ['01', '02', '03', '05', '07']

    def test_compiles_placeholder(self):
        ast = grammar.placeholder.parseString("|V|")[0]
        assert traversal.compile_ast(ast, {'V': 'X'})[0].compiled == 'X'

    def test_compiles_iterator(self):
        ast = grammar.iter.parseString("V in Q CH G I DS")[0]
        assert traversal.compile_ast(ast).compiled == {'names': ['V', '$V'],
                                              'lists': [('Q', 1), ('CH', 2), ('G', 3), ('I', 4), ('DS', 5)]}
        ast = grammar.iter.parseString("(c, s) in (01 02 03, 04 05 06)")[0]
        assert traversal.compile_ast(ast).compiled == {'names': ['c', 's', '$c', '$s'],
                                              'lists': [('01', '04', 1, 1),
                                                        ('02', '05', 2, 2),
                                                        ('03', '06', 3, 3)]}

class TestGenerator(object):
    def test_generates_integer(self):
        ast = grammar.integer.parseString("42")[0]
        assert traversal.generate(traversal.compile_ast(ast)) == "42"

    def test_generates_real(self):
        ast = grammar.real.parseString("3.14159")[0]
        assert traversal.generate(traversal.compile_ast(ast)) == "3.14159"

    def test_generates_variableName(self):
        ast = grammar.variableName.parseString("_test9_Variable")[0]
        assert traversal.generate(traversal.compile_ast(ast)) == "_test9_Variable"

    def test_generates_identifier(self):
        ast = grammar.identifier.parseString("test|V|_energy|O|")[0]
        traversal.compile_ast(ast, {'V': 'Q', 'O': 'M'})
        assert traversal.generate(ast) == "testQ_energyM"

    def test_generates_array(self):
        ast = grammar.array.parseString("arrayName8[com, 5, sec]")[0]
        assert traversal.generate(traversal.compile_ast(ast, {'com': '24', 'sec': '2403'})) == "arrayName8_24_5_2403"
        ast = grammar.array.parseString("timeAry[5](-1)")[0]
        assert traversal.generate(traversal.compile_ast(ast)) == "timeAry_5(-1)"
        ast = grammar.array.parseString("test[$s]")[0]
        assert traversal.generate(traversal.compile_ast(ast, {'$s': 15})) == "test_15"

    def test_generates_function(self):
        ast = grammar.func.parseString("d(log(test))")[0]
        assert traversal.generate(traversal.compile_ast(ast)) == "d(log(test))"
        ast = grammar.func.parseString("@elem(PK, %baseyear)")[0]
        assert traversal.generate(traversal.compile_ast(ast)) == "@elem(PK, %baseyear)"
        ast = grammar.func.parseString("@elem(PK(-1), %baseyear)")[0]
        res = traversal.generate(traversal.compile_ast(ast))
        assert res == "@elem(PK(- 1), %baseyear)"
#         res = grammar.func.parseString("ES_KLEM($s, 1)")[0]
#         assert res.compile({grammar.VariableName('$s'): '42'}, {}, '') == "ES_KLEM(42, 1)"
#         res = grammar.func.parseString("value(QD[c] + ID[c])")[0]
#         assert res.compile({grammar.VariableName('c'): '42'}, {}, '') == "PQD_42 * QD_42 + PID_42 * ID_42"

    def test_generates_equation(self):
        ast = grammar.equation.parseString("energy[com] = B[3]")[0]
        assert traversal.generate(traversal.compile_ast(ast, {'com': '24'})) == "energy_24 = B_3"
        # ast = grammar.equation.parseString("energy[com] = log(B[3])")[0]
        # assert traversal.generate(traversal.compile_ast(ast, {'com': '24'})) == "energy_24 = log(B_3)"
        # ast = grammar.equation.parseString("energy[com] = B[3]")[0]
        # traversal.compile_ast(ast, {'com': '24'})
        # assert traversal.generate(ast) == "Penergy_24 * energy_24 = PB_3 * B_3\nenergy_24 = B_3"

        # def test_compiles_Expression(self):
    #     ast = grammar.expression.parseString("D[com, sec] + d(log(Q[com, sec])) - A / B")[0]
    #     traversal.compile_ast(ast, {'com': '24', 'sec': '2403'})
    #     assert traversal.generate(ast) == "D_24_2403 + d(log(Q_24_2403)) - A / B"
        # ast = grammar.expression.parseString("D[com, sec] + Q[com, sec] - A")[0]
        # assert traversal.compile_ast(ast, {grammar.VariableName('com'): '24', grammar.VariableName('sec'): '2403'}, {}, '!pv') == "PD_24_2403 * D_24_2403 + PQ_24_2403 * Q_24_2403 - PA * A"
        # ast = grammar.expression.parseString("( (CH[c]>0) * CH[c] + (CH[c]<=0) * 1 )")[0]
        # assert traversal.compile_ast(ast, {grammar.VariableName('c'): '01'}, {}, '') == "( ( CH_01 > 0 ) * CH_01 + ( CH_01 <= 0 ) * 1 )"
        # ast = grammar.expression.parseString("EBE[s] - @elem(PK[s](-1), %baseyear) * Tdec[s] * K[s](-1)")[0]
        # assert traversal.compile_ast(ast, {grammar.VariableName('s'): '02'}, {}, '') == "EBE_02 - @elem(PK_02(-1), %baseyear) * Tdec_02 * K_02(-1)"
        # ast = grammar.expression.parseString("s")[0]
        # assert traversal.compile_ast(ast, {grammar.VariableName('s'): '02'}, {}, '') == "02"


    def test_generates_formula(self):
        expected = ("Q_01 = QD_01 + QM_01\n"
                    "Q_02 = QD_02 + QM_02\n"
                    "CH_01 = CHD_01 + CHM_01\n"
                    "CH_02 = CHD_02 + CHM_02")
        ast = grammar.formula.parseString("|V|[com] = |V|D[com] + |V|M[com], V in Q CH, com in 01 02")[0]
        assert '\n'.join(traversal.generate(traversal.compile_ast(ast))) == expected
#         expected = ("Q_02 = QD_02 + QM_02\n"
#                     "CH_02 = CHD_02 + CHM_02")
#         res = grammar.formula.parseString("|V|[com] = |V|D[com] + |V|M[com] if CHD[com] > 0, V in Q CH, com in 01 02")[0]
#         assert res.compile({"CHD_01": 0, "CHD_02": 15}) == expected
#         expected = ("PQ_02 * Q_02 = PQD_02 * QD_02 + PQM_02 * QM_02\n"
#                     "Q_02 = QD_02 + QM_02\n"
#                     "PCH_02 * CH_02 = PCHD_02 * CHD_02 + PCHM_02 * CHM_02\n"
#                     "CH_02 = CHD_02 + CHM_02")
#         res = grammar.formula.parseString("!Pv |V|[com] = |V|D[com] + |V|M[com] if CHD[com] > 0, V in Q CH, com in 01 02")[0]
#         assert res.compile({"CHD_01": 0, "CHD_02": 15}) == expected
#         expected = ("Q_10 = 0 + Q_01_10 + Q_03_10\n"
#                     "Q_11 = 0 + Q_01_11 + Q_02_11 + Q_03_11\n"
#                     "Q_12 = 0 + Q_01_12 + Q_02_12")
#         res = grammar.formula.parseString("Q[s] = sum(Q[c, s] if Q[c, s] <> 0, c in 01 02 03), s in 10 11 12")[0]
#         assert res.compile({'Q_01_10': 15, 'Q_02_10': 0,  'Q_03_10': 20,
#                             'Q_01_11': 15, 'Q_02_11': 42, 'Q_03_11': 20,
#                             'Q_01_12': 15, 'Q_02_12': 13, 'Q_03_12': 0}) == expected
#         expected = ("PQ_10 * Q_10 = 0 + PQ_01_10 * Q_01_10 + PQ_03_10 * Q_03_10\n"
#                     "Q_10 = 0 + Q_01_10 + Q_03_10\n"
#                     "PQ_11 * Q_11 = 0 + PQ_01_11 * Q_01_11 + PQ_02_11 * Q_02_11 + PQ_03_11 * Q_03_11\n"
#                     "Q_11 = 0 + Q_01_11 + Q_02_11 + Q_03_11")
#         res = grammar.formula.parseString("!pv Q[s] = sum(Q[c, s] if Q[c, s] <> 0, c in 01 02 03), s in 10 11")[0]
#         assert res.compile({'Q_01_10': 15, 'Q_02_10': 0,  'Q_03_10': 20,
#                             'Q_01_11': 15, 'Q_02_11': 42, 'Q_03_11': 20}) == expected
#         expected = ("Q_04 = Test_1 + 2 * 1\n"
#                     "Q_05 = Test_2 + 2 * 2\n"
#                     "Q_06 = Test_3 + 2 * 3")
#         res = grammar.formula.parseString("Q[c] = Test[$c] + 2 * $c, c in 04 05 06")[0]
#         assert res.compile({}) == expected
