import { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import api from '@/lib/api';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { Activity, TrendingUp, Shield, Sparkles, Target, AlertTriangle } from 'lucide-react';

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#8B5CF6', '#EF4444', '#06B6D4'];

const CircularScore = ({ value, size = 140, label }) => {
  const r = (size - 16) / 2;
  const circ = r * 2 * Math.PI;
  const offset = circ - (value / 100) * circ;
  const color = value >= 70 ? '#10B981' : value >= 50 ? '#F59E0B' : '#EF4444';
  return (
    <div className="flex flex-col items-center">
      <svg width={size} height={size} className="transform -rotate-90">
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="#F3F4F6" strokeWidth="10" />
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={color} strokeWidth="10"
          strokeDasharray={circ} strokeDashoffset={offset} strokeLinecap="round"
          style={{ transition: 'stroke-dashoffset 1.2s ease' }} />
      </svg>
      <div className="absolute flex flex-col items-center justify-center" style={{ width: size, height: size }}>
        <span className="text-3xl font-bold text-gray-900">{value}</span>
        <span className="text-xs text-gray-400 font-medium">{label}</span>
      </div>
    </div>
  );
};

const StatCard = ({ icon: Icon, label, value, sub, color = 'blue', className = '' }) => (
  <div className={`card-base card-hover p-6 flex flex-col gap-3 ${className}`} data-testid={`stat-${label.toLowerCase().replace(/\s+/g, '-')}`}>
    <div className={`w-10 h-10 rounded-2xl flex items-center justify-center bg-${color}-50`}>
      <Icon className={`w-5 h-5 text-${color}-500`} strokeWidth={1.8} />
    </div>
    <div>
      <p className="text-sm text-gray-500 font-medium">{label}</p>
      <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
      {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
    </div>
  </div>
);

export default function OverviewPage() {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/overview/summary').then(r => setData(r.data.data)).catch(() => {}).finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="w-8 h-8 border-2 border-dhan-blue border-t-transparent rounded-full animate-spin" />
    </div>
  );

  const d = data || {};
  const health = d.financialHealth || { score: 0, confidence: 0, explanation: '' };
  const risk = d.riskPersonality || { personality: 'N/A', explanation: '' };
  const alloc = d.portfolioAllocation || [];
  const sentiment = d.sectorSentiment || [];

  const riskColors = { Aggressive: 'red', Growth: 'blue', Moderate: 'amber', Conservative: 'emerald', Undetermined: 'gray' };
  const rc = riskColors[risk.personality] || 'gray';

  return (
    <div className="space-y-6 animate-fade-in" data-testid="overview-page">
      <div>
        <h1 className="text-3xl font-semibold text-gray-900 tracking-tight">
          Welcome back, {user?.name?.split(' ')[0] || 'User'}
        </h1>
        <p className="text-base text-gray-500 mt-1">Here's your financial overview</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Financial Health Score */}
        <div className="card-base card-hover p-6 md:col-span-2 lg:col-span-2 flex items-center gap-8 stagger-1 animate-fade-in" data-testid="financial-health-card">
          <div className="relative">
            <CircularScore value={health.score} label="Health" />
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900">Financial Health</h3>
            <p className="text-sm text-gray-500 mt-1">{health.explanation}</p>
            <div className="flex items-center gap-2 mt-3">
              <span className="text-xs font-medium text-gray-400">Confidence</span>
              <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                <div className="h-full bg-dhan-blue rounded-full" style={{ width: `${health.confidence}%`, transition: 'width 1s ease' }} />
              </div>
              <span className="text-xs font-semibold text-gray-600">{health.confidence}%</span>
            </div>
          </div>
        </div>

        {/* Risk Personality */}
        <div className="card-base card-hover p-6 stagger-2 animate-fade-in" data-testid="risk-personality-card">
          <div className={`w-10 h-10 rounded-2xl flex items-center justify-center bg-${rc}-50 mb-4`}>
            <Target className={`w-5 h-5 text-${rc}-500`} strokeWidth={1.8} />
          </div>
          <p className="text-sm text-gray-500 font-medium">Risk Personality</p>
          <p className="text-xl font-bold text-gray-900 mt-1">{risk.personality}</p>
          <p className="text-xs text-gray-400 mt-2">{risk.explanation}</p>
        </div>

        {/* Portfolio Value */}
        <div className="card-base card-hover p-6 stagger-3 animate-fade-in" data-testid="portfolio-value-card">
          <div className="w-10 h-10 rounded-2xl flex items-center justify-center bg-emerald-50 mb-4">
            <TrendingUp className="w-5 h-5 text-emerald-500" strokeWidth={1.8} />
          </div>
          <p className="text-sm text-gray-500 font-medium">Portfolio Value</p>
          <p className="text-xl font-bold text-gray-900 mt-1">
            {d.totalValue ? `Rs.${d.totalValue.toLocaleString('en-IN')}` : 'Rs.0'}
          </p>
          <p className="text-xs text-gray-400 mt-2">{alloc.length} asset types</p>
        </div>

        {/* Portfolio Allocation Donut */}
        <div className="card-base card-hover p-6 md:col-span-2 stagger-4 animate-fade-in" data-testid="portfolio-allocation-card">
          <h3 className="text-sm font-semibold text-gray-900 mb-2">Portfolio Allocation</h3>
          {alloc.length > 0 ? (
            <div className="flex items-center gap-4">
              <ResponsiveContainer width="50%" height={160}>
                <PieChart>
                  <Pie data={alloc} cx="50%" cy="50%" innerRadius={45} outerRadius={65} paddingAngle={3} dataKey="value" nameKey="name">
                    {alloc.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                  </Pie>
                  <Tooltip formatter={(v) => `Rs.${v.toLocaleString('en-IN')}`} />
                </PieChart>
              </ResponsiveContainer>
              <div className="space-y-2">
                {alloc.map((a, i) => (
                  <div key={a.name} className="flex items-center gap-2 text-sm">
                    <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: COLORS[i % COLORS.length] }} />
                    <span className="text-gray-600 capitalize">{a.name.replace('_', ' ')}</span>
                    <span className="text-gray-400 font-medium ml-auto">{a.percentage}%</span>
                  </div>
                ))}
              </div>
            </div>
          ) : <p className="text-sm text-gray-400">No assets in portfolio</p>}
        </div>

        {/* Quick Stats */}
        <StatCard icon={Activity} label="Prediction Accuracy" value={`${d.predictionAccuracy || 0}%`} sub="Based on your market calls" color="blue" className="stagger-5 animate-fade-in" />
        <StatCard icon={Shield} label="Tax Optimization" value={`${d.taxOptimization?.score || 0}%`} sub={d.taxOptimization?.explanation} color="emerald" className="stagger-6 animate-fade-in" />
      </div>

      {/* AI Insight */}
      <div className="glass-card p-6 card-hover stagger-7 animate-fade-in" data-testid="ai-insight-card">
        <div className="flex items-start gap-4">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-dhan-blue to-blue-400 flex items-center justify-center shrink-0">
            <Sparkles className="w-5 h-5 text-white" strokeWidth={1.8} />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-gray-900">AI Insight</h3>
            <p className="text-sm text-gray-600 mt-1 leading-relaxed">{d.aiInsight || 'No insights yet.'}</p>
          </div>
        </div>
      </div>

      {/* Sector Sentiment Strip */}
      {sentiment.length > 0 && (
        <div className="stagger-8 animate-fade-in" data-testid="sector-sentiment-strip">
          <h3 className="text-sm font-semibold text-gray-900 mb-3">Sector Sentiment</h3>
          <div className="flex gap-3 overflow-x-auto pb-2">
            {sentiment.map(s => {
              const c = s.label === 'Bullish' ? 'emerald' : s.label === 'Bearish' ? 'red' : 'amber';
              return (
                <div key={s.sector} className={`flex items-center gap-2 px-4 py-2.5 rounded-full bg-${c}-50 border border-${c}-100 shrink-0`}>
                  <div className={`w-2 h-2 rounded-full bg-${c}-500`} />
                  <span className="text-sm font-medium text-gray-700">{s.sector}</span>
                  <span className={`text-xs font-semibold text-${c}-600`}>{s.label}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
