import re

import pytest

from fastapi_depends_ext.utils import get_base_class
from fastapi_depends_ext.utils import patch_defaults
from tests.utils_for_tests import SimpleDependency


def dependency():
    return 1


def method(self):
    return self


class Dependency(SimpleDependency):
    var = dependency

    def __call__(self, *args, **kwargs):
        return self

    @classmethod
    def class_method(cls):
        return cls

    @staticmethod
    def static_method():
        return 1

    @property
    def property(self):
        return dependency


class IncorrectDependency:
    var = "str"

    @property
    def property(self):
        return 1


# Simpler tests. Property should return identical object to tst `A` is `B`
dependency_instance = Dependency()
dependency_method = dependency_instance.dependency
dependency_class_method = dependency_instance.class_method
dependency_static_method = dependency_instance.static_method
dependency_property = dependency_instance.property


supported_callable = [
    lambda self: self,  # method
    classmethod(lambda cls: cls),  # classmethod
    staticmethod(lambda: None),  # staticmethod
    property(lambda self: method),  # property return method
    property(lambda self: method),  # property return type
    property(lambda self: dependency_instance),  # property return callable instance
    property(lambda self: dependency_method),  # property return bound_method
    property(lambda self: dependency_class_method),  # property return class_method
    property(lambda self: dependency_static_method),  # property return staticmethod
    property(lambda self: dependency_instance.property),  # property return staticmethod
    property(lambda self: dependency_instance.var),  # property return instance property
    property(lambda self: dependency_property),  # property return calculable property
    Dependency,  # type
    Dependency(),  # callable instance
    Dependency().dependency,  # instance method
    Dependency.class_method,  # instance classmethod
    Dependency.static_method,  # instance staticmethod
    Dependency().var,  # instance property
    Dependency().property,  # instance calculable property
]


incorrect_dependency = IncorrectDependency()
incorrect_dependency_property = incorrect_dependency.property
incorrect_dependency_var = incorrect_dependency.var


unsupported = [
    1,
    "str",
    dict(),
    incorrect_dependency,
    incorrect_dependency_var,
    incorrect_dependency_property,
    property(lambda self: incorrect_dependency),  # property return type
    property(lambda self: incorrect_dependency_var),  # property return instance property
    property(lambda self: incorrect_dependency_property),  # property return calculable property
]


@pytest.mark.parametrize("_method", supported_callable)
def test_get_base_class__class_defined__class(_method):
    TestClass = type("TestClass", (object,), {"method": _method})

    instance = TestClass()

    assert get_base_class(instance, "method", instance.method) is TestClass


@pytest.mark.parametrize("_method", supported_callable)
def test_get_base_class__parent_class_defined__class(_method):
    class ParentClass:
        method = _method

    class TestClass(ParentClass):
        pass

    instance = TestClass()

    assert get_base_class(instance, "method", instance.method) is ParentClass


@pytest.mark.parametrize("_method", supported_callable)
def test_get_base_class__deep_parent_class_defined__deep_parent_class(_method):
    class DeepParentClass:
        method = _method

    class ParentClass(DeepParentClass):
        pass

    class TestClass(ParentClass):
        pass

    instance = TestClass()

    assert get_base_class(instance, "method", instance.method) is DeepParentClass


@pytest.mark.parametrize("_method", supported_callable)
def test_get_base_class__class_redefined__correct_class(_method):
    class ParentClass:
        def method(self):
            return 1

    TestClass = type("TestClass", (ParentClass,), {"method": _method})

    instance = TestClass()

    assert get_base_class(instance, "method", instance.method) is TestClass
    assert get_base_class(instance, "method", super(TestClass, instance).method) is ParentClass


@pytest.mark.parametrize("_method", unsupported)
def test_get_base_class__class_defined_not_callable__AttributeError(_method):
    TestClass = type("TestClass", (object,), {"method": _method})

    instance = TestClass()

    with pytest.raises(TypeError, match=re.escape(f"Incorrect type of `{instance.method}`")):
        get_base_class(instance, "method", instance.method)


@pytest.mark.parametrize("_method", supported_callable)
def test_get_base_class__patched_method__correct_class(_method):
    class TestClass:
        def __init__(self):
            setattr(self, "method", patch_defaults(self.method))

        def method(self):
            pass

    instance = TestClass()

    assert get_base_class(instance, "method", instance.method) is TestClass
