import { Outlet } from 'react-router-dom';
import { Sidebar } from '@/components/Sidebar';
import { NotificationBell } from '@/components/NotificationBell';

export const DashboardLayout = () => (
  <div className="flex h-screen bg-dhan-bg overflow-hidden">
    <Sidebar />
    <div className="flex-1 flex flex-col overflow-hidden">
      <header className="flex items-center justify-end px-8 py-3 shrink-0">
        <NotificationBell />
      </header>
      <main className="flex-1 overflow-y-auto">
        <div className="px-6 pb-6 md:px-8 md:pb-8 lg:px-10 lg:pb-10 max-w-[1400px]">
          <Outlet />
        </div>
      </main>
    </div>
  </div>
);
