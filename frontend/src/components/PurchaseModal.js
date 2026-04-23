import React from "react";
import { Button, Modal } from "react-bootstrap";

function PurchaseModal({ show, slot, submitting, onConfirm, onHide }) {
  if (!slot) {
    return null;
  }

  return (
    <Modal show={show} onHide={onHide} centered>
      <Modal.Header closeButton>
        <Modal.Title>Confirm Purchase</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <p className="mb-2">
          Purchase <strong>{slot.item_name}</strong>?
        </p>
        <div className="text-muted small">Slot: {slot.slot_id}</div>
        <div className="text-muted small">Price: ${slot.price.toFixed(2)}</div>
      </Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" onClick={onHide} disabled={submitting}>
          Cancel
        </Button>
        <Button variant="primary" onClick={onConfirm} disabled={submitting}>
          {submitting ? "Confirming…" : "Confirm"}
        </Button>
      </Modal.Footer>
    </Modal>
  );
}

export default PurchaseModal;