import { useState } from 'react';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { ShieldCheck, AlertTriangle, ScanSearch, FileWarning, CheckCircle } from 'lucide-react';
import { toast } from 'sonner';

export default function RiskSafetyPage() {
  const [txForm, setTxForm] = useState({ amount: 75000, type: 'bank_transfer', description: 'Payment for services', recipientNew: false });
  const [txResult, setTxResult] = useState(null);
  const [fraudText, setFraudText] = useState('');
  const [fraudResult, setFraudResult] = useState(null);
  const [loadingTx, setLoadingTx] = useState(false);
  const [loadingFraud, setLoadingFraud] = useState(false);

  const checkTx = async () => {
    setLoadingTx(true);
    try { const r = await api.post('/risk/transaction', txForm); setTxResult(r.data.data); } catch { toast.error('Check failed'); }
    finally { setLoadingTx(false); }
  };

  const checkFraud = async () => {
    if (!fraudText.trim()) { toast.error('Enter text to analyze'); return; }
    setLoadingFraud(true);
    try { const r = await api.post('/risk/fraud', { text: fraudText }); setFraudResult(r.data.data); } catch { toast.error('Detection failed'); }
    finally { setLoadingFraud(false); }
  };

  const riskColor = (score) => score > 70 ? 'red' : score > 40 ? 'amber' : 'emerald';
  const verdictColor = { 'High Risk': 'red', 'Suspicious': 'amber', 'Low Risk': 'blue', 'Safe': 'emerald' };

  const highlightText = (text, highlights) => {
    if (!highlights?.length) return <span>{text}</span>;
    const sorted = [...highlights].sort((a, b) => a.start - b.start);
    const parts = [];
    let lastEnd = 0;
    sorted.forEach((h, i) => {
      if (h.start > lastEnd) parts.push(<span key={`t-${i}`}>{text.slice(lastEnd, h.start)}</span>);
      parts.push(<mark key={`h-${i}`} className="bg-red-100 text-red-700 px-0.5 rounded font-medium">{text.slice(h.start, h.end)}</mark>);
      lastEnd = h.end;
    });
    if (lastEnd < text.length) parts.push(<span key="end">{text.slice(lastEnd)}</span>);
    return <>{parts}</>;
  };

  return (
    <div className="space-y-6 animate-fade-in" data-testid="risk-page">
      <div>
        <h1 className="text-3xl font-semibold text-gray-900 tracking-tight">Risk & Safety</h1>
        <p className="text-base text-gray-500 mt-1">Assess transaction risks and detect fraud</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Transaction Risk Engine */}
        <div className="space-y-4">
          <div className="card-base p-6" data-testid="transaction-risk-form">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-dhan-blue" /> Transaction Risk Check
            </h3>
            <div className="space-y-3">
              <div className="space-y-1">
                <Label className="text-xs text-gray-500">Amount (Rs.)</Label>
                <Input type="number" value={txForm.amount} onChange={e => setTxForm({ ...txForm, amount: parseFloat(e.target.value) || 0 })}
                  data-testid="tx-amount" className="h-10 rounded-xl border-gray-200 bg-gray-50/50" />
              </div>
              <div className="space-y-1">
                <Label className="text-xs text-gray-500">Transaction Type</Label>
                <Select value={txForm.type} onValueChange={v => setTxForm({ ...txForm, type: v })}>
                  <SelectTrigger className="h-10 rounded-xl" data-testid="tx-type"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="bank_transfer">Bank Transfer</SelectItem>
                    <SelectItem value="upi">UPI Payment</SelectItem>
                    <SelectItem value="international_transfer">International Transfer</SelectItem>
                    <SelectItem value="wire_transfer">Wire Transfer</SelectItem>
                    <SelectItem value="card_payment">Card Payment</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1">
                <Label className="text-xs text-gray-500">Description</Label>
                <Input value={txForm.description} onChange={e => setTxForm({ ...txForm, description: e.target.value })}
                  data-testid="tx-description" className="h-10 rounded-xl border-gray-200 bg-gray-50/50" placeholder="Payment description..." />
              </div>
              <div className="flex items-center justify-between py-2">
                <Label className="text-sm text-gray-700">New Recipient?</Label>
                <Switch checked={txForm.recipientNew} onCheckedChange={v => setTxForm({ ...txForm, recipientNew: v })} data-testid="tx-new-recipient" />
              </div>
              <Button onClick={checkTx} disabled={loadingTx} data-testid="check-tx-btn" className="w-full rounded-full bg-dhan-blue hover:bg-dhan-blue-dark text-white">
                {loadingTx ? 'Checking...' : 'Analyze Risk'}
              </Button>
            </div>
          </div>

          {txResult && (
            <div className="card-base p-6 animate-scale-in" data-testid="tx-result">
              <div className="flex items-center gap-4 mb-4">
                <div className={`w-16 h-16 rounded-2xl flex items-center justify-center bg-${riskColor(txResult.risk_score)}-50`}>
                  <span className={`text-2xl font-bold text-${riskColor(txResult.risk_score)}-600`}>{txResult.risk_score}</span>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Risk Score</p>
                  <p className={`text-lg font-bold text-${riskColor(txResult.risk_score)}-600`}>
                    {txResult.risk_score > 70 ? 'High Risk' : txResult.risk_score > 40 ? 'Medium Risk' : 'Low Risk'}
                  </p>
                </div>
              </div>
              {txResult.reasons?.length > 0 && (
                <div className="space-y-2 mb-4">
                  {txResult.reasons.map((r, i) => (
                    <div key={i} className="flex items-start gap-2 text-sm">
                      <AlertTriangle className={`w-4 h-4 text-${riskColor(txResult.risk_score)}-500 shrink-0 mt-0.5`} />
                      <span className="text-gray-600">{r}</span>
                    </div>
                  ))}
                </div>
              )}
              <div className={`p-3 rounded-xl bg-${riskColor(txResult.risk_score)}-50 border border-${riskColor(txResult.risk_score)}-100`}>
                <p className={`text-sm font-medium text-${riskColor(txResult.risk_score)}-700`}>{txResult.recommendation}</p>
                <p className={`text-xs text-${riskColor(txResult.risk_score)}-600 mt-1`}>{txResult.delay}</p>
              </div>
            </div>
          )}
        </div>

        {/* Fraud Detector */}
        <div className="space-y-4">
          <div className="card-base p-6" data-testid="fraud-detector-form">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <ScanSearch className="w-5 h-5 text-dhan-blue" /> Fraud Message Detector
            </h3>
            <div className="space-y-3">
              <div className="space-y-1">
                <Label className="text-xs text-gray-500">Paste suspicious message</Label>
                <Textarea
                  value={fraudText} onChange={e => setFraudText(e.target.value)}
                  data-testid="fraud-text-input"
                  placeholder="Paste a suspicious SMS, email, or message here to analyze for fraud indicators..."
                  className="min-h-[140px] rounded-xl border-gray-200 bg-gray-50/50 resize-none"
                />
              </div>
              <Button onClick={checkFraud} disabled={loadingFraud} data-testid="check-fraud-btn" className="w-full rounded-full bg-dhan-blue hover:bg-dhan-blue-dark text-white">
                {loadingFraud ? 'Analyzing...' : 'Detect Fraud'}
              </Button>
            </div>
          </div>

          {fraudResult && (
            <div className="card-base p-6 animate-scale-in" data-testid="fraud-result">
              <div className="flex items-center gap-4 mb-4">
                <div className={`w-16 h-16 rounded-2xl flex items-center justify-center bg-${verdictColor[fraudResult.verdict] || 'gray'}-50`}>
                  {fraudResult.verdict === 'Safe' ? <CheckCircle className="w-8 h-8 text-emerald-500" /> : <FileWarning className={`w-8 h-8 text-${verdictColor[fraudResult.verdict]}-500`} />}
                </div>
                <div>
                  <Badge className={`bg-${verdictColor[fraudResult.verdict] || 'gray'}-50 text-${verdictColor[fraudResult.verdict] || 'gray'}-700 border border-${verdictColor[fraudResult.verdict] || 'gray'}-200 text-sm`}>
                    {fraudResult.verdict}
                  </Badge>
                  <p className="text-sm text-gray-500 mt-1">Probability: {fraudResult.probability}%</p>
                </div>
              </div>

              {fraudText && fraudResult.highlights?.length > 0 && (
                <div className="p-4 bg-gray-50 rounded-xl mb-4 text-sm leading-relaxed" data-testid="fraud-highlighted-text">
                  {highlightText(fraudText, fraudResult.highlights)}
                </div>
              )}

              {Object.keys(fraudResult.keywords_found || {}).length > 0 && (
                <div className="mb-4">
                  <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Detected Keywords</p>
                  <div className="flex flex-wrap gap-1.5">
                    {Object.entries(fraudResult.keywords_found).map(([kw, w]) => (
                      <Badge key={kw} className="bg-red-50 text-red-600 border border-red-100 text-xs">{kw} ({w})</Badge>
                    ))}
                  </div>
                </div>
              )}

              <div className={`p-3 rounded-xl bg-${verdictColor[fraudResult.verdict] || 'gray'}-50 border border-${verdictColor[fraudResult.verdict] || 'gray'}-100`}>
                <p className={`text-sm font-medium text-${verdictColor[fraudResult.verdict] || 'gray'}-700`}>{fraudResult.recommendation}</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
