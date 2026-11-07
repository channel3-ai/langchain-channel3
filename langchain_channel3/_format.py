"""Shapes Channel3 SDK products into compact, JSON-safe dicts for agents."""

from __future__ import annotations

from typing import Any

from channel3_sdk.types.product import Product

CDN_IMAGE_PREFIX = "https://cdn.trychannel3.com/"


def _cdn_images(product: Product) -> list[dict[str, Any]]:
    return [
        image.model_dump(exclude_none=True)
        for image in product.images or []
        if image.url.startswith(CDN_IMAGE_PREFIX)
    ]


def _with_cleaned_url(image: dict[str, Any]) -> dict[str, Any]:
    cleaned = image.get("cleaned_url")
    return {**image, "url": cleaned} if cleaned else image


def _summary_images(product: Product) -> list[dict[str, Any]]:
    """Up to two display images: the background-removed or main image first, then one other."""
    images = _cdn_images(product)
    primary_source = (
        next((i for i in images if i.get("cleaned_url")), None)
        or next((i for i in images if i.get("is_main_image")), None)
        or (images[0] if images else None)
    )
    if primary_source is None:
        return []
    primary = _with_cleaned_url(primary_source)
    second = next(
        (
            i
            for i in images
            if i is not primary_source
            and i["url"] != primary["url"]
            and i.get("cleaned_url") != primary["url"]
        ),
        None,
    )
    return [primary, _with_cleaned_url(second)] if second else [primary]


def _offers(product: Product) -> list[dict[str, Any]]:
    return [
        offer.model_dump(mode="json", exclude_none=True, exclude={"max_commission_rate"})
        for offer in product.offers or []
    ]


def product_summary(product: Product) -> dict[str, Any]:
    return {
        "id": product.id,
        "title": product.title,
        "brands": [
            brand.model_dump(mode="json", exclude_none=True) for brand in product.brands or []
        ],
        "images": _summary_images(product),
        "offers": _offers(product),
    }


def product_detail(product: Product) -> dict[str, Any]:
    detail = product.model_dump(mode="json", exclude_none=True, exclude={"images", "offers"})
    detail["images"] = _cdn_images(product)[:5]
    detail["offers"] = _offers(product)
    return detail


def _lead_offer(offers: list[dict[str, Any]]) -> dict[str, Any] | None:
    """The lowest-priced in-stock offer, or the lowest-priced offer when none are in stock."""
    by_price = sorted(offers, key=lambda offer: offer["price"]["price"])
    return next((o for o in by_price if o.get("availability") == "InStock"), None) or (
        by_price[0] if by_price else None
    )


def _format_price(amount: float, currency: str) -> str:
    return f"${amount:,.2f}" if currency == "USD" else f"{currency} {amount:,.2f}"


def product_line(product: dict[str, Any]) -> str:
    """One line for the model: title, brands, best price and retailer, and the ID."""
    parts = [f'"{product["title"]}"']
    brands = ", ".join(brand["name"] for brand in product.get("brands") or [])
    if brands:
        parts.append(brands)
    best = _lead_offer(product.get("offers") or [])
    if best:
        parts.append(
            f"{_format_price(best['price']['price'], best['price']['currency'])} at {best['domain']}"
        )
    return f"- {' — '.join(parts)} [id: {product['id']}]"


def summarize_search(
    query: str | None, image_url: str | None, products: list[dict[str, Any]]
) -> str:
    what = f' for "{query}"' if query else " for the image" if image_url else ""
    return "\n".join(
        [f"Found {len(products)} products{what}.", *(product_line(p) for p in products)]
    )
