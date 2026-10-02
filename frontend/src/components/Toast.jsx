import React from 'react';

export default function Toast({ toast }) {
  if (!toast?.visible) return null;

  return (
    <div className={`toast-notification ${toast.visible ? 'show' : ''}`}>
      <svg className="toast-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
        <polyline points="20 6 9 17 4 12" />
      </svg>
      <span>{toast.message}</span>
    </div>
  );
}
