#  This file is part of Pynguin.
#
#  SPDX-FileCopyrightText: 2019–2022 Pynguin Contributors
#
#  SPDX-License-Identifier: LGPL-3.0-or-later
#
"""Provides the CodaMOSA test-generation strategy."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, cast

from ordered_set import OrderedSet

import pynguin.configuration as config
import pynguin.ga.computations as ff
import pynguin.ga.testcasechromosome as tcc
import pynguin.utils.statistics.statistics as stat
from pynguin.analyses.seeding import languagemodelseeding
from pynguin.ga.operators.ranking.crowdingdistance import (
    fast_epsilon_dominance_assignment,
)
from pynguin.generation.algorithms.abstractmosastrategy import AbstractMOSATestStrategy
from pynguin.utils import randomness
from pynguin.utils.statistics.runtimevariable import RuntimeVariable

if TYPE_CHECKING:
    import pynguin.ga.testsuitechromosome as tsc


# pylint: disable=too-many-instance-attributes
class CodaMOSATestStrategy(AbstractMOSATestStrategy):
    """MOSA + Regular seeding by large language model."""

    _logger = logging.getLogger(__name__)

    def generate_tests(self) -> tsc.TestSuiteChromosome:
        self.before_search_start()
        self._number_of_goals = len(self._test_case_fitness_functions)
        stat.set_output_variable_for_runtime_variable(
            RuntimeVariable.Goals, self._number_of_goals
        )

        self._population = self._get_random_population()
        self._archive.update(self._population)

        # Calculate dominance ranks and crowding distance
        fronts = self._ranking_function.compute_ranking_assignment(
            self._population, self._archive.uncovered_goals  # type: ignore
        )
        for i in range(fronts.get_number_of_sub_fronts()):
            fast_epsilon_dominance_assignment(
                fronts.get_sub_front(i), self._archive.uncovered_goals  # type: ignore
            )

        self.before_first_search_iteration(
            self.create_test_suite(self._archive.solutions)
        )

        last_num_covered_goals = len(self._archive.covered_goals)
        its_without_update = 0
        while (
            self.resources_left()
            and self._number_of_goals - len(self._archive.covered_goals) != 0
        ):
            num_covered_goals = len(self._archive.covered_goals)
            if num_covered_goals == last_num_covered_goals:
                its_without_update += 1
            else:
                its_without_update = 0
            last_num_covered_goals = num_covered_goals
            if its_without_update > 25:
                its_without_update = 0
                self.evolve_targeted(self.create_test_suite(self._archive.solutions))
            else:
                self.evolve()
            self.after_search_iteration(self.create_test_suite(self._archive.solutions))

        self.after_search_finish()
        return self.create_test_suite(
            self._archive.solutions
            if len(self._archive.solutions) > 0
            else self._get_best_individuals()
        )

    def evolve_targeted(self, test_suite: tsc.TestSuiteChromosome):
        """Runs an evolution step that targets uncovered functions.

        Args:
            test_suite: the test suite to base coverage off of.
        """
        test_cases = languagemodelseeding.target_uncovered_functions(test_suite, 10)
        test_case_chromosomes = [
            tcc.TestCaseChromosome(test_case, self.test_factory)
            for test_case in test_cases
        ]
        while (
            len(test_case_chromosomes)
            < config.configuration.search_algorithm.population
        ):
            to_mutate = randomness.choice(test_cases)
            offspring = cast(tcc.TestCaseChromosome, to_mutate.clone())
            self._mutate(offspring)
            if offspring.has_changed() and offspring.size() > 0:
                test_case_chromosomes.append(offspring)

        self.evolve_common(test_cases)

    def evolve(self) -> None:
        """Runs one evolution step."""
        offspring_population = self._breed_next_generation()
        self.evolve_common(offspring_population)

    def evolve_common(self, offspring_population) -> None:
        """The core logic to save offspring if they are interesting.

        Args:
            offspring_population: the offspring to try and save
        """

        # Create union of parents and offspring
        union: list[tcc.TestCaseChromosome] = []
        union.extend(self._population)
        union.extend(offspring_population)

        uncovered_goals: OrderedSet[
            ff.FitnessFunction
        ] = self._archive.uncovered_goals  # type: ignore

        # Ranking the union
        self._logger.debug("Union Size = %d", len(union))
        # Ranking the union using the best rank algorithm
        fronts = self._ranking_function.compute_ranking_assignment(
            union, uncovered_goals
        )

        remain = len(self._population)
        index = 0
        self._population.clear()

        # Obtain the next front
        front = fronts.get_sub_front(index)

        while remain > 0 and remain >= len(front) != 0:
            # Assign crowding distance to individuals
            fast_epsilon_dominance_assignment(front, uncovered_goals)
            # Add the individuals of this front
            self._population.extend(front)
            # Decrement remain
            remain -= len(front)
            # Obtain the next front
            index += 1
            if remain > 0:
                front = fronts.get_sub_front(index)

        # Remain is less than len(front[index]), insert only the best one
        if remain > 0 and len(front) != 0:
            fast_epsilon_dominance_assignment(front, uncovered_goals)
            front.sort(key=lambda t: t.distance, reverse=True)
            for k in range(remain):
                self._population.append(front[k])

        self._archive.update(self._population)
