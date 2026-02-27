import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Eye, EyeOff } from 'lucide-react';
import { toast } from 'sonner';

export default function RegisterPage() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name || !email || !password) { toast.error('Please fill in all fields'); return; }
    if (password.length < 6) { toast.error('Password must be at least 6 characters'); return; }
    setLoading(true);
    try {
      await register(name, email, password);
      toast.success('Account created successfully!');
      navigate('/overview');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-white to-gray-50 p-4" data-testid="register-page">
      <div className="w-full max-w-[420px] animate-fade-in">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-gray-900 tracking-tight">
            <span className="text-dhan-blue">Dhan</span>Draft
          </h1>
          <p className="text-sm text-gray-500 mt-2">Financial Intelligence Platform</p>
        </div>

        <div className="bg-white rounded-3xl border border-gray-100 shadow-soft p-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-1">Create account</h2>
          <p className="text-sm text-gray-500 mb-6">Start your financial journey</p>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-2">
              <Label htmlFor="name" className="text-sm font-medium text-gray-700">Full Name</Label>
              <Input
                id="name" type="text" placeholder="Arjun Mehta"
                value={name} onChange={(e) => setName(e.target.value)}
                data-testid="register-name-input"
                className="h-12 rounded-xl border-gray-200 bg-gray-50/50 focus:border-dhan-blue focus:ring-dhan-blue/20"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email" className="text-sm font-medium text-gray-700">Email</Label>
              <Input
                id="email" type="email" placeholder="you@example.com"
                value={email} onChange={(e) => setEmail(e.target.value)}
                data-testid="register-email-input"
                className="h-12 rounded-xl border-gray-200 bg-gray-50/50 focus:border-dhan-blue focus:ring-dhan-blue/20"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password" className="text-sm font-medium text-gray-700">Password</Label>
              <div className="relative">
                <Input
                  id="password" type={showPw ? 'text' : 'password'} placeholder="Min. 6 characters"
                  value={password} onChange={(e) => setPassword(e.target.value)}
                  data-testid="register-password-input"
                  className="h-12 rounded-xl border-gray-200 bg-gray-50/50 pr-10 focus:border-dhan-blue focus:ring-dhan-blue/20"
                />
                <button type="button" onClick={() => setShowPw(!showPw)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
                  {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>
            <Button
              type="submit" disabled={loading}
              data-testid="register-submit-btn"
              className="w-full h-12 rounded-full bg-dhan-blue hover:bg-dhan-blue-dark text-white font-medium transition-colors"
            >
              {loading ? 'Creating account...' : 'Create account'}
            </Button>
          </form>

          <p className="text-center text-sm text-gray-500 mt-6">
            Already have an account?{' '}
            <Link to="/login" className="text-dhan-blue font-medium hover:underline" data-testid="go-to-login">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
