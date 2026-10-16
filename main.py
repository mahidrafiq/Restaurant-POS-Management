from datetime import datetime
from pathlib import Path
import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk

DB_PATH = Path(__file__).with_name("restaurant.db")
TAX_RATE = 0.18
SERVICE_RATE = 0.05

MENU = {
    "Pizza": 240.0,
    "Burger": 125.0,
    "Ice Cream": 80.0,
    "Drinks": 60.0,
}


class RestaurantDatabase:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.initialize()

    def connect(self):
        conn = sqlite3.connect(self.db_path)
        # SQLite only enforces foreign keys when the pragma is enabled on
        # each connection; without this the ON DELETE CASCADE declared on
        # order_items is silently ignored.
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def initialize(self):
        with self.connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS orders (
                    order_id TEXT PRIMARY KEY,
                    customer_name TEXT NOT NULL,
                    subtotal REAL NOT NULL,
                    tax REAL NOT NULL,
                    service_charge REAL NOT NULL,
                    total REAL NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS order_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id TEXT NOT NULL,
                    item_name TEXT NOT NULL,
                    quantity INTEGER NOT NULL CHECK(quantity > 0),
                    unit_price REAL NOT NULL,
                    FOREIGN KEY(order_id) REFERENCES orders(order_id) ON DELETE CASCADE
                )
                """
            )

    def save_order(self, order_id, customer_name, items, subtotal, tax, service_charge, total):
        created_at = datetime.now().isoformat(timespec="seconds")
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?)",
                (order_id, customer_name, subtotal, tax, service_charge, total, created_at),
            )
            conn.executemany(
                "INSERT INTO order_items (order_id, item_name, quantity, unit_price) VALUES (?, ?, ?, ?)",
                [(order_id, name, quantity, MENU[name]) for name, quantity in items.items() if quantity > 0],
            )

    def recent_orders(self):
        with self.connect() as conn:
            return conn.execute(
                "SELECT order_id, customer_name, subtotal, tax, service_charge, total, created_at FROM orders ORDER BY created_at DESC"
            ).fetchall()

    def delete_order(self, order_id):
        with self.connect() as conn:
            conn.execute("DELETE FROM order_items WHERE order_id = ?", (order_id,))
            conn.execute("DELETE FROM orders WHERE order_id = ?", (order_id,))


class RestaurantPOS(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Restaurant POS Management")
        self.geometry("980x650")
        self.minsize(900, 600)
        self.database = RestaurantDatabase()
        self.customer_var = tk.StringVar()
        self.quantity_vars = {name: tk.StringVar(value="0") for name in MENU}
        self.subtotal_var = tk.StringVar(value="₹0.00")
        self.tax_var = tk.StringVar(value="₹0.00")
        self.service_var = tk.StringVar(value="₹0.00")
        self.total_var = tk.StringVar(value="₹0.00")
        self.build_ui()
        self.refresh_orders()

    def build_ui(self):
        style = ttk.Style(self)
        style.configure("Treeview", rowheight=28)

        header = ttk.Frame(self, padding=15)
        header.pack(fill="x")
        ttk.Label(header, text="Restaurant POS Management", font=("Segoe UI", 22, "bold")).pack(anchor="w")
        ttk.Label(header, text="Simple desktop billing and order history", font=("Segoe UI", 10)).pack(anchor="w")

        content = ttk.Frame(self, padding=(15, 0, 15, 15))
        content.pack(fill="both", expand=True)
        content.columnconfigure(1, weight=1)
        content.rowconfigure(0, weight=1)

        order_frame = ttk.LabelFrame(content, text="New Order", padding=15)
        order_frame.grid(row=0, column=0, sticky="nsw", padx=(0, 12))

        ttk.Label(order_frame, text="Customer name").grid(row=0, column=0, sticky="w", pady=(0, 5))
        ttk.Entry(order_frame, textvariable=self.customer_var, width=28).grid(row=1, column=0, pady=(0, 15))

        ttk.Label(order_frame, text="Menu", font=("Segoe UI", 11, "bold")).grid(row=2, column=0, sticky="w", pady=(0, 8))
        for row, (name, price) in enumerate(MENU.items(), start=3):
            ttk.Label(order_frame, text=f"{name} — ₹{price:,.0f}").grid(row=row, column=0, sticky="w", pady=3)
            ttk.Spinbox(order_frame, from_=0, to=99, textvariable=self.quantity_vars[name], width=8).grid(row=row, column=1, padx=(10, 0))

        ttk.Separator(order_frame).grid(row=7, column=0, columnspan=2, sticky="ew", pady=15)
        totals = [("Subtotal", self.subtotal_var), ("GST (18%)", self.tax_var), ("Service (5%)", self.service_var), ("Grand Total", self.total_var)]
        for row, (label, variable) in enumerate(totals, start=8):
            ttk.Label(order_frame, text=label).grid(row=row, column=0, sticky="w", pady=3)
            ttk.Label(order_frame, textvariable=variable, font=("Segoe UI", 10, "bold")).grid(row=row, column=1, sticky="e", pady=3)

        buttons = ttk.Frame(order_frame)
        buttons.grid(row=12, column=0, columnspan=2, pady=(15, 0), sticky="ew")
        ttk.Button(buttons, text="Calculate", command=self.calculate).pack(side="left", padx=(0, 5))
        ttk.Button(buttons, text="Save Order", command=self.save_order).pack(side="left", padx=5)
        ttk.Button(buttons, text="Reset", command=self.reset).pack(side="left", padx=5)

        history_frame = ttk.LabelFrame(content, text="Order History", padding=10)
        history_frame.grid(row=0, column=1, sticky="nsew")
        history_frame.rowconfigure(0, weight=1)
        history_frame.columnconfigure(0, weight=1)

        columns = ("order", "customer", "subtotal", "tax", "service", "total", "date")
        self.tree = ttk.Treeview(history_frame, columns=columns, show="headings")
        headings = {
            "order": "Order ID", "customer": "Customer", "subtotal": "Subtotal",
            "tax": "GST", "service": "Service", "total": "Total", "date": "Created"
        }
        for column in columns:
            self.tree.heading(column, text=headings[column])
            self.tree.column(column, width=105, anchor="center")
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(history_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

        ttk.Button(history_frame, text="Delete Selected Order", command=self.delete_selected).grid(row=1, column=0, sticky="e", pady=(10, 0))

    def quantities(self):
        result = {}
        for name, variable in self.quantity_vars.items():
            try:
                quantity = int(variable.get())
            except ValueError:
                raise ValueError(f"Quantity for {name} must be a whole number.")
            if quantity < 0:
                raise ValueError(f"Quantity for {name} cannot be negative.")
            result[name] = quantity
        if not any(result.values()):
            raise ValueError("Add at least one item to the order.")
        return result

    def calculate(self):
        try:
            quantities = self.quantities()
        except ValueError as exc:
            messagebox.showwarning("Check order", str(exc))
            return None

        subtotal = sum(MENU[name] * quantity for name, quantity in quantities.items())
        tax = subtotal * TAX_RATE
        service = subtotal * SERVICE_RATE
        total = subtotal + tax + service
        self.subtotal_var.set(f"₹{subtotal:,.2f}")
        self.tax_var.set(f"₹{tax:,.2f}")
        self.service_var.set(f"₹{service:,.2f}")
        self.total_var.set(f"₹{total:,.2f}")
        return quantities, subtotal, tax, service, total

    def save_order(self):
        customer = self.customer_var.get().strip()
        if not customer:
            messagebox.showwarning("Missing customer", "Enter the customer name first.")
            return
        calculated = self.calculate()
        if not calculated:
            return
        quantities, subtotal, tax, service, total = calculated
        order_id = f"ORD-{datetime.now().strftime('%Y%m%d-%H%M%S-%f')[:-3]}"
        self.database.save_order(order_id, customer, quantities, subtotal, tax, service, total)
        messagebox.showinfo("Order saved", f"Order {order_id} saved successfully.")
        self.reset()
        self.refresh_orders()

    def refresh_orders(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for row in self.database.recent_orders():
            order_id, customer, subtotal, tax, service, total, created = row
            self.tree.insert("", "end", values=(order_id, customer, f"₹{subtotal:,.2f}", f"₹{tax:,.2f}", f"₹{service:,.2f}", f"₹{total:,.2f}", created))

    def delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No selection", "Select an order to delete.")
            return
        values = self.tree.item(selected[0], "values")
        order_id = values[0]
        if messagebox.askyesno("Delete order", f"Delete {order_id}?"):
            self.database.delete_order(order_id)
            self.refresh_orders()

    def reset(self):
        self.customer_var.set("")
        for variable in self.quantity_vars.values():
            variable.set("0")
        self.subtotal_var.set("₹0.00")
        self.tax_var.set("₹0.00")
        self.service_var.set("₹0.00")
        self.total_var.set("₹0.00")


if __name__ == "__main__":
    RestaurantPOS().mainloop()
