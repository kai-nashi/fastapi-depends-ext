import pytest

from fastapi_depends_ext.utils import get_super_for_method


def test_get_super_for_method__has_not_method__error():
    class TestClass:
        pass

    with pytest.raises(AttributeError):
        get_super_for_method(TestClass, "method")


def test_get_super_for_method__super_has_not_method__error():
    class BaseClass:
        pass

    class TestClass(BaseClass):
        def method(self):
            pass

    with pytest.raises(AttributeError):
        get_super_for_method(TestClass, "method")


def test_get_super_for_method__mixin_and_super_has_not_method__error():
    class BaseClass:
        pass

    class MixinClass(BaseClass):
        pass

    class TestClass(MixinClass, BaseClass):
        def method(self):
            pass

    with pytest.raises(AttributeError):
        get_super_for_method(TestClass, "method")


def test_get_super_for_method__super_of_super_has_not_method__error():
    class BaseClass:
        pass

    class MixinClass(BaseClass):
        def method(self):
            pass

    class TestClass(MixinClass, BaseClass):
        def method(self):
            pass

    with pytest.raises(AttributeError):
        get_super_for_method(TestClass, "method", super_from=MixinClass)


def test_get_super_for_method__super_method__super_class():
    class BaseClass:
        def method(self):
            pass

    class TestClass(BaseClass):
        def method(self):
            pass

    result = get_super_for_method(TestClass, "method")
    assert result is BaseClass


def test_get_super_for_method__super_from_instance_type__super_class():
    class BaseClass:
        def method(self):
            pass

    class TestClass(BaseClass):
        def method(self):
            pass

    result = get_super_for_method(TestClass, "method", super_from=TestClass)
    assert result is BaseClass


def test_get_super_for_method__super_of_super_method__super_class():
    class BaseClass:
        def method(self):
            pass

    class MixinClass(BaseClass):
        def method(self):
            pass

    class TestClass(MixinClass, BaseClass):
        def method(self):
            pass

    result = get_super_for_method(TestClass, "method", super_from=MixinClass)
    assert result is BaseClass


def test_get_super_for_method__mixin_without_method__class_with_method():
    class BaseClass:
        def method(self):
            pass

    class MixinClass(BaseClass):
        pass

    class TestClass(MixinClass, BaseClass):
        def method(self):
            pass

    result = get_super_for_method(TestClass, "method")
    assert result is BaseClass
