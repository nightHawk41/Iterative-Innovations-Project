from app import db
from app.models.item_slot import ItemSlot


class ItemSlotRepository:
	"""Repository wrapper for ItemSlot persistence and lookup operations."""

	def __init__(self, session=None):
		# Allow injection for tests; default to Flask-SQLAlchemy session.
		self.session = session or db.session

	def get_all(self) -> list[ItemSlot]:
		"""Return all item slots ordered by slot_id."""
		return ItemSlot.query.order_by(ItemSlot.slot_id.asc()).all()

	def get_by_id(self, slot_id: str) -> ItemSlot | None:
		"""Return one slot by primary key, or None when not found."""
		if not slot_id:
			return None
		return self.session.get(ItemSlot, slot_id)

	def get_by_price(self, price: float) -> ItemSlot | None:
		"""Return one slot by unique price, or None when not found."""
		return ItemSlot.query.filter_by(price=price).first()

	def save(self, slot: ItemSlot, commit: bool = True) -> ItemSlot:
		"""Persist a new or updated ItemSlot instance."""
		self.session.add(slot)
		if commit:
			self.session.commit()
		return slot

	def get_all_prices(self) -> list[float]:
		"""Return all configured prices in ascending order."""
		rows = ItemSlot.query.with_entities(ItemSlot.price).order_by(ItemSlot.price.asc()).all()
		return [price for (price,) in rows]
