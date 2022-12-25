import inspect
import re

import pytest
from fastapi.dependencies.utils import get_typed_signature

from fastapi_depends_ext.utils import patch_defaults


def test_patch_defaults__no_changes__clone_of_function():
    def test_function(a, b: int, c: int = 1, *args, d: int = 2, **kwargs):
        """doc string"""
        pass

    func = patch_defaults(test_function)

    assert func is not test_function
    assert inspect.isfunction(func)

    assert func.__code__ is test_function.__code__
    assert func.__globals__ is test_function.__globals__
    assert func.__name__ is test_function.__name__
    assert func.__closure__ is test_function.__closure__
    assert func.__defaults__ is not test_function.__defaults__
    assert func.__defaults__ == test_function.__defaults__
    assert func.__kwdefaults__ is not test_function.__kwdefaults__
    assert func.__kwdefaults__ == test_function.__kwdefaults__


def test_patch_defaults__no_changes__clone_of_bound_method():
    class TestClass:
        def test_function(self, a, b: int, c: int = 1, *args, d: int = 2, **kwargs):
            """doc string"""
            pass

    instance = TestClass()
    method = patch_defaults(instance.test_function)

    assert inspect.ismethod(method)
    assert method.__self__ is instance
    assert method.__func__ is not instance.test_function.__func__

    assert method.__code__ is TestClass.test_function.__code__
    assert method.__globals__ is TestClass.test_function.__globals__
    assert method.__name__ is TestClass.test_function.__name__
    assert method.__closure__ is TestClass.test_function.__closure__
    assert method.__defaults__ is not TestClass.test_function.__defaults__
    assert method.__defaults__ == TestClass.test_function.__defaults__
    assert method.__kwdefaults__ is not TestClass.test_function.__kwdefaults__
    assert method.__kwdefaults__ == TestClass.test_function.__kwdefaults__


def test_patch_defaults__no_changes__clone_of_unbound_method():
    class TestClass:
        def test_function(self, a, b: int, c: int = 1, *args, d: int = 2, **kwargs):
            """doc string"""
            pass

    func = patch_defaults(TestClass.test_function)

    assert func is not TestClass.test_function
    assert inspect.isfunction(func)

    assert func.__code__ is TestClass.test_function.__code__
    assert func.__globals__ is TestClass.test_function.__globals__
    assert func.__name__ is TestClass.test_function.__name__
    assert func.__closure__ is TestClass.test_function.__closure__
    assert func.__defaults__ is not TestClass.test_function.__defaults__
    assert func.__defaults__ == TestClass.test_function.__defaults__
    assert func.__kwdefaults__ is not TestClass.test_function.__kwdefaults__
    assert func.__kwdefaults__ == TestClass.test_function.__kwdefaults__


def test_patch_defaults__no_changes__clone_of_class_method():
    class TestClass:
        @classmethod
        def test_function(cls, a, b: int, c: int = 1, *args, d: int = 2, **kwargs):
            """doc string"""
            pass

    method = patch_defaults(TestClass.test_function)

    assert method is not TestClass.test_function
    assert inspect.ismethod(method)

    assert method.__code__ is TestClass.test_function.__func__.__code__
    assert method.__globals__ is TestClass.test_function.__func__.__globals__
    assert method.__name__ is TestClass.test_function.__func__.__name__
    assert method.__closure__ is TestClass.test_function.__func__.__closure__
    assert method.__defaults__ is not TestClass.test_function.__func__.__defaults__
    assert method.__defaults__ == TestClass.test_function.__func__.__defaults__
    assert method.__kwdefaults__ is not TestClass.test_function.__func__.__kwdefaults__
    assert method.__kwdefaults__ == TestClass.test_function.__func__.__kwdefaults__


def test_patch_defaults__no_changes__clone_of_static_method():
    class TestClass:
        @staticmethod
        def test_function(a, b: int, c: int = 1, *args, d: int = 2, **kwargs):
            """doc string"""
            pass

    func = patch_defaults(TestClass.test_function)

    assert func is not TestClass.test_function
    assert inspect.isfunction(func)

    assert func.__code__ is TestClass.test_function.__code__
    assert func.__globals__ is TestClass.test_function.__globals__
    assert func.__name__ is TestClass.test_function.__name__
    assert func.__closure__ is TestClass.test_function.__closure__
    assert func.__defaults__ is not TestClass.test_function.__defaults__
    assert func.__defaults__ == TestClass.test_function.__defaults__
    assert func.__kwdefaults__ is not TestClass.test_function.__kwdefaults__
    assert func.__kwdefaults__ == TestClass.test_function.__kwdefaults__


def test_patch_defaults__change_not_exist_arg__error():
    def test_function():
        pass

    message = "Trying to provide for method `test_function` not existing keyword argument `argument`"
    with pytest.raises(KeyError, match=re.escape(message)):
        patch_defaults(test_function, argument=1)


def test_patch_defaults__change_not_exist_kwarg__error():
    def test_function(*, a=1):
        pass

    message = "Trying to provide for method `test_function` not existing keyword argument `argument`"
    with pytest.raises(KeyError, match=re.escape(message)):
        patch_defaults(test_function, argument=1)


def test_patch_defaults__change_arg_no_default__patched():
    def test_function(a):
        pass

    expected_value = object()
    func = patch_defaults(test_function, a=expected_value)

    signature = get_typed_signature(test_function)
    assert signature.parameters["a"].default is inspect._empty

    signature = get_typed_signature(func)
    assert signature.parameters["a"].default is expected_value


def test_patch_defaults__change_typed_arg_no_default__patched():
    def test_function(a: int):
        pass

    expected_value = object()
    func = patch_defaults(test_function, a=expected_value)

    signature = get_typed_signature(test_function)
    assert signature.parameters["a"].default is inspect._empty

    signature = get_typed_signature(func)
    assert signature.parameters["a"].default is expected_value


def test_patch_defaults__change_typed_arg__patched():
    def test_function(a: int = 1):
        pass

    expected_value = object()
    func = patch_defaults(test_function, a=expected_value)

    signature = get_typed_signature(test_function)
    assert signature.parameters["a"].default == 1

    signature = get_typed_signature(func)
    assert signature.parameters["a"].default is expected_value


def test_patch_defaults__change_typed_arg_no_default_pos_only__patched():
    def test_function(a: int, *args):
        pass

    expected_value = object()
    func = patch_defaults(test_function, a=expected_value)

    signature = get_typed_signature(test_function)
    assert signature.parameters["a"].default is inspect._empty

    signature = get_typed_signature(func)
    assert signature.parameters["a"].default is expected_value


def test_patch_defaults__change_typed_arg_pos_only__patched():
    def test_function(a: int = 1, *args):
        pass

    expected_value = object()
    func = patch_defaults(test_function, a=expected_value)

    signature = get_typed_signature(test_function)
    assert signature.parameters["a"].default == 1

    signature = get_typed_signature(func)
    assert signature.parameters["a"].default is expected_value


def test_patch_defaults__change_multiple_args__patched():
    def test_function(a: int, b: int):
        pass

    expected_value = object()
    func = patch_defaults(test_function, a=expected_value, b=expected_value)

    signature = get_typed_signature(test_function)
    assert signature.parameters["a"].default is inspect._empty
    assert signature.parameters["b"].default is inspect._empty

    signature = get_typed_signature(func)
    assert signature.parameters["a"].default is expected_value
    assert signature.parameters["b"].default is expected_value


def test_patch_defaults__change_partial_default_args__patched():
    def test_function(a: int, b: int = None, c: int = None):
        pass

    expected_value = object()
    func = patch_defaults(test_function, c=expected_value)

    signature = get_typed_signature(test_function)
    assert signature.parameters["a"].default is inspect._empty
    assert signature.parameters["b"].default is None
    assert signature.parameters["c"].default is None

    signature = get_typed_signature(func)
    assert signature.parameters["a"].default is inspect._empty
    assert signature.parameters["b"].default is None
    assert signature.parameters["c"].default is expected_value


def test_patch_defaults__change_partial_args_not_trailing__patched():
    def test_function(a: int, b: int = None, c: int = None):
        pass

    expected_value = object()
    func = patch_defaults(test_function, b=expected_value)

    signature = get_typed_signature(test_function)
    assert signature.parameters["a"].default is inspect._empty
    assert signature.parameters["b"].default is None
    assert signature.parameters["c"].default is None

    signature = get_typed_signature(func)
    assert signature.parameters["a"].default is inspect._empty
    assert signature.parameters["b"].default is expected_value
    assert signature.parameters["c"].default is None


def test_patch_defaults__change_broke_arguments_order__error():
    def test_function(a: int, b: int):
        pass

    message = "Trying to set default for argument before arguments with default values"
    with pytest.raises(AttributeError, match=re.escape(message)):
        patch_defaults(test_function, a=1)


def test_patch_defaults__change_kwonly_no_defaults__patched():
    def test_function(a: int, *, kwonly, **kwargs):
        pass

    expected_value = object()
    func = patch_defaults(test_function, kwonly=expected_value)

    signature = get_typed_signature(test_function)
    assert signature.parameters["kwonly"].default is inspect._empty

    signature = get_typed_signature(func)
    assert signature.parameters["kwonly"].default is expected_value


def test_patch_defaults__change_typed_kwonly_no_defaults__patched():
    def test_function(a: int, *, kwonly: int, **kwargs):
        pass

    expected_value = object()
    func = patch_defaults(test_function, kwonly=expected_value)

    signature = get_typed_signature(test_function)
    assert signature.parameters["kwonly"].default is inspect._empty

    signature = get_typed_signature(func)
    assert signature.parameters["kwonly"].default is expected_value


def test_patch_defaults__change_kwonly__patched():
    def test_function(a: int, *, kwonly: int = 1, **kwargs):
        pass

    expected_value = object()
    func = patch_defaults(test_function, kwonly=expected_value)

    signature = get_typed_signature(test_function)
    assert signature.parameters["kwonly"].default == 1

    signature = get_typed_signature(func)
    assert signature.parameters["kwonly"].default is expected_value


def test_patch_defaults__change_kwonly_after_args__patched():
    def test_function(a: int, *args, kwonly: int = 1, **kwargs):
        pass

    expected_value = object()
    func = patch_defaults(test_function, kwonly=expected_value)

    signature = get_typed_signature(test_function)
    assert signature.parameters["kwonly"].default == 1

    signature = get_typed_signature(func)
    assert signature.parameters["kwonly"].default is expected_value
