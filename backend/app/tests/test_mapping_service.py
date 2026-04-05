"""
TASK B-17: Unit tests for MappingService
Covers:
  - Exact price match → returns correct ItemSlot
  - No match (unknown amount) → raises LookupError
  - Duplicate/colliding prices → has_price_collision() returns True
"""

import pytest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers — build lightweight ItemSlot stand-ins without a DB
# ---------------------------------------------------------------------------

def _make_slot(slot_id: str, item_name: str, price: float):
    """Return a simple mock that quacks like an ItemSlot."""
    slot = MagicMock()
    slot.slot_id   = slot_id
    slot.item_name = item_name
    slot.price     = price
    return slot


# ---------------------------------------------------------------------------
# Fixture — a MappingService whose repository is fully mocked
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_repo():
    return MagicMock()


@pytest.fixture
def service(mock_repo):
    # Import here so Flask-SQLAlchemy doesn't blow up at collection time.
    from app.services.mapping_service import MappingService
    return MappingService(repository=mock_repo)


# ===========================================================================
# resolve_slot_by_amount
# ===========================================================================

class TestResolveSlotByAmount:

    def test_exact_price_match_returns_slot(self, service, mock_repo):
        """A transaction amount that matches a slot price returns that slot."""
        expected_slot = _make_slot("A1", "Granola Bar", 2.15)
        mock_repo.get_by_price.return_value = expected_slot

        result = service.resolve_slot_by_amount(2.15)

        mock_repo.get_by_price.assert_called_once_with(2.15)
        assert result is expected_slot
        assert result.slot_id   == "A1"
        assert result.item_name == "Granola Bar"

    def test_amount_rounded_before_lookup(self, service, mock_repo):
        """Floating-point drift is rounded to 2dp before the repo query."""
        slot = _make_slot("A2", "Trail Mix", 2.35)
        mock_repo.get_by_price.return_value = slot

        # 2.3499999... should resolve to the $2.35 slot
        result = service.resolve_slot_by_amount(2.3499999)

        mock_repo.get_by_price.assert_called_once_with(2.35)
        assert result is slot

    def test_unknown_amount_raises_lookup_error(self, service, mock_repo):
        """An amount with no matching slot price raises LookupError."""
        mock_repo.get_by_price.return_value = None

        with pytest.raises(LookupError, match=r"\$9\.99"):
            service.resolve_slot_by_amount(9.99)

    def test_zero_amount_raises_lookup_error(self, service, mock_repo):
        """$0.00 has no slot and must raise LookupError."""
        mock_repo.get_by_price.return_value = None

        with pytest.raises(LookupError):
            service.resolve_slot_by_amount(0.00)

    def test_negative_amount_raises_lookup_error(self, service, mock_repo):
        """Negative amounts are not valid slot prices."""
        mock_repo.get_by_price.return_value = None

        with pytest.raises(LookupError):
            service.resolve_slot_by_amount(-1.50)

    def test_different_slots_resolved_independently(self, service, mock_repo):
        """Two different amounts map to two different slots."""
        slot_a = _make_slot("A1", "Granola Bar", 2.15)
        slot_b = _make_slot("A2", "Trail Mix",   2.35)

        mock_repo.get_by_price.side_effect = lambda price: (
            slot_a if round(price, 2) == 2.15 else
            slot_b if round(price, 2) == 2.35 else
            None
        )

        assert service.resolve_slot_by_amount(2.15) is slot_a
        assert service.resolve_slot_by_amount(2.35) is slot_b


# ===========================================================================
# has_price_collision
# ===========================================================================

class TestHasPriceCollision:

    def test_no_collision_returns_false(self, service, mock_repo):
        """All unique prices → no collision, returns False."""
        mock_repo.get_all_prices.return_value = [1.25, 1.75, 2.05, 2.15, 2.35]

        assert service.has_price_collision() is False

    def test_duplicate_prices_returns_true(self, service, mock_repo):
        """Two slots sharing the same price → collision, returns True."""
        # 2.15 appears twice
        mock_repo.get_all_prices.return_value = [1.25, 2.15, 2.15, 2.35]

        assert service.has_price_collision() is True

    def test_multiple_collision_pairs_returns_true(self, service, mock_repo):
        """Multiple duplicate pairs all detected correctly."""
        mock_repo.get_all_prices.return_value = [1.25, 1.25, 2.15, 2.15, 3.00]

        assert service.has_price_collision() is True

    def test_empty_price_list_returns_false(self, service, mock_repo):
        """No slots configured → nothing to collide, returns False."""
        mock_repo.get_all_prices.return_value = []

        assert service.has_price_collision() is False

    def test_single_slot_returns_false(self, service, mock_repo):
        """A single slot cannot collide with itself."""
        mock_repo.get_all_prices.return_value = [2.15]

        assert service.has_price_collision() is False

    def test_floating_point_near_duplicates_detected(self, service, mock_repo):
        """Prices that round to the same 2dp value are treated as collisions."""
        # 2.154 rounds to 2.15; 2.156 rounds to 2.16 — no collision
        mock_repo.get_all_prices.return_value = [2.154, 2.156]
        assert service.has_price_collision() is False

        # But 2.150 and 2.151 both round to 2.15 → collision
        mock_repo.get_all_prices.return_value = [2.150, 2.151]
        assert service.has_price_collision() is True


# ===========================================================================
# get_price_map (bonus utility coverage)
# ===========================================================================

class TestGetPriceMap:

    def test_returns_price_to_slot_id_dict(self, service, mock_repo):
        """get_price_map() returns {price: slot_id} for all slots."""
        slots = [
            _make_slot("A1", "Granola Bar", 2.15),
            _make_slot("A2", "Trail Mix",   2.35),
        ]
        mock_repo.get_all.return_value = slots

        result = service.get_price_map()

        assert result == {2.15: "A1", 2.35: "A2"}

    def test_empty_inventory_returns_empty_dict(self, service, mock_repo):
        mock_repo.get_all.return_value = []

        assert service.get_price_map() == {}