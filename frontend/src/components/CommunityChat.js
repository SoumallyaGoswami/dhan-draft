import { useState, useEffect, useRef } from 'react';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Send, Users, MessageCircle } from 'lucide-react';

export const CommunityChat = () => {
  const { user, token } = useAuth();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);
  const scrollRef = useRef(null);
  const bottomRef = useRef(null);

  useEffect(() => {
    if (!token) return;
    const wsUrl = process.env.REACT_APP_BACKEND_URL.replace('https://', 'wss://').replace('http://', 'ws://');
    const ws = new WebSocket(`${wsUrl}/api/ws/chat?token=${token}`);

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data);
      if (msg.type === 'history') {
        setMessages(msg.data || []);
      } else if (msg.type === 'message') {
        setMessages(prev => [...prev, msg.data]);
      }
    };
    wsRef.current = ws;
    return () => { ws.close(); };
  }, [token]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = () => {
    const msg = input.trim();
    if (!msg || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    wsRef.current.send(JSON.stringify({ message: msg }));
    setInput('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  };

  const formatTime = (ts) => {
    try {
      const d = new Date(ts);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch { return ''; }
  };

  return (
    <div className="card-base flex flex-col h-full overflow-hidden" data-testid="community-chat">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-100 flex items-center gap-2 shrink-0">
        <Users className="w-4 h-4 text-dhan-blue" strokeWidth={2} />
        <h3 className="text-sm font-semibold text-gray-900">Community</h3>
        <div className={`ml-auto w-2 h-2 rounded-full ${connected ? 'bg-emerald-400' : 'bg-gray-300'}`} />
        <span className="text-[10px] text-gray-400">{connected ? 'Live' : 'Connecting'}</span>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3 min-h-0" ref={scrollRef}>
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center py-8">
            <MessageCircle className="w-8 h-8 text-gray-200 mb-2" />
            <p className="text-xs text-gray-400">No messages yet. Start the conversation!</p>
          </div>
        )}
        {messages.map((msg, i) => {
          const isMe = msg.userId === user?.id;
          return (
            <div key={msg.id || i} className={`flex ${isMe ? 'justify-end' : 'justify-start'} animate-fade-in`} data-testid={`chat-msg-${i}`}>
              <div className={`max-w-[85%] ${isMe ? '' : ''}`}>
                {!isMe && (
                  <div className="flex items-center gap-1.5 mb-0.5">
                    <span className="text-[10px] font-semibold text-dhan-blue">{msg.username}</span>
                    <span className="text-[10px] text-gray-300">{formatTime(msg.timestamp)}</span>
                  </div>
                )}
                <div className={`px-3.5 py-2 rounded-2xl text-sm ${
                  isMe
                    ? 'bg-dhan-blue text-white rounded-br-md'
                    : 'bg-gray-100 text-gray-700 rounded-bl-md'
                }`}>
                  {msg.message}
                </div>
                {isMe && (
                  <div className="flex justify-end mt-0.5">
                    <span className="text-[10px] text-gray-300">{formatTime(msg.timestamp)}</span>
                  </div>
                )}
              </div>
            </div>
          );
        })}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-100 p-3 shrink-0">
        <div className="flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type a message..."
            disabled={!connected}
            data-testid="community-chat-input"
            className="flex-1 h-10 rounded-full border-gray-200 bg-gray-50/50 px-4 text-sm focus:border-dhan-blue"
          />
          <Button
            onClick={sendMessage}
            disabled={!connected || !input.trim()}
            data-testid="community-chat-send"
            className="h-10 w-10 rounded-full bg-dhan-blue hover:bg-dhan-blue-dark text-white p-0 shrink-0"
          >
            <Send className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </div>
  );
};
