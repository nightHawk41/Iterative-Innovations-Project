import logging
from typing import Optional
from app.models.item_slot import ItemSlot
from app.repositories.item_slot_repository import ItemSlotRepository

logger = logging.getLogger(__name__)


class MappingService:
    """
    Resolves a transaction amount to its corresponding ItemSlot using the
    unique-price mapping strategy at the core of this project's business logic.

    Every slot is assigned a unique price. When a transaction amount arrives
    from the CBORD CSV log, this service looks up the matching slot — enabling
    the system to identify which item was sold from an otherwise item-blind log.
    """

    def __init__(self, repository: Optional[ItemSlotRepository] = None):
        # Repository is injected so it can be swapped with a mock in unit tests.
        self._repo = repository or ItemSlotRepository()

    # ------------------------------------------------------------------
    # Core mapping
    # ------------------------------------------------------------------

    def resolve_slot_by_amount(self, amount: float) -> ItemSlot:
        """
        Look up the ItemSlot whose price matches the given transaction amount.

        Rounds the amount to 2 decimal places before querying to guard against
        floating-point representation drift common in CSV-sourced values
        (e.g. 2.1499999 should resolve to the $2.15 slot).

        Returns:
            The matching ItemSlot instance.

        Raises:
            LookupError: if no slot with the given price exists.
        """
        rounded = round(amount, 2)
        slot = self._repo.get_by_price(rounded)

        if slot is None:
            logger.warning(
                "[MappingService] No slot found for amount: $%.2f", rounded
            )
            raise LookupError(
                f"No ItemSlot configured for transaction amount ${rounded:.2f}. "
                "The price may be missing from inventory_config.csv or the "
                "transaction amount may be incorrect."
            )

        logger.info(
            "[MappingService] $%.2f -> slot %s (%s)",
            rounded, slot.slot_id, slot.item_name,
        )
        return slot

    # ------------------------------------------------------------------
    # Startup validation
    # ------------------------------------------------------------------

    def has_price_collision(self) -> bool:
        """
        Check whether any two slots share the same price.

        A collision makes price-to-slot mapping ambiguous and must be treated
        as a configuration error. This should be called at startup after the
        inventory config is loaded.

        Returns:
            True  if at least one duplicate price is found (collision exists).
            False if all prices are unique (mapping is safe).
        """
        prices = self._repo.get_all_prices()  # sorted ascending

        seen: set[float] = set()
        collisions: list[float] = []

        for price in prices:
            key = round(price, 2)
            if key in seen:
                collisions.append(key)
            seen.add(key)

        if collisions:
            for dup in set(collisions):
                logger.error(
                    "[MappingService] Price collision: $%.2f is assigned to more "
                    "than one slot — mapping is ambiguous for this amount.", dup
                )
            return True

        return False

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def get_price_map(self) -> dict[float, str]:
        """
        Return a snapshot of the current price -> slot_id mapping.

        Useful for startup logging and debugging the price configuration.
        Example: { 2.15: 'A1', 2.35: 'A2', ... }
        """
        slots = self._repo.get_all()
        return {round(slot.price, 2): slot.slot_id for slot in slots}
