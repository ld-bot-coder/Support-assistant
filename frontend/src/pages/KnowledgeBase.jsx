import { useState, useEffect } from 'react'

export default function KnowledgeBase({ API, showToast }) {
  const [articles, setArticles] = useState([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ title: '', content: '', category: 'general', tags: '' })
  const [saving, setSaving] = useState(false)
  const [errors, setErrors] = useState({})

  const fetchArticles = () => {
    setLoading(true)
    fetch(`${API}/api/knowledge-base`)
      .then(r => r.json())
      .then(setArticles)
      .catch(() => {})
      .finally(() => setLoading(false))
  }

  useEffect(() => { fetchArticles() }, [])

  const validate = () => {
    const e = {}
    if (!form.title.trim()) e.title = 'Title is required'
    if (!form.content.trim()) e.content = 'Content is required'
    return e
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    const v = validate()
    if (Object.keys(v).length > 0) { setErrors(v); return }
    setSaving(true)
    try {
      const res = await fetch(`${API}/api/knowledge-base`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form)
      })
      if (!res.ok) throw new Error('Failed to create article')
      setForm({ title: '', content: '', category: 'general', tags: '' })
      setErrors({})
      setShowForm(false)
      fetchArticles()
      showToast('Article created')
    } catch (err) {
      showToast(err.message, 'error')
    } finally {
      setSaving(false)
    }
  }

  const deleteArticle = async (id, title) => {
    if (!confirm(`Delete "${title}"?`)) return
    try {
      await fetch(`${API}/api/knowledge-base/${id}`, { method: 'DELETE' })
      fetchArticles()
      showToast('Article deleted')
    } catch (err) {
      showToast(err.message, 'error')
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1>Knowledge Base</h1>
        <div className="header-actions">
          <span className="text-muted">{articles.length} articles</span>
          <button className="btn btn-primary" onClick={() => { setShowForm(!showForm); setErrors({}) }}>
            {showForm ? 'Cancel' : '+ Add Article'}
          </button>
        </div>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="ticket-form kb-form">
          <div className="form-group">
            <label>Title *</label>
            <input value={form.title} onChange={e => setForm({...form, title: e.target.value})} className={errors.title ? 'input-error' : ''} />
            {errors.title && <span className="field-error">{errors.title}</span>}
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>Category</label>
              <select value={form.category} onChange={e => setForm({...form, category: e.target.value})}>
                <option value="general">General</option>
                <option value="billing">Billing</option>
                <option value="technical">Technical</option>
                <option value="account">Account</option>
              </select>
            </div>
            <div className="form-group">
              <label>Tags (comma-separated)</label>
              <input value={form.tags} onChange={e => setForm({...form, tags: e.target.value})} placeholder="e.g., password,login" />
            </div>
          </div>
          <div className="form-group">
            <label>Content *</label>
            <textarea value={form.content} onChange={e => setForm({...form, content: e.target.value})} rows={6} className={errors.content ? 'input-error' : ''} />
            {errors.content && <span className="field-error">{errors.content}</span>}
          </div>
          <button type="submit" className="btn btn-primary" disabled={saving}>
            {saving ? 'Saving...' : 'Save Article'}
          </button>
        </form>
      )}

      {loading ? (
        <div className="loading"><div className="spinner"></div><p>Loading articles...</p></div>
      ) : articles.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">📚</div>
          <h3>No articles yet</h3>
          <p>Add your first knowledge base article to get started.</p>
        </div>
      ) : (
        <div className="kb-grid">
          {articles.map(a => (
            <div key={a.id} className="kb-card">
              <div className="kb-card-header">
                <h3>{a.title}</h3>
                <button className="btn-delete" onClick={() => deleteArticle(a.id, a.title)} title="Delete">✕</button>
              </div>
              <span className="badge kb-category">{a.category}</span>
              <p className="kb-preview">{a.content.slice(0, 200)}{a.content.length > 200 ? '...' : ''}</p>
              {a.tags && <div className="kb-tags">{a.tags.split(',').map(t => <span key={t} className="tag">{t.trim()}</span>)}</div>}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
