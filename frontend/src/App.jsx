import { useState, useEffect } from 'react'
import Dashboard from './pages/Dashboard'
import TicketDetail from './pages/TicketDetail'
import CreateTicket from './pages/CreateTicket'
import KnowledgeBase from './pages/KnowledgeBase'
import ActivityLogs from './pages/ActivityLogs'
import Toast from './components/Toast'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function App() {
  const [page, setPage] = useState('dashboard')
  const [selectedTicketId, setSelectedTicketId] = useState(null)
  const [tickets, setTickets] = useState([])
  const [refreshKey, setRefreshKey] = useState(0)
  const [toast, setToast] = useState(null)

  useEffect(() => {
    fetch(`${API}/api/tickets`)
      .then(r => r.json())
      .then(setTickets)
      .catch(() => {})
  }, [refreshKey])

  const showToast = (message, type = 'success') => {
    setToast({ message, type })
    setTimeout(() => setToast(null), 3000)
  }

  const navigateToTicket = (id) => {
    setSelectedTicketId(id)
    setPage('ticket')
  }

  const renderPage = () => {
    switch (page) {
      case 'dashboard':
        return <Dashboard tickets={tickets} onSelectTicket={navigateToTicket} onRefresh={() => setRefreshKey(k => k + 1)} API={API} />
      case 'ticket':
        return <TicketDetail ticketId={selectedTicketId} onBack={() => setPage('dashboard')} onRefresh={() => setRefreshKey(k => k + 1)} API={API} showToast={showToast} />
      case 'create':
        return <CreateTicket onCreated={(t) => { setPage('dashboard'); setRefreshKey(k => k + 1); showToast('Ticket created successfully') }} onCancel={() => setPage('dashboard')} API={API} />
      case 'kb':
        return <KnowledgeBase API={API} showToast={showToast} />
      case 'logs':
        return <ActivityLogs API={API} />
      default:
        return <Dashboard tickets={tickets} onSelectTicket={navigateToTicket} onRefresh={() => setRefreshKey(k => k + 1)} API={API} />
    }
  }

  return (
    <div className="app">
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
      <nav className="nav">
        <div className="nav-brand" onClick={() => setPage('dashboard')}>
          <strong>Support Assistant</strong>
        </div>
        <div className="nav-links">
          <button className={`nav-link ${page === 'dashboard' ? 'active' : ''}`} onClick={() => setPage('dashboard')}>Dashboard</button>
          <button className={`nav-link ${page === 'create' ? 'active' : ''}`} onClick={() => setPage('create')}>New Ticket</button>
          <button className={`nav-link ${page === 'kb' ? 'active' : ''}`} onClick={() => setPage('kb')}>Knowledge Base</button>
          <button className={`nav-link ${page === 'logs' ? 'active' : ''}`} onClick={() => setPage('logs')}>Activity Logs</button>
        </div>
      </nav>
      <main className="main">
        {renderPage()}
      </main>
    </div>
  )
}

export default App
