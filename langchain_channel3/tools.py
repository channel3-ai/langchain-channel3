"""Channel3 product search tools for LangChain."""

from __future__ import annotations

import asyncio
import json
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Literal, Optional
from urllib.parse import urlparse

from channel3_sdk import AsyncChannel3, Channel3
from channel3_sdk.types.product import Product
from langchain_core.callbacks import AsyncCallbackManagerForToolRun, CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field, SecretStr, model_validator

from langchain_channel3._format import product_detail, product_summary, summarize_search

CONVERSATION_ID_HEADER = "X-Conversation-Id"
_CHANNEL3_HOSTS = {"trychannel3.com", "channel3.ai"}


class _Channel3ToolBase(BaseTool):
    """Shared client configuration for Channel3 tools."""

    api_key: Optional[SecretStr] = Field(default=None, exclude=True)
    """Channel3 API key. Defaults to the ``CHANNEL3_API_KEY`` environment variable."""
    base_url: Optional[str] = None
    """Overrides the API base URL."""
    conversation_id: Optional[str] = None
    """Groups one chat's calls together in your Channel3 analytics. Sent as ``X-Conversation-Id``."""

    response_format: Literal["content", "content_and_artifact"] = "content_and_artifact"

    @model_validator(mode="after")
    def _resolve_api_key(self) -> _Channel3ToolBase:
        if self.api_key is None:
            env_key = os.environ.get("CHANNEL3_API_KEY")
            if not env_key:
                raise ValueError(
                    "Missing Channel3 API key. Set CHANNEL3_API_KEY or pass `api_key`. "
                    "Create a free key at https://channel3.ai/sign-up/developer."
                )
            self.api_key = SecretStr(env_key)
        return self

    def _client_kwargs(self) -> dict[str, Any]:
        assert self.api_key is not None
        kwargs: dict[str, Any] = {"api_key": self.api_key.get_secret_value()}
        if self.base_url:
            kwargs["base_url"] = self.base_url
        if self.conversation_id:
            kwargs["headers"] = {CONVERSATION_ID_HEADER: self.conversation_id}
        return kwargs

    def _client(self) -> Channel3:
        return Channel3(**self._client_kwargs())

    def _async_client(self) -> AsyncChannel3:
        return AsyncChannel3(**self._client_kwargs())


class SearchProductsInput(BaseModel):
    """Input for ``search_products``. At least one of ``query`` or ``image_url`` is required."""

    query: Optional[str] = Field(
        default=None,
        description=(
            "One product type and its constraints in natural language "
            "(brand, color, material, size, price, gender).\n"
            'Good: "red leather jacket under $200"; "leather golf glove under $40".\n'
            'Bad: "gift ideas for dad"; "cool sneakers"; "golf glove or rangefinder".'
        ),
    )
    image_url: Optional[str] = Field(
        default=None,
        description="Public image URL for visual search. Combine with `query` for text + image.",
    )

    @model_validator(mode="after")
    def _require_query_or_image(self) -> SearchProductsInput:
        if not (self.query and self.query.strip()) and not self.image_url:
            raise ValueError("At least one of `query` or `image_url` is required.")
        return self


class Channel3SearchProducts(_Channel3ToolBase):
    """Search 100M+ products across thousands of retailers with Channel3.

    Setup:
        Install ``langchain-channel3`` and set ``CHANNEL3_API_KEY``.

        .. code-block:: bash

            pip install -U langchain-channel3
            export CHANNEL3_API_KEY="your-api-key"

    Instantiate:
        .. code-block:: python

            from langchain_channel3 import Channel3SearchProducts

            tool = Channel3SearchProducts(limit=8)

    Invoke directly with args:
        .. code-block:: python

            tool.invoke({"query": "leather golf glove under $40"})

    Invoke with a ToolCall:
        The model sees one line per product; the full results are the ``ToolMessage`` artifact.

        .. code-block:: python

            message = tool.invoke(
                {"args": {"query": "leather golf glove under $40"}, "id": "1", "name": tool.name, "type": "tool_call"}
            )
            message.artifact["products"]
    """

    name: str = "search_products"
    description: str = (
        "Search 100M+ products across thousands of retailers for one product type. "
        "Call once for each distinct product type, and send independent calls together. "
        "Put relevant constraints in `query`.\n"
        "Returns products with their retailer offers and live prices."
    )
    args_schema: type[BaseModel] = SearchProductsInput

    limit: int = Field(default=8, ge=1, le=30)
    """Maximum products per search."""

    def _search_kwargs(self, query: Optional[str], image_url: Optional[str]) -> dict[str, Any]:
        return {
            "query": query,
            "image_url": image_url,
            "limit": self.limit,
            "filters": {"availability": ["InStock"]},
            "config": {"mode": "agentic"},
        }

    def _result(
        self, query: Optional[str], image_url: Optional[str], products: list[Product]
    ) -> tuple[str, dict[str, Any]]:
        summaries = [product_summary(p) for p in products]
        return summarize_search(query, image_url, summaries), {"products": summaries}

    def _run(
        self,
        query: Optional[str] = None,
        image_url: Optional[str] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> tuple[str, dict[str, Any]]:
        page = self._client().products.search(**self._search_kwargs(query, image_url))
        return self._result(query, image_url, list(page.items or []))

    async def _arun(
        self,
        query: Optional[str] = None,
        image_url: Optional[str] = None,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> tuple[str, dict[str, Any]]:
        page = await self._async_client().products.search(**self._search_kwargs(query, image_url))
        return self._result(query, image_url, list(page.items or []))


class GetProductsInput(BaseModel):
    """Input for ``get_products``."""

    product_ids: list[str] = Field(
        min_length=1,
        max_length=40,
        description="Products to fetch in parallel: product IDs from `search_products`, or product URLs.",
    )


def _channel3_product_id(value: str) -> Optional[str]:
    """Channel3 product page or buy-link URLs carry the product ID in their path."""
    parsed = urlparse(value)
    host = (parsed.hostname or "").lower().removeprefix("www.")
    parts = [p for p in parsed.path.split("/") if p]
    if host == "buy.trychannel3.com" and parts:
        return parts[0].split("-")[0] or None
    if host in _CHANNEL3_HOSTS and len(parts) >= 2 and parts[0] == "products":
        return parts[1]
    return None


def _is_url(value: str) -> bool:
    return value.lower().startswith(("http://", "https://"))


class Channel3GetProducts(_Channel3ToolBase):
    """Get full Channel3 product data by product ID or retailer URL.

    Setup:
        Install ``langchain-channel3`` and set ``CHANNEL3_API_KEY``.

    Instantiate:
        .. code-block:: python

            from langchain_channel3 import Channel3GetProducts

            tool = Channel3GetProducts()

    Invoke directly with args:
        .. code-block:: python

            tool.invoke({"product_ids": ["u0cYUCj", "https://www.example.com/product-page"]})
    """

    name: str = "get_products"
    description: str = (
        "Get full product data (offers, description, attributes, images) by product ID "
        "from a search result, or by retailer URL. Pass several IDs in one call to compare.\n"
        "Use search_products to find products."
    )
    args_schema: type[BaseModel] = GetProductsInput

    def _resolve(self, client: Channel3, value: str) -> Product:
        value = value.strip()
        if not _is_url(value):
            return client.products.retrieve(value)
        product_id = _channel3_product_id(value)
        if product_id:
            return client.products.retrieve(product_id)
        return client.products.lookup(url=value).product

    async def _aresolve(self, client: AsyncChannel3, value: str) -> Product:
        value = value.strip()
        if not _is_url(value):
            return await client.products.retrieve(value)
        product_id = _channel3_product_id(value)
        if product_id:
            return await client.products.retrieve(product_id)
        return (await client.products.lookup(url=value)).product

    @staticmethod
    def _result(product_ids: list[str], outcomes: list[Any]) -> tuple[str, dict[str, Any]]:
        products = [product_detail(o) for o in outcomes if isinstance(o, Product)]
        if not products:
            failure = next((o for o in outcomes if isinstance(o, BaseException)), None)
            raise failure if failure else ValueError("No products resolved.")
        result: dict[str, Any] = {"products": products}
        unresolved = [
            pid for pid, o in zip(product_ids, outcomes, strict=True) if not isinstance(o, Product)
        ]
        if unresolved:
            result["unresolved"] = unresolved
        return json.dumps(result), result

    def _run(
        self,
        product_ids: list[str],
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> tuple[str, dict[str, Any]]:
        client = self._client()

        def resolve(value: str) -> Any:
            try:
                return self._resolve(client, value)
            except Exception as error:  # noqa: BLE001 - reported per input via `unresolved`
                return error

        with ThreadPoolExecutor(max_workers=min(8, len(product_ids))) as pool:
            outcomes = list(pool.map(resolve, product_ids))
        return self._result(product_ids, outcomes)

    async def _arun(
        self,
        product_ids: list[str],
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> tuple[str, dict[str, Any]]:
        client = self._async_client()
        outcomes = await asyncio.gather(
            *(self._aresolve(client, value) for value in product_ids), return_exceptions=True
        )
        return self._result(product_ids, list(outcomes))
