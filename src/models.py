"""
Models for Coles scrapers.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional


@dataclass
class ProductTile:
    """
    Model for product tiles found on Coles' **category browsing pages**.
    """

    name: str = field(default="Unknown Product")
    url: str = field(default=None)
    price: Optional[str] = field(default=None)
    price_calc_method: Optional[str] = field(default=None)
    image_url: Optional[str] = field(default=None)
    # Discount-related fields
    was_price: Optional[str] = field(default=None)
    discount_percentage: Optional[str] = field(default=None)
    special_type: Optional[str] = field(default=None)  # e.g., "Half Price", "Special", "Down Down"
    is_on_special: bool = field(default=False)

    def __repr__(self):
        repr_string = (
            f"\n{'='*40}\n"
            f"ProductTile:\n"
            f"  Name               : {self.name or 'N/A'}\n"
            f"  URL                : {self.url or 'N/A'}\n"
            f"  Price              : {self.price or 'N/A'}\n"
            f"  Was Price          : {self.was_price or 'N/A'}\n"
            f"  Discount %         : {self.discount_percentage or 'N/A'}\n"
            f"  Special Type       : {self.special_type or 'N/A'}\n"
            f"  On Special         : {self.is_on_special}\n"
            f"  Price Calculation  : {self.price_calc_method or 'N/A'}\n"
            f"  Image URL          : {self.image_url or 'N/A'}\n"
            f"{'='*40}\n"
        )
        return repr_string

    dict = asdict


@dataclass
class Product:
    """
    Model for product details on Coles' **dedicated product pages**.
    """

    name: str = field(default="Unknown Product")
    brand_name: Optional[str] = field(default=None)
    brand_url: Optional[str] = field(default=None)
    categories: List[str] = field(default_factory=list)
    retail_limit: Optional[str] = field(default=None)
    promotional_limit: Optional[str] = field(default=None)
    product_code: Optional[str] = field(default=None)

    def __repr__(self):
        repr_string = (
            f"\n{'='*40}\n"
            f"Product:\n"
            f"  Name               : {self.name or 'N/A'}\n"
            f"  Brand              : {self.brand_name or 'N/A'}\n"
            f"  Brand URL          : {self.brand_url or 'N/A'}\n"
            f"  Categories         : {', '.join(self.categories) or 'N/A'}\n"
            f"  Retail Limit       : {self.retail_limit or 'N/A'}\n"
            f"  Promotional Limit  : {self.promotional_limit or 'N/A'}\n"
            f"  Product Code       : {self.product_code or 'N/A'}\n"
            f"{'='*40}\n"
        )
        return repr_string
