
import pytest

from decimal import Decimal
from setup_db import initialize
from repository import StoreRepository
from cart import ShoppingCart
from payments import FakePaymentGateway
from checkout import CheckoutService



@pytest.fixture
def setup_store(tmp_path):
    db = tmp_path / "test.db"
    initialize(str(db))
    repo = StoreRepository(str(db))
    return repo



# 1. Check that a seeded product exists
def test_seed_product(setup_store):
    product = setup_store.get_product("MOU-01")
    assert product.name == "Wireless mouse"

# 2. Check that a valid item can be added
def test_cart_adds_valid_item(setup_store):
    cart = ShoppingCart('student', setup_store)
    assert cart.add_item('USB-01', 2)
    assert len(cart.lines) == 1
