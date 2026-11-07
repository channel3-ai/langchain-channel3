from langchain_tests.unit_tests import ToolsUnitTests

from langchain_channel3 import Channel3GetProducts, Channel3SearchProducts


class TestChannel3SearchProductsUnit(ToolsUnitTests):
    @property
    def tool_constructor(self) -> type[Channel3SearchProducts]:
        return Channel3SearchProducts

    @property
    def tool_constructor_params(self) -> dict:
        return {"api_key": "test-key"}

    @property
    def tool_invoke_params_example(self) -> dict:
        return {"query": "leather golf glove under $40"}


class TestChannel3GetProductsUnit(ToolsUnitTests):
    @property
    def tool_constructor(self) -> type[Channel3GetProducts]:
        return Channel3GetProducts

    @property
    def tool_constructor_params(self) -> dict:
        return {"api_key": "test-key"}

    @property
    def tool_invoke_params_example(self) -> dict:
        return {"product_ids": ["u0cYUCj"]}
