import { useState, useEffect } from 'react';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, BarChart, Bar, XAxis, YAxis } from 'recharts';
import { Wallet, PieChart as PieIcon, Calculator, TrendingUp, TrendingDown, ArrowUpDown, Plus } from 'lucide-react';
import { toast } from 'sonner';
import { AddAssetModal } from '@/components/AddAssetModal';

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#8B5CF6', '#EF4444', '#06B6D4'];

export default function PortfolioTaxPage() {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [taxForm, setTaxForm] = useState({ income: 1200000, deductions_80c: 150000, deductions_80d: 25000, hra_exemption: 50000, other_deductions: 0 });
  const [taxResult, setTaxResult] = useState(null);
  const [cgForm, setCgForm] = useState({ buyPrice: 100, sellPrice: 150, quantity: 100, holdingMonths: 14, assetType: 'equity' });
  const [cgResult, setCgResult] = useState(null);
  const [fdForm, setFdForm] = useState({ principal: 500000, rate: 7, years: 3, taxBracket: 30 });
  const [fdResult, setFdResult] = useState(null);

  useEffect(() => {
    loadSummary();
  }, []);

  const loadSummary = () => {
    setLoading(true);
    api.get('/portfolio/summary').then(r => setSummary(r.data.data)).catch(() => {}).finally(() => setLoading(false));
  };

  const calcTax = async () => { try { const r = await api.post('/portfolio/tax/compare', taxForm); setTaxResult(r.data.data); } catch { toast.error('Calculation failed'); } };
  const calcCG = async () => { try { const r = await api.post('/portfolio/tax/capital-gains', cgForm); setCgResult(r.data.data); } catch { toast.error('Calculation failed'); } };
  const calcFD = async () => { try { const r = await api.post('/portfolio/tax/fd', fdForm); setFdResult(r.data.data); } catch { toast.error('Calculation failed'); } };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="w-8 h-8 border-2 border-dhan-blue border-t-transparent rounded-full animate-spin" /></div>;

  const s = summary || {};
  const assets = s.assets || [];
  const allocation = s.allocation || [];
  const sectorDiv = s.sectorDiversification || [];

  return (
    <div className="space-y-6 animate-fade-in" data-testid="portfolio-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold text-gray-900 tracking-tight">Portfolio & Tax</h1>
          <p className="text-base text-gray-500 mt-1">Manage your assets and optimize taxes</p>
        </div>
        <Button onClick={() => setShowAddModal(true)} data-testid="add-asset-btn" className="rounded-full bg-dhan-blue hover:bg-dhan-blue-dark text-white px-5 gap-2">
          <Plus className="w-4 h-4" /> Add Asset
        </Button>
      </div>

      <AddAssetModal open={showAddModal} onClose={() => setShowAddModal(false)} onAdded={loadSummary} />

      {/* Portfolio Summary Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { l: 'Total Value', v: `Rs.${(s.totalValue || 0).toLocaleString('en-IN')}`, c: 'blue', icon: Wallet },
          { l: 'Total Cost', v: `Rs.${(s.totalCost || 0).toLocaleString('en-IN')}`, c: 'gray', icon: ArrowUpDown },
          { l: 'Total Gain', v: `Rs.${(s.totalGain || 0).toLocaleString('en-IN')}`, c: s.totalGain >= 0 ? 'emerald' : 'red', icon: s.totalGain >= 0 ? TrendingUp : TrendingDown },
          { l: 'Volatility', v: s.volatility || 'N/A', c: s.volatility === 'High' ? 'red' : s.volatility === 'Moderate' ? 'amber' : 'emerald', icon: ArrowUpDown },
        ].map(({ l, v, c, icon: Icon }) => (
          <div key={l} className="card-base p-5 card-hover" data-testid={`portfolio-${l.toLowerCase().replace(/\s+/g, '-')}`}>
            <Icon className={`w-5 h-5 text-${c}-500 mb-2`} strokeWidth={1.8} />
            <p className="text-xs text-gray-500 font-medium">{l}</p>
            <p className="text-lg font-bold text-gray-900 mt-1">{v}</p>
            {l === 'Total Gain' && s.gainPct !== undefined && <p className={`text-xs font-medium mt-0.5 ${s.gainPct >= 0 ? 'text-emerald-600' : 'text-red-500'}`}>{s.gainPct >= 0 ? '+' : ''}{s.gainPct}%</p>}
          </div>
        ))}
      </div>

      <Tabs defaultValue="portfolio" className="w-full">
        <TabsList className="bg-gray-100/70 rounded-full p-1 mb-6">
          <TabsTrigger value="portfolio" className="rounded-full text-sm px-5 data-[state=active]:bg-white data-[state=active]:shadow-sm" data-testid="tab-portfolio">Portfolio</TabsTrigger>
          <TabsTrigger value="regime" className="rounded-full text-sm px-5 data-[state=active]:bg-white data-[state=active]:shadow-sm" data-testid="tab-regime">Tax Regime</TabsTrigger>
          <TabsTrigger value="capgains" className="rounded-full text-sm px-5 data-[state=active]:bg-white data-[state=active]:shadow-sm" data-testid="tab-capgains">Capital Gains</TabsTrigger>
          <TabsTrigger value="fd" className="rounded-full text-sm px-5 data-[state=active]:bg-white data-[state=active]:shadow-sm" data-testid="tab-fd">FD Tax</TabsTrigger>
        </TabsList>

        <TabsContent value="portfolio">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Charts */}
            <div className="card-base p-6" data-testid="allocation-chart">
              <h3 className="text-sm font-semibold text-gray-900 mb-4 flex items-center gap-2"><PieIcon className="w-4 h-4 text-dhan-blue" /> Allocation</h3>
              {allocation.length > 0 ? (
                <>
                  <ResponsiveContainer width="100%" height={180}>
                    <PieChart><Pie data={allocation} cx="50%" cy="50%" innerRadius={50} outerRadius={70} paddingAngle={3} dataKey="value" nameKey="name">
                      {allocation.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                    </Pie><Tooltip formatter={v => `Rs.${v.toLocaleString('en-IN')}`} /></PieChart>
                  </ResponsiveContainer>
                  <div className="space-y-2 mt-2">
                    {allocation.map((a, i) => (
                      <div key={a.name} className="flex items-center gap-2 text-sm">
                        <div className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: COLORS[i % COLORS.length] }} />
                        <span className="text-gray-600 capitalize flex-1">{a.name.replace('_', ' ')}</span>
                        <span className="text-gray-400 font-medium">{a.percentage}%</span>
                      </div>
                    ))}
                  </div>
                </>
              ) : <p className="text-sm text-gray-400">No allocation data</p>}
            </div>

            <div className="card-base p-6" data-testid="sector-chart">
              <h3 className="text-sm font-semibold text-gray-900 mb-4">Sector Diversification</h3>
              {sectorDiv.length > 0 ? (
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={sectorDiv} layout="vertical" margin={{ left: 0 }}>
                    <XAxis type="number" tick={{ fontSize: 11, fill: '#9CA3AF' }} tickFormatter={v => `${v}%`} axisLine={false} tickLine={false} />
                    <YAxis type="category" dataKey="name" tick={{ fontSize: 11, fill: '#6B7280' }} width={90} axisLine={false} tickLine={false} />
                    <Tooltip formatter={v => `${v}%`} />
                    <Bar dataKey="percentage" radius={[0, 6, 6, 0]}>
                      {sectorDiv.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              ) : <p className="text-sm text-gray-400">No sector data</p>}
            </div>

            {/* Asset Table */}
            <div className="card-base p-6 lg:col-span-1" data-testid="asset-table">
              <h3 className="text-sm font-semibold text-gray-900 mb-4">Holdings</h3>
              <div className="space-y-2 max-h-[300px] overflow-y-auto">
                {assets.map(a => (
                  <div key={a.id} className="p-3 bg-gray-50 rounded-xl">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-semibold text-gray-900">{a.symbol}</p>
                        <p className="text-xs text-gray-400">{a.sector} &middot; {a.type}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-semibold text-gray-900">Rs.{a.currentValue?.toLocaleString('en-IN')}</p>
                        <p className={`text-xs font-medium ${a.gainPct >= 0 ? 'text-emerald-600' : 'text-red-500'}`}>{a.gainPct >= 0 ? '+' : ''}{a.gainPct}%</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="regime">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6" data-testid="regime-calculator">
            <div className="card-base p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2"><Calculator className="w-5 h-5 text-dhan-blue" /> Tax Regime Comparison</h3>
              <div className="space-y-3">
                {[{ k: 'income', l: 'Annual Income' }, { k: 'deductions_80c', l: '80C Deductions' }, { k: 'deductions_80d', l: '80D Deductions' }, { k: 'hra_exemption', l: 'HRA Exemption' }, { k: 'other_deductions', l: 'Other Deductions' }].map(({ k, l }) => (
                  <div key={k} className="space-y-1">
                    <Label className="text-xs text-gray-500">{l}</Label>
                    <Input type="number" value={taxForm[k]} onChange={e => setTaxForm({ ...taxForm, [k]: parseFloat(e.target.value) || 0 })} data-testid={`regime-${k}`} className="h-10 rounded-xl border-gray-200 bg-gray-50/50" />
                  </div>
                ))}
                <Button onClick={calcTax} data-testid="calc-regime-btn" className="w-full rounded-full bg-dhan-blue hover:bg-dhan-blue-dark text-white">Compare Regimes</Button>
              </div>
            </div>
            {taxResult && (
              <div className="card-base p-6 animate-scale-in" data-testid="regime-result">
                {['old_regime', 'new_regime'].map(key => (
                  <div key={key} className={`p-4 rounded-2xl border mb-4 ${taxResult.recommended === key.split('_')[0] ? 'bg-blue-50 border-dhan-blue/30' : 'bg-gray-50 border-gray-200'}`}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-semibold text-gray-900">{key === 'old_regime' ? 'Old Regime' : 'New Regime'}</span>
                      {taxResult.recommended === key.split('_')[0] && <Badge className="bg-dhan-blue text-white text-xs">Best</Badge>}
                    </div>
                    <p className="text-2xl font-bold text-gray-900">Rs.{taxResult[key].total.toLocaleString('en-IN')}</p>
                    <p className="text-xs text-gray-500 mt-1">Effective rate: {taxResult[key].effective_rate}%</p>
                  </div>
                ))}
                <div className="p-3 bg-emerald-50 rounded-xl border border-emerald-100 text-sm text-emerald-700 font-medium">Savings: Rs.{taxResult.savings.toLocaleString('en-IN')}</div>
              </div>
            )}
          </div>
        </TabsContent>

        <TabsContent value="capgains">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6" data-testid="capgains-calculator">
            <div className="card-base p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Capital Gains Calculator</h3>
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1"><Label className="text-xs text-gray-500">Buy Price</Label><Input type="number" value={cgForm.buyPrice} onChange={e => setCgForm({ ...cgForm, buyPrice: parseFloat(e.target.value) || 0 })} data-testid="cg-buy" className="h-10 rounded-xl border-gray-200 bg-gray-50/50" /></div>
                  <div className="space-y-1"><Label className="text-xs text-gray-500">Sell Price</Label><Input type="number" value={cgForm.sellPrice} onChange={e => setCgForm({ ...cgForm, sellPrice: parseFloat(e.target.value) || 0 })} data-testid="cg-sell" className="h-10 rounded-xl border-gray-200 bg-gray-50/50" /></div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1"><Label className="text-xs text-gray-500">Quantity</Label><Input type="number" value={cgForm.quantity} onChange={e => setCgForm({ ...cgForm, quantity: parseInt(e.target.value) || 0 })} data-testid="cg-qty" className="h-10 rounded-xl border-gray-200 bg-gray-50/50" /></div>
                  <div className="space-y-1"><Label className="text-xs text-gray-500">Holding (months)</Label><Input type="number" value={cgForm.holdingMonths} onChange={e => setCgForm({ ...cgForm, holdingMonths: parseInt(e.target.value) || 0 })} data-testid="cg-months" className="h-10 rounded-xl border-gray-200 bg-gray-50/50" /></div>
                </div>
                <div className="space-y-1">
                  <Label className="text-xs text-gray-500">Asset Type</Label>
                  <Select value={cgForm.assetType} onValueChange={v => setCgForm({ ...cgForm, assetType: v })}>
                    <SelectTrigger className="h-10 rounded-xl" data-testid="cg-type"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="equity">Equity</SelectItem>
                      <SelectItem value="debt">Debt</SelectItem>
                      <SelectItem value="gold">Gold</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <Button onClick={calcCG} data-testid="calc-cg-btn" className="w-full rounded-full bg-dhan-blue hover:bg-dhan-blue-dark text-white">Calculate</Button>
              </div>
            </div>
            {cgResult && (
              <div className="card-base p-6 animate-scale-in" data-testid="cg-result">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Capital Gains Result</h3>
                <div className="space-y-3">
                  <div className="flex justify-between text-sm"><span className="text-gray-500">Total Gain</span><span className={`font-bold ${cgResult.gain >= 0 ? 'text-emerald-600' : 'text-red-500'}`}>Rs.{cgResult.gain.toLocaleString('en-IN')}</span></div>
                  <div className="flex justify-between text-sm"><span className="text-gray-500">Gain %</span><span className="font-medium text-gray-900">{cgResult.gain_pct}%</span></div>
                  <div className="flex justify-between text-sm"><span className="text-gray-500">Tax Type</span><Badge className="bg-blue-50 text-dhan-blue border border-blue-100">{cgResult.tax_type}</Badge></div>
                  <div className="flex justify-between text-sm"><span className="text-gray-500">Tax Amount</span><span className="font-bold text-gray-900">Rs.{cgResult.tax.toLocaleString('en-IN')}</span></div>
                  <div className="flex justify-between text-sm border-t border-gray-100 pt-3"><span className="text-gray-500">Net Gain</span><span className={`font-bold text-lg ${cgResult.net_gain >= 0 ? 'text-emerald-600' : 'text-red-500'}`}>Rs.{cgResult.net_gain.toLocaleString('en-IN')}</span></div>
                  <p className="text-xs text-gray-400 mt-2">{cgResult.explanation}</p>
                </div>
              </div>
            )}
          </div>
        </TabsContent>

        <TabsContent value="fd">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6" data-testid="fd-calculator">
            <div className="card-base p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">FD Tax Estimator</h3>
              <div className="space-y-3">
                {[{ k: 'principal', l: 'Principal (Rs.)' }, { k: 'rate', l: 'Interest Rate (%)' }, { k: 'years', l: 'Tenure (Years)' }, { k: 'taxBracket', l: 'Tax Bracket (%)' }].map(({ k, l }) => (
                  <div key={k} className="space-y-1"><Label className="text-xs text-gray-500">{l}</Label><Input type="number" value={fdForm[k]} onChange={e => setFdForm({ ...fdForm, [k]: parseFloat(e.target.value) || 0 })} data-testid={`fd-${k}`} className="h-10 rounded-xl border-gray-200 bg-gray-50/50" /></div>
                ))}
                <Button onClick={calcFD} data-testid="calc-fd-btn" className="w-full rounded-full bg-dhan-blue hover:bg-dhan-blue-dark text-white">Calculate</Button>
              </div>
            </div>
            {fdResult && (
              <div className="card-base p-6 animate-scale-in" data-testid="fd-result">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">FD Tax Result</h3>
                <div className="space-y-3">
                  <div className="flex justify-between text-sm"><span className="text-gray-500">Total Interest</span><span className="font-bold text-emerald-600">Rs.{fdResult.total_interest.toLocaleString('en-IN')}</span></div>
                  <div className="flex justify-between text-sm"><span className="text-gray-500">Tax Per Year</span><span className="font-medium text-gray-900">Rs.{fdResult.tax_per_year.toLocaleString('en-IN')}</span></div>
                  <div className="flex justify-between text-sm"><span className="text-gray-500">Total Tax</span><span className="font-bold text-red-500">Rs.{fdResult.total_tax.toLocaleString('en-IN')}</span></div>
                  <div className="flex justify-between text-sm border-t border-gray-100 pt-3"><span className="text-gray-500">Post-Tax Return</span><span className="font-bold text-lg text-emerald-600">Rs.{fdResult.post_tax_return.toLocaleString('en-IN')}</span></div>
                  <div className="flex justify-between text-sm"><span className="text-gray-500">Effective Rate</span><span className="font-bold text-dhan-blue">{fdResult.effective_rate}%</span></div>
                  <p className="text-xs text-gray-400 mt-2">{fdResult.explanation}</p>
                </div>
              </div>
            )}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
