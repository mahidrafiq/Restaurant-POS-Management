"""Regression tests for the restaurant database layer.

These exercise database integrity only, not the Tkinter UI. ``main.py``
imports Tkinter at module load and defines a ``tk.Tk`` subclass, so a small
stub is installed first when Tkinter is unavailable. That keeps these
database tests runnable on a headless CI runner.
"""
import sqlite3
import sys
import types

import pytest


def _install_tkinter_stub_if_missing():
    try:
        import tkinter  # noqa: F401
        return
    except Exception:
        pass

    tkinter = types.ModuleType("tkinter")

    class _Tk:
        def __init__(self, *args, **kwargs):
            pass

    tkinter.Tk = _Tk
    ttk = types.ModuleType("tkinter.ttk")
    messagebox = types.ModuleType("tkinter.messagebox")
    tkinter.ttk = ttk
    tkinter.messagebox = messagebox
    sys.modules["tkinter"] = tkinter
    sys.modules["tkinter.ttk"] = ttk
    sys.modules["tkinter.messagebox"] = messagebox


_install_tkinter_stub_if_missing()

import main  # noqa: E402  (imported after the Tkinter stub on purpose)


def test_foreign_keys_are_enabled_on_every_connection(tmp_path):
    db = main.RestaurantDatabase(tmp_path / "restaurant.db")
    with db.connect() as conn:
        assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1


def test_order_items_require_an_existing_order(tmp_path):
    db = main.RestaurantDatabase(tmp_path / "restaurant.db")
    with pytest.raises(sqlite3.IntegrityError):
        with db.connect() as conn:
            conn.execute(
                "INSERT INTO order_items (order_id, item_name, quantity, unit_price)"
                " VALUES (?, ?, ?, ?)",
                ("MISSING-ORDER", "Pizza", 1, 240.0),
            )


def test_saving_then_deleting_an_order_removes_its_items(tmp_path):
    db = main.RestaurantDatabase(tmp_path / "restaurant.db")
    items = {name: 0 for name in main.MENU}
    items["Pizza"] = 2

    db.save_order("ORD-TEST", "Test Customer", items, 480.0, 86.4, 24.0, 590.4)

    with db.connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM order_items").fetchone()[0] == 1

    db.delete_order("ORD-TEST")

    with db.connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM order_items").fetchone()[0] == 0
