"""Theme blueprints for WPGen."""

from wpgen.blueprints.ecommerce_blueprint import EcommerceBlueprint
from wpgen.blueprints.blog_blueprint import BlogBlueprint
from wpgen.blueprints.portfolio_blueprint import PortfolioBlueprint
from wpgen.blueprints.magazine_blueprint import MagazineBlueprint

__all__ = [
    'EcommerceBlueprint',
    'BlogBlueprint',
    'PortfolioBlueprint',
    'MagazineBlueprint',
]


def get_blueprint(blueprint_name: str):
    """Get a blueprint instance by name."""
    blueprints = {
        'ecommerce_blueprint': EcommerceBlueprint(),
        'blog_blueprint': BlogBlueprint(),
        'portfolio_blueprint': PortfolioBlueprint(),
        'magazine_blueprint': MagazineBlueprint(),
    }
    return blueprints.get(blueprint_name)
