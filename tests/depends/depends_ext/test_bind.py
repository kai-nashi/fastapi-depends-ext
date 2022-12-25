import re

import pytest
from fastapi import Depends
from fastapi import params
from fastapi.dependencies.utils import get_typed_signature

from fastapi_depends_ext.depends import DependsExt


def test_bind__no_args__error():
    def endpoint():
        ...

    message = f"Trying to provide for method `{endpoint.__name__}` not existing keyword argument `arg`"
    with pytest.raises(KeyError, match=message):
        DependsExt(endpoint).bind(arg=Depends())


def test_bind__arg_no_default_depends__arg_has_default():
    def endpoint(arg: int):
        ...

    dependency = Depends()
    depends = DependsExt(endpoint).bind(arg=dependency)
    signature = get_typed_signature(depends.dependency)

    assert signature.parameters["arg"].default is dependency


@pytest.mark.parametrize(
    "dependency",
    [
        params.Depends(),
        params.Path(default=None),
        params.Query(default=None),
        params.Header(default=None),
        params.Cookie(default=None),
        params.Body(default=None),
        params.Form(default=None),
        params.File(default=None),
        params.Security(),
    ],
)
def test_bind__arg_change_default__arg_has_new_default(dependency):
    def endpoint(arg: int = None):
        return arg

    depends = DependsExt(endpoint).bind(arg=dependency)
    signature = get_typed_signature(depends.dependency)

    assert signature.parameters["arg"].default is dependency
    assert depends.dependency.__origin__ is endpoint
    assert depends.dependency() is dependency


def test_bind__multiple_args_depends_first__error():
    def endpoint(arg_0: int, arg_1: int):
        ...

    message = "Trying to set default for argument before arguments with default values"
    with pytest.raises(AttributeError, match=re.escape(message)):
        DependsExt(endpoint).bind(arg_0=Depends())


def test_bind__multiple_args_depends_second__second_arg_has_default():
    def endpoint(arg_0: int, arg_1: int):
        return arg_0, arg_1

    dependency = Depends()

    depends = DependsExt(endpoint).bind(arg_1=dependency)
    signature = get_typed_signature(depends.dependency)

    assert signature.parameters["arg_1"].default is dependency
    assert depends.dependency.__origin__ is endpoint
    assert depends.dependency(0) == (0, dependency)


def test_bind__multiple_args_depends_all__args_have_new_default():
    def endpoint(arg_0: int = None, arg_1: int = None):
        return arg_0, arg_1

    dependencies = (Depends(), Depends())
    depends = DependsExt(endpoint).bind(arg_0=dependencies[0], arg_1=dependencies[1])
    signature = get_typed_signature(depends.dependency)

    assert signature.parameters["arg_0"].default is dependencies[0]
    assert signature.parameters["arg_1"].default is dependencies[1]
    assert depends.dependency.__origin__ is endpoint
    assert depends.dependency() == dependencies


def test_bind__multiple_args_depends_partial__some_args_have_new_default():
    dependency_old = object()

    def endpoint(arg_0: int = dependency_old, arg_1: int = dependency_old, arg_2: int = dependency_old):
        return arg_0, arg_1, arg_2

    dependency = Depends()
    depends = DependsExt(endpoint).bind(arg_1=dependency)
    signature = get_typed_signature(depends.dependency)

    assert signature.parameters["arg_0"].default is dependency_old
    assert signature.parameters["arg_1"].default is dependency
    assert signature.parameters["arg_2"].default is dependency_old
    assert depends.dependency.__origin__ is endpoint
    assert depends.dependency() == (dependency_old, dependency, dependency_old)


def test_bind__depends_kwonly_arg__arg_have_new_default():
    def endpoint(*, arg: int = None):
        return arg

    dependency = Depends()
    depends = DependsExt(endpoint).bind(arg=dependency)
    signature = get_typed_signature(depends.dependency)

    assert signature.parameters["arg"].default is dependency
    assert depends.dependency.__origin__ is endpoint
    assert depends.dependency() is dependency
