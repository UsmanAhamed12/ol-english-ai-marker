import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { FilePlus2, Library, LogOut, NotebookPen } from "lucide-react";
import { useAuth } from "./../../hooks/useAuth.jsx";

const NAV = [
  { to: "/papers", label: "Papers", icon: NotebookPen },
  { to: "/knowledge", label: "Knowledge", icon: Library },
  { to: "/new", label: "New marking", icon: FilePlus2 },
];

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const signOut = () => {
    logout();
    navigate("/login", { replace: true });
  };

  return (
    <div className="min-h-screen">
      <header className="no-print sticky top-0 z-10 border-b border-line bg-paper/90 backdrop-blur">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-5 gap-y-2 px-5 py-3 sm:px-8">
          <NavLink to="/" className="flex items-center gap-2.5">
            <span className="display text-lg font-semibold leading-none">Red Pen</span>
            <span className="text-[0.5rem] font-medium uppercase leading-[1.3] tracking-[0.16em] text-inkSoft">
              O/L English marking
              <br />
              Studio
            </span>
          </NavLink>

          <nav className="order-3 flex w-full gap-1 sm:order-2 sm:w-auto">
            {NAV.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  `inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium transition ${
                    isActive ? "bg-ink text-paper" : "text-inkSoft hover:bg-paperDeep hover:text-ink"
                  }`
                }
              >
                <Icon className="h-3.5 w-3.5" />
                {label}
              </NavLink>
            ))}
          </nav>

          <div className="ml-auto flex items-center gap-3">
            <span className="hidden text-xs text-inkSoft sm:block">{user?.email}</span>
            <button
              type="button"
              onClick={signOut}
              className="inline-flex items-center gap-1.5 text-xs text-inkSoft transition hover:text-ink"
            >
              <LogOut className="h-3.5 w-3.5" /> Sign out
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-5 pb-24 pt-8 sm:px-8">
        <Outlet />
      </main>
    </div>
  );
}