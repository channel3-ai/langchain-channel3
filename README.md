# langchain-channel3

[Channel3](https://channel3.ai) product search tools for [LangChain](https://python.langchain.com). Give your agent search across 100M+ products from thousands of retailers, with every retailer's offer and live price.

## Installation

```bash
pip install -U langchain-channel3
```

Set `CHANNEL3_API_KEY` in your environment. [Create a free API key](https://channel3.ai/sign-up/developer): every account gets 1,000 free credits a month. A search uses one credit; product details by ID are free, and each retailer URL lookup uses one credit.

## Usage

```python
from langchain.agents import create_agent
from langchain_channel3 import channel3_tools

agent = create_agent(
    model="anthropic:claude-sonnet-5-5",
    tools=channel3_tools(),
)

result = agent.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": "Find me a leather golf glove under $40 and tell me which retailer has it cheapest.",
            }
        ]
    }
)
print(result["messages"][-1].content)
```

## Tools

### `Channel3SearchProducts` (`search_products`)

Searches for one product type and returns in-stock products, each with up to two images and every retailer's offer.

- `query`: one product type and its constraints in natural language, such as `"red leather jacket under $200"`.
- `image_url`: a public image URL for visual search. Combine it with `query` for text plus image.

At least one is required.

### `Channel3GetProducts` (`get_products`)

Gets full product data (description, attributes, variants, images and offers) for up to 40 products in parallel.

- `product_ids`: product IDs from `search_products`, or retailer product URLs.

Inputs that can't be resolved are listed in `unresolved`. The call fails only when none resolve.

Both tools use `response_format="content_and_artifact"`. For `search_products` the model sees one line per product with title, brand, best price and ID; for `get_products` it sees JSON. The full structured result is on the `ToolMessage` as `artifact`, so your UI can render product cards from it.

Offer URLs are Channel3 buy links, so purchases earn affiliate commission for the API key's account.

## Options

```python
from langchain_channel3 import Channel3SearchProducts

search = Channel3SearchProducts(api_key="...", conversation_id=chat_id, limit=12)
```

| Option | Description |
| --- | --- |
| `api_key` | Channel3 API key. Defaults to `CHANNEL3_API_KEY`. |
| `conversation_id` | Groups one chat's calls together in your Channel3 analytics. |
| `limit` | Products per search, from 1 to 30. Defaults to 8. Search tool only. |
| `base_url` | Overrides the API base URL. |

`channel3_tools(**options)` returns both tools with shared options.

## Links

- [Channel3 docs](https://channel3.ai/docs)
- [TypeScript version](https://github.com/channel3-ai/agent-toolkit) for LangChain.js, the Vercel AI SDK and Mastra
- [Channel3 Python SDK](https://pypi.org/project/channel3-sdk/) for the rest of the API

## License

MIT
