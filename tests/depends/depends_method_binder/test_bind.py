import unittest.mock
from typing import Any

from fastapi import Depends
from fastapi.dependencies.utils import get_typed_signature

from fastapi_depends_ext.depends import DependsMethod
from fastapi_depends_ext.depends import DependsMethodBinder


class SimpleDependency:
    def dependency(self) -> int:
        return 2


def test_bind__method_has_no_depends__method_not_change(mocker):
    class TestClass(DependsMethodBinder):
        def method(self, arg=1, *args, kwarg=2, **kwargs):
            pass

    with mocker.patch.object(DependsMethodBinder, "__init__", unittest.mock.MagicMock(return_value=None)):
        instance = TestClass()
    instance.bind(instance.method)

    assert instance.method.__self__ is instance
    assert instance.method.__func__ is TestClass.method


def test_bind__method_has_depends__method_not_change(mocker):
    depends = Depends(SimpleDependency.dependency)

    class TestClass(SimpleDependency, DependsMethodBinder):
        def method(self, depends: Any = depends):
            pass

    with mocker.patch.object(DependsMethodBinder, "__init__", unittest.mock.MagicMock(return_value=None)):
        instance = TestClass()
    instance.bind(instance.method)

    assert instance.method.__self__ is instance
    assert instance.method.__func__ is TestClass.method
    assert instance.method.__func__.__code__ is TestClass.method.__code__

    signature = get_typed_signature(instance.method)
    assert signature.parameters["depends"].default is depends


def test_bind__method_has_depends_method__method_changed(mocker):
    depends = DependsMethod("dependency")

    class TestClass(SimpleDependency, DependsMethodBinder):
        def method(self, depends_method: Any = depends):
            pass

    with mocker.patch.object(DependsMethodBinder, "__init__", unittest.mock.MagicMock(return_value=None)):
        instance = TestClass()
    instance.bind(instance.method)

    assert instance.method.__self__ is instance
    assert instance.method.__func__ is not TestClass.method
    assert instance.method.__func__.__code__ is TestClass.method.__code__

    signature = get_typed_signature(instance.method)
    depends_method = signature.parameters["depends_method"]
    assert isinstance(depends_method.default, DependsMethod)
    assert depends_method.default is not depends
    assert depends_method.default.is_bound
    assert depends_method.default.dependency.__func__ is TestClass.dependency


def test_bind__method_has_depends_class_method__method_change(mocker):
    depends = DependsMethod("dependency")

    class TestClass(DependsMethodBinder):
        @classmethod
        def dependency(cls):
            pass

        def method(self, depends_method: Any = depends):
            pass

    with mocker.patch.object(DependsMethodBinder, "__init__", unittest.mock.MagicMock(return_value=None)):
        instance = TestClass()
    instance.bind(instance.method)

    assert instance.method.__self__ is instance
    assert instance.method.__func__ is not TestClass.method
    assert instance.method.__func__.__code__ is TestClass.method.__code__

    signature = get_typed_signature(instance.method)
    depends_method = signature.parameters["depends_method"]
    assert isinstance(depends_method.default, DependsMethod)
    assert depends_method.default is not depends
    assert depends_method.default.is_bound
    assert depends_method.default.dependency.__func__ is TestClass.dependency.__func__


def test_bind__method_has_depends_static_method__method_change(mocker):
    depends = DependsMethod("dependency")

    class TestClass(DependsMethodBinder):
        @staticmethod
        def dependency():
            pass

        def method(self, depends_method: Any = depends):
            pass

    with mocker.patch.object(DependsMethodBinder, "__init__", unittest.mock.MagicMock(return_value=None)):
        instance = TestClass()
    instance.bind(instance.method)

    assert instance.method.__self__ is instance
    assert instance.method.__func__ is not TestClass.method
    assert instance.method.__func__.__code__ is TestClass.method.__code__

    signature = get_typed_signature(instance.method)
    depends_method = signature.parameters["depends_method"]
    assert isinstance(depends_method.default, DependsMethod)
    assert depends_method.default is not depends
    assert depends_method.default.is_bound
    assert depends_method.default.dependency is TestClass.dependency


def test_bind__method_has_depends_method_chained__method_changed_all(mocker):
    depends = [DependsMethod("dependency"), DependsMethod("method_1")]

    class TestClass(SimpleDependency, DependsMethodBinder):
        def method_1(self, depends_method: Any = depends[0]):
            pass

        def method_2(self, depends_method: Any = depends[1]):
            pass

    with mocker.patch.object(DependsMethodBinder, "__init__", unittest.mock.MagicMock(return_value=None)):
        instance = TestClass()
    instance.bind(instance.method_2)

    # method_2
    assert instance.method_2.__self__ is instance
    assert instance.method_2.__func__ is not TestClass.method_2
    assert instance.method_2.__func__.__code__ is TestClass.method_2.__code__

    signature = get_typed_signature(instance.method_2)
    depends_method = signature.parameters["depends_method"]
    assert isinstance(depends_method.default, DependsMethod)
    assert depends_method.default is not depends[1]
    assert depends_method.default.is_bound
    assert depends_method.default.dependency.__self__ is instance
    assert depends_method.default.dependency.__func__ is instance.method_1.__func__
    assert depends_method.default.dependency.__func__.__code__ is instance.method_1.__func__.__code__

    # method_1
    signature = get_typed_signature(instance.method_1)
    depends_method = signature.parameters["depends_method"]
    assert isinstance(depends_method.default, DependsMethod)
    assert depends_method.default is not depends[0]
    assert depends_method.default.is_bound
    assert depends_method.default.dependency.__self__ is instance
    assert depends_method.default.dependency.__func__ is TestClass.dependency


def test_bind__method_has_depends_method_chained_to_super__method_changed_all(mocker):
    depends = DependsMethod("dependency", from_super=True)

    class BaseClass(SimpleDependency):
        pass

    class TestClass(BaseClass, DependsMethodBinder):
        def dependency(self, depends_method: Any = depends):
            pass

    with mocker.patch.object(DependsMethodBinder, "__init__", unittest.mock.MagicMock(return_value=None)):
        instance = TestClass()
    instance.bind(instance.dependency)

    # TestClass.dependency
    assert instance.dependency.__self__ is instance
    assert instance.dependency.__func__ is not TestClass.dependency
    assert instance.dependency.__func__.__code__ is TestClass.dependency.__code__

    signature = get_typed_signature(instance.dependency)
    depends_method = signature.parameters["depends_method"]
    assert isinstance(depends_method.default, DependsMethod)
    assert depends_method.default is not depends
    assert depends_method.default.is_bound
    assert depends_method.default.dependency.__self__ is instance
    assert depends_method.default.dependency.__func__ is BaseClass.dependency


def test_bind__method_has_depends_method_chained_to_super_deep__method_changed_all(mocker):
    depends = DependsMethod("dependency", from_super=True)
    depends_mixin = DependsMethod("dependency", from_super=True)

    class BaseClass(SimpleDependency):
        def dependency(self, depends_method: Any = depends_mixin):
            pass

    class TestClass(BaseClass, DependsMethodBinder):
        def dependency(self, depends_method: Any = depends):
            pass

    with mocker.patch.object(DependsMethodBinder, "__init__", unittest.mock.MagicMock(return_value=None)):
        instance = TestClass()
    instance.bind(instance.dependency)

    # TestClass.dependency
    assert instance.dependency.__self__ is instance
    assert instance.dependency.__func__ is not TestClass.dependency
    assert instance.dependency.__func__.__code__ is TestClass.dependency.__code__

    signature = get_typed_signature(instance.dependency)
    depends_method = signature.parameters["depends_method"]
    assert isinstance(depends_method.default, DependsMethod)
    assert depends_method.default is not depends
    assert depends_method.default.is_bound
    assert depends_method.default.dependency.__self__ is instance
    assert depends_method.default.dependency.__func__ is not BaseClass.dependency
    assert depends_method.default.dependency.__func__.__code__ is BaseClass.dependency.__code__

    # Mixin.dependency
    signature = get_typed_signature(depends_method.default.dependency)
    depends_method = signature.parameters["depends_method"]
    assert isinstance(depends_method.default, DependsMethod)
    assert depends_method.default is not depends
    assert depends_method.default.is_bound
    assert depends_method.default.dependency.__self__ is instance
    assert depends_method.default.dependency.__func__ is SimpleDependency.dependency


# todo
# def test_bind__multiple_method_depends_one_method__depends_is_one_object():
#     raise ValueError()
