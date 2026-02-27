import { useState, useEffect } from 'react';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { X, Plus } from 'lucide-react';
import { toast } from 'sonner';

export const AddAssetModal = ({ open, onClose, onAdded }) => {
  const [stocks, setStocks] = useState([]);
  const [symbol, setSymbol] = useState('');
  const [quantity, setQuantity] = useState(10);
  const [buyPrice, setBuyPrice] = useState(0);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (open) {
      api.get('/markets/stocks').then(r => {
        setStocks(r.data.data || []);
      }).catch(() => {});
    }
  }, [open]);

  useEffect(() => {
    if (symbol && stocks.length > 0) {
      const s = stocks.find(s => s.symbol === symbol);
      if (s) setBuyPrice(s.currentPrice);
    }
  }, [symbol, stocks]);

  const handleSubmit = async () => {
    if (!symbol) { toast.error('Select a stock'); return; }
    if (quantity <= 0) { toast.error('Quantity must be positive'); return; }
    if (buyPrice <= 0) { toast.error('Buy price must be positive'); return; }
    setLoading(true);
    try {
      const r = await api.post('/portfolio/add-asset', { symbol, quantity, buyPrice });
      toast.success(r.data.message);
      onAdded?.();
      onClose();
      setSymbol('');
      setQuantity(10);
      setBuyPrice(0);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to add asset');
    } finally {
      setLoading(false);
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center" data-testid="add-asset-modal-overlay">
      <div className="absolute inset-0 bg-black/20 backdrop-blur-sm" onClick={onClose} />
      <div className="relative glass-card border border-gray-200/60 shadow-float w-full max-w-md p-6 animate-scale-in" data-testid="add-asset-modal">
        <div className="flex items-center justify-between mb-5">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <Plus className="w-5 h-5 text-dhan-blue" /> Add Asset
          </h3>
          <button onClick={onClose} className="p-1.5 hover:bg-gray-100 rounded-xl transition-colors" data-testid="close-add-asset-modal">
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>

        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label className="text-xs text-gray-500 font-medium">Stock Symbol</Label>
            <Select value={symbol} onValueChange={setSymbol}>
              <SelectTrigger className="h-11 rounded-xl" data-testid="asset-symbol-select">
                <SelectValue placeholder="Select a stock" />
              </SelectTrigger>
              <SelectContent>
                {stocks.map(s => (
                  <SelectItem key={s.symbol} value={s.symbol}>
                    <div className="flex items-center gap-2">
                      <span className="font-semibold">{s.symbol}</span>
                      <span className="text-gray-400 text-xs">{s.name}</span>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label className="text-xs text-gray-500 font-medium">Quantity</Label>
              <Input
                type="number" value={quantity}
                onChange={e => setQuantity(parseInt(e.target.value) || 0)}
                data-testid="asset-quantity-input"
                className="h-11 rounded-xl border-gray-200 bg-gray-50/50"
                min="1"
              />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs text-gray-500 font-medium">Buy Price (Rs.)</Label>
              <Input
                type="number" value={buyPrice}
                onChange={e => setBuyPrice(parseFloat(e.target.value) || 0)}
                data-testid="asset-buyprice-input"
                className="h-11 rounded-xl border-gray-200 bg-gray-50/50"
                min="0" step="0.01"
              />
            </div>
          </div>

          {symbol && buyPrice > 0 && (
            <div className="p-3 bg-blue-50/60 rounded-xl border border-blue-100/60">
              <p className="text-xs text-blue-700 font-medium">
                Total investment: Rs.{(quantity * buyPrice).toLocaleString('en-IN')}
              </p>
            </div>
          )}

          <Button
            onClick={handleSubmit} disabled={loading}
            data-testid="submit-add-asset"
            className="w-full h-11 rounded-full bg-dhan-blue hover:bg-dhan-blue-dark text-white font-medium"
          >
            {loading ? 'Adding...' : 'Add to Portfolio'}
          </Button>
        </div>
      </div>
    </div>
  );
};
