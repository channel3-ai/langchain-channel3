"""Channel3 product search tools for LangChain."""

from langchain_channel3.tools import (
    Channel3GetProducts,
    Channel3SearchProducts,
    GetProductsInput,
    SearchProductsInput,
)


def channel3_tools(**kwargs):
    """Both Channel3 tools, sharing the same options (``api_key``, ``base_url``, ``conversation_id``)."""
    limit = kwargs.pop("limit", None)
    search_kwargs = {**kwargs, **({"limit": limit} if limit is not None else {})}
    return [Channel3SearchProducts(**search_kwargs), Channel3GetProducts(**kwargs)]


__all__ = [
    "Channel3GetProducts",
    "Channel3SearchProducts",
    "GetProductsInput",
    "SearchProductsInput",
    "channel3_tools",
]
