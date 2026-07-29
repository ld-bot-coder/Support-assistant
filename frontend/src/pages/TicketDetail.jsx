import { useState, useEffect } from 'react'

const AI_STEPS = [
  'Classifying issue...',
  'Retrieving knowledge articles...',
  'Identifying missing info...',
  'Drafting response...',
  'Suggesting action...'
]

export default function TicketDetail({ ticketId, onBack, onRefresh, API, showToast }) {
  const [ticket, setTicket] = useState(null)
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState(false)
  const [currentStep, setCurrentStep] = useState(0)
  const [stepLogs, setStepLogs] = useState([])
  const [error, setError] = useState('')
  const [logs, setLogs] = useState([])
  const [communications, setCommunications] = useState([])
  const [commsLoading, setCommsLoading] = useState(false)
  const [newComm, setNewComm] = useState({ sender: 'agent', content: '', communication_type: 'note' })
  const [sendingComm, setSendingComm] = useState(false)
  const [editingResponse, setEditingResponse] = useState(false)
  const [editedResponse, setEditedResponse] = useState('')
  const [savingEdit, setSavingEdit] = useState(false)

  const fetchTicket = () => {
    setLoading(true)
    fetch(`${API}/api/tickets/${ticketId}`)
      .then(r => { if (!r.ok) throw new Error('Failed to load ticket'); return r.json() })
      .then(t => { setTicket(t); setLoading(false); setEditedResponse(t.ai_drafted_response || '') })
      .catch(() => { setError('Failed to load ticket'); setLoading(false) })
  }

  const fetchLogs = () => {
    fetch(`${API}/api/logs?ticket_id=${ticketId}`)
      .then(r => r.json())
      .then(setLogs)
      .catch(() => {})
  }

  const fetchCommunications = () => {
    setCommsLoading(true)
    fetch(`${API}/api/tickets/${ticketId}/communications`)
      .then(r => r.json())
      .then(setCommunications)
      .catch(() => {})
      .finally(() => setCommsLoading(false))
  }

  useEffect(() => { fetchTicket(); fetchLogs(); fetchCommunications() }, [ticketId])

  const runAIWorkflow = async () => {
    setRunning(true)
    setCurrentStep(0)
    setStepLogs([])
    setError('')
    for (let i = 0; i < AI_STEPS.length; i++) {
      setCurrentStep(i)
      await new Promise(r => setTimeout(r, 800))
    }
    try {
      const res = await fetch(`${API}/api/tickets/${ticketId}/run-ai-workflow`, { method: 'POST' })
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'AI workflow failed')
      }
      const updated = await res.json()
      setTicket(updated)
      setEditedResponse(updated.ai_drafted_response || '')
      fetchLogs()
      onRefresh()
      showToast('AI workflow completed successfully')
    } catch (err) {
      setError(err.message)
      showToast(err.message, 'error')
    } finally {
      setRunning(false)
      setCurrentStep(0)
    }
  }

  const updateTicket = async (patch) => {
    try {
      const res = await fetch(`${API}/api/tickets/${ticketId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(patch)
      })
      if (!res.ok) throw new Error('Update failed')
      const updated = await res.json()
      setTicket(updated)
      if (patch.ai_drafted_response) setEditedResponse(patch.ai_drafted_response)
      onRefresh()
      showToast('Ticket updated')
    } catch (err) {
      setError(err.message)
      showToast(err.message, 'error')
    }
  }

  const saveEditedResponse = async () => {
    setSavingEdit(true)
    await updateTicket({ ai_drafted_response: editedResponse })
    setEditingResponse(false)
    setSavingEdit(false)
  }

  const sendCommunication = async (e) => {
    e.preventDefault()
    if (!newComm.content.trim()) return
    setSendingComm(true)
    try {
      const res = await fetch(`${API}/api/tickets/${ticketId}/communications`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newComm)
      })
      if (!res.ok) throw new Error('Failed to send')
      const comm = await res.json()
      setCommunications(prev => [...prev, comm])
      setNewComm({ sender: 'agent', content: '', communication_type: 'note' })
      showToast('Communication added')
    } catch (err) {
      showToast(err.message, 'error')
    } finally {
      setSendingComm(false)
    }
  }

  if (loading) return <div className="loading"><div className="spinner"></div><p>Loading ticket...</p></div>
  if (!ticket) return <div className="error-message">{error || 'Ticket not found'}</div>

  const retrievedArticles = safeParse(ticket.ai_retrieved_articles, [])
  const missingInfo = safeParse(ticket.ai_missing_info, [])
  const followUp = safeParse(ticket.ai_follow_up_questions, [])
  const citations = safeParse(ticket.ai_suggested_action_citations, {})

  return (
    <div>
      <div className="page-header">
        <h1>Ticket #{ticket.id}</h1>
        <button className="btn btn-secondary" onClick={onBack}>← Back to Dashboard</button>
      </div>

      {error && <div className="error-message">{error}<button className="error-dismiss" onClick={() => setError('')}>✕</button></div>}

      <div className="ticket-meta">
        <div className="meta-card">
          <label>Customer Type</label>
          <span>{ticket.customer_type}</span>
        </div>
        <div className="meta-card">
          <label>Product Area</label>
          <span>{ticket.product_area}</span>
        </div>
        <div className="meta-card">
          <label>Urgency</label>
          <span className={`badge urgency-${ticket.ai_suggested_urgency || ticket.urgency}`}>
            {ticket.ai_suggested_urgency || ticket.urgency}
          </span>
        </div>
        <div className="meta-card">
          <label>Status</label>
          <select value={ticket.status} onChange={e => updateTicket({ status: e.target.value })}>
            <option value="open">Open</option>
            <option value="in_progress">In Progress</option>
            <option value="resolved">Resolved</option>
            <option value="closed">Closed</option>
          </select>
        </div>
        <div className="meta-card">
          <label>AI Category</label>
          <span>{ticket.ai_category || 'Not classified'}</span>
        </div>
        <div className="meta-card">
          <label>Draft Status</label>
          <span className={`badge draft-${ticket.ai_draft_status}`}>{ticket.ai_draft_status}</span>
        </div>
        <div className="meta-card">
          <label>Created</label>
          <span>{new Date(ticket.created_at).toLocaleString()}</span>
        </div>
      </div>

      <div className="card">
        <h3>Issue Description</h3>
        <p className="issue-text">{ticket.issue_description}</p>
        {ticket.previous_communication && (
          <>
            <h4>Previous Communication</h4>
            <p className="issue-text">{ticket.previous_communication}</p>
          </>
        )}
      </div>

      {ticket.ai_classification_raw && (
        <div className="card">
          <h3>AI Classification</h3>
          <p><strong>Category:</strong> {ticket.ai_category}</p>
          <p><strong>Suggested Urgency:</strong> {ticket.ai_suggested_urgency}</p>
          <details>
            <summary>Classification Details</summary>
            <pre>{ticket.ai_classification_raw}</pre>
          </details>
        </div>
      )}

      {retrievedArticles.length > 0 && (
        <div className="card">
          <h3>Retrieved Knowledge Base Articles ({retrievedArticles.length})</h3>
          {retrievedArticles.map((a, i) => (
            <details key={i} className="kb-article">
              <summary>{a.title}</summary>
              <p>{a.content}</p>
              <small>Category: {a.category}</small>
            </details>
          ))}
        </div>
      )}

      {missingInfo.length > 0 && (
        <div className="card">
          <h3>Missing Information</h3>
          <ul>{missingInfo.map((m, i) => <li key={i}>{m}</li>)}</ul>
          <h4>Follow-up Questions</h4>
          <ul>{followUp.map((q, i) => <li key={i}>{q}</li>)}</ul>
        </div>
      )}

      {ticket.ai_drafted_response && (
        <div className="card">
          <div className="card-header-row">
            <h3>Drafted Response</h3>
            {!editingResponse && (
              <button className="btn btn-sm" onClick={() => { setEditingResponse(true); setEditedResponse(ticket.ai_drafted_response) }}>
                Edit Response
              </button>
            )}
          </div>
          {editingResponse ? (
            <div className="edit-response">
              <textarea
                className="response-editor"
                value={editedResponse}
                onChange={e => setEditedResponse(e.target.value)}
                rows={10}
              />
              <div className="edit-actions">
                <button className="btn btn-secondary" onClick={() => setEditingResponse(false)} disabled={savingEdit}>Cancel</button>
                <button className="btn btn-primary" onClick={saveEditedResponse} disabled={savingEdit}>
                  {savingEdit ? 'Saving...' : 'Save & Approve'}
                </button>
              </div>
            </div>
          ) : (
            <div className="response-text">{ticket.ai_drafted_response}</div>
          )}
          <div className="draft-actions">
            <button className="btn btn-success" onClick={() => updateTicket({ ai_draft_status: 'approved' })} disabled={ticket.ai_draft_status === 'approved'}>
              {ticket.ai_draft_status === 'approved' ? '✓ Approved' : 'Approve'}
            </button>
            <button className="btn btn-danger" onClick={() => updateTicket({ ai_draft_status: 'rejected' })} disabled={ticket.ai_draft_status === 'rejected'}>
              {ticket.ai_draft_status === 'rejected' ? '✕ Rejected' : 'Reject'}
            </button>
            {citations.citations && citations.citations.length > 0 && (
              <span className="citation-info">Uses articles: {citations.citations.join(', ')}</span>
            )}
          </div>
        </div>
      )}

      {ticket.ai_suggested_action_type && (
        <div className="card">
          <h3>Suggested Internal Action</h3>
          <p><strong>Action:</strong> <span className="badge action-type">{ticket.ai_suggested_action_type.replace(/_/g, ' ')}</span></p>
          <p>{ticket.ai_suggested_action_description}</p>
          {citations.action_reasoning && <p><strong>Reasoning:</strong> {citations.action_reasoning}</p>}
          <div className="draft-actions">
            <button className="btn btn-success" onClick={() => updateTicket({ ai_action_status: 'approved' })} disabled={ticket.ai_action_status === 'approved'}>
              {ticket.ai_action_status === 'approved' ? '✓ Approved' : 'Approve Action'}
            </button>
            <button className="btn btn-danger" onClick={() => updateTicket({ ai_action_status: 'rejected' })} disabled={ticket.ai_action_status === 'rejected'}>
              {ticket.ai_action_status === 'rejected' ? '✕ Rejected' : 'Reject Action'}
            </button>
          </div>
        </div>
      )}

      <div className="card">
        <h3>AI Workflow</h3>
        {running ? (
          <div className="ai-progress">
            <div className="progress-steps">
              {AI_STEPS.map((step, i) => (
                <div key={i} className={`progress-step ${i < currentStep ? 'done' : i === currentStep ? 'active' : ''}`}>
                  <span className="step-icon">{i < currentStep ? '✓' : i === currentStep ? <span className="spinner-sm"></span> : '○'}</span>
                  <span className="step-text">{step}</span>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <button className="btn btn-primary" onClick={runAIWorkflow}>
            {ticket.ai_category ? 'Re-run AI Workflow' : 'Run AI Workflow'}
          </button>
        )}
      </div>

      <div className="card">
        <h3>Communication History ({communications.length})</h3>
        {commsLoading ? (
          <div className="loading-sm">Loading...</div>
        ) : communications.length === 0 ? (
          <p className="text-muted">No communications yet.</p>
        ) : (
          <div className="comms-list">
            {communications.map(c => (
              <div key={c.id} className={`comm-item comm-${c.communication_type}`}>
                <div className="comm-header">
                  <strong>{c.sender}</strong>
                  <span className="badge comm-type">{c.communication_type}</span>
                  <span className="comm-time">{new Date(c.created_at).toLocaleString()}</span>
                </div>
                <p className="comm-content">{c.content}</p>
              </div>
            ))}
          </div>
        )}
        <form onSubmit={sendCommunication} className="comm-form">
          <div className="comm-form-row">
            <select value={newComm.sender} onChange={e => setNewComm({...newComm, sender: e.target.value})}>
              <option value="agent">Agent</option>
              <option value="customer">Customer</option>
              <option value="system">System</option>
            </select>
            <select value={newComm.communication_type} onChange={e => setNewComm({...newComm, communication_type: e.target.value})}>
              <option value="note">Internal Note</option>
              <option value="email">Email</option>
              <option value="chat">Chat</option>
            </select>
          </div>
          <textarea
            value={newComm.content}
            onChange={e => setNewComm({...newComm, content: e.target.value})}
            placeholder="Add a communication..."
            rows={3}
          />
          <button type="submit" className="btn btn-primary btn-sm" disabled={sendingComm || !newComm.content.trim()}>
            {sendingComm ? 'Sending...' : 'Add Communication'}
          </button>
        </form>
      </div>

      {logs.length > 0 && (
        <div className="card">
          <h3>AI Workflow Logs</h3>
          <table className="table log-table">
            <thead>
              <tr><th>Step</th><th>Action</th><th>Model</th><th>Tokens</th><th>Latency</th><th>Status</th><th>Details</th></tr>
            </thead>
            <tbody>
              {logs.map(log => (
                <tr key={log.id}>
                  <td>{log.step_number || '—'}</td>
                  <td><span className="badge action-badge">{log.action.replace(/_/g, ' ')}</span></td>
                  <td>{log.model_used || '—'}</td>
                  <td>{log.tokens_used || '—'}</td>
                  <td>{log.latency_ms ? `${log.latency_ms}ms` : '—'}</td>
                  <td><span className={`badge status-${log.status}`}>{log.status}</span></td>
                  <td className="log-details">{log.details?.slice(0, 100)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function safeParse(str, fallback) {
  if (!str) return fallback
  try { return JSON.parse(str) } catch { return fallback }
}
