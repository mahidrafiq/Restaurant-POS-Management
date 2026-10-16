# Restaurant POS Management System

A desktop point-of-sale and order-history application built with **Python, Tkinter and SQLite**.

This project started as a basic restaurant billing application and has been rebuilt with a cleaner architecture, separate order/item records, validation, and a more practical desktop workflow.

## Features

- Customer name and order creation
- Menu with configurable prices
- Quantity validation
- Automatic subtotal calculation
- 18% GST calculation
- 5% service-charge calculation
- Grand-total calculation
- Persistent SQLite database
- Separate `orders` and `order_items` tables
- Order history table
- Delete selected orders
- Reset and validation controls
- Parameterized SQL operations
- No third-party Python packages required

## Menu

| Item | Price |
|---|---:|
| Pizza | ₹240 |
| Burger | ₹125 |
| Ice Cream | ₹80 |
| Drinks | ₹60 |

## Run locally

Requires Python 3.9+ with Tkinter available.

```bash
python main.py
```

The database file `restaurant.db` is created automatically at runtime.

## Architecture

```text
Tkinter UI
    ↓
Order validation & calculation
    ↓
RestaurantDatabase
    ↓
SQLite
    ├── orders
    └── order_items
```

## Roadmap

- [ ] Editable menu stored in the database
- [ ] Search and filter order history
- [ ] Daily sales dashboard
- [ ] PDF receipts
- [ ] CSV/Excel export
- [ ] Inventory tracking
- [ ] Discount support
- [ ] Customer history

## Note

This is a portfolio/learning project. Tax, service-charge and menu values are configurable sample values and should be adapted to the actual business's requirements before real-world use.

## Author

**Mahid Rafiq**

- GitHub: https://github.com/mahidrafiq
- LinkedIn: https://www.linkedin.com/in/mahidrafiq
