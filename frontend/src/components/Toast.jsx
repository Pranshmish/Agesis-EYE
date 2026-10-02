import React from 'react';

export default function Toast({ toast }) {
  if (!toast?.visible) return null;

  return (
    <div className={`toast-notification ${toast.visible ? 'show' : ''}`}>
      <span className="toast-icon">✓</span>
      <span>{toast.message}</span>
    </div>
  );
}
