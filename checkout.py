"""Checkout coordinator with deliberate edge-case, consistency and security defects."""
from models import OrderResult
from decimal import Decimal



class CheckoutService:
    def __init__(self, repository, payment_gateway):
        self.repository = repository
        self.payment_gateway = payment_gateway



    def checkout(self, cart, payment_token, request_id):
        if not cart.lines:
            return OrderResult(None, "empty", Decimal("0.00"))

        if not request_id:
            return OrderResult(None, "invalid_request", cart.total())

        existing_order = self.repository.get_order_by_request(
            cart.user_id,
            request_id
        )

        if existing_order is not None:
            order_id, _, amount, status = existing_order
            return OrderResult(order_id, status, amount)

        amount = cart.total()
        updated_stock = []

        for line in cart.lines:
            if not self.repository.update_stock(line.sku, line.quantity):
                for sku, quantity in reversed(updated_stock):
                    self.repository.restore_stock(sku, quantity)

                return OrderResult(None, "out_of_stock", amount)
            updated_stock.append((line.sku, line.quantity))

        try:
            response = self.payment_gateway.charge(amount, payment_token)
            approved = response.get("approved", False)
            status = "paid" if approved else "declined"

        except Exception:
            status = "payment_error"

        if status != "paid":
            for sku, quantity in reversed(updated_stock):
                self.repository.restore_stock(sku, quantity)
            
            order_id = self.repository.save_order(
                cart.user_id,
                amount,
                status,
                request_id
            )

            return OrderResult(order_id, status, amount)

        try:
            order_id = self.repository.save_order(
                cart.user_id,
                amount,
                status,
                request_id
            )
        except Exception:
            raise

        cart.lines.clear()
        cart.discount_code = None
        cart.save()

        return OrderResult(order_id, status, amount)
