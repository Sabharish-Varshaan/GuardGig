import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';

const initialStats = {
  total_premium: 0,
  total_payout: 0,
  loss_ratio: 0,
  loss_ratio_percentage: 0,
  status: 'healthy',
  last_updated: '',
};

const initialPrediction = {
  next_week_risk: 'LOW',
  risk_score: 0,
  expected_disruption: '',
  last_updated: '',
};

export default function DashboardPage() {
  const auth = useAuth();
  const [metrics, setMetrics] = useState(initialStats);
  const [prediction, setPrediction] = useState(initialPrediction);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [lastUpdated, setLastUpdated] = useState('');

  useEffect(() => {
    let mounted = true;

    const loadMetrics = async () => {
      try {
        const response = await api.get('/api/admin/metrics');
        if (!mounted) {
          return;
        }
        setMetrics(response.data);
        setError('');
        setLastUpdated(new Date(response.data.last_updated).toLocaleTimeString());
      } catch (err) {
        if (!mounted) {
          return;
        }
        setError(err?.response?.data?.detail || 'Unable to load metrics');
      }
    };

    const loadPrediction = async () => {
      try {
        const response = await api.get('/api/admin/predictions', {
          headers: auth.token ? { Authorization: `Bearer ${auth.token}` } : {},
        });
        if (!mounted) {
          return;
        }
        setPrediction(response.data);
      } catch (err) {
        if (!mounted) {
          return;
        }
        setError(err?.response?.data?.detail || 'Unable to load predictions');
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    loadMetrics();
    loadPrediction();
    const intervalId = window.setInterval(loadMetrics, 10000);

    return () => {
      mounted = false;
      window.clearInterval(intervalId);
    };
  }, []);

  const cards = [
    { label: 'Total premium', value: `₹${Number(metrics.total_premium).toFixed(2)}` },
    { label: 'Total payout', value: `₹${Number(metrics.total_payout).toFixed(2)}` },
    { label: 'Loss ratio', value: `${Number(metrics.loss_ratio_percentage).toFixed(2)}%` },
    { label: 'Risk status', value: metrics.status },
  ];

  const predictionTone = String(prediction.next_week_risk || 'LOW').toLowerCase();

  return (
    <div className="dashboard-shell">
      <header className="dashboard-header">
        <div>
          <div className="eyebrow">GuardGig Admin</div>
          <h1>System status</h1>
          <p>Live operational metrics for policy and claims performance.</p>
        </div>
        <div className="header-actions">
          <div className="status-pill">{auth.role || 'admin'}</div>
          <button type="button" className="secondary-btn" onClick={auth.logout}>
            Logout
          </button>
        </div>
      </header>

      <section className="dashboard-meta">
        <div>Auto-refresh: every 10 seconds</div>
        <div>{lastUpdated ? `Last updated: ${lastUpdated}` : 'Waiting for first refresh...'}</div>
      </section>

      {error ? <div className="error-banner">{error}</div> : null}
      {loading ? <div className="loading-card">Loading metrics...</div> : null}

      <section className="metrics-grid">
        {cards.map((card) => (
          <article key={card.label} className="metric-card">
            <span>{card.label}</span>
            <strong>{card.value}</strong>
          </article>
        ))}
      </section>

      <section className="prediction-panel">
        <div className="section-heading">
          <div className="eyebrow">AI Predictions</div>
          <h2>Next week outlook</h2>
        </div>

        <div className="prediction-grid">
          <article className={`prediction-card prediction-${predictionTone}`}>
            <span>Next Week Risk</span>
            <strong>{prediction.next_week_risk}</strong>
          </article>

          <article className="prediction-card">
            <span>Risk Score</span>
            <strong>{Number(prediction.risk_score).toFixed(2)}</strong>
          </article>

          <article className="prediction-card prediction-wide">
            <span>Expected Disruption</span>
            <strong>{prediction.expected_disruption || 'Waiting for prediction...'}</strong>
          </article>
        </div>
      </section>
    </div>
  );
}
