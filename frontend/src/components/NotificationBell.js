import { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from '@/context/AuthContext';
import api from '@/lib/api';
import { Bell, X, Check, AlertTriangle, Info } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

export const NotificationBell = () => {
  const { token } = useAuth();
  const [alerts, setAlerts] = useState([]);
  const [unread, setUnread] = useState(0);
  const [open, setOpen] = useState(false);
  const wsRef = useRef(null);
  const panelRef = useRef(null);

  const fetchAlerts = useCallback(async () => {
    try {
      const r = await api.get('/alerts');
      setAlerts(r.data.data?.alerts || []);
      setUnread(r.data.data?.unread_count || 0);
    } catch {}
  }, []);

  useEffect(() => { fetchAlerts(); }, [fetchAlerts]);

  useEffect(() => {
    if (!token) return;
    const wsUrl = process.env.REACT_APP_BACKEND_URL.replace('https://', 'wss://').replace('http://', 'ws://');
    const ws = new WebSocket(`${wsUrl}/api/ws/alerts?token=${token}`);
    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data);
      if (msg.type === 'new_alert') {
        setAlerts(prev => [msg.data, ...prev]);
        setUnread(prev => prev + 1);
      }
    };
    wsRef.current = ws;
    return () => { ws.close(); };
  }, [token]);

  useEffect(() => {
    const handler = (e) => {
      if (panelRef.current && !panelRef.current.contains(e.target)) setOpen(false);
    };
    if (open) document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [open]);

  const markRead = async (id) => {
    await api.post('/alerts/mark-read', { alertId: id });
    setAlerts(prev => prev.map(a => a.id === id ? { ...a, is_read: true } : a));
    setUnread(prev => Math.max(0, prev - 1));
  };

  const markAllRead = async () => {
    await api.post('/alerts/mark-all-read');
    setAlerts(prev => prev.map(a => ({ ...a, is_read: true })));
    setUnread(0);
  };

  const sevColor = { High: 'red', Medium: 'amber' };

  return (
    <div className="relative" ref={panelRef}>
      <button
        onClick={() => setOpen(!open)}
        data-testid="notification-bell"
        className="relative p-2.5 rounded-2xl hover:bg-gray-100 transition-colors"
      >
        <Bell className="w-5 h-5 text-gray-500" strokeWidth={1.8} />
        {unread > 0 && (
          <span className="absolute -top-0.5 -right-0.5 w-5 h-5 bg-red-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center animate-scale-in" data-testid="notification-badge">
            {unread > 9 ? '9+' : unread}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-12 w-[380px] glass-card border border-gray-200/60 shadow-float z-50 animate-scale-in overflow-hidden" data-testid="notification-panel">
          <div className="flex items-center justify-between px-5 py-3.5 border-b border-gray-100">
            <h3 className="text-sm font-semibold text-gray-900">Notifications</h3>
            <div className="flex items-center gap-2">
              {unread > 0 && (
                <button onClick={markAllRead} className="text-xs text-dhan-blue hover:underline font-medium" data-testid="mark-all-read-btn">
                  Mark all read
                </button>
              )}
              <button onClick={() => setOpen(false)} className="p-1 hover:bg-gray-100 rounded-lg">
                <X className="w-4 h-4 text-gray-400" />
              </button>
            </div>
          </div>

          <div className="max-h-[400px] overflow-y-auto">
            {alerts.length === 0 ? (
              <div className="p-8 text-center">
                <Info className="w-8 h-8 text-gray-300 mx-auto mb-2" />
                <p className="text-sm text-gray-400">No notifications yet</p>
              </div>
            ) : (
              alerts.slice(0, 15).map(a => {
                const sc = sevColor[a.severity] || 'blue';
                return (
                  <div
                    key={a.id}
                    data-testid={`alert-${a.id}`}
                    className={`px-5 py-3.5 border-b border-gray-50 hover:bg-gray-50/50 transition-colors ${!a.is_read ? 'bg-blue-50/30' : ''}`}
                  >
                    <div className="flex items-start gap-3">
                      <div className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 bg-${sc}-50 mt-0.5`}>
                        <AlertTriangle className={`w-4 h-4 text-${sc}-500`} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-0.5">
                          <p className={`text-sm font-medium truncate ${!a.is_read ? 'text-gray-900' : 'text-gray-600'}`}>{a.title}</p>
                          {!a.is_read && <div className="w-2 h-2 rounded-full bg-dhan-blue shrink-0" />}
                        </div>
                        <p className="text-xs text-gray-500 leading-relaxed">{a.explanation}</p>
                        <div className="flex items-center gap-2 mt-1.5">
                          <Badge className={`bg-${sc}-50 text-${sc}-700 border border-${sc}-100 text-[10px] px-1.5 py-0`}>{a.severity}</Badge>
                          <span className="text-[10px] text-gray-400">Score: {a.impact_score}</span>
                          {a.impacted_sectors?.map(s => (
                            <span key={s} className="text-[10px] text-gray-400">{s}</span>
                          ))}
                          {!a.is_read && (
                            <button onClick={() => markRead(a.id)} className="ml-auto text-[10px] text-dhan-blue hover:underline font-medium" data-testid={`mark-read-${a.id}`}>
                              <Check className="w-3 h-3" />
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
};
