"""Business logic. Several design and correctness issues are intentional."""
from models import CartLine
from decimal import Decimal, ROUND_HALF_UP


"""Converts values to monetary standards rounded to cents"""
def convert_to_cash(value):
    return Decimal(str(value)).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )


class ShoppingCart:
    """All Discount Codes"""
    PERCENT_DISCOUNTS = {
        "WELCOME10": Decimal("0.10"),
        "STUDENT20": Decimal("0.20")
    }

    SET_DISCOUNTS = {
        "SAVE15": Decimal("15.00")
    }

    OTHER_DISCOUNTS = {
        "FREESHIP": 'Shipping is free'
    }


    def __init__(self, user_id, repository):
        self.user_id = user_id
        self.repository = repository
        self.lines = []
        self.discount_code = None


    def add_item(self, sku, quantity):
        if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
            return False

        product = self.repository.get_product(sku)

        if not product:
            print('Unknown product')
            return False

        existing = next(
            (line for line in self.lines if line.sku == sku),
            None
        )

        current_quantity = existing.quantity if existing else 0
        new_quantity = current_quantity + quantity

        if new_quantity > product.stock:
            print('Not enough stock')
            return False


        if existing:
            existing.quantity = new_quantity
        else:
            self.lines.append(
                CartLine(
                    sku, 
                    product.name, 
                    convert_to_cash(product.price), 
                    quantity
                )
            )

        return True



    def remove_item(self, sku, quantity=None):
        if quantity is not None:
            if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
                return False


        for line in self.lines:
            if line.sku == sku:
                if quantity is None or quantity >= line.quantity:
                    self.lines.remove(line)
                else:
                    line.quantity -= quantity

                return True

        print('Item not found')
        return False



    def subtotal(self):
        return convert_to_cash(
            sum(
                (line.unit_price * line.quantity for line in self.lines),
                Decimal("0.00")
            )
        )

    def total(self):
        temp_amount = self.subtotal()

        if self.discount_code in self.PERCENT_DISCOUNTS:
            discount = self.PERCENT_DISCOUNTS[self.discount_code]
            temp_amount *= (Decimal("1.00") - discount)

        elif self.discount_code in self.SET_DISCOUNTS:
            discount = self.SET_DISCOUNTS[self.discount_code]
            temp_amount -= discount

        elif self.discount_code in self.OTHER_DISCOUNTS:
            discount = self.OTHER_DISCOUNTS[self.discount_code]
            print(discount)
            pass

        return max(Decimal("0.00"), convert_to_cash(temp_amount))



    def apply_discount(self, code):
        valid_codes = (
            *self.PERCENT_DISCOUNTS.keys(),
            *self.SET_DISCOUNTS.keys(),
            *self.OTHER_DISCOUNTS.keys()
        )

        if code not in valid_codes:
            print('Invalid coupon')
            return False

        self.discount_code = code
        return True



    def load(self):
        self.lines.clear()
        self.discount_code = None

        for sku, quantity in self.repository.get_saved_cart(self.user_id):
            self.add_item(sku, quantity)



    def save(self):
        self.repository.save_cart(self.user_id, self.lines)
