import re

import pytest
from fastapi import Depends

from fastapi_depends_ext import DependsExt
from fastapi_depends_ext import DependsAttr
from fastapi_depends_ext import DependsAttrBinder
from tests.utils_for_tests import SimpleDependency


def function_dependency():
    return 1


def test_init__no_methods_with_depends_attrs__do_nothing(mocker):
    class TestClass(DependsAttrBinder):
        def method_no_depends(self):
            pass

    spy_bind = mocker.spy(TestClass, "bind")
    TestClass()

    assert not spy_bind.called


@pytest.mark.parametrize("dependency", [Depends(function_dependency), DependsExt(function_dependency)])
def test_init__method_with_depends__do_nothing(mocker, dependency):
    class TestClass(DependsAttrBinder):
        def method_with_depends(self, arg: int = dependency):
            pass

    spy_bind = mocker.spy(TestClass, "bind")
    TestClass()

    assert not spy_bind.called


def test_init__methods_with_depends_attr__all_have_been_patched(mocker):
    class TestClass(SimpleDependency, DependsAttrBinder):
        def method_with_depends(self, arg: int = Depends(function_dependency)):
            pass

        def method_with_depends_attr_0(self, arg: int = DependsAttr("dependency")):
            pass

        def method_with_depends_attr_1(self, arg: int = DependsAttr("dependency")):
            pass

    spy_bind = mocker.spy(TestClass, "bind")
    instance = TestClass()

    call_args_list_actual = [(_call.args[0], _call.args[1].__func__) for _call in spy_bind.call_args_list]
    call_args_list_expected = [
        (instance, TestClass.method_with_depends_attr_0),
        (instance, TestClass.dependency),  # recursive call from TestClass.method_with_depends_attr_0
        (instance, TestClass.method_with_depends_attr_1),
        (instance, TestClass.dependency),  # recursive call from TestClass.method_with_depends_attr_1
    ]

    assert call_args_list_actual == call_args_list_expected


def test_init__class_methods_with_depends_attr__all_have_been_patched(mocker):
    class TestClass(SimpleDependency, DependsAttrBinder):
        def method_with_depends(self, arg: int = Depends(function_dependency)):
            pass

        @classmethod
        def method_with_depends_attr_0(cls, arg: int = DependsAttr("dependency")):
            pass

        @classmethod
        def method_with_depends_attr_1(cls, arg: int = DependsAttr("dependency")):
            pass

    spy_bind = mocker.spy(TestClass, "bind")
    instance = TestClass()

    call_args_list_expected = [
        mocker.call(instance, TestClass.method_with_depends_attr_0),
        mocker.call(instance, instance.dependency),  # recursive call from TestClass.method_with_depends_attr_0
        mocker.call(instance, TestClass.method_with_depends_attr_1),
        mocker.call(instance, instance.dependency),  # recursive call from TestClass.method_with_depends_attr_1
    ]

    assert spy_bind.call_args_list == call_args_list_expected
    assert instance.method_with_depends_attr_0.__func__.__defaults__[0].dependency.__self__ is instance
    assert instance.method_with_depends_attr_1.__func__.__defaults__[0].dependency.__self__ is instance


def test_init__static_methods_with_depends_attr__all_have_been_patched(mocker):
    class TestClass(SimpleDependency, DependsAttrBinder):
        def method_with_depends(self, arg: int = Depends(function_dependency)):
            pass

        @staticmethod
        def method_with_depends_attr_0(arg: int = DependsAttr("dependency")):
            pass

        @staticmethod
        def method_with_depends_attr_1(arg: int = DependsAttr("dependency")):
            pass

    spy_bind = mocker.spy(TestClass, "bind")
    instance = TestClass()

    call_args_list_expected = [
        mocker.call(instance, TestClass.method_with_depends_attr_0),
        mocker.call(instance, instance.dependency),  # recursive call from TestClass.method_with_depends_attr_0
        mocker.call(instance, TestClass.method_with_depends_attr_1),
        mocker.call(instance, instance.dependency),  # recursive call from TestClass.method_with_depends_attr_1
    ]

    assert spy_bind.call_args_list == call_args_list_expected
    assert instance.method_with_depends_attr_0.__defaults__[0].dependency.__self__ is instance
    assert instance.method_with_depends_attr_1.__defaults__[0].dependency.__self__ is instance


def test_init__new_init_depends_attr__ignored(mocker):
    class TestClass(SimpleDependency, DependsAttrBinder):
        def __init__(self, *args, arg: int = DependsAttr("dependency"), **kwargs):
            super(TestClass, self).__init__(*args, **kwargs)

        def __new__(cls, *args, arg: int = DependsAttr("dependency"), **kwargs):
            return super().__new__(cls, *args, **kwargs)

    spy_bind = mocker.spy(TestClass, "bind")
    TestClass()

    assert not spy_bind.called


def test_init__call_depends_attr__error():
    class TestClass(SimpleDependency, DependsAttrBinder):
        def __call__(self, *args, arg: int = DependsAttr("dependency"), **kwargs):
            super(TestClass, self).__init__(*args, **kwargs)

    message = f"`TestClass.__call__` can't have `DependsAttr` as default value for arguments"
    with pytest.raises(AttributeError, match=re.escape(message)):
        TestClass()
