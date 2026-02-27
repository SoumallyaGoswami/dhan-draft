import { useState, useEffect } from 'react';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { BookOpen, CheckCircle, Award, Calculator, Building2, ChevronRight, X } from 'lucide-react';
import { toast } from 'sonner';

export default function LearnPage() {
  const [lessons, setLessons] = useState([]);
  const [selectedLesson, setSelectedLesson] = useState(null);
  const [quizAnswers, setQuizAnswers] = useState({});
  const [quizResult, setQuizResult] = useState(null);
  const [quizHistory, setQuizHistory] = useState([]);
  const [taxForm, setTaxForm] = useState({ income: 1000000, deductions_80c: 150000, deductions_80d: 25000, hra_exemption: 0, other_deductions: 0 });
  const [taxResult, setTaxResult] = useState(null);
  const [bankRates, setBankRates] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get('/learn/lessons'),
      api.get('/learn/quiz/history'),
      api.get('/learn/bank-rates'),
    ]).then(([l, q, b]) => {
      setLessons(l.data.data || []);
      setQuizHistory(q.data.data || []);
      setBankRates(b.data.data || []);
    }).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const submitQuiz = async () => {
    if (!selectedLesson) return;
    const quiz = selectedLesson.quiz || [];
    const answers = quiz.map((_, i) => quizAnswers[i] ?? -1);
    if (answers.includes(-1)) { toast.error('Answer all questions'); return; }
    try {
      const r = await api.post('/learn/quiz/submit', { lessonId: selectedLesson.id, answers });
      setQuizResult(r.data.data);
      toast.success(`Score: ${r.data.data.score}%`);
      const qh = await api.get('/learn/quiz/history');
      setQuizHistory(qh.data.data || []);
      const ls = await api.get('/learn/lessons');
      setLessons(ls.data.data || []);
    } catch (err) { toast.error(err.response?.data?.detail || 'Failed to submit quiz'); }
  };

  const calcTax = async () => {
    try {
      const r = await api.post('/learn/tax-compare', taxForm);
      setTaxResult(r.data.data);
    } catch (err) { toast.error('Tax calculation failed'); }
  };

  const diffMap = { beginner: 'bg-emerald-50 text-emerald-700 border-emerald-100', intermediate: 'bg-amber-50 text-amber-700 border-amber-100', advanced: 'bg-red-50 text-red-700 border-red-100' };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="w-8 h-8 border-2 border-dhan-blue border-t-transparent rounded-full animate-spin" /></div>;

  return (
    <div className="space-y-6 animate-fade-in" data-testid="learn-page">
      <div>
        <h1 className="text-3xl font-semibold text-gray-900 tracking-tight">Learn</h1>
        <p className="text-base text-gray-500 mt-1">Build your financial knowledge</p>
      </div>

      <Tabs defaultValue="lessons" className="w-full">
        <TabsList className="bg-gray-100/70 rounded-full p-1 mb-6">
          <TabsTrigger value="lessons" className="rounded-full text-sm px-5 data-[state=active]:bg-white data-[state=active]:shadow-sm" data-testid="tab-lessons">Lessons</TabsTrigger>
          <TabsTrigger value="history" className="rounded-full text-sm px-5 data-[state=active]:bg-white data-[state=active]:shadow-sm" data-testid="tab-history">Quiz History</TabsTrigger>
          <TabsTrigger value="tax" className="rounded-full text-sm px-5 data-[state=active]:bg-white data-[state=active]:shadow-sm" data-testid="tab-tax">Tax Calculator</TabsTrigger>
          <TabsTrigger value="rates" className="rounded-full text-sm px-5 data-[state=active]:bg-white data-[state=active]:shadow-sm" data-testid="tab-rates">Bank Rates</TabsTrigger>
        </TabsList>

        <TabsContent value="lessons">
          {selectedLesson ? (
            <div className="card-base p-6 animate-scale-in" data-testid="lesson-detail">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-gray-900">{selectedLesson.title}</h2>
                <button onClick={() => { setSelectedLesson(null); setQuizResult(null); setQuizAnswers({}); }} className="p-2 hover:bg-gray-100 rounded-xl transition-colors"><X className="w-5 h-5 text-gray-400" /></button>
              </div>
              <p className="text-sm text-gray-600 leading-relaxed mb-6">{selectedLesson.content}</p>

              <div className="border-t border-gray-100 pt-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Quiz</h3>
                {selectedLesson.quiz?.map((q, qi) => (
                  <div key={qi} className="mb-5">
                    <p className="text-sm font-medium text-gray-800 mb-2">{qi + 1}. {q.question}</p>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {q.options.map((opt, oi) => {
                        const selected = quizAnswers[qi] === oi;
                        const isCorrect = quizResult && quizResult.answers?.[qi] === oi;
                        const isWrong = quizResult && selected && !isCorrect;
                        return (
                          <button key={oi} onClick={() => !quizResult && setQuizAnswers({ ...quizAnswers, [qi]: oi })}
                            data-testid={`quiz-option-${qi}-${oi}`}
                            className={`text-left px-4 py-2.5 rounded-xl text-sm border transition-colors ${
                              isCorrect ? 'bg-emerald-50 border-emerald-300 text-emerald-700' :
                              isWrong ? 'bg-red-50 border-red-300 text-red-700' :
                              selected ? 'bg-blue-50 border-dhan-blue text-dhan-blue' :
                              'border-gray-200 hover:border-gray-300 text-gray-600'
                            }`}>
                            {opt}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                ))}
                {!quizResult ? (
                  <Button onClick={submitQuiz} data-testid="submit-quiz-btn" className="rounded-full bg-dhan-blue hover:bg-dhan-blue-dark text-white px-8">Submit Quiz</Button>
                ) : (
                  <div className="p-4 bg-blue-50 rounded-2xl border border-blue-100" data-testid="quiz-result">
                    <div className="flex items-center gap-3">
                      <Award className="w-6 h-6 text-dhan-blue" />
                      <span className="text-lg font-bold text-gray-900">Score: {quizResult.score}%</span>
                      <span className="text-sm text-gray-500">({quizResult.correct}/{quizResult.total} correct)</span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {lessons.map((l, i) => (
                <div key={l.id} onClick={() => { setSelectedLesson(l); setQuizResult(null); setQuizAnswers({}); }}
                  data-testid={`lesson-card-${i}`}
                  className={`card-base card-hover p-5 cursor-pointer stagger-${i + 1} animate-fade-in`}>
                  <div className="flex items-start justify-between mb-3">
                    <div className="w-10 h-10 rounded-2xl bg-blue-50 flex items-center justify-center">
                      <BookOpen className="w-5 h-5 text-dhan-blue" strokeWidth={1.8} />
                    </div>
                    <Badge className={`${diffMap[l.difficulty] || diffMap.beginner} text-xs border`}>{l.difficulty}</Badge>
                  </div>
                  <h3 className="text-sm font-semibold text-gray-900 mb-1">{l.title}</h3>
                  <p className="text-xs text-gray-500 mb-3">{l.description}</p>
                  {l.completed && (
                    <div className="flex items-center gap-2">
                      <CheckCircle className="w-3.5 h-3.5 text-emerald-500" />
                      <span className="text-xs text-emerald-600 font-medium">Best: {l.bestScore}%</span>
                      <Progress value={l.bestScore} className="h-1 flex-1" />
                    </div>
                  )}
                  {!l.completed && <div className="flex items-center gap-1 text-xs text-dhan-blue font-medium"><span>Start lesson</span><ChevronRight className="w-3.5 h-3.5" /></div>}
                </div>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="history">
          <div className="card-base p-6" data-testid="quiz-history">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Quiz History</h3>
            {quizHistory.length === 0 ? <p className="text-sm text-gray-400">No quizzes taken yet.</p> : (
              <div className="space-y-3">
                {quizHistory.map((q, i) => (
                  <div key={q.id || i} className="flex items-center gap-4 p-3 bg-gray-50 rounded-xl">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold ${q.score >= 75 ? 'bg-emerald-100 text-emerald-700' : q.score >= 50 ? 'bg-amber-100 text-amber-700' : 'bg-red-100 text-red-700'}`}>{q.score}%</div>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-800">{q.lessonTitle || 'Quiz'}</p>
                      <p className="text-xs text-gray-400">{q.correct}/{q.total} correct &middot; {new Date(q.completedAt).toLocaleDateString()}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </TabsContent>

        <TabsContent value="tax">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6" data-testid="tax-calculator">
            <div className="card-base p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2"><Calculator className="w-5 h-5 text-dhan-blue" /> Old vs New Regime</h3>
              <div className="space-y-4">
                {[
                  { k: 'income', l: 'Annual Income (Rs.)' },
                  { k: 'deductions_80c', l: '80C Deductions (max 1.5L)' },
                  { k: 'deductions_80d', l: '80D Deductions (max 25K)' },
                  { k: 'hra_exemption', l: 'HRA Exemption' },
                  { k: 'other_deductions', l: 'Other Deductions' },
                ].map(({ k, l }) => (
                  <div key={k} className="space-y-1">
                    <Label className="text-xs text-gray-500">{l}</Label>
                    <Input type="number" value={taxForm[k]} onChange={e => setTaxForm({ ...taxForm, [k]: parseFloat(e.target.value) || 0 })}
                      data-testid={`tax-input-${k}`} className="h-10 rounded-xl border-gray-200 bg-gray-50/50" />
                  </div>
                ))}
                <Button onClick={calcTax} data-testid="calc-tax-btn" className="w-full rounded-full bg-dhan-blue hover:bg-dhan-blue-dark text-white">Calculate</Button>
              </div>
            </div>
            {taxResult && (
              <div className="card-base p-6 animate-scale-in" data-testid="tax-result">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Comparison</h3>
                <div className="space-y-4">
                  {[{ key: 'old_regime', label: 'Old Regime' }, { key: 'new_regime', label: 'New Regime' }].map(({ key, label }) => (
                    <div key={key} className={`p-4 rounded-2xl border ${taxResult.recommended === key.split('_')[0] ? 'bg-blue-50 border-dhan-blue/30' : 'bg-gray-50 border-gray-200'}`}>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-semibold text-gray-900">{label}</span>
                        {taxResult.recommended === key.split('_')[0] && <Badge className="bg-dhan-blue text-white text-xs">Recommended</Badge>}
                      </div>
                      <div className="grid grid-cols-2 gap-2 text-sm">
                        <div><span className="text-gray-500">Taxable:</span> <span className="font-medium">Rs.{taxResult[key].taxable_income.toLocaleString('en-IN')}</span></div>
                        <div><span className="text-gray-500">Tax:</span> <span className="font-medium">Rs.{taxResult[key].tax.toLocaleString('en-IN')}</span></div>
                        <div><span className="text-gray-500">Cess:</span> <span className="font-medium">Rs.{taxResult[key].cess.toLocaleString('en-IN')}</span></div>
                        <div><span className="text-gray-500">Total:</span> <span className="font-bold text-gray-900">Rs.{taxResult[key].total.toLocaleString('en-IN')}</span></div>
                      </div>
                      <p className="text-xs text-gray-400 mt-2">Effective rate: {taxResult[key].effective_rate}%</p>
                    </div>
                  ))}
                  <div className="p-3 bg-emerald-50 rounded-xl border border-emerald-100 text-sm text-emerald-700 font-medium">
                    You save Rs.{taxResult.savings.toLocaleString('en-IN')} with the {taxResult.recommended === 'old' ? 'Old' : 'New'} regime
                  </div>
                </div>
              </div>
            )}
          </div>
        </TabsContent>

        <TabsContent value="rates">
          <div className="card-base p-6" data-testid="bank-rates-table">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2"><Building2 className="w-5 h-5 text-dhan-blue" /> Bank Account Types & Interest Rates</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-100">
                    {['Account Type', 'Interest Rate', 'Min Balance', 'Taxable', 'Liquidity'].map(h => (
                      <th key={h} className="text-left py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {bankRates.map((r, i) => (
                    <tr key={i} className="border-b border-gray-50 hover:bg-gray-50/50 transition-colors">
                      <td className="py-3 px-4 font-medium text-gray-800">{r.type}</td>
                      <td className="py-3 px-4 text-dhan-blue font-semibold">{r.rate}</td>
                      <td className="py-3 px-4 text-gray-600">{r.minBalance}</td>
                      <td className="py-3 px-4 text-gray-600">{r.taxable}</td>
                      <td className="py-3 px-4 text-gray-600">{r.liquidity}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
