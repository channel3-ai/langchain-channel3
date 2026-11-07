from langchain_tests.integration_tests import ToolsIntegrationTests

from langchain_channel3 import Channel3GetProducts, Channel3SearchProducts


class TestChannel3SearchProductsIntegration(ToolsIntegrationTests):
    @property
    def tool_constructor(self) -> type[Channel3SearchProducts]:
        return Channel3SearchProducts

    @property
    def tool_constructor_params(self) -> dict:
        return {}

    @property
    def tool_invoke_params_example(self) -> dict:
        return {"query": "leather golf glove under $40"}


class TestChannel3GetProductsIntegration(ToolsIntegrationTests):
    @property
    def tool_constructor(self) -> type[Channel3GetProducts]:
        return Channel3GetProducts

    @property
    def tool_constructor_params(self) -> dict:
        return {}

    @property
    def tool_invoke_params_example(self) -> dict:
        return {"product_ids": ["u0cYUCj"]}


def test_get_products_reports_unresolved() -> None:
    _, artifact = Channel3GetProducts()._run(["u0cYUCj", "definitely-not-a-product-id"])
    assert [p["id"] for p in artifact["products"]] == ["u0cYUCj"]
    assert artifact["unresolved"] == ["definitely-not-a-product-id"]
