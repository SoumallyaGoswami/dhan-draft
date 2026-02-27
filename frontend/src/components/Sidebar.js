import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { LayoutDashboard, GraduationCap, BarChart3, Wallet, ShieldCheck, Sparkles, LogOut, ChevronRight } from 'lucide-react';

const navItems = [
  { to: '/overview', label: 'Overview', icon: LayoutDashboard },
  { to: '/learn', label: 'Learn', icon: GraduationCap },
  { to: '/markets', label: 'Markets', icon: BarChart3 },
  { to: '/portfolio', label: 'Portfolio & Tax', icon: Wallet },
  { to: '/risk', label: 'Risk & Safety', icon: ShieldCheck },
  { to: '/advisor', label: 'AI Advisor', icon: Sparkles },
];

export const Sidebar = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <aside className="w-[280px] h-screen bg-white border-r border-gray-100 flex flex-col py-8 px-5 shrink-0" data-testid="sidebar">
      <div className="mb-10 px-3">
        <h1 className="text-xl font-bold tracking-tight text-gray-900" data-testid="app-logo">
          <span className="text-dhan-blue">Dhan</span>Draft
        </h1>
        <p className="text-xs text-gray-400 mt-1 font-medium tracking-wide">Financial Intelligence</p>
      </div>

      <nav className="flex-1 space-y-1" data-testid="sidebar-nav">
        {navItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            data-testid={`nav-${to.slice(1)}`}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-3 rounded-2xl text-sm font-medium transition-colors duration-200 group ${
                isActive
                  ? 'bg-dhan-blue text-white shadow-sm'
                  : 'text-gray-500 hover:text-gray-900 hover:bg-gray-50'
              }`
            }
          >
            <Icon className="w-[18px] h-[18px]" strokeWidth={1.8} />
            <span>{label}</span>
            <ChevronRight className="w-3.5 h-3.5 ml-auto opacity-0 group-hover:opacity-50 transition-opacity duration-200" />
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-gray-100 pt-5 mt-4 px-3">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-9 h-9 rounded-full bg-gradient-to-br from-dhan-blue to-blue-400 flex items-center justify-center text-white text-sm font-semibold">
            {user?.name?.charAt(0)?.toUpperCase() || 'U'}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-900 truncate" data-testid="user-name">{user?.name || 'User'}</p>
            <p className="text-xs text-gray-400 truncate">{user?.email || ''}</p>
          </div>
        </div>
        <button
          onClick={handleLogout}
          data-testid="logout-btn"
          className="flex items-center gap-2 text-sm text-gray-400 hover:text-red-500 transition-colors duration-200 font-medium"
        >
          <LogOut className="w-4 h-4" />
          Sign out
        </button>
      </div>
    </aside>
  );
};
