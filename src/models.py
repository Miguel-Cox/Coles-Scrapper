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

    def __repr__(self):
        repr_string = (
            f"\n{'='*40}\n"
            f"ProductTile:\n"
            f"  Name               : {self.name or 'N/A'}\n"
            f"  URL                : {self.url or 'N/A'}\n"
            f"  Price              : {self.price or 'N/A'}\n"
            f"  Price Calculation  : {self.price_calc_method or 'N/A'}\n"
            f"  Image URL          : {self.image_url or 'N/A'}\n"
            f"{'='*40}\n"
        )
        return repr_string

    dict = asdict
