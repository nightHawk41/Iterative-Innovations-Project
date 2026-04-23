import React from 'react';

function AppHeader() {
  return (
    <header className="app-header">
      <div className="logo-area">
        <svg className="umbc-shield" viewBox="0 0 52 52" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" focusable="false">
          <path d="M26 2 L50 10 L50 32 C50 44 38 50 26 52 C14 50 2 44 2 32 L2 10 Z" fill="#f0a500" stroke="#111" strokeWidth="1.5" />
          <path d="M26 6 L46 13 L46 31 C46 41 36 47 26 49 C16 47 6 41 6 31 L6 13 Z" fill="white" />
          <rect x="6" y="6" width="20" height="22" fill="#c8102e" />
          <rect x="26" y="28" width="20" height="20" fill="#c8102e" />
          <text x="14" y="21" fontSize="13" fontWeight="bold" fill="white" textAnchor="middle" fontFamily="serif">M</text>
          <text x="36" y="42" fontSize="11" fontWeight="bold" fill="white" textAnchor="middle" fontFamily="serif">BC</text>
        </svg>
        <span className="umbc-text">UMBC</span>
      </div>
      <span className="header-title">Vending Inventory System</span>
    </header>
  );
}

export default AppHeader;