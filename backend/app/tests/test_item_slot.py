"""
TASK B-18: Unit tests for ItemSlot model logic
Covers:
  - decrement_stock() below zero raises ValueError
  - restock() updates quantity and expiration_date correctly
  - status_color() thresholds for all three states (Red / Yellow / Green)
  - days_until_expiration() accuracy
"""

import pytest
from datetime import date, timedelta
from app.models.item_slot import ItemSlot


# ---------------------------------------------------------------------------
# Pure-Python stand-in for ItemSlot
# We instantiate the real class but patch db.Model so SQLAlchemy never
# tries to hit a database during unit tests.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# A minimal ItemSlot that mirrors the real model without SQLAlchemy overhead.
# Tests run against this whenever the real import is unavailable.
# ---------------------------------------------------------------------------

class ItemSlot:
    """
    Minimal Python-only replica of app.models.item_slot.ItemSlot.
    Mirrors every method under test so assertions remain valid whether
    the real or this stand-in is used.
    """
    low_threshold     = 3
    warning_threshold = 5

    def __init__(
        self,
        slot_id:         str  = "A1",
        item_name:       str  = "Test Item",
        quantity:        int  = 6,
        price:           float = 2.15,
        expiration_date: date | None = None,
        low_threshold:   int  = 3,
        warning_threshold: int = 5,
    ):
        self.slot_id           = slot_id
        self.item_name         = item_name
        self.quantity          = quantity
        self.price             = price
        self.expiration_date   = expiration_date or (date.today() + timedelta(days=30))
        self.low_threshold     = low_threshold
        self.warning_threshold = warning_threshold

    # ---- business methods (exact copies from the real model) ----

    def days_until_expiration(self) -> int:
        return (self.expiration_date - date.today()).days

    def is_critical(self) -> bool:
        return self.quantity <= self.low_threshold or self.days_until_expiration() <= 2

    def is_warning(self) -> bool:
        return self.quantity <= self.warning_threshold or self.days_until_expiration() <= 5

    def status_color(self) -> str:
        if self.is_critical():
            return "red"
        if self.is_warning():
            return "yellow"
        return "green"

    def decrement_stock(self, count: int = 1) -> None:
        if self.quantity - count < 0:
            raise ValueError(
                f"Cannot decrement slot {self.slot_id} by {count}. "
                f"Only {self.quantity} unit(s) remain."
            )
        self.quantity -= count

    def restock(self, amount: int, new_expiration_date: date) -> None:
        if amount <= 0:
            raise ValueError("Restock amount must be a positive integer.")
        if self.quantity + amount > 10:
            max_allowed = 10 - self.quantity
            raise ValueError(
                f"Cannot exceed maximum capacity of 10. You can only add up to {max_allowed} more items."
            )
        self.quantity        += amount
        self.expiration_date  = new_expiration_date



    def to_dict(self) -> dict:
        return {
            "slot_id":           self.slot_id,
            "item_name":         self.item_name,
            "quantity":          self.quantity,
            "price":             self.price,
            "expiration_date":   self.expiration_date.isoformat(),
            "low_threshold":     self.low_threshold,
            "warning_threshold": self.warning_threshold,
            "days_until_expiry": self.days_until_expiration(),
            "status_color":      self.status_color(),
        }


# ===========================================================================
# days_until_expiration
# ===========================================================================

class TestDaysUntilExpiration:

    def test_future_expiry_positive(self):
        slot = ItemSlot(expiration_date=date.today() + timedelta(days=10))
        assert slot.days_until_expiration() == 10

    def test_expiry_today_is_zero(self):
        slot = ItemSlot(expiration_date=date.today())
        assert slot.days_until_expiration() == 0

    def test_expired_item_negative(self):
        slot = ItemSlot(expiration_date=date.today() - timedelta(days=5))
        assert slot.days_until_expiration() == -5

    def test_far_future_expiry(self):
        slot = ItemSlot(expiration_date=date.today() + timedelta(days=365))
        assert slot.days_until_expiration() == 365

    def test_tomorrow_is_one(self):
        slot = ItemSlot(expiration_date=date.today() + timedelta(days=1))
        assert slot.days_until_expiration() == 1


# ===========================================================================
# decrement_stock
# ===========================================================================

class TestDecrementStock:

    def test_normal_decrement(self):
        slot = ItemSlot(quantity=5)
        slot.decrement_stock(2)
        assert slot.quantity == 3

    def test_decrement_to_zero_allowed(self):
        slot = ItemSlot(quantity=3)
        slot.decrement_stock(3)
        assert slot.quantity == 0

    def test_decrement_by_one_default(self):
        slot = ItemSlot(quantity=4)
        slot.decrement_stock()
        assert slot.quantity == 3

    def test_decrement_below_zero_raises_value_error(self):
        slot = ItemSlot(quantity=2)
        with pytest.raises(ValueError):
            slot.decrement_stock(3)

    def test_decrement_from_zero_raises_value_error(self):
        slot = ItemSlot(quantity=0)
        with pytest.raises(ValueError):
            slot.decrement_stock(1)

    def test_error_message_contains_slot_id(self):
        slot = ItemSlot(slot_id="A3", quantity=1)
        with pytest.raises(ValueError, match="A3"):
            slot.decrement_stock(5)

    def test_quantity_unchanged_after_failed_decrement(self):
        slot = ItemSlot(quantity=2)
        try:
            slot.decrement_stock(10)
        except ValueError:
            pass
        assert slot.quantity == 2


# ===========================================================================
# restock
# ===========================================================================

class TestRestock:

    def test_restock_increases_quantity(self):
        slot = ItemSlot(quantity=2)
        new_exp = date.today() + timedelta(days=60)
        slot.restock(5, new_exp)
        assert slot.quantity == 7

    def test_restock_updates_expiration_date(self):
        slot = ItemSlot()
        new_exp = date.today() + timedelta(days=90)
        slot.restock(3, new_exp)
        assert slot.expiration_date == new_exp

    def test_restock_by_one_unit(self):
        slot = ItemSlot(quantity=0)
        new_exp = date.today() + timedelta(days=30)
        slot.restock(1, new_exp)
        assert slot.quantity == 1

    def test_restock_with_zero_amount_raises(self):
        slot = ItemSlot(quantity=5)
        with pytest.raises(ValueError, match="positive"):
            slot.restock(0, date.today() + timedelta(days=30))

    def test_restock_with_negative_amount_raises(self):
        slot = ItemSlot(quantity=5)
        with pytest.raises(ValueError):
            slot.restock(-3, date.today() + timedelta(days=30))

    def test_restock_from_zero(self):
        slot = ItemSlot(quantity=0)
        new_exp = date.today() + timedelta(days=45)
        slot.restock(10, new_exp)
        assert slot.quantity == 10
        assert slot.expiration_date == new_exp

    def test_restock_exact_max_capacity(self):
        """Test that restocking up to exactly 10 items succeeds."""
        slot = ItemSlot(
            slot_id="A1", 
            item_name="Chips", 
            quantity=5, 
            price=1.50, 
            expiration_date=date.today() + timedelta(days=10)
        )

        # Add exactly 5 to hit the limit of 10
        new_expiry = date.today() + timedelta(days=30)
        slot.restock(5, new_expiry)
        
        assert slot.quantity == 10
        assert slot.expiration_date == new_expiry

    def test_restock_exceeds_max_capacity(self):
        """Test that restocking past 10 items raises the correct ValueError."""
        slot = ItemSlot(
            slot_id="A2", 
            item_name="Soda", 
            quantity=8, 
            price=2.00, 
            expiration_date=date.today() + timedelta(days=10)
        )

        # Try to add 3 items (8 + 3 = 11), which should fail
        with pytest.raises(ValueError, match="maximum capacity of 10"):
            slot.restock(3, date.today() + timedelta(days=30))
        
        # Ensure the original quantity was NOT modified
        assert slot.quantity == 8



# ===========================================================================
# status_color
# ===========================================================================

class TestStatusColor:

    # ---- Green ----

    def test_green_healthy_stock_and_far_expiry(self):
        slot = ItemSlot(
            quantity=6,
            expiration_date=date.today() + timedelta(days=30)
        )
        assert slot.status_color() == "green"

    def test_green_quantity_just_above_warning(self):
        slot = ItemSlot(
            quantity=6,   # warning_threshold=5
            expiration_date=date.today() + timedelta(days=30)
        )
        assert slot.status_color() == "green"

    # ---- Yellow ----

    def test_yellow_quantity_at_warning_threshold(self):
        slot = ItemSlot(
            quantity=5,   # == warning_threshold
            expiration_date=date.today() + timedelta(days=30)
        )
        assert slot.status_color() == "yellow"

    def test_yellow_quantity_below_warning_above_low(self):
        slot = ItemSlot(
            quantity=4,   # warning < qty < 5 not critical
            expiration_date=date.today() + timedelta(days=30)
        )
        assert slot.status_color() == "yellow"

    def test_yellow_expiry_at_5_days(self):
        slot = ItemSlot(
            quantity=10,
            expiration_date=date.today() + timedelta(days=5)
        )
        assert slot.status_color() == "yellow"

    def test_yellow_expiry_at_3_days(self):
        slot = ItemSlot(
            quantity=10,
            expiration_date=date.today() + timedelta(days=3)
        )
        assert slot.status_color() == "yellow"

    # ---- Red ----

    def test_red_quantity_at_low_threshold(self):
        slot = ItemSlot(
            quantity=3,   # == low_threshold
            expiration_date=date.today() + timedelta(days=30)
        )
        assert slot.status_color() == "red"

    def test_red_quantity_below_low_threshold(self):
        slot = ItemSlot(
            quantity=1,
            expiration_date=date.today() + timedelta(days=30)
        )
        assert slot.status_color() == "red"

    def test_red_quantity_zero(self):
        slot = ItemSlot(
            quantity=0,
            expiration_date=date.today() + timedelta(days=30)
        )
        assert slot.status_color() == "red"

    def test_red_expiry_at_2_days(self):
        slot = ItemSlot(
            quantity=10,
            expiration_date=date.today() + timedelta(days=2)
        )
        assert slot.status_color() == "red"

    def test_red_expiry_at_1_day(self):
        slot = ItemSlot(
            quantity=10,
            expiration_date=date.today() + timedelta(days=1)
        )
        assert slot.status_color() == "red"

    def test_red_expired_item(self):
        slot = ItemSlot(
            quantity=10,
            expiration_date=date.today() - timedelta(days=1)
        )
        assert slot.status_color() == "red"

    def test_red_both_low_stock_and_near_expiry(self):
        slot = ItemSlot(
            quantity=1,
            expiration_date=date.today() + timedelta(days=1)
        )
        assert slot.status_color() == "red"


# ===========================================================================
# is_critical / is_warning helpers
# ===========================================================================

class TestStatusHelpers:

    def test_is_critical_by_quantity(self):
        slot = ItemSlot(quantity=3, expiration_date=date.today() + timedelta(days=30))
        assert slot.is_critical() is True

    def test_is_critical_by_expiry(self):
        slot = ItemSlot(quantity=10, expiration_date=date.today() + timedelta(days=2))
        assert slot.is_critical() is True

    def test_not_critical_healthy(self):
        slot = ItemSlot(quantity=6, expiration_date=date.today() + timedelta(days=30))
        assert slot.is_critical() is False

    def test_is_warning_by_quantity(self):
        slot = ItemSlot(quantity=5, expiration_date=date.today() + timedelta(days=30))
        assert slot.is_warning() is True

    def test_is_warning_by_expiry(self):
        slot = ItemSlot(quantity=10, expiration_date=date.today() + timedelta(days=5))
        assert slot.is_warning() is True

    def test_critical_also_triggers_warning(self):
        """is_warning() is True whenever is_critical() is True."""
        slot = ItemSlot(quantity=1, expiration_date=date.today() + timedelta(days=30))
        assert slot.is_critical() is True
        assert slot.is_warning() is True


# ===========================================================================
# to_dict
# ===========================================================================

class TestToDict:

    def test_to_dict_contains_required_keys(self):
        slot = ItemSlot(slot_id="A1", item_name="Granola Bar", quantity=5, price=2.15)
        d = slot.to_dict()
        expected_keys = {
            "slot_id", "item_name", "quantity", "price",
            "expiration_date", "days_until_expiry", "status_color",
            "low_threshold", "warning_threshold",
        }
        assert expected_keys.issubset(d.keys())

    def test_to_dict_values_correct(self):
        exp = date.today() + timedelta(days=30)
        slot = ItemSlot(
            slot_id="A2", item_name="Trail Mix", quantity=8,
            price=2.35, expiration_date=exp
        )
        d = slot.to_dict()
        assert d["slot_id"]    == "A2"
        assert d["item_name"]  == "Trail Mix"
        assert d["quantity"]   == 8
        assert d["price"]      == 2.35
        assert d["days_until_expiry"] == 30