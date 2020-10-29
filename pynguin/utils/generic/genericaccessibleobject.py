#  This file is part of Pynguin.
#
#  SPDX-FileCopyrightText: 2019–2020 Pynguin Contributors
#
#  SPDX-License-Identifier: LGPL-3.0-or-later
#
"""
Provide wrappers around constructors, methods, function and fields.
Think of these like the reflection classes in Java.
"""
import abc
from typing import Callable, Optional, Set, Type

from pynguin.typeinference.strategy import InferredSignature


class GenericAccessibleObject(metaclass=abc.ABCMeta):
    """Abstract base class for something that can be accessed."""

    def __init__(self, owner: Optional[Type]):
        self._owner = owner

    @abc.abstractmethod
    def generated_type(self) -> Optional[Type]:
        """Provides the type that is generated by this accessible object.

        Returns:
            The generated type  # noqa: DAR202
        """

    @property
    def owner(self) -> Optional[Type]:
        """The type which owns this accessible object.

        Returns:
            The owner of this accessible object
        """
        return self._owner

    # pylint: disable=no-self-use
    def is_method(self) -> bool:
        """Is this a method?

        Returns:
            Whether or not this is a method
        """
        return False

    # pylint: disable=no-self-use
    def is_constructor(self) -> bool:
        """Is this a constructor?

        Returns:
            Whether or not this is a constructor
        """
        return False

    # pylint: disable=no-self-use
    def is_function(self) -> bool:
        """Is this a function?

        Returns:
            Whether or not this is a function
        """
        return False

    # pylint: disable=no-self-use
    def is_field(self) -> bool:
        """Is this a field?

        Returns:
            Whether or not this is a field
        """
        return False

    # pylint: disable=no-self-use
    def get_num_parameters(self) -> int:
        """Number of parameters.

        Returns:
            The number of parameters
        """
        return 0

    @abc.abstractmethod
    def get_dependencies(self) -> Set[Type]:
        """A set of types that are required to use this accessible.

        Returns:
            A set of types  # noqa: DAR202
        """


class GenericCallableAccessibleObject(
    GenericAccessibleObject, metaclass=abc.ABCMeta
):  # pylint: disable=W0223
    """Abstract base class for something that can be called."""

    def __init__(
        self,
        owner: Optional[Type],
        callable_: Callable,
        inferred_signature: InferredSignature,
    ) -> None:
        super().__init__(owner)
        self._callable = callable_
        self._inferred_signature = inferred_signature

    def generated_type(self) -> Optional[Type]:
        return self._inferred_signature.return_type

    @property
    def inferred_signature(self) -> InferredSignature:
        """Provides access to the inferred type signature information.

        Returns:
            The inferred type signature
        """
        return self._inferred_signature

    @property
    def callable(self) -> Callable:
        """Provides the callable.

        Returns:
            The callable
        """
        return self._callable

    def get_num_parameters(self) -> int:
        return len(self.inferred_signature.parameters)

    def get_dependencies(self) -> Set[Type]:
        return {
            value
            for value in self.inferred_signature.parameters.values()
            if value is not None
        }


class GenericConstructor(GenericCallableAccessibleObject):
    """A constructor."""

    def __init__(self, owner: Type, inferred_signature: InferredSignature) -> None:
        super().__init__(owner, owner.__init__, inferred_signature)
        assert owner

    def generated_type(self) -> Optional[Type]:
        return self.owner

    def is_constructor(self) -> bool:
        return True

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, GenericConstructor):
            return False
        return self._owner == other._owner

    def __hash__(self):
        return hash(self._owner)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.owner}, {self.inferred_signature})"


class GenericMethod(GenericCallableAccessibleObject):
    """A method."""

    def __init__(
        self, owner: Type, method: Callable, inferred_signature: InferredSignature
    ) -> None:
        super().__init__(owner, method, inferred_signature)
        assert owner

    def is_method(self) -> bool:
        return True

    def get_dependencies(self) -> Set[Type]:
        assert self.owner, "Method must have an owner"
        dependencies = super().get_dependencies()
        dependencies.add(self.owner)
        return dependencies

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, GenericMethod):
            return False
        return self._callable == other._callable

    def __hash__(self):
        return hash(self._callable)

    def __repr__(self):
        return (
            f"{self.__class__.__name__}({self.owner},"
            + f" {self._callable.__name__}, {self.inferred_signature})"
        )


class GenericFunction(GenericCallableAccessibleObject):
    """A function, which does not belong to any class."""

    def __init__(
        self, function: Callable, inferred_signature: InferredSignature
    ) -> None:
        super().__init__(None, function, inferred_signature)

    def is_function(self) -> bool:
        return True

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, GenericFunction):
            return False
        return self._callable == other._callable

    def __hash__(self):
        return hash(self._callable)

    def __repr__(self):
        return (
            f"{self.__class__.__name__}({self._callable.__name__}, "
            + f"{self.inferred_signature})"
        )


class GenericField(GenericAccessibleObject):
    """A field."""

    def __init__(self, owner: Type, field: str, field_type: Optional[Type]) -> None:
        super().__init__(owner)
        self._field = field
        self._field_type = field_type

    def is_field(self) -> bool:
        return True

    def get_dependencies(self) -> Set[Type]:
        assert self.owner, "Field must have an owner"
        return {self.owner}

    def generated_type(self) -> Optional[Type]:
        return self._field_type

    @property
    def field(self) -> str:
        """Provides the name of the field.

        Returns:
            The name of the field
        """
        return self._field

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, GenericField):
            return False
        return self._owner == other._owner and self._field == self._field

    def __hash__(self):
        return 31 + 17 * hash(self._owner) + 17 * hash(self._field)

    def __repr__(self):
        return (
            f"{self.__class__.__name__}({self.owner}, {self._field},"
            + f" {self._field_type})"
        )
