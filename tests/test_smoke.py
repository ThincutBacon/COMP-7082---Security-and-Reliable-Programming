
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

# 3. Unknown products should be rejected.
def test_cart_rejects_unknown_product(setup_store):
    cart = ShoppingCart("student", setup_store)
    assert cart.add_item("INVALID", 1) is False

# 4. Zero quantities should be rejected.
def test_cart_rejects_zero_quantity(setup_store):
    cart = ShoppingCart("student", setup_store)
    assert cart.add_item("USB-01", 0) is False

# 5. Negative quantities should be rejected.
def test_cart_rejects_negative_quantity(setup_store):
    cart = ShoppingCart("student", setup_store)
    assert cart.add_item("USB-01", -2) is False

# 6. Adding the same item should increase its quantity.
def test_cart_combines_duplicate_items(setup_store):
    cart = ShoppingCart("student", setup_store)
    cart.add_item("USB-01", 2)
    cart.add_item("USB-01", 3)
    assert len(cart.lines) == 1
    assert cart.lines[0].quantity == 5

# 7. Cart subtotal should be calculated correctly.
def test_cart_subtotal(setup_store):
    cart = ShoppingCart("student", setup_store)
    cart.add_item("USB-01", 2)
    assert cart.subtotal() == Decimal("19.98")

# 8. Percentage discount should calculate correctly.
def test_welcome_discount(setup_store):
    cart = ShoppingCart("student", setup_store)
    cart.add_item("USB-01", 2)
    cart.apply_discount("WELCOME10")
    assert cart.total() == Decimal("17.98")

# 9. Invalid discount codes should be rejected.
def test_invalid_discount(setup_store):
    cart = ShoppingCart("student", setup_store)
    assert cart.apply_discount("NOTREAL") is False

# 10. Stock should decrease after a successful update.
def test_update_stock(setup_store):
    assert setup_store.update_stock("USB-01", 2)
    assert setup_store.get_product("USB-01").stock == 48

# 11. Stock should not decrease below zero.
def test_stock_cannot_be_negative(setup_store):
    assert setup_store.update_stock("USB-01", 100) is False
    assert setup_store.get_product("USB-01").stock == 50

# 12. Successful checkout should create a paid order.
def test_successful_checkout(setup_store):
    cart = ShoppingCart("student", setup_store)
    cart.add_item("USB-01", 2)

    gateway = FakePaymentGateway(should_approve=True)
    service = CheckoutService(setup_store, gateway)

    result = service.checkout(cart, "TEST_TOKEN", "request-001")

    assert result.status == "paid"
    assert result.order_id is not None
    assert len(cart.lines) == 0
    assert setup_store.get_product("USB-01").stock == 48

# 13. Declined payment should restore stock and preserve the cart.
def test_declined_payment_restores_stock(setup_store):
    cart = ShoppingCart("student", setup_store)
    cart.add_item("USB-01", 2)

    gateway = FakePaymentGateway(should_approve=False)
    service = CheckoutService(setup_store, gateway)

    result = service.checkout(cart, "TEST_TOKEN", "request-002")

    assert result.status == "declined"
    assert setup_store.get_product("USB-01").stock == 50
    assert len(cart.lines) == 1

# 14. Empty carts should not be charged.
def test_empty_cart_checkout(setup_store):
    cart = ShoppingCart("student", setup_store)
    gateway = FakePaymentGateway()
    service = CheckoutService(setup_store, gateway)

    result = service.checkout(cart, "TEST_TOKEN", "request-003")

    assert result.status == "empty"
    assert len(gateway.calls) == 0