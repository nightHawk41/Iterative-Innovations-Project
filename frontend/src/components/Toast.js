import React, { useEffect, useRef, useState } from 'react';
import { registerToast } from '../utils/toast';

function Toast() {
  const [message, setMessage] = useState('');
  const [visible, setVisible] = useState(false);
  const hideTimeoutRef = useRef(null);

  useEffect(() => {
    registerToast((msg) => {
      setMessage(String(msg ?? ''));
      setVisible(true);

      if (hideTimeoutRef.current) {
        window.clearTimeout(hideTimeoutRef.current);
      }

      hideTimeoutRef.current = window.setTimeout(() => {
        setVisible(false);
      }, 3000);
    });

    return () => {
      registerToast(null);
      if (hideTimeoutRef.current) {
        window.clearTimeout(hideTimeoutRef.current);
      }
    };
  }, []);

  return (
    <div className={`toast ${visible ? 'show' : ''}`} role="status" aria-live="polite">
      {message}
    </div>
  );
}

export default Toast;
