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

const initialRisk = {
  risk_level: 'LOW',
  risk_score: 0,
  total_expected_claims: 0,
  projected_payout: 0,
  high_risk_cities: [],
  max_payout_tier: 0,
  days_with_triggers: 0,
  city_breakdown: [],
  forecast_summary: [],
  last_updated: '',
};

export default function DashboardPage() {
  const auth = useAuth();
  const [metrics, setMetrics] = useState(initialStats);
  const [risk, setRisk] = useState(initialRisk);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [lastUpdated, setLastUpdated] = useState('');

  useEffect(() => {
    let mounted = true;

    const loadMetrics = async () => {
      try {
        const response = await api.get('/api/admin/metrics');
        console.log(response.data);
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
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    loadMetrics();
    const intervalId = window.setInterval(loadMetrics, 10000);

    return () => {
      mounted = false;
      window.clearInterval(intervalId);
    };
  }, []);

  useEffect(() => {
    const fetchRisk = async () => {
      try {
        const res = await api.get('/api/admin/next-week-risk');
        setRisk(res.data);
      } catch (err) {
        console.error(err);
      }
    };

    fetchRisk();
  }, []);

  const cards = [
    { label: 'Total premium', value: `₹${Number(metrics.total_premium).toFixed(2)}` },
    { label: 'Total payout', value: `₹${Number(metrics.total_payout).toFixed(2)}` },
    { label: 'Loss ratio', value: `${Number(metrics.loss_ratio_percentage).toFixed(2)}%` },
    { label: 'Risk status', value: metrics.status },
  ];

  const riskCards = [
    { label: 'Next week risk', value: risk.risk_level },
    { label: 'Expected claims', value: risk.total_expected_claims },
    { label: 'Projected payout', value: `₹${Number(risk.projected_payout).toFixed(2)}` },
    { label: 'Max trigger tier', value: `${risk.max_payout_tier}%` },
  ];

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

      <div className="prediction-panel">
        <h2>🔮 Next Week Risk Forecast</h2>

        {risk && (
          <>
            <section className="risk-grid">
              {riskCards.map((card) => (
                <article key={card.label} className="risk-card">
                  <span>{card.label}</span>
                  <strong className={`risk-${risk.risk_level.toLowerCase()}`}>{card.value}</strong>
                </article>
              ))}
            </section>

            {risk.high_risk_cities && risk.high_risk_cities.length > 0 && (
              <div className="high-risk-alert">
                <strong>⚠️ High Risk Cities:</strong> {risk.high_risk_cities.join(', ')}
              </div>
            )}

            {risk.city_breakdown && risk.city_breakdown.length > 0 && (
              <div className="city-breakdown">
                <h3>City Breakdown</h3>
                <table className="breakdown-table">
                  <thead>
                    <tr>
                      <th>City</th>
                      <th>Policies</th>
                      <th>Max Trigger</th>
                      <th>Expected Claims</th>
                      <th>Projected Payout</th>
                      <th>Risk</th>
                    </tr>
                  </thead>
                  <tbody>
                    {risk.city_breakdown.map((city) => (
                      <tr key={city.city}>
                        <td>{city.city}</td>
                        <td>{city.num_policies}</td>
                        <td>{city.max_payout_pct}%</td>
                        <td>{city.expected_claims}</td>
                        <td>₹{Number(city.projected_payout).toFixed(2)}</td>
                        <td className={`risk-${city.risk_level.toLowerCase()}`}>{city.risk_level}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {risk.forecast_summary && risk.forecast_summary.length > 0 && (
              <div className="forecast-summary">
                <h3>7-Day Weather Forecast</h3>
                <div className="forecast-days">
                  {risk.forecast_summary.map((day) => (
                    <div key={day.date} className="forecast-day">
                      <div className="day-name">{day.day}</div>
                      <div className="day-date">{day.date}</div>
                      <div className="day-rain">🌧️ {Number(day.rain).toFixed(1)}mm</div>
                      <div className="day-temp">🌡️ {Number(day.temperature).toFixed(1)}°C</div>
                      <div className={`day-payout payout-${day.payout_pct}`}>{day.payout_pct}%</div>
                      {day.triggers && day.triggers.length > 0 && (
                        <div className="day-triggers">{day.triggers.join(', ')}</div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>

      <style jsx>{`
        .risk-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 1rem;
          margin: 1rem 0;
        }

        .risk-card {
          padding: 1rem;
          background: #f5f5f5;
          border-radius: 8px;
          display: flex;
          flex-direction: column;
        }

        .risk-card span {
          font-size: 0.85rem;
          color: #666;
        }

        .risk-card strong {
          font-size: 1.5rem;
          margin-top: 0.5rem;
        }

        .risk-high {
          color: #d32f2f;
        }

        .risk-medium {
          color: #f57c00;
        }

        .risk-low {
          color: #388e3c;
        }

        .high-risk-alert {
          padding: 1rem;
          background: #ffebee;
          border-left: 4px solid #d32f2f;
          margin: 1rem 0;
          border-radius: 4px;
        }

        .city-breakdown {
          margin: 2rem 0;
        }

        .breakdown-table {
          width: 100%;
          border-collapse: collapse;
          font-size: 0.9rem;
        }

        .breakdown-table th,
        .breakdown-table td {
          padding: 0.75rem;
          text-align: left;
          border-bottom: 1px solid #ddd;
        }

        .breakdown-table th {
          background: #f5f5f5;
          font-weight: 600;
        }

        .breakdown-table tbody tr:hover {
          background: #fafafa;
        }

        .forecast-summary {
          margin: 2rem 0;
        }

        .forecast-days {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
          gap: 1rem;
          margin-top: 1rem;
        }

        .forecast-day {
          padding: 1rem;
          background: #f9f9f9;
          border: 1px solid #ddd;
          border-radius: 8px;
          text-align: center;
          font-size: 0.85rem;
        }

        .day-name {
          font-weight: 600;
          margin-bottom: 0.25rem;
        }

        .day-date {
          color: #999;
          font-size: 0.75rem;
          margin-bottom: 0.5rem;
        }

        .day-rain,
        .day-temp {
          margin: 0.25rem 0;
        }

        .day-payout {
          font-weight: 600;
          padding: 0.5rem;
          border-radius: 4px;
          margin: 0.5rem 0;
        }

        .payout-100 {
          background: #ffcdd2;
          color: #b71c1c;
        }

        .payout-60 {
          background: #ffe0b2;
          color: #e65100;
        }

        .payout-30 {
          background: #c8e6c9;
          color: #2e7d32;
        }

        .payout-0 {
          background: #e8f5e9;
          color: #558b2f;
        }

        .day-triggers {
          font-size: 0.7rem;
          color: #666;
          margin-top: 0.25rem;
        }
      `}</style>
    </div>
  );
}
