"""Asymmetric descriptor protocol for typehinting properties that can be read and written differently."""

__all__ = [
    "AsymmetricDescriptor",
]

from typing import Protocol, Self, TypeVar, overload

_GT = TypeVar("_GT", covariant=True)
_ST = TypeVar("_ST", contravariant=True)


class AsymmetricDescriptor(Protocol[_GT, _ST]):
    """
    A protocol for asymmetric descriptors, supporting different types for getting and setting values.

    Type Parameters:
        _GT: The type returned by __get__ when accessed via an instance.
        _ST: The type accepted by __set__ when assigning a value.

    Methods:
        __get__(self, instance: None, owner: type[object]) -> Self:
            Returns the descriptor itself when accessed through the class.

        __get__(self, instance: object, owner: type[object]) -> _GT:
            Returns the value associated with the instance when accessed through an instance.

        __set__(self, instance: object, value: _ST) -> None:
            Sets the value associated with the instance.
    """

    @overload
    def __get__(self, instance: None, owner: type[object]) -> Self: ...
    @overload
    def __get__(self, instance: object, owner: type[object]) -> _GT: ...

    def __set__(self, instance: object, value: _ST) -> None: ...
