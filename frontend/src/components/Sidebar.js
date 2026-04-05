import React, { useState } from "react";
import { NavLink } from "react-router-dom";

function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);

  const linkClass = ({ isActive }) =>
    "nav-link text-white" + (isActive ? " active-link" : "");

  return (
    <>
      {/* Mobile top bar — visible only on small screens */}
      <nav className="navbar navbar-dark bg-dark d-md-none px-3">
        <span className="navbar-brand fw-bold">UMBC Vending</span>
        <button
          className="navbar-toggler"
          type="button"
          onClick={() => setCollapsed(!collapsed)}
          aria-expanded={collapsed}
          aria-label="Toggle navigation"
        >
          <span className="navbar-toggler-icon" />
        </button>
        {collapsed && (
          <div className="w-100 mt-2">
            <ul className="navbar-nav">
              <li className="nav-item">
                <NavLink to="/dashboard" className={linkClass} onClick={() => setCollapsed(false)}>
                  Dashboard
                </NavLink>
              </li>
              <li className="nav-item">
                <NavLink to="/admin" className={linkClass} onClick={() => setCollapsed(false)}>
                  Admin Panel
                </NavLink>
              </li>
            </ul>
          </div>
        )}
      </nav>

      {/* Desktop sidebar — visible only on md+ screens */}
      <nav className="sidebar d-none d-md-flex flex-column bg-dark text-white p-3">
        <h5 className="sidebar-brand">UMBC Vending</h5>
        <hr className="border-secondary" />
        <ul className="nav flex-column gap-1">
          <li className="nav-item">
            <NavLink to="/dashboard" className={linkClass}>
              Dashboard
            </NavLink>
          </li>
          <li className="nav-item">
            <NavLink to="/admin" className={linkClass}>
              Admin Panel
            </NavLink>
          </li>
        </ul>
      </nav>
    </>
  );
}

export default Sidebar;