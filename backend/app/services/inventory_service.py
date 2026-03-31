from datetime import date, datetime
from typing import Optional

from app import db
from app.models.transaction import Transaction
from app.repositories.item_slot_repository import ItemSlotRepository
from app.services.mapping_service import MappingService


class InventoryService:
	"""Application service that owns inventory reads and inventory mutations."""

	def __init__(
		self,
		repository: Optional[ItemSlotRepository] = None,
		mapping_service: Optional[MappingService] = None,
	):
		self._repo = repository or ItemSlotRepository()
		self._mapping = mapping_service or MappingService(self._repo)

	def get_inventory(self) -> list[dict]:
		"""Return all slots as serialized dictionaries for API responses."""
		slots = self._repo.get_all()
		return [slot.to_dict() for slot in slots]

	def restock_slot(self, slot_id: str, quantity_added: int, expiration_date) -> dict:
		"""
		Restock one slot and return the updated slot payload.

		Validation:
		- slot_id must exist
		- quantity_added must be > 0
		- expiration_date must be a valid date in the future
		"""
		if quantity_added is None or quantity_added <= 0:
			raise ValueError("quantity_added must be a positive integer.")

		parsed_expiration = self._parse_expiration_date(expiration_date)
		if parsed_expiration <= date.today():
			raise ValueError("expiration_date must be a future date.")

		slot = self._repo.get_by_id(slot_id)
		if slot is None:
			raise LookupError(f"Slot '{slot_id}' was not found.")

		try:
			slot.restock(quantity_added, parsed_expiration)
			self._repo.save(slot, commit=False)
			db.session.commit()
		except Exception:
			db.session.rollback()
			raise

		return slot.to_dict()

	def apply_sale(self, transaction: Transaction) -> dict:
		"""
		Resolve a sale by amount, decrement inventory by one, and return updated slot.

		Raises LookupError if no matching slot exists for the transaction amount.
		Raises ValueError if stock cannot be decremented (e.g., already zero).
		"""
		if transaction is None:
			raise ValueError("transaction is required.")

		try:
			slot = self._mapping.resolve_slot_by_amount(transaction.amount)
			slot.decrement_stock(1)

			# Mark the transaction with the resolved slot for downstream reporting.
			transaction.resolved_slot_id = slot.slot_id

			self._repo.save(slot, commit=False)
			db.session.add(transaction)
			db.session.commit()
		except Exception:
			db.session.rollback()
			raise

		return slot.to_dict()

	@staticmethod
	def _parse_expiration_date(value) -> date:
		"""Accept date objects or ISO date strings and return a date object."""
		if isinstance(value, date):
			return value

		if isinstance(value, str):
			try:
				return datetime.strptime(value, "%Y-%m-%d").date()
			except ValueError as exc:
				raise ValueError(
					"expiration_date must be in 'YYYY-MM-DD' format."
				) from exc

		raise ValueError("expiration_date must be a date or YYYY-MM-DD string.")
