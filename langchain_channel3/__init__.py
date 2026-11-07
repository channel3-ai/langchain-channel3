"""Channel3 product search tools for LangChain."""

from typing import Any

from langchain_core.tools import BaseTool

from langchain_channel3.toolkit import Channel3Toolkit
from langchain_channel3.tools import (
    Channel3GetProducts,
    Channel3SearchProducts,
    GetProductsInput,
    SearchProductsInput,
)


def channel3_tools(**kwargs: Any) -> list[BaseTool]:
    """Both Channel3 tools, sharing the options ``Channel3Toolkit`` accepts."""
    return Channel3Toolkit(**kwargs).get_tools()


__all__ = [
    "Channel3GetProducts",
    "Channel3SearchProducts",
    "Channel3Toolkit",
    "GetProductsInput",
    "SearchProductsInput",
    "channel3_tools",
]
