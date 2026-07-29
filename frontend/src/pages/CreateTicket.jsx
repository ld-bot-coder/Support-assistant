import { useState } from 'react'

export default function CreateTicket({ onCreated, onCancel, API }) {
  const [form, setForm] = useState({
    customer_type: 'customer',
    product_area: '',
    issue_description: '',
    previous_communication: '',
    urgency: 'medium'
  })
  const [saving, setSaving] = useState(false)
  const [errors, setErrors] = useState({})

  const handleChange = (e) => {
    const { name, value } = e.target
    setForm(prev => ({ ...prev, [name]: value }))
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }))
    }
  }

  const validate = () => {
    const e = {}
    if (!form.product_area) e.product_area = 'Product area is required'
    if (!form.issue_description.trim()) e.issue_description = 'Issue description is required'
    if (form.issue_description.length < 10) e.issue_description = 'Issue description must be at least 10 characters'
    return e
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    const validationErrors = validate()
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors)
      return
    }
    setSaving(true)
    try {
      const res = await fetch(`${API}/api/tickets`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form)
      })
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Failed to create ticket')
      }
      const ticket = await res.json()
      onCreated(ticket)
    } catch (err) {
      setErrors({ submit: err.message })
    } finally {
      setSaving(false)
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1>Create New Ticket</h1>
        <button className="btn btn-secondary" onClick={onCancel}>Back</button>
      </div>
      <form onSubmit={handleSubmit} className="ticket-form">
        <div className="form-row">
          <div className="form-group">
            <label>Customer Type</label>
            <select name="customer_type" value={form.customer_type} onChange={handleChange}>
              <option value="customer">Customer</option>
              <option value="partner">Partner</option>
              <option value="internal">Internal</option>
              <option value="trial_user">Trial User</option>
            </select>
          </div>
          <div className="form-group">
            <label>Urgency</label>
            <select name="urgency" value={form.urgency} onChange={handleChange}>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>
          </div>
        </div>
        <div className="form-group">
          <label>Product Area *</label>
          <select name="product_area" value={form.product_area} onChange={handleChange} className={errors.product_area ? 'input-error' : ''}>
            <option value="">Select product area...</option>
            <option value="billing">Billing</option>
            <option value="api">API</option>
            <option value="dashboard">Dashboard</option>
            <option value="integrations">Integrations</option>
            <option value="account">Account</option>
            <option value="mobile">Mobile App</option>
            <option value="other">Other</option>
          </select>
          {errors.product_area && <span className="field-error">{errors.product_area}</span>}
        </div>
        <div className="form-group">
          <label>Issue Description *</label>
          <textarea name="issue_description" value={form.issue_description} onChange={handleChange} rows={5} className={errors.issue_description ? 'input-error' : ''} placeholder="Describe the issue in detail..." />
          {errors.issue_description && <span className="field-error">{errors.issue_description}</span>}
        </div>
        <div className="form-group">
          <label>Previous Communication</label>
          <textarea name="previous_communication" value={form.previous_communication} onChange={handleChange} rows={3} placeholder="Any prior conversation with the customer (optional)" />
        </div>
        {errors.submit && <div className="error-message">{errors.submit}</div>}
        <div className="form-actions">
          <button type="button" className="btn btn-secondary" onClick={onCancel}>Cancel</button>
          <button type="submit" className="btn btn-primary" disabled={saving}>
            {saving ? 'Creating...' : 'Create Ticket'}
          </button>
        </div>
      </form>
    </div>
  )
}
