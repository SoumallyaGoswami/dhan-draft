import { useState, useEffect } from 'react';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar, Cell } from 'recharts';
import { TrendingUp, TrendingDown, Minus, ArrowUpRight, ArrowDownRight, BarChart3, Newspaper } from 'lucide-react';
import { toast } from 'sonner';

const HEAT_COLORS = { positive: '#10B981', negative: '#EF4444', neutral: '#F59E0B' };

export default function MarketsPage() {
  const [stocks, setStocks] = useState([]);
  const [selected, setSelected] = useState(null);
  const [stockDetail, setStockDetail] = useState(null);
  const [predictions, setPredictions] = useState({ predictions: [], accuracy: 0, total: 0 });
  const [news, setNews] = useState([]);
  const [heatmap, setHeatmap] = useState([]);
  const [loading, setLoading] = useState(true);
  const [predicting, setPredicting] = useState(false);

  useEffect(() => {
    Promise.all([
      api.get('/markets/stocks'),
      api.get('/markets/predictions'),
      api.get('/markets/sentiment'),
      api.get('/markets/heatmap'),
    ]).then(([s, p, n, h]) => {
      const st = s.data.data || [];
      setStocks(st);
      setPredictions(p.data.data || { predictions: [], accuracy: 0, total: 0 });
      setNews(n.data.data || []);
      setHeatmap(h.data.data || []);
      if (st.length > 0) selectStock(st[0].symbol);
    }).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const selectStock = async (symbol) => {
    setSelected(symbol);
    try {
      const r = await api.get(`/markets/stocks/${symbol}`);
      setStockDetail(r.data.data);
    } catch { toast.error('Failed to load stock data'); }
  };

  const makePrediction = async (direction) => {
    if (!selected || predicting) return;
    setPredicting(true);
    try {
      const r = await api.post('/markets/predict', { stockSymbol: selected, predictedDirection: direction });
      toast.success(r.data.data.match ? 'Your prediction matches AI!' : `AI predicts: ${r.data.data.aiPrediction.direction}`);
      const p = await api.get('/markets/predictions');
      setPredictions(p.data.data || { predictions: [], accuracy: 0, total: 0 });
    } catch { toast.error('Prediction failed'); }
    finally { setPredicting(false); }
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="w-8 h-8 border-2 border-dhan-blue border-t-transparent rounded-full animate-spin" /></div>;

  const hist = stockDetail?.historicalData || [];
  const chartData = hist.slice(-30);
  const ai = stockDetail?.aiPrediction || {};

  return (
    <div className="space-y-6 animate-fade-in" data-testid="markets-page">
      <div>
        <h1 className="text-3xl font-semibold text-gray-900 tracking-tight">Markets</h1>
        <p className="text-base text-gray-500 mt-1">Track stocks and test your predictions</p>
      </div>

      <Tabs defaultValue="stocks" className="w-full">
        <TabsList className="bg-gray-100/70 rounded-full p-1 mb-6">
          <TabsTrigger value="stocks" className="rounded-full text-sm px-5 data-[state=active]:bg-white data-[state=active]:shadow-sm" data-testid="tab-stocks">Stocks</TabsTrigger>
          <TabsTrigger value="sentiment" className="rounded-full text-sm px-5 data-[state=active]:bg-white data-[state=active]:shadow-sm" data-testid="tab-sentiment">Sentiment</TabsTrigger>
          <TabsTrigger value="heatmap" className="rounded-full text-sm px-5 data-[state=active]:bg-white data-[state=active]:shadow-sm" data-testid="tab-heatmap">Heatmap</TabsTrigger>
        </TabsList>

        <TabsContent value="stocks">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Stock List */}
            <div className="card-base p-4 space-y-1 lg:col-span-1 max-h-[600px] overflow-y-auto" data-testid="stock-list">
              <div className="flex items-center justify-between px-2 mb-2">
                <h3 className="text-sm font-semibold text-gray-900">Stocks</h3>
                <Badge className="bg-blue-50 text-dhan-blue border border-blue-100 text-xs">Accuracy: {predictions.accuracy}%</Badge>
              </div>
              {stocks.map(s => (
                <button key={s.symbol} onClick={() => selectStock(s.symbol)}
                  data-testid={`stock-${s.symbol}`}
                  className={`w-full flex items-center justify-between p-3 rounded-xl text-left transition-colors ${selected === s.symbol ? 'bg-blue-50 border border-dhan-blue/20' : 'hover:bg-gray-50'}`}>
                  <div>
                    <p className="text-sm font-semibold text-gray-900">{s.symbol}</p>
                    <p className="text-xs text-gray-400 truncate max-w-[140px]">{s.name}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-semibold text-gray-900">Rs.{s.currentPrice?.toLocaleString('en-IN')}</p>
                    <p className={`text-xs font-medium flex items-center justify-end gap-0.5 ${s.change >= 0 ? 'text-emerald-600' : 'text-red-500'}`}>
                      {s.change >= 0 ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                      {Math.abs(s.change)}%
                    </p>
                  </div>
                </button>
              ))}
            </div>

            {/* Chart & Detail */}
            <div className="lg:col-span-2 space-y-4">
              {stockDetail && (
                <>
                  <div className="card-base p-6" data-testid="stock-chart">
                    <div className="flex items-center justify-between mb-4">
                      <div>
                        <h2 className="text-xl font-bold text-gray-900">{stockDetail.name}</h2>
                        <p className="text-sm text-gray-500">{stockDetail.sector} &middot; {stockDetail.marketCap}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-2xl font-bold text-gray-900">Rs.{stockDetail.currentPrice?.toLocaleString('en-IN')}</p>
                        <p className={`text-sm font-medium ${stockDetail.change >= 0 ? 'text-emerald-600' : 'text-red-500'}`}>
                          {stockDetail.change >= 0 ? '+' : ''}{stockDetail.change}%
                        </p>
                      </div>
                    </div>
                    <ResponsiveContainer width="100%" height={250}>
                      <AreaChart data={chartData}>
                        <defs>
                          <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.15} />
                            <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
                          </linearGradient>
                        </defs>
                        <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#9CA3AF' }} tickFormatter={v => v.slice(5)} axisLine={false} tickLine={false} />
                        <YAxis domain={['auto', 'auto']} tick={{ fontSize: 11, fill: '#9CA3AF' }} axisLine={false} tickLine={false} width={60} tickFormatter={v => `${(v/1000).toFixed(1)}k`} />
                        <Tooltip contentStyle={{ borderRadius: 12, border: '1px solid #E5E7EB', fontSize: 12 }} formatter={(v) => [`Rs.${v}`, 'Close']} />
                        <Area type="monotone" dataKey="close" stroke="#3B82F6" strokeWidth={2} fillOpacity={1} fill="url(#colorPrice)" />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>

                  {/* AI Prediction & User Prediction */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="card-base p-5" data-testid="ai-prediction">
                      <h3 className="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-2">
                        <BarChart3 className="w-4 h-4 text-dhan-blue" /> AI Prediction
                      </h3>
                      <div className="flex items-center gap-3 mb-2">
                        {ai.direction === 'up' ? <TrendingUp className="w-6 h-6 text-emerald-500" /> : ai.direction === 'down' ? <TrendingDown className="w-6 h-6 text-red-500" /> : <Minus className="w-6 h-6 text-amber-500" />}
                        <span className="text-lg font-bold text-gray-900 capitalize">{ai.direction || 'N/A'}</span>
                        <Badge className="bg-blue-50 text-dhan-blue border border-blue-100 text-xs">{ai.confidence || 0}% confidence</Badge>
                      </div>
                      <p className="text-xs text-gray-500">{ai.explanation || ''}</p>
                    </div>

                    <div className="card-base p-5" data-testid="user-prediction">
                      <h3 className="text-sm font-semibold text-gray-900 mb-3">Your Prediction</h3>
                      <p className="text-xs text-gray-500 mb-3">Where do you think {selected} is heading?</p>
                      <div className="flex gap-2">
                        <Button onClick={() => makePrediction('up')} disabled={predicting} data-testid="predict-up-btn"
                          className="flex-1 rounded-full bg-emerald-50 text-emerald-700 hover:bg-emerald-100 border border-emerald-200 font-medium text-sm">
                          <TrendingUp className="w-4 h-4 mr-1" /> Bullish
                        </Button>
                        <Button onClick={() => makePrediction('down')} disabled={predicting} data-testid="predict-down-btn"
                          className="flex-1 rounded-full bg-red-50 text-red-700 hover:bg-red-100 border border-red-200 font-medium text-sm">
                          <TrendingDown className="w-4 h-4 mr-1" /> Bearish
                        </Button>
                      </div>
                    </div>
                  </div>

                  {/* Recent Predictions */}
                  {predictions.predictions?.length > 0 && (
                    <div className="card-base p-5" data-testid="predictions-history">
                      <h3 className="text-sm font-semibold text-gray-900 mb-3">Recent Predictions</h3>
                      <div className="space-y-2 max-h-48 overflow-y-auto">
                        {predictions.predictions.slice(0, 5).map((p, i) => (
                          <div key={p.id || i} className="flex items-center justify-between p-2.5 bg-gray-50 rounded-xl text-sm">
                            <div className="flex items-center gap-2">
                              <span className="font-semibold text-gray-800">{p.stockSymbol}</span>
                              <span className={`capitalize ${p.predictedDirection === 'up' ? 'text-emerald-600' : 'text-red-500'}`}>{p.predictedDirection}</span>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="text-gray-400">AI: {p.aiDirection}</span>
                              {p.correct ? <Badge className="bg-emerald-50 text-emerald-600 border-emerald-100 text-xs">Match</Badge> : <Badge className="bg-red-50 text-red-500 border-red-100 text-xs">Miss</Badge>}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        </TabsContent>

        <TabsContent value="sentiment">
          <div className="space-y-4" data-testid="sentiment-section">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2"><Newspaper className="w-5 h-5 text-dhan-blue" /> News Sentiment Analysis</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {news.map((n, i) => {
                const sa = n.sentiment_analysis || {};
                const c = sa.label === 'Bullish' ? 'emerald' : sa.label === 'Bearish' ? 'red' : 'amber';
                return (
                  <div key={n.id || i} className="card-base p-5 card-hover" data-testid={`news-${i}`}>
                    <div className="flex items-start justify-between mb-2">
                      <Badge className={`bg-${c}-50 text-${c}-700 border border-${c}-100 text-xs`}>{n.sector}</Badge>
                      <Badge className={`bg-${c}-50 text-${c}-700 border border-${c}-100 text-xs`}>{sa.label || 'N/A'}</Badge>
                    </div>
                    <h4 className="text-sm font-semibold text-gray-900 mb-1">{n.title}</h4>
                    <p className="text-xs text-gray-500 leading-relaxed">{n.content?.slice(0, 120)}...</p>
                    <div className="mt-3 flex items-center gap-2">
                      <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                        <div className={`h-full rounded-full bg-${c}-500`} style={{ width: `${(sa.score || 0.5) * 100}%` }} />
                      </div>
                      <span className="text-xs font-medium text-gray-400">{sa.confidence || 0}%</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </TabsContent>

        <TabsContent value="heatmap">
          <div data-testid="heatmap-section">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Sector Heatmap</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {heatmap.map(sector => (
                <div key={sector.sector} className="card-base p-5" data-testid={`heatmap-${sector.sector}`}>
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-sm font-semibold text-gray-900">{sector.sector}</h4>
                    <span className={`text-sm font-bold ${sector.avgChange >= 0 ? 'text-emerald-600' : 'text-red-500'}`}>
                      {sector.avgChange >= 0 ? '+' : ''}{sector.avgChange}%
                    </span>
                  </div>
                  <div className="space-y-2">
                    {sector.stocks?.map(st => (
                      <div key={st.symbol} className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">{st.symbol}</span>
                        <span className={`font-medium ${st.change >= 0 ? 'text-emerald-600' : 'text-red-500'}`}>
                          {st.change >= 0 ? '+' : ''}{st.change}%
                        </span>
                      </div>
                    ))}
                  </div>
                  <div className="mt-3 h-2 rounded-full overflow-hidden bg-gray-100">
                    <div className={`h-full rounded-full ${sector.avgChange >= 0 ? 'bg-emerald-400' : 'bg-red-400'}`}
                      style={{ width: `${Math.min(Math.abs(sector.avgChange) * 20, 100)}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
