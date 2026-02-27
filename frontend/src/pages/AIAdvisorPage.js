import { useState, useEffect, useRef } from 'react';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Sparkles, Send, Target, Shield, TrendingUp, FileText, RefreshCw, Lightbulb } from 'lucide-react';
import { toast } from 'sonner';
import { CommunityChat } from '@/components/CommunityChat';

const quickChips = [
  { label: 'Portfolio Review', query: 'Review my portfolio allocation and suggest improvements' },
  { label: 'Tax Strategy', query: 'What tax-saving strategies do you recommend for my portfolio?' },
  { label: 'Risk Assessment', query: 'Assess the current risk level of my investments' },
  { label: 'Sector Analysis', query: 'Analyze sector allocation and suggest rebalancing' },
  { label: 'Growth Plan', query: 'Create a growth-focused investment plan based on my risk profile' },
];

const iconMap = {
  strategy: TrendingUp,
  tax_suggestion: FileText,
  risk_alert: Shield,
  sector_warning: Target,
  explanation: Lightbulb,
};

export default function AIAdvisorPage() {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  const scrollRef = useRef(null);

  useEffect(() => {
    api.get('/advisor/history').then(r => {
      const h = r.data.data || [];
      const msgs = [];
      h.slice().reverse().forEach(item => {
        msgs.push({ type: 'user', text: item.query, time: item.timestamp });
        msgs.push({ type: 'ai', data: item.response, time: item.timestamp });
      });
      setMessages(msgs);
    }).catch(() => {}).finally(() => setInitialLoading(false));
  }, []);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages]);

  const sendQuery = async (q) => {
    const text = q || query.trim();
    if (!text) return;
    setQuery('');
    setMessages(prev => [...prev, { type: 'user', text, time: new Date().toISOString() }]);
    setLoading(true);
    try {
      const r = await api.post('/advisor/analyze', { query: text });
      setMessages(prev => [...prev, { type: 'ai', data: r.data.data, time: new Date().toISOString() }]);
    } catch {
      toast.error('Failed to get advice');
      setMessages(prev => [...prev, { type: 'ai', data: { strategy: 'Sorry, unable to process your request. Please try again.' }, time: new Date().toISOString() }]);
    } finally { setLoading(false); }
  };

  const handleKeyDown = (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendQuery(); } };

  if (initialLoading) return <div className="flex items-center justify-center h-64"><div className="w-8 h-8 border-2 border-dhan-blue border-t-transparent rounded-full animate-spin" /></div>;

  return (
    <div className="space-y-4 animate-fade-in" data-testid="advisor-page">
      <div>
        <h1 className="text-3xl font-semibold text-gray-900 tracking-tight">AI Advisor</h1>
        <p className="text-base text-gray-500 mt-1">Get personalized strategies & chat with the community</p>
      </div>

      {/* Quick Chips */}
      <div className="flex gap-2 overflow-x-auto pb-1 shrink-0" data-testid="quick-chips">
        {quickChips.map(chip => (
          <button key={chip.label} onClick={() => sendQuery(chip.query)} disabled={loading}
            data-testid={`chip-${chip.label.toLowerCase().replace(/\s+/g, '-')}`}
            className="px-4 py-2 rounded-full bg-white border border-gray-200 text-sm text-gray-600 hover:border-dhan-blue hover:text-dhan-blue transition-colors whitespace-nowrap font-medium shrink-0">
            {chip.label}
          </button>
        ))}
      </div>

      {/* Split Layout: AI Advisor (60%) + Community Chat (40%) */}
      <div className="flex flex-col lg:flex-row gap-4" style={{ height: 'calc(100vh - 260px)' }}>
        {/* AI Advisor Section */}
        <div className="flex-[3] card-base overflow-hidden flex flex-col min-h-[400px] lg:min-h-0" data-testid="advisor-chat-section">
          <ScrollArea className="flex-1 p-5" ref={scrollRef} data-testid="chat-area">
            {messages.length === 0 && (
              <div className="flex flex-col items-center justify-center h-full text-center py-12">
                <div className="w-14 h-14 rounded-3xl bg-gradient-to-br from-dhan-blue to-blue-400 flex items-center justify-center mb-4">
                  <Sparkles className="w-7 h-7 text-white" />
                </div>
                <h3 className="text-base font-semibold text-gray-900">Financial AI Advisor</h3>
                <p className="text-sm text-gray-500 mt-1.5 max-w-sm">Ask about your portfolio, tax strategies, risk management, or investment recommendations.</p>
              </div>
            )}
            <div className="space-y-3">
              {messages.map((msg, i) => (
                <div key={i} className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in`}>
                  {msg.type === 'user' ? (
                    <div className="max-w-[75%] bg-dhan-blue text-white rounded-2xl rounded-br-md px-4 py-2.5" data-testid={`msg-user-${i}`}>
                      <p className="text-sm">{msg.text}</p>
                    </div>
                  ) : (
                    <div className="max-w-[88%] space-y-2" data-testid={`msg-ai-${i}`}>
                      {msg.data && Object.entries(msg.data).filter(([k]) => k !== 'explanation').map(([key, value]) => {
                        if (!value || value === 'N/A') return null;
                        const Icon = iconMap[key] || Sparkles;
                        const label = key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
                        return (
                          <div key={key} className="bg-gray-50 rounded-2xl rounded-bl-md px-4 py-2.5 border border-gray-100">
                            <div className="flex items-center gap-2 mb-0.5">
                              <Icon className="w-3 h-3 text-dhan-blue" strokeWidth={2} />
                              <span className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider">{label}</span>
                            </div>
                            <p className="text-sm text-gray-700 leading-relaxed">{value}</p>
                          </div>
                        );
                      })}
                      {msg.data?.explanation && (
                        <div className="glass-card px-4 py-2.5 border border-blue-100/50">
                          <div className="flex items-center gap-2 mb-0.5">
                            <Lightbulb className="w-3 h-3 text-dhan-blue" strokeWidth={2} />
                            <span className="text-[10px] font-semibold text-dhan-blue uppercase tracking-wider">Why AI Suggested This</span>
                          </div>
                          <p className="text-sm text-gray-600 leading-relaxed">{msg.data.explanation}</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
              {loading && (
                <div className="flex justify-start">
                  <div className="bg-gray-50 rounded-2xl px-4 py-2.5 border border-gray-100">
                    <div className="flex items-center gap-2">
                      <RefreshCw className="w-3.5 h-3.5 text-dhan-blue animate-spin" />
                      <span className="text-sm text-gray-500">Analyzing your portfolio...</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </ScrollArea>

          <div className="border-t border-gray-100 p-3" data-testid="chat-input-area">
            <div className="flex gap-2">
              <Input
                value={query} onChange={e => setQuery(e.target.value)} onKeyDown={handleKeyDown}
                placeholder="Ask about your finances..." disabled={loading}
                data-testid="advisor-input"
                className="flex-1 h-11 rounded-full border-gray-200 bg-gray-50/50 px-4 text-sm focus:border-dhan-blue"
              />
              <Button onClick={() => sendQuery()} disabled={loading || !query.trim()}
                data-testid="advisor-send-btn"
                className="h-11 w-11 rounded-full bg-dhan-blue hover:bg-dhan-blue-dark text-white p-0 shrink-0">
                <Send className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>

        {/* Community Chat Section */}
        <div className="flex-[2] min-h-[400px] lg:min-h-0">
          <CommunityChat />
        </div>
      </div>
    </div>
  );
}
