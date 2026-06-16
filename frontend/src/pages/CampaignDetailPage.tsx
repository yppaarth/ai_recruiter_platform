import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { campaignsApi, contactsApi, analyticsApi, repliesApi, exportApi } from '../services/api'
import { Campaign, Contact, Reply } from '../types'
import { ArrowLeft, Play, Pause, Download, Search, ChevronDown, Mail } from 'lucide-react'

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    draft: 'bg-gray-100 text-gray-600',
    running: 'bg-green-100 text-green-700',
    paused: 'bg-yellow-100 text-yellow-700',
    completed: 'bg-blue-100 text-blue-700',
    scheduled: 'bg-purple-100 text-purple-700',
    pending: 'bg-gray-100 text-gray-500',
    sent: 'bg-blue-100 text-blue-600',
    opened: 'bg-green-100 text-green-600',
    clicked: 'bg-purple-100 text-purple-600',
    replied: 'bg-orange-100 text-orange-600',
    failed: 'bg-red-100 text-red-600',
  }
  return <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${colors[status] || 'bg-gray-100 text-gray-600'}`}>{status}</span>
}

function Metric({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4 text-center">
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-sm text-gray-500 mt-0.5">{label}</p>
      {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
    </div>
  )
}

export default function CampaignDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [campaign, setCampaign] = useState<Campaign | null>(null)
  const [contacts, setContacts] = useState<Contact[]>([])
  const [replies, setReplies] = useState<Reply[]>([])
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState<'contacts' | 'replies'>('contacts')
  const [search, setSearch] = useState('')
  const [actionLoading, setActionLoading] = useState(false)
  const [template, setTemplate] = useState({ subject: '', body: '' })
  const [showComposer, setShowComposer] = useState(false)

  const load = async () => {
    if (!id) return
    setLoading(true)
    try {
      const [c, ct, r] = await Promise.all([
        campaignsApi.get(id),
        contactsApi.list(id, { limit: 100 }),
        repliesApi.list(id),
      ])
      setCampaign(c)
      setContacts(ct)
      setReplies(r)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [id])

  const handleAction = async (action: string) => {
    if (!id) return
    setActionLoading(true)
    try {
      if (action === 'launch') await campaignsApi.launch(id)
      if (action === 'pause') await campaignsApi.pause(id)
      if (action === 'resume') await campaignsApi.resume(id)
      await load()
    } catch (e: any) {
      alert(e?.response?.data?.detail || 'Action failed')
    } finally {
      setActionLoading(false)
    }
  }

  const handleGenerateEmails = async () => {
    if (!id || !template.subject.trim() || !template.body.trim()) return
    setActionLoading(true)
    try {
      await campaignsApi.generateEmails(id, template)
      await load()
      setShowComposer(false)
    } catch (e: any) {
      alert(e?.response?.data?.detail || 'Email generation failed')
    } finally {
      setActionLoading(false)
    }
  }

  if (loading) return (
    <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" /></div>
  )
  if (!campaign) return <div>Campaign not found</div>

  const filteredContacts = contacts.filter(c =>
    !search || c.name.toLowerCase().includes(search.toLowerCase()) ||
    c.email.toLowerCase().includes(search.toLowerCase()) ||
    (c.company || '').toLowerCase().includes(search.toLowerCase())
  )

  const stats = campaign.stats

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-3">
          <Link to="/campaigns" className="p-2 text-gray-500 hover:bg-gray-100 rounded-lg"><ArrowLeft className="w-5 h-5" /></Link>
          <div>
            <div className="flex items-center gap-2"><h1 className="text-xl font-bold text-gray-900">{campaign.name}</h1><StatusBadge status={campaign.status} /></div>
            {campaign.description && <p className="text-sm text-gray-500 mt-0.5">{campaign.description}</p>}
          </div>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          {campaign.status === 'draft' && (
            <button onClick={() => setShowComposer(s => !s)} disabled={actionLoading} className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-60">
              <Mail className="w-4 h-4" /> Generate Emails
            </button>
          )}
          {campaign.status === 'draft' && (
            <button onClick={() => handleAction('launch')} disabled={actionLoading} className="flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-green-700 disabled:opacity-60">
              <Play className="w-4 h-4" /> Launch
            </button>
          )}
          {campaign.status === 'running' && (
            <button onClick={() => handleAction('pause')} disabled={actionLoading} className="flex items-center gap-2 bg-yellow-500 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-yellow-600 disabled:opacity-60">
              <Pause className="w-4 h-4" /> Pause
            </button>
          )}
          {campaign.status === 'paused' && (
            <button onClick={() => handleAction('resume')} disabled={actionLoading} className="flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-green-700 disabled:opacity-60">
              <Play className="w-4 h-4" /> Resume
            </button>
          )}
          <div className="relative group">
            <button className="flex items-center gap-2 bg-white border border-gray-200 text-gray-700 px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-50">
              <Download className="w-4 h-4" /> Export <ChevronDown className="w-3 h-3" />
            </button>
            <div className="absolute right-0 top-full mt-1 w-32 bg-white border border-gray-200 rounded-lg shadow-lg opacity-0 group-hover:opacity-100 transition-opacity z-10">
              <a href={exportApi.csv(id!)} target="_blank" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50">CSV</a>
              <a href={exportApi.excel(id!)} target="_blank" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50">Excel</a>
              <a href={exportApi.pdf(id!)} target="_blank" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50">PDF Report</a>
            </div>
          </div>
        </div>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          <Metric label="Total" value={String(stats.total_contacts)} />
          <Metric label="Sent" value={String(stats.sent)} />
          <Metric label="Opened" value={`${stats.open_rate.toFixed(1)}%`} sub={`${stats.opened} emails`} />
          <Metric label="Clicked" value={`${stats.click_rate.toFixed(1)}%`} sub={`${stats.clicked} emails`} />
          <Metric label="Replied" value={`${stats.reply_rate.toFixed(1)}%`} sub={`${stats.replied} contacts`} />
          <Metric label="Failed" value={String(stats.failed)} />
        </div>
      )}

      {showComposer && (
        <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Email Subject</label>
            <input
              value={template.subject}
              onChange={e => setTemplate(t => ({ ...t, subject: e.target.value }))}
              placeholder="Opportunity at {{company}}"
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Email Body</label>
            <textarea
              value={template.body}
              onChange={e => setTemplate(t => ({ ...t, body: e.target.value }))}
              rows={10}
              placeholder={'Hi {{name}},\n\nI wanted to reach out regarding opportunities at {{company}}.\n\nBest,\nYour Name'}
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            />
            <p className="text-xs text-gray-400 mt-1">Use {'{{name}}'}, {'{{company}}'}, {'{{title}}'}, {'{{email}}'}, and any custom Excel column name.</p>
          </div>
          <div className="flex items-center gap-3">
            <button onClick={handleGenerateEmails} disabled={actionLoading || !template.subject.trim() || !template.body.trim()} className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-60">
              {actionLoading ? 'Generating...' : 'Create Drafts'}
            </button>
            <button onClick={() => setShowComposer(false)} disabled={actionLoading} className="bg-white border border-gray-200 text-gray-700 px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-50 disabled:opacity-60">
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="bg-white rounded-xl border border-gray-200">
        <div className="flex border-b border-gray-100 px-4 gap-1">
          {(['contacts', 'replies'] as const).map(t => (
            <button key={t} onClick={() => setTab(t)} className={`px-4 py-3 text-sm font-medium capitalize border-b-2 transition-colors ${tab === t ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}>
              {t} {t === 'contacts' ? `(${contacts.length})` : `(${replies.length})`}
            </button>
          ))}
        </div>

        {tab === 'contacts' && (
          <div>
            <div className="px-4 py-3 border-b border-gray-50">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search contacts..." className="w-full pl-9 pr-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left font-medium text-gray-500">Name</th>
                    <th className="px-4 py-3 text-left font-medium text-gray-500">Company</th>
                    <th className="px-4 py-3 text-left font-medium text-gray-500">Title</th>
                    <th className="px-4 py-3 text-left font-medium text-gray-500">Status</th>
                    <th className="px-4 py-3 text-center font-medium text-gray-500">Opens</th>
                    <th className="px-4 py-3 text-center font-medium text-gray-500">Clicks</th>
                    <th className="px-4 py-3 text-center font-medium text-gray-500">Replied</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {filteredContacts.map(c => (
                    <tr key={c.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3">
                        <p className="font-medium text-gray-900">{c.name}</p>
                        <p className="text-gray-400 text-xs">{c.email}</p>
                      </td>
                      <td className="px-4 py-3 text-gray-600">{c.company || '-'}</td>
                      <td className="px-4 py-3 text-gray-600">{c.title || '-'}</td>
                      <td className="px-4 py-3"><StatusBadge status={c.status} /></td>
                      <td className="px-4 py-3 text-center text-gray-700">{c.open_count}</td>
                      <td className="px-4 py-3 text-center text-gray-700">{c.click_count}</td>
                      <td className="px-4 py-3 text-center">
                        {c.has_replied ? <span className="text-green-600 font-medium">✓</span> : <span className="text-gray-300">—</span>}
                      </td>
                    </tr>
                  ))}
                  {filteredContacts.length === 0 && (
                    <tr><td colSpan={7} className="px-4 py-10 text-center text-gray-400">No contacts found</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {tab === 'replies' && (
          <div className="divide-y divide-gray-50">
            {replies.length === 0 ? (
              <div className="py-12 text-center text-gray-400">No replies detected yet</div>
            ) : replies.map(r => (
              <div key={r.id} className="px-6 py-4">
                <p className="font-medium text-gray-900 text-sm">{r.subject}</p>
                <p className="text-gray-500 text-sm mt-1 line-clamp-2">{r.body_preview}</p>
                <p className="text-xs text-gray-400 mt-2">{r.received_at ? new Date(r.received_at).toLocaleString() : ''}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
