#  This file is part of Pynguin.
#
#  SPDX-FileCopyrightText: 2019–2022 Pynguin Contributors
#
#  SPDX-License-Identifier: LGPL-3.0-or-later
#
import pytest

from pynguin.generation.stoppingconditions.stoppingcondition import (
    MaxTestExecutionsStoppingCondition,
)


@pytest.fixture
def stopping_condition():
    return MaxTestExecutionsStoppingCondition()


def test_set_get_limit(stopping_condition):
    stopping_condition.set_limit(42)
    assert stopping_condition.limit() == 42


def test_is_not_fulfilled(stopping_condition):
    stopping_condition.reset()
    assert not stopping_condition.is_fulfilled()


def test_is_fulfilled(stopping_condition):
    stopping_condition.set_limit(1)
    stopping_condition.after_test_case_execution(None, None)
    stopping_condition.after_test_case_execution(None, None)
    assert stopping_condition.is_fulfilled()
