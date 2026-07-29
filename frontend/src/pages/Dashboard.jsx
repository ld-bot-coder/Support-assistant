import { useState } from 'react'

export default function Dashboard({ tickets, onSelectTicket, onRefresh, API }) {
  const [statusFilter, setStatusFilter] = useState('')
  const [loading, setLoading] = useState(false)

  const filtered = statusFilter
    ? tickets.filter(t => t.status === statusFilter)
    : tickets

  return (
    <div>
      <div className="page-header">
        <h1>Tickets</h1>
        <div className="header-actions">
          <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)}>
            <option value="">All Status</option>
            <option value="open">Open</option>
            <option value="in_progress">In Progress</option>
            <option value="resolved">Resolved</option>
            <option value="closed">Closed</option>
          </select>
          <button className="btn btn-secondary" onClick={onRefresh} disabled={loading}>
            {loading ? 'Loading...' : 'Refresh'}
          </button>
        </div>
      </div>
      {tickets.length === 0 && !statusFilter ? (
        <div className="empty-state">
          <div className="empty-icon">📋</div>
          <h3>No tickets yet</h3>
          <p>Create your first support ticket to get started.</p>
        </div>
      ) : filtered.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">🔍</div>
          <h3>No matching tickets</h3>
          <p>No tickets match the selected filter.</p>
        </div>
      ) : (
        <table className="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Customer</th>
              <th>Product Area</th>
              <th>Issue</th>
              <th>Urgency</th>
              <th>Category</th>
              <th>Status</th>
              <th>Draft</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map(t => (
              <tr key={t.id} onClick={() => onSelectTicket(t.id)} className="clickable">
                <td>#{t.id}</td>
                <td>{t.customer_type}</td>
                <td>{t.product_area}</td>
                <td className="issue-cell">{t.issue_description.slice(0, 80)}{t.issue_description.length > 80 ? '...' : ''}</td>
                <td><span className={`badge urgency-${t.ai_suggested_urgency || t.urgency}`}>{t.ai_suggested_urgency || t.urgency}</span></td>
                <td>{t.ai_category || '—'}</td>
                <td><span className={`badge status-${t.status}`}>{t.status}</span></td>
                <td><span className={`badge draft-${t.ai_draft_status}`}>{t.ai_draft_status}</span></td>
                <td>{new Date(t.created_at).toLocaleDateString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
