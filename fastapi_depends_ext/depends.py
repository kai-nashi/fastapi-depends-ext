import functools
import inspect
from typing import Any
from typing import Callable
from typing import Final
from typing import Optional
from typing import Union

from fastapi import params
from fastapi.dependencies.utils import get_typed_signature
from pydantic.fields import FieldInfo

from fastapi_depends_ext.utils import get_base_class
from fastapi_depends_ext.utils import patch_defaults


SUPPORTED_DEPENDS = Union[Callable[..., Any], FieldInfo, params.Depends]
SPECIAL_METHODS_ERROR: Final = ("__call__",)
SPECIAL_METHODS_IGNORE: Final = ("__init__", "__new__")


class DependsAttrBinder:
    def __init__(self, *args, **kwargs):
        super(DependsAttrBinder, self).__init__(*args, **kwargs)

        methods = inspect.getmembers(self, predicate=inspect.ismethod)
        functions = inspect.getmembers(self, predicate=inspect.isfunction)

        for method_name, method in methods + functions:
            if method_name in SPECIAL_METHODS_IGNORE:
                continue

            signature = get_typed_signature(method)
            values_is_depends_attr = [
                param.default for param in signature.parameters.values() if isinstance(param.default, DependsAttr)
            ]

            if not values_is_depends_attr:
                continue

            if method_name in SPECIAL_METHODS_ERROR:
                class_method = f"{type(self).__name__}.{method.__name__}"
                raise AttributeError(f"`{class_method}` can't have `DependsAttr` as default value for arguments")

            self.bind(method)

    def bind(self, method: Callable) -> Callable:
        def depends_attr_bind(depends: DependsAttr, _base_class: type, instance) -> DependsAttr:

            # todo: DependsAttr.__copy__
            depends_copy = DependsAttr(
                method_name=depends.method_name,
                from_super=depends.from_super,
                use_cache=depends.use_cache,
            )

            method_definition = getattr(_base_class, depends.method_name)
            if isinstance(method_definition, property):
                depends_copy.dependency = method_definition.fget(instance)
            else:
                dependency = depends_attr_get_method(depends, _base_class, instance)
                depends_copy.dependency = self.bind(dependency)
            return depends_copy

        def depends_attr_get_method(depends: DependsAttr, _base_class: type, instance) -> Callable:
            # todo: DependsAttr.get_method
            obj = super(_base_class, instance) if depends.from_super else instance
            return getattr(obj, depends.method_name)

        base_class = get_base_class(self, method.__name__, method)
        signature = get_typed_signature(method)
        parameters = (param for param in signature.parameters.values() if isinstance(param.default, DependsAttr))
        instance_method_params = {
            parameter.name: depends_attr_bind(parameter.default, base_class, self) for parameter in parameters
        }

        if instance_method_params:
            # todo substitute in external method
            if inspect.ismethod(method):
                substitute = getattr(self, method.__name__).__func__ is method.__func__
            else:
                substitute = getattr(self, method.__name__) is method

            method = patch_defaults(method, **instance_method_params)
            if substitute:
                setattr(self, method.__name__, method)

        return method


class DependsExt(params.Depends):
    __origin__: Callable

    def __init__(self, dependency: Optional[Callable[..., Any]] = None, *, use_cache: bool = True):
        self.__origin__ = dependency
        super(DependsExt, self).__init__(dependency, use_cache=use_cache)

    def bind(self, **kwargs: SUPPORTED_DEPENDS) -> "DependsExt":
        patched = patch_defaults(self.dependency, **kwargs)
        return DependsExt(patched, use_cache=self.use_cache)


class DependsAttr(DependsExt):
    def __init__(self, method_name: str, *, from_super: bool = False, use_cache=True):
        super(DependsAttr, self).__init__(use_cache=use_cache)
        self.from_super = from_super
        self.method_name = method_name

    def __repr__(self):
        method = self.dependency.__name__ if self.dependency else f"<{self.method_name}>"
        cache = "" if self.use_cache else f", use_cache={self.use_cache}"
        from_super = ", from_super=True" if self.from_super else ""
        return f"{type(self).__name__}({method}{from_super}{cache})"

    def bind(self, instance, super_from: type = None):
        if self.is_bound:
            return

        if self.from_super:
            super_from = super_from or type(instance)
            method = getattr(super(super_from, instance), self.method_name, None)
        else:
            method = getattr(instance, self.method_name, None)

        if not method:
            cls_name = (super_from or type(instance)).__name__
            if self.from_super:
                cls_name = f"super({cls_name}, instance)"
            raise AttributeError(f"{cls_name} has not method `{self.method_name}`")

        cls = get_base_class(instance, self.method_name, method)
        signature = get_typed_signature(method)

        for parameter in signature.parameters.values():
            depends: DependsAttr = parameter.default
            if not isinstance(depends, DependsAttr) or depends.is_bound:
                continue

            elif depends.method_name != self.method_name or depends.from_super:
                depends.bind(instance, cls)

            else:
                message = f"`{cls.__name__}`.`{self.method_name}` has {self} recursively depends self"
                raise RecursionError(message)

        self.dependency = method

    @property
    def is_bound(self):
        return bool(self.dependency)
