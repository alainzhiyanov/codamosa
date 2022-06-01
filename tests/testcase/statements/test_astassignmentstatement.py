#  This file is part of Pynguin.
#
#  SPDX-FileCopyrightText: 2019–2022 Pynguin Contributors
#
#  SPDX-License-Identifier: LGPL-3.0-or-later
#


from typing import TYPE_CHECKING, Set

import pytest

import pynguin.configuration as config
from pynguin.analyses.codedeserializer import deserialize_code_to_testcases
from pynguin.generation.export.exportprovider import ExportProvider
from pynguin.setup.testclustergenerator import TestClusterGenerator

# End-to-end test of the ast assign statement's get_variable_references
from pynguin.testcase.testfactory import TestFactory

if TYPE_CHECKING:
    import pynguin.testcase.testcase as tc
    from pynguin.testcase.statement import ASTAssignStatement


def test_delete_statement():
    # This tests the replace operator of the AST
    config.configuration.seeding.uninterpreted_statements = True
    test_case_str = """def test_case_0():
    int_0 = 0
    int_1 = 1
    var_0 = lambda x: x + int_1"""

    expected_out = """def test_case_0():
    int_0 = 0
    var_0 = lambda x: x + int_0"""

    # Dummy test cluster
    test_cluster = TestClusterGenerator(
        "tests.fixtures.grammar.parameters"
    ).generate_cluster()

    test_cases, _, _ = deserialize_code_to_testcases(test_case_str, test_cluster)
    assert len(test_cases) == 1
    test_case = test_cases[0]
    assert len(test_case.statements) == 3
    TestFactory.delete_statement_gracefully(test_case, 1)
    out_test_case = ExportProvider.get_exporter().export_sequences_to_str(test_cases)
    assert out_test_case == expected_out


def test_ast_get_variable_refs():
    config.configuration.seeding.uninterpreted_statements = True

    test_case_str = """def test_case_0():
    int_0 = 15
    int_1 = [int_0, int_0, int_0]
    var_0 = [lambda x: x/y + int_0 for y in int_1]"""

    # Dummy test cluster
    test_cluster = TestClusterGenerator(
        "tests.fixtures.grammar.parameters"
    ).generate_cluster()

    test_cases, _, _ = deserialize_code_to_testcases(test_case_str, test_cluster)
    assert len(test_cases) == 1
    test_case = test_cases[0]
    assert len(test_case.statements) == 3
    stmt: ASTAssignStatement = test_case.statements[2]  # type: ignore
    assert len(stmt.get_variable_references()) == 2


# End-to-end test of the ast assign statement's mutation operation
def test_mutate_ast_assign_tc():
    config.configuration.seeding.uninterpreted_statements = True
    config.configuration.seeding.include_partially_parsable = True

    test_case_str = """def test_case_0():
    int_0 = 0
    int_1 = 1
    var_0 = lambda x: x + int_1 """

    # There is only one possible mutation here.
    mutated_test_case_str = """def test_case_0():
    int_0 = 0
    int_1 = 1
    var_0 = lambda x: x + int_0"""

    # Dummy test cluster
    test_cluster = TestClusterGenerator(
        "tests.fixtures.grammar.parameters"
    ).generate_cluster()

    test_cases, _, _ = deserialize_code_to_testcases(test_case_str, test_cluster)
    assert len(test_cases) == 1
    test_case = test_cases[0]
    orig_test_case = test_case.clone()
    assert len(test_case.statements) == 3
    assert test_case.statements[-1].mutate()
    out_test_case = ExportProvider.get_exporter().export_sequences_to_str([test_case])
    assert out_test_case == mutated_test_case_str
    assert test_case != orig_test_case


def test_mutate_differs():
    # This test is flaky with probability 2.6e-13
    # 25 possible mutants, each with probability 1/25
    # Probability of a particular mutant happening 10 times: 1/25^10
    # Probability any mutant happening 10 times: 1/25^9
    config.configuration.seeding.uninterpreted_statements = True
    config.configuration.seeding.include_partially_parsable = True

    test_case_str = """def test_case_0():
    int_0 = 0
    int_1 = 1
    int_2 = 2
    int_3 = 3
    int_4 = 4
    int_5 = 5
    var_0 = int_0 + int_0 + int_0 + int_0 + int_0"""

    # Dummy test cluster
    test_cluster = TestClusterGenerator(
        "tests.fixtures.grammar.parameters"
    ).generate_cluster()

    test_cases, _, _ = deserialize_code_to_testcases(test_case_str, test_cluster)
    assert len(test_cases) == 1
    test_case = test_cases[0]
    mutants: Set[tc.TestCase] = set()
    for _ in range(10):
        mutant = test_case.clone()
        assert mutant.statements[-1].mutate()
        mutants.add(mutant)
    assert len(mutants) > 1


@pytest.mark.parametrize(
    "test_case_str",
    [
        (
            """def test_case_0():
    int_0 = 0
    var_0 = lambda x: x + 2 """
        ),
        (
            """def test_case_0():
    int_0 = 0
    var_0 = lambda x: x + int_0 """
        ),
    ],
)
def test_mutate_ast_assign_no_options(test_case_str):
    config.configuration.seeding.uninterpreted_statements = True
    config.configuration.seeding.include_partially_parsable = True

    # Dummy test cluster
    test_cluster = TestClusterGenerator(
        "tests.fixtures.grammar.parameters"
    ).generate_cluster()

    test_cases, _, _ = deserialize_code_to_testcases(test_case_str, test_cluster)
    assert len(test_cases) == 1
    test_case = test_cases[0]
    assert len(test_case.statements) == 2
    assert not test_case.statements[-1].mutate()


@pytest.mark.parametrize(
    "test_cases_str",
    [
        (
            """def test_case_0():
    int_0 = 0
    var_0 = lambda x: x + 2

def test_case_1():
    int_0 = 0
    var_0 = lambda x: x + 'bar' """
        ),
        (
            """def test_case_0():
    int_0 = 0
    var_0 = lambda x: [x]

def test_case_1():
    int_0 = 0
    var_0 = lambda x: [x, x] """
        ),
        (
            """def test_case_0():
    int_0 = 0
    var_0 = lambda x: [x, int_0]

def test_case_1():
    int_0 = 0
    var_0 = lambda x: [x, x] """
        ),
        (
            """def test_case_0():
    int_0 = 0
    var_0 = lambda x: [x, int_0]

def test_case_1():
    int_0 = 0
    var_0 = {x for x in int_0} """
        ),
    ],
)
def test_not_equal_constants(test_cases_str):
    config.configuration.seeding.uninterpreted_statements = True
    config.configuration.seeding.include_partially_parsable = True

    # Dummy test cluster
    test_cluster = TestClusterGenerator(
        "tests.fixtures.grammar.parameters"
    ).generate_cluster()

    test_cases, _, _ = deserialize_code_to_testcases(test_cases_str, test_cluster)
    assert len(test_cases) == 2
    assert test_cases[0] != test_cases[1]


# End-to-end test of the ast assign statement's clone and eq. The first has no
# uninterpreted assigns, actually... just checking nothing is going wrong.
@pytest.mark.parametrize(
    "test_case_str",
    [
        (
            """def test_case_0():
    int_0 = 0
    int_1 = 1
    var_0 = module_0.positional_only(int_0, int_1)
    """
        ),
        (
            """def test_case_0():
    int_0 = 0
    int_1 = 1
    var_0 = lambda x: x + int_1
    """
        ),
        (
            """def test_case_0():
    int_0 = 0
    int_1 = 1
    var_0 = lambda *x, **y: x + int_1 + y
    """
        ),
    ],
)
def test_clone_eq_ast_assign_tc(test_case_str):
    config.configuration.seeding.uninterpreted_statements = True
    config.configuration.seeding.include_partially_parsable = True

    # Dummy test cluster
    test_cluster = TestClusterGenerator(
        "tests.fixtures.grammar.parameters"
    ).generate_cluster()

    test_cases, _, _ = deserialize_code_to_testcases(test_case_str, test_cluster)
    assert len(test_cases) == 1
    test_case = test_cases[0]
    assert len(test_case.statements) == 3
    clone_test_case = test_case.clone()
    assert clone_test_case is not test_case
    assert clone_test_case.__hash__() == test_case.__hash__()
    assert test_case == clone_test_case
