import { useState, useEffect } from 'react'

export default function ActivityLogs({ API }) {
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('')

  useEffect(() => {
    setLoading(true)
    fetch(`${API}/api/logs`)
      .then(r => r.json())
      .then(setLogs)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const filtered = filter ? logs.filter(l => l.action.includes(filter)) : logs

  return (
    <div>
      <div className="page-header">
        <h1>Activity Logs</h1>
        <div className="header-actions">
          <select value={filter} onChange={e => setFilter(e.target.value)}>
            <option value="">All Actions</option>
            <option value="ai_classification">Classification</option>
            <option value="ai_retrieval">Retrieval</option>
            <option value="ai_missing_info">Missing Info</option>
            <option value="ai_draft">Draft</option>
            <option value="ai_action">Action</option>
            <option value="ticket">Ticket</option>
          </select>
        </div>
      </div>
      {loading ? (
        <div className="loading"><div className="spinner"></div><p>Loading logs...</p></div>
      ) : logs.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">📝</div>
          <h3>No activity yet</h3>
          <p>Activity will appear here as you use the system.</p>
        </div>
      ) : (
        <div className="card">
          <p className="text-muted" style={{marginBottom: '12px'}}>{filtered.length} log entries</p>
          <table className="table log-table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Ticket</th>
                <th>Step</th>
                <th>Action</th>
                <th>Model</th>
                <th>Tokens</th>
                <th>Latency</th>
                <th>Status</th>
                <th>Details</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(log => (
                <tr key={log.id}>
                  <td>{new Date(log.created_at).toLocaleString()}</td>
                  <td>{log.ticket_id ? `#${log.ticket_id}` : '—'}</td>
                  <td>{log.step_number || '—'}</td>
                  <td><span className="badge action-badge">{log.action.replace(/_/g, ' ')}</span></td>
                  <td>{log.model_used || '—'}</td>
                  <td>{log.tokens_used || '—'}</td>
                  <td>{log.latency_ms ? `${log.latency_ms}ms` : '—'}</td>
                  <td><span className={`badge status-${log.status}`}>{log.status}</span></td>
                  <td className="log-details">{log.details?.slice(0, 120)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
