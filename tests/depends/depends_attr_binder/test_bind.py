import unittest.mock
from typing import Any

from fastapi import Depends
from fastapi.dependencies.utils import get_typed_signature

from fastapi_depends_ext.depends import DependsAttr
from fastapi_depends_ext.depends import DependsAttrBinder
from tests.utils_for_tests import SimpleDependency


def test_bind__method_has_no_depends__method_not_change(mocker):
    class TestClass(DependsAttrBinder):
        def method(self, arg=1, *args, kwarg=2, **kwargs):
            pass

    with mocker.patch.object(DependsAttrBinder, "__init__", unittest.mock.MagicMock(return_value=None)):
        instance = TestClass()
    instance.bind(instance.method)

    assert instance.method.__self__ is instance
    assert instance.method.__func__ is TestClass.method


def test_bind__method_has_depends__method_not_change(mocker):
    depends = Depends(SimpleDependency.dependency)

    class TestClass(SimpleDependency, DependsAttrBinder):
        def method(self, depends: Any = depends):
            pass

    with mocker.patch.object(DependsAttrBinder, "__init__", unittest.mock.MagicMock(return_value=None)):
        instance = TestClass()
    instance.bind(instance.method)

    assert instance.method.__self__ is instance
    assert instance.method.__func__ is TestClass.method
    assert instance.method.__func__.__code__ is TestClass.method.__code__

    signature = get_typed_signature(instance.method)
    assert signature.parameters["depends"].default is depends


def test_bind__method_has_depends_method__method_changed(mocker):
    depends = DependsAttr("dependency")

    class TestClass(SimpleDependency, DependsAttrBinder):
        def method(self, depends_attr: Any = depends):
            pass

    with mocker.patch.object(DependsAttrBinder, "__init__", unittest.mock.MagicMock(return_value=None)):
        instance = TestClass()
    instance.bind(instance.method)

    assert instance.method.__self__ is instance
    assert instance.method.__func__ is not TestClass.method
    assert instance.method.__func__.__code__ is TestClass.method.__code__

    signature = get_typed_signature(instance.method)
    depends_attr = signature.parameters["depends_attr"]
    assert isinstance(depends_attr.default, DependsAttr)
    assert depends_attr.default is not depends
    assert depends_attr.default.is_bound
    assert depends_attr.default.dependency.__func__ is TestClass.dependency


def test_bind__method_has_depends_class_method__method_change(mocker):
    depends = DependsAttr("dependency")

    class TestClass(DependsAttrBinder):
        @classmethod
        def dependency(cls):
            pass

        def method(self, depends_attr: Any = depends):
            pass

    with mocker.patch.object(DependsAttrBinder, "__init__", unittest.mock.MagicMock(return_value=None)):
        instance = TestClass()
    instance.bind(instance.method)

    assert instance.method.__self__ is instance
    assert instance.method.__func__ is not TestClass.method
    assert instance.method.__func__.__code__ is TestClass.method.__code__

    signature = get_typed_signature(instance.method)
    depends_attr = signature.parameters["depends_attr"]
    assert isinstance(depends_attr.default, DependsAttr)
    assert depends_attr.default is not depends
    assert depends_attr.default.is_bound
    assert depends_attr.default.dependency.__func__ is TestClass.dependency.__func__


def test_bind__method_has_depends_static_method__method_change(mocker):
    depends = DependsAttr("dependency")

    class TestClass(DependsAttrBinder):
        @staticmethod
        def dependency():
            pass

        def method(self, depends_attr: Any = depends):
            pass

    with mocker.patch.object(DependsAttrBinder, "__init__", unittest.mock.MagicMock(return_value=None)):
        instance = TestClass()
    instance.bind(instance.method)

    assert instance.method.__self__ is instance
    assert instance.method.__func__ is not TestClass.method
    assert instance.method.__func__.__code__ is TestClass.method.__code__

    signature = get_typed_signature(instance.method)
    depends_attr = signature.parameters["depends_attr"]
    assert isinstance(depends_attr.default, DependsAttr)
    assert depends_attr.default is not depends
    assert depends_attr.default.is_bound
    assert depends_attr.default.dependency is TestClass.dependency


def test_bind__method_has_depends_property__method_change(mocker):
    depends = DependsAttr("dependency")

    def real_dependency():
        return 1

    class TestClass(DependsAttrBinder):
        @property
        def dependency(self):
            return real_dependency

        def method(self, depends_attr: Any = depends):
            pass

    with mocker.patch.object(DependsAttrBinder, "__init__", unittest.mock.MagicMock(return_value=None)):
        instance = TestClass()
    instance.bind(instance.method)

    assert instance.method.__self__ is instance
    assert instance.method.__func__ is not TestClass.method
    assert instance.method.__func__.__code__ is TestClass.method.__code__

    signature = get_typed_signature(instance.method)
    depends_attr = signature.parameters["depends_attr"]
    assert isinstance(depends_attr.default, DependsAttr)
    assert depends_attr.default is not depends
    assert depends_attr.default.is_bound
    assert depends_attr.default.dependency is real_dependency


def test_bind__method_has_depends_class__method_change(mocker):
    depends = DependsAttr("dependency")

    class Dependency:
        pass

    class TestClass(DependsAttrBinder):
        dependency = Dependency

        def method(self, depends_attr: Any = depends):
            pass

    with mocker.patch.object(DependsAttrBinder, "__init__", unittest.mock.MagicMock(return_value=None)):
        instance = TestClass()
    instance.bind(instance.method)

    assert instance.method.__self__ is instance
    assert instance.method.__func__ is not TestClass.method
    assert instance.method.__func__.__code__ is TestClass.method.__code__

    signature = get_typed_signature(instance.method)
    depends_attr = signature.parameters["depends_attr"]
    assert isinstance(depends_attr.default, DependsAttr)
    assert depends_attr.default is not depends
    assert depends_attr.default.is_bound
    assert depends_attr.default.dependency is Dependency


def test_bind__method_has_depends_callable__method_change(mocker):
    depends = DependsAttr("dependency")

    class Dependency:
        def __call__(self):
            return 1

    class TestClass(DependsAttrBinder):
        dependency = Dependency()

        def method(self, depends_attr: Any = depends):
            pass

    with mocker.patch.object(DependsAttrBinder, "__init__", unittest.mock.MagicMock(return_value=None)):
        instance = TestClass()
    instance.bind(instance.method)

    assert instance.method.__self__ is instance
    assert instance.method.__func__ is not TestClass.method
    assert instance.method.__func__.__code__ is TestClass.method.__code__

    signature = get_typed_signature(instance.method)
    depends_attr = signature.parameters["depends_attr"]
    assert isinstance(depends_attr.default, DependsAttr)
    assert depends_attr.default is not depends
    assert depends_attr.default.is_bound
    assert depends_attr.default.dependency is TestClass.dependency


def test_bind__method_has_depends_instance_defined_variable__method_change(mocker):
    depends = DependsAttr("dependency")

    class Dependency:
        def __call__(self):
            return 1

    class TestClass(DependsAttrBinder):
        dependency: Dependency

        def __init__(self, *args, **kwargs):
            self.dependency = Dependency()
            super(TestClass, self).__init__(*args, **kwargs)

        def method(self, depends_attr: Any = depends):
            pass

    with mocker.patch.object(DependsAttrBinder, "__init__", unittest.mock.MagicMock(return_value=None)):
        instance = TestClass()
    instance.bind(instance.method)

    assert instance.method.__self__ is instance
    assert instance.method.__func__ is not TestClass.method
    assert instance.method.__func__.__code__ is TestClass.method.__code__

    signature = get_typed_signature(instance.method)
    depends_attr = signature.parameters["depends_attr"]
    assert isinstance(depends_attr.default, DependsAttr)
    assert depends_attr.default is not depends
    assert depends_attr.default.is_bound
    assert depends_attr.default.dependency is instance.dependency


def test_bind__method_has_depends_method_chained__method_changed_all(mocker):
    depends = [DependsAttr("dependency"), DependsAttr("method_1")]

    class TestClass(SimpleDependency, DependsAttrBinder):
        def method_1(self, depends_attr: Any = depends[0]):
            pass

        def method_2(self, depends_attr: Any = depends[1]):
            pass

    with mocker.patch.object(DependsAttrBinder, "__init__", unittest.mock.MagicMock(return_value=None)):
        instance = TestClass()
    instance.bind(instance.method_2)

    # method_2
    assert instance.method_2.__self__ is instance
    assert instance.method_2.__func__ is not TestClass.method_2
    assert instance.method_2.__func__.__code__ is TestClass.method_2.__code__

    signature = get_typed_signature(instance.method_2)
    depends_attr = signature.parameters["depends_attr"]
    assert isinstance(depends_attr.default, DependsAttr)
    assert depends_attr.default is not depends[1]
    assert depends_attr.default.is_bound
    assert depends_attr.default.dependency.__self__ is instance
    assert depends_attr.default.dependency.__func__ is instance.method_1.__func__
    assert depends_attr.default.dependency.__func__.__code__ is instance.method_1.__func__.__code__

    # method_1
    signature = get_typed_signature(instance.method_1)
    depends_attr = signature.parameters["depends_attr"]
    assert isinstance(depends_attr.default, DependsAttr)
    assert depends_attr.default is not depends[0]
    assert depends_attr.default.is_bound
    assert depends_attr.default.dependency.__self__ is instance
    assert depends_attr.default.dependency.__func__ is TestClass.dependency


def test_bind__method_has_depends_method_chained_to_super__method_changed_all(mocker):
    depends = DependsAttr("dependency", from_super=True)

    class BaseClass(SimpleDependency):
        pass

    class TestClass(BaseClass, DependsAttrBinder):
        def dependency(self, depends_attr: Any = depends):
            pass

    with mocker.patch.object(DependsAttrBinder, "__init__", unittest.mock.MagicMock(return_value=None)):
        instance = TestClass()
    instance.bind(instance.dependency)

    # TestClass.dependency
    assert instance.dependency.__self__ is instance
    assert instance.dependency.__func__ is not TestClass.dependency
    assert instance.dependency.__func__.__code__ is TestClass.dependency.__code__

    signature = get_typed_signature(instance.dependency)
    depends_attr = signature.parameters["depends_attr"]
    assert isinstance(depends_attr.default, DependsAttr)
    assert depends_attr.default is not depends
    assert depends_attr.default.is_bound
    assert depends_attr.default.dependency.__self__ is instance
    assert depends_attr.default.dependency.__func__ is BaseClass.dependency


def test_bind__method_has_depends_method_chained_to_super_deep__method_changed_all(mocker):
    depends = DependsAttr("dependency", from_super=True)
    depends_mixin = DependsAttr("dependency", from_super=True)

    class BaseClass(SimpleDependency):
        def dependency(self, depends_attr: Any = depends_mixin):
            pass

    class TestClass(BaseClass, DependsAttrBinder):
        def dependency(self, depends_attr: Any = depends):
            pass

    with mocker.patch.object(DependsAttrBinder, "__init__", unittest.mock.MagicMock(return_value=None)):
        instance = TestClass()
    instance.bind(instance.dependency)

    # TestClass.dependency
    assert instance.dependency.__self__ is instance
    assert instance.dependency.__func__ is not TestClass.dependency
    assert instance.dependency.__func__.__code__ is TestClass.dependency.__code__

    signature = get_typed_signature(instance.dependency)
    depends_attr = signature.parameters["depends_attr"]
    assert isinstance(depends_attr.default, DependsAttr)
    assert depends_attr.default is not depends
    assert depends_attr.default.is_bound
    assert depends_attr.default.dependency.__self__ is instance
    assert depends_attr.default.dependency.__func__ is not BaseClass.dependency
    assert depends_attr.default.dependency.__func__.__code__ is BaseClass.dependency.__code__

    # Mixin.dependency
    signature = get_typed_signature(depends_attr.default.dependency)
    depends_attr = signature.parameters["depends_attr"]
    assert isinstance(depends_attr.default, DependsAttr)
    assert depends_attr.default is not depends
    assert depends_attr.default.is_bound
    assert depends_attr.default.dependency.__self__ is instance
    assert depends_attr.default.dependency.__func__ is SimpleDependency.dependency


# todo
# def test_bind__multiple_method_depends_one_method__depends_is_one_object():
#     raise ValueError()
