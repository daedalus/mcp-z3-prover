__version__ = "0.1.0"
__all__ = ["mcp"]

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._core import *

from ._core import mcp
