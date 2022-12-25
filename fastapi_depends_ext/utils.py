import functools
import inspect
from inspect import Signature
from types import FunctionType
from types import MethodType
from typing import Callable

from fastapi.dependencies.utils import get_typed_signature


def get_base_class(method: Callable) -> type:
    if inspect.ismethod(method):
        for cls in inspect.getmro(method.__self__.__class__):
            if cls.__dict__.get(method.__name__) is method.__func__:
                return cls
        method = method.__func__  # fallback to __qualname__ parsing

    if inspect.isfunction(method):
        cls = getattr(inspect.getmodule(method), method.__qualname__.split(".<locals>", 1)[0].rsplit(".", 1)[0])
        if isinstance(cls, type):
            return cls
    return getattr(method, "__objclass__", None)  # handle special descriptor objects


def get_super_for_method(base_class: type, method_name: str, super_from: type = None) -> type:
    super_from = super_from or base_class
    mro = list(inspect.getmro(base_class))

    super_class_for_method = None
    mro = mro[mro.index(super_from) + 1 :]
    while mro:
        cls = mro.pop()
        method = getattr(cls, method_name, None)
        if not method:
            continue

        methods_exclude = (
            getattr(super_class_for_method, method_name, None),
            getattr(base_class, method_name, None),
        )
        if method not in methods_exclude:
            super_class_for_method = cls

    if super_class_for_method:
        return super_class_for_method

    raise AttributeError(f"super({super_from.__name__}, {base_class.__name__}) has not method `{method_name}`")


# todo: split to clone and patch_defaults
def patch_defaults(origin: Callable, **kwargs) -> Callable:
    signature: Signature = get_typed_signature(origin)
    for keyword, dependency in kwargs.items():
        if keyword not in signature.parameters:
            raise KeyError(
                f"Trying to provide for method `{origin.__name__}` not existing keyword argument `{keyword}`"
            )

    func = origin
    if inspect.ismethod(origin):
        func = func.__func__

    defaults = func.__defaults__ and list(func.__defaults__)
    func_args = func.__code__.co_varnames[: func.__code__.co_argcount]
    args_change_defaults_keys = [key for key in func_args if key in kwargs]
    if func_args and args_change_defaults_keys:
        args_have_defaults = func_args[-(len(func.__defaults__)) :] if func.__defaults__ else []
        args_can_change_defaults = set(kwargs) | set(args_have_defaults)
        args_change_defaults_from = min(func_args.index(key) for key in args_change_defaults_keys if key in func_args)
        args_change_defaults = func_args[args_change_defaults_from:]
        if not all(key in args_can_change_defaults for key in args_change_defaults):
            raise AttributeError("Trying to set default for argument before arguments with default values")

        defaults_not_changed = defaults[: -len(args_change_defaults)] if defaults else list()
        defaults_changes = [kwargs.get(key) or defaults[args_have_defaults.index(key)] for key in args_change_defaults]
        defaults = defaults_not_changed + defaults_changes

    patched = FunctionType(
        func.__code__,
        func.__globals__,
        name=func.__name__,
        argdefs=tuple(defaults) if defaults else None,
        closure=func.__closure__,
    )

    patched = functools.update_wrapper(patched, func)
    delattr(patched, "__wrapped__")  # prevent fastapi to use as target dependency __wrapped__ method
    setattr(patched, "__origin__", func)

    kwdefaults = func.__kwdefaults__.copy() if func.__kwdefaults__ else dict()
    kwdefaults.update({k: kwargs[k] for k in set(kwargs) if k in kwdefaults})
    if func.__code__.co_kwonlyargcount:
        _from = func.__code__.co_argcount + func.__code__.co_posonlyargcount
        _to = -func.__code__.co_kwonlyargcount
        kwonlyargs = func.__code__.co_varnames[_from:_to]
        kwdefaults.update({key: kwargs[key] for key in kwonlyargs if key in kwargs})
    patched.__kwdefaults__ = kwdefaults or None

    if inspect.ismethod(origin):
        patched = MethodType(patched, origin.__self__)

    return patched
