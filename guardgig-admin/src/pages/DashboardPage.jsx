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

  const sortedCities = [...(risk.city_breakdown || [])].sort(
    (a, b) => b.max_payout_pct - a.max_payout_pct || b.risk_score - a.risk_score,
  );

  const totalPortfolioUsers = (risk.city_breakdown || []).reduce(
    (sum, city) => sum + Number(city.num_users || 0),
    0,
  );
  const portfolioRiskPct = totalPortfolioUsers
    ? (Number(risk.total_expected_claims || 0) / totalPortfolioUsers) * 100
    : 0;

  const insightByRisk = {
    LOW: 'No major disruptions expected',
    MEDIUM: 'Moderate disruptions expected in some cities',
    HIGH: 'High risk of claims across multiple cities',
  };

  const getPayoutClass = (payoutPct) => {
    if (payoutPct >= 100) return 'payout-red';
    if (payoutPct >= 60) return 'payout-orange';
    if (payoutPct >= 30) return 'payout-yellow';
    return 'payout-green';
  };

  const getDisruptionLabel = (payoutPct) => {
    if (payoutPct >= 100) return 'Severe Disruption';
    if (payoutPct >= 60) return 'Moderate Disruption';
    if (payoutPct >= 30) return 'Mild Disruption';
    return 'No Trigger';
  };

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
        <h2>Next Week Risk Forecast</h2>

        {risk && (
          <>
            <section className="ai-insight-card">
              <div className="insight-title">AI Insight</div>
              <p>{insightByRisk[risk.risk_level] || insightByRisk.LOW}</p>
            </section>

            <section className="risk-grid">
              {riskCards.map((card) => (
                <article key={card.label} className="risk-card">
                  <span>{card.label}</span>
                  <strong className={`risk-${risk.risk_level.toLowerCase()}`}>{card.value}</strong>
                </article>
              ))}
            </section>

            <section className="portfolio-insights-grid">
              <article className="risk-card">
                <span>Total affected users (estimated)</span>
                <strong>{risk.total_expected_claims}</strong>
              </article>
              <article className="risk-card">
                <span>% of portfolio at risk</span>
                <strong>{portfolioRiskPct.toFixed(1)}%</strong>
              </article>
            </section>

            <section className="trigger-legend">
              <h3>Trigger to Payout Guide</h3>
              <div className="legend-items">
                <span className="legend-chip payout-green">0% - No Trigger</span>
                <span className="legend-chip payout-yellow">30% - Mild Disruption</span>
                <span className="legend-chip payout-orange">60% - Moderate Disruption</span>
                <span className="legend-chip payout-red">100% - Severe Disruption</span>
              </div>
            </section>

            {risk.high_risk_cities && risk.high_risk_cities.length > 0 && (
              <div className="high-risk-alert">
                <strong>High Risk Cities:</strong> {risk.high_risk_cities.join(', ')}
              </div>
            )}

            {sortedCities.length > 0 && (
              <section className="top-risk-cities">
                <h3>Top Risk Cities</h3>
                <div className="top-city-list">
                  {sortedCities.map((city) => (
                    <article key={`priority-${city.city}`} className="top-city-item">
                      <div>
                        <strong>{city.city}</strong>
                        <div className="top-city-meta">
                          {city.max_payout_pct}% max payout · {city.risk_level}
                        </div>
                      </div>
                      <span className={`city-risk-pill risk-${city.risk_level.toLowerCase()}`}>
                        {city.risk_level}
                      </span>
                    </article>
                  ))}
                </div>
              </section>
            )}

            {sortedCities.length > 0 && (
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
                    {sortedCities.map((city) => (
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

            {sortedCities.length > 0 && (
              <section className="city-forecast-section">
                <h3>City-wise 7-Day Forecast</h3>
                {sortedCities.map((city) => (
                  <article key={`forecast-${city.city}`} className="city-forecast-block">
                    <div className="city-forecast-header">
                      <h4>{city.city}</h4>
                      <span className={`city-risk-pill risk-${city.risk_level.toLowerCase()}`}>
                        {city.max_payout_pct}% max payout
                      </span>
                    </div>

                    <div className="forecast-days">
                      {(city.forecast_days || []).map((day) => {
                        const payout = Number(day.payout_percentage || 0);
                        const triggerType = day.trigger_type || 'NONE';
                        return (
                          <div key={`${city.city}-${day.date}`} className="forecast-day">
                            <div className="day-date">{day.date}</div>
                            <div className="day-temp">Temp: {Number(day.temperature).toFixed(1)}°C</div>
                            <div className="day-rain">Rain: {Number(day.rain).toFixed(1)} mm</div>
                            <div className="day-trigger">Trigger: {triggerType}</div>
                            <div className={`day-payout ${getPayoutClass(payout)}`}>
                              {payout}% · {getDisruptionLabel(payout)}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </article>
                ))}
              </section>
            )}
          </>
        )}
      </div>
    </div>
  );
}
