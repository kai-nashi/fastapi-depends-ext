import re
from typing import Any

import pytest

from fastapi_depends_ext.depends import DependsAttr
from tests.utils_for_tests import SimpleDependency


def test_bind__attribute_not_exist__error():
    instance = object()
    depends = DependsAttr("method")

    with pytest.raises(AttributeError):
        depends.bind(instance)


def test_bind__dependence_depends_instance_method__dependency_has_been_set():
    depends = DependsAttr("dependency")

    class TestClass(SimpleDependency):
        def method(self, depends_attr: Any = depends):
            pass

    instance = TestClass()
    depends.bind(instance)

    assert depends.dependency.__func__ is TestClass.dependency


def test_bind__dependence_recursive__error():
    depends = DependsAttr("method")

    class TestClass:
        def method(self, depends_attr: Any = depends):
            pass

    instance = TestClass()

    message = f"{depends} recursively depends self"
    with pytest.raises(RecursionError, match=re.escape(message)):
        depends.bind(instance)


def test_bind__dependence_depends_attr__dependency_has_been_set():
    depends_bounded = DependsAttr("depends_bounded")
    depends_bounded.dependency = lambda x: None

    class TestClass:
        def method_bounded(self, depends_attr: int = depends_bounded):
            pass

    instance = TestClass()
    depends = DependsAttr("method_bounded")
    depends.bind(instance)

    assert depends.dependency.__func__ is TestClass.method_bounded


def test_bind__dependency_depends_from_super_but_super_has_no_method__dependency_has_been_set():
    class BaseClass:
        pass

    class TestClass(BaseClass):
        def dependency(self):
            pass

    instance = TestClass()
    depends = DependsAttr("method", from_super=True)

    message = f"super(TestClass, instance) has not method `method`"
    with pytest.raises(AttributeError, match=re.escape(message)):
        depends.bind(instance)


def test_bind__dependence_depends_from_super__dependency_has_been_set():
    depends = DependsAttr("dependency", from_super=True)

    class TestClass(SimpleDependency):
        def dependency(self, depends_attr: Any = depends):
            pass

    instance = TestClass()
    depends.bind(instance)

    assert depends.dependency.__func__ is SimpleDependency.dependency


def test_bind__dependence_depends_from_super_deep_method__dependency_has_been_set():
    depends = DependsAttr("dependency", from_super=True)
    depends_mixin = DependsAttr("dependency", from_super=True)

    class MixinClass:
        def dependency(self, depends_attr: Any = depends_mixin):
            pass

    class TestClass(MixinClass, SimpleDependency):
        def dependency(self, depends_attr: Any = depends):
            pass

    instance = TestClass()
    depends.bind(instance)

    assert depends.dependency.__func__ is MixinClass.dependency
    assert depends_mixin.dependency.__func__ is SimpleDependency.dependency


def test_bind__dependence_depends_from_super_another_method__dependency_has_been_set():
    depends = DependsAttr("method", from_super=True)
    depends_mixin = DependsAttr("dependency", from_super=True)

    class MixinClass(SimpleDependency):
        def dependency(self):
            pass

        def method(self, depends_attr: Any = depends_mixin):  # DependsAttr("dependency", from_super=True)
            pass

    class TestClass(MixinClass, SimpleDependency):
        def method(self, depends_attr: Any = depends):  # DependsAttr("method", from_super=True)
            pass

    instance = TestClass()
    depends.bind(instance)

    assert depends.dependency.__func__ is MixinClass.method
    assert depends_mixin.dependency.__func__ is SimpleDependency.dependency


def test_bind__dependence_depends_another_method_with_depends_super__dependency_has_been_set():
    depends = DependsAttr("dependency")
    depends_mixin = DependsAttr("dependency", from_super=True)

    class MixinClass(SimpleDependency):
        def dependency(self, depends_attr: Any = depends_mixin):  # DependsAttr("dependency", from_super=True)
            pass

    class TestClass(MixinClass):
        def method(self, depends_attr: Any = depends):  # DependsAttr("dependency")
            pass

    instance = TestClass()
    depends.bind(instance)

    assert depends.dependency.__func__ is MixinClass.dependency
    assert depends_mixin.dependency.__func__ is SimpleDependency.dependency


def test_bind__dependence_recursive_deep__error():
    depends = DependsAttr("method", from_super=True)

    class BaseClass:
        def method(self, depends_attr: Any = DependsAttr("method")):
            pass

    class TestClass(BaseClass):
        def method(self, depends_attr: Any = depends):  # DependsAttr("method", from_super=True)
            pass

    instance = TestClass()

    message = f"`BaseClass`.`method` has {depends} recursively depends self"
    with pytest.raises(RecursionError, match=re.escape(message)):
        depends.bind(instance)


def test_bind__dependence_has_unbounded_depends_attr__bind_all():
    depends = DependsAttr("method_unbounded")
    depends_unbounded = DependsAttr("dependency")

    class TestClass(SimpleDependency):
        def method_unbounded(self, depends_attr: int = depends_unbounded):
            pass

    instance = TestClass()

    depends.bind(instance)

    assert depends.dependency.__func__ is TestClass.method_unbounded
    assert depends_unbounded.dependency.__func__ is SimpleDependency.dependency


def test_bind__dependence_has_unbounded_chained__bind_all():
    depends = [DependsAttr("method_2"), DependsAttr("method_3"), DependsAttr("dependency")]

    class TestClass(SimpleDependency):
        def method_1(self, depends_attr: Any = depends[0]):
            pass

        def method_2(self, depends_attr: Any = depends[1]):
            pass

        def method_3(self, depends_attr: Any = depends[2]):
            pass

    instance = TestClass()

    depends[0].bind(instance)

    result = [_depends.dependency.__func__ for _depends in depends]
    expected = [getattr(TestClass, _depends.method_name) for _depends in depends]
    assert result == expected


def test_bind__methods_chained_recursive__error():
    depends = [DependsAttr("method_2"), DependsAttr("method_1")]

    class TestClass(SimpleDependency):
        def method_1(self, depends_attr: Any = depends[0]):
            pass

        def method_2(self, depends_attr: Any = depends[1]):
            pass

    instance = TestClass()

    with pytest.raises(RecursionError):
        depends[0].bind(instance)


def test_bind__methods_chained_deep_recursive__error():
    depends = [DependsAttr("method_2"), DependsAttr("method_3"), DependsAttr("method_1")]

    class TestClass(SimpleDependency):
        def method_1(self, depends_attr: Any = depends[0]):
            pass

        def method_2(self, depends_attr: Any = depends[1]):
            pass

        def method_3(self, depends_attr: Any = depends[2]):
            pass

    instance = TestClass()

    with pytest.raises(RecursionError):
        depends[0].bind(instance)


def test_bind__has_method_depends_super__bind_all():
    depends = [DependsAttr("dependency"), DependsAttr("dependency", from_super=True)]

    class TestClass(SimpleDependency):
        def method(self, depends_attr: Any = depends[0]):  # DependsAttr("dependency")
            pass

        def dependency(self, depends_attr: Any = depends[1]):  # DependsAttr("dependency", from_super=True)
            pass

    instance = TestClass()

    depends[0].bind(instance)

    assert depends[0].dependency.__func__ is TestClass.dependency
    assert depends[1].dependency.__func__ is SimpleDependency.dependency


def test_bind__has_method_depends_super_chained__bind_all():
    depends = [DependsAttr("method_1", from_super=True), DependsAttr("dependency")]
    depends_super = DependsAttr("method_2")

    class BaseClass:
        def method_1(self, depends_attr: Any = depends_super):  # DependsAttr("method_2")
            pass

    class TestClass(SimpleDependency, BaseClass):
        def method_1(self, depends_attr: Any = depends[0]):  # DependsAttr("method_1", from_super=True)
            pass

        def method_2(self, depends_attr: Any = depends[1]):  # DependsAttr("dependency")
            pass

    instance = TestClass()

    depends[0].bind(instance)

    assert depends[0].dependency.__func__ is BaseClass.method_1
    assert depends[1].dependency.__func__ is SimpleDependency.dependency
    assert depends_super.dependency.__func__ is TestClass.method_2
