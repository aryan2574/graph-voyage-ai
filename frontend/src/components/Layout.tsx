import { ReactNode } from "react";
import { Link, useLocation } from "react-router-dom";
import { Plane, BarChart3, Info } from "lucide-react";
import "./Layout.css";

interface LayoutProps {
  children: ReactNode;
}

const Layout = ({ children }: LayoutProps) => {
  const location = useLocation();

  return (
    <div className="layout">
      <nav className="navbar">
        <div className="navbar-container">
          <Link to="/" className="navbar-brand">
            <div className="brand-logo">
              <Plane className="brand-icon" />
            </div>
            <div className="brand-content">
              <span className="brand-text gradient-text">graph-voyage-ai</span>
              <span className="brand-tagline">AI Travel Intelligence</span>
            </div>
          </Link>

          <div className="navbar-links">
            <Link
              to="/"
              className={`nav-link ${location.pathname === "/" ? "active" : ""}`}
            >
              <Plane size={18} />
              Travel Planner
            </Link>
            <Link
              to="/dashboard"
              className={`nav-link ${location.pathname === "/dashboard" ? "active" : ""}`}
            >
              <BarChart3 size={18} />
              Dashboard
            </Link>
            <Link
              to="/about"
              className={`nav-link ${location.pathname === "/about" ? "active" : ""}`}
            >
              <Info size={18} />
              About
            </Link>
          </div>
        </div>
      </nav>

      <main className="main-content">{children}</main>

      <footer className="footer">
        <p>Built with FastAPI, LangGraph, React, TypeScript, and PostgreSQL</p>
        <p className="footer-copyright">
          © 2026 graph-voyage-ai - Multi-Agent Travel Planning System
        </p>
      </footer>
    </div>
  );
};

export default Layout;
