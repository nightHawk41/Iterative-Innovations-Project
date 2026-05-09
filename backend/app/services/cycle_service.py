"""
====================================
backend/app/services/cycle_service.py
====================================
Service for managing sales cycles.

Handles cycle rotation when new inventory is uploaded.
"""

import logging
from datetime import datetime, timezone

from app import db
from app.models.sales_cycle import SalesCycle

logger = logging.getLogger(__name__)


class CycleService:
    """
    Manages sales cycle lifecycle:
    - Closing the current active cycle when new inventory is uploaded
    - Creating a new active cycle for fresh transaction reporting
    """

    @staticmethod
    def rotate_cycle() -> SalesCycle:
        """
        End the current active cycle and create a new one.
        
        This is called when new inventory is uploaded to isolate
        sales reporting by inventory batch.
        
        Returns:
            The newly created active SalesCycle
            
        Raises:
            RuntimeError if cycle creation fails
        """
        try:
            # Step 1: Close the current active cycle
            active_cycle = db.session.query(SalesCycle).filter_by(is_active=True).first()
            
            if active_cycle:
                active_cycle.is_active = False
                active_cycle.ended_at = datetime.now(timezone.utc)
                db.session.flush()
                
                logger.info(
                    "[CycleService] Closed sales cycle %d", 
                    active_cycle.cycle_id
                )
            
            # Step 2: Create a new active cycle
            new_cycle = SalesCycle(
                started_at=datetime.now(timezone.utc),
                is_active=True
            )
            db.session.add(new_cycle)
            db.session.flush()
            
            logger.info(
                "[CycleService] Created new sales cycle %d", 
                new_cycle.cycle_id
            )
            
            return new_cycle
            
        except Exception as exc:
            logger.error(
                "[CycleService] Failed to rotate cycle: %s", exc
            )
            db.session.rollback()
            raise RuntimeError(f"Failed to rotate sales cycle: {exc}")
