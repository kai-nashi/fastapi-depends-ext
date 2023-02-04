![CDNJS](https://img.shields.io/badge/Python-3.8%20%7C%203.9%20%7C%203.10%20%7C%203.11-2334D058)
![CDNJS](https://shields.io/badge/FastAPI-%3E=0.7.0-009485)

# FastAPI depends extension

## Introduction

Sometimes your FastAPI dependencies have to get value from functions cannot be available on initialization. The problem is particularly acute to use class dependencies with inheritance. This project try to solve problem of modify `Depends` after application initialization.

## Installation

```
pip install fastapi-depends-ext
```

## Tutorial

#### DependsAttr

```python
from typing import List

from fastapi import Depends
from fastapi import FastAPI
from fastapi import Query
from pydantic import conint

from fastapi_depends_ext import DependsAttr
from fastapi_depends_ext import DependsAttrBinder


class ItemsPaginated(DependsAttrBinder):
    _items = list(range(100))

    async def get_page(self, page: conint(ge=1) = Query(1)):
        return page

    async def items(self, page: int = DependsAttr("get_page")):
        _slice = slice(page * 10, (page + 1) * 10)
        return self._items[_slice]


class ItemsSquarePaginated(ItemsPaginated):
    async def items(self, items: List[int] = DependsAttr("items", from_super=True)):
        return [i**2 for i in items]


app = FastAPI()


@app.get("/")
def items_list(items: List[int] = Depends(ItemsPaginated().items)) -> List[int]:
    return items


@app.get("/square")
def items_list_square(items: List[int] = Depends(ItemsSquarePaginated().items)) -> List[int]:
    return items
```

Use `DependsAttr` to `Depends` from current instance attributes. All examples use `asyncio`, but you can write all methods synchronous.

`DependsAttr` support next properties:
- class variables (must contains `callable` object)
- class methods
- static methods
- instance methods
- `property` returning `callable`

Your class must inherit from `DependsAttrBinder` and attributes must be `DependsAttr`. `DependsAttrBinder` automatically patch all methods with `DependsAttr` by instance attributes.

`DependsAttr` arguments:
- `method_name` - `str`, name of instance attribute to use as dependency
- `from_super` - `bool`, on true, will use attribute `method_name` from super class like `super().method_name()`
- `use_cache` - `bool`, allow to cache depends result for the same dependencies in request

#### DependsExt

Useless(?) class created to proof of concept of patching methods and correct work `FastAPI` applications.

`DependsExt` allow you define default values of method arguments after `FastAPI` endpoint has been created.  

Example:
```
from fastapi import FastAPI
from fastapi import Query

from fastapi_depends_ext import DependsExt


def pagination(page: int = Query()):
    return page


depends = DependsExt(pagination)


app = FastAPI()


@app.on_event("startup")
def setup_depends():
    depends.bind(page=Query(1))


@app.get("/")
def get_method(value: int = depends) -> int:
    return value

```

Is equivalent for
```
from fastapi import Depends
from fastapi import FastAPI
from fastapi import Query


def pagination(page: int = Query(1)):
    return page


app = FastAPI()


@app.get("/")
def get_method(value: int = Depends(pagination)) -> int:
    return value

```