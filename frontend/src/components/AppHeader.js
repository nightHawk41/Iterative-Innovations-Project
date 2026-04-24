import React from 'react';
import umbcLogo from "../assets/umbc-logo.png";
function AppHeader() {
return (
<header className="app-header">
<div className="logo-area">
<img src={umbcLogo} alt="UMBC Logo" className="umbc-logo" />
</div>
<span className="header-title">Vending Inventory System</span>
</header>
);
}

export default AppHeader;