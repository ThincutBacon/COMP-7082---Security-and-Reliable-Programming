# List of Observed and Fixed Defects

| # | Location | Defect and potential problem | Correction |
|---|---|---|---|
| 1 | `repository.py` — `get_product()` | SQL query used string formatting, allowing SQL injection. | Replaced string formatting with parameterized SQL queries. |
| 2 | `repository.py` — `get_saved_cart()` | User ID was inserted directly into the SQL query. | Used parameterized SQL queries. |
| 3 | `repository.py` — database connections | Connections were not reliably closed. | Used connection-closing context managers. |
| 4 | `repository.py` — `update_stock()` | Inventory could become negative if an order exceeded available stock. | Added a stock availability condition and validated quantities. |
| 5 | `repository.py` — `list_orders()` | The method returned orders belonging to every user. | Filtered results by the requested user ID. |
| 6 | `models.py`, `cart.py` | Floating-point arithmetic could produce inaccurate monetary calculations. | Used `Decimal` for prices and totals, with rounding to cents. |
| 7 | `cart.py` — `add_item()` | Invalid quantities and quantities exceeding available stock could be accepted. | Added quantity validation and cumulative stock checks. |
| 8 | `cart.py` — `apply_discount()` and `total()` | Discount calculations could become stale when the cart changed, and fixed discounts could produce negative totals. | Recalculated totals from the current cart and prevented negative totals. |
| 9 | `cart.py` — `load()` | Loading a saved cart repeatedly could duplicate existing cart lines. | Cleared existing lines before loading saved items. |
| 10 | `checkout.py` — payment handling | Stock was deducted before payment and was not restored after a decline or payment error. | Added stock restoration when payment is unsuccessful. |
| 11 | `checkout.py` — cart handling | The original checkout cleared the cart even when payment was declined. | Preserved the cart unless payment succeeds. |
| 12 | `checkout.py` — payment logging | The original code printed the payment token. | Removed printing of sensitive payment-token information. |
| 13 | `checkout.py` and `repository.py` — repeated requests | Repeated checkout requests could create duplicate orders. | Added request-ID lookup and a database uniqueness constraint. |
| 14 | `checkout.py` — request validation | Large orders could proceed without a request ID. | Added request-ID validation before checkout. |

## Assumptions

- The supplied payment gateway is a simulator and remains in use. No real payment processing is performed.
- Monetary values are represented using `Decimal` and rounded to two decimal places.
- The `FREESHIP` discount does not change the product subtotal because the application does not calculate shipping charges.
- The `SAVE15` discount reduces the total by $15 but cannot make the total negative.
- A declined payment or payment error does not complete the order or clear the shopping cart.
- A request ID is unique for each user's checkout request.
- If payment succeeds but saving the order fails, manual reconciliation may be necessary because SQLite and an external payment service cannot share one atomic transaction.