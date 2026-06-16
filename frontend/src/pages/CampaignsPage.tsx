import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { campaignsApi } from '../services/api'
import { Campaign } from '../types'
import { Plus, Send, Play, Pause, Copy, Trash2, Eye } from 'lucide-react'

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    draft: 'bg-gray-100 text-gray-600',
    running: 'bg-green-100 text-green-700',
    paused: 'bg-yellow-100 text-yellow-700',
    completed: 'bg-blue-100 text-blue-700',
    scheduled: 'bg-purple-100 text-purple-700',
  }
  return <span className={`text-xs font-medium px-2.5 py-1 rounded-full ${colors[status] || 'bg-gray-100 text-gray-600'}`}>{status}</span>
}

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('')

  const load = () => {
    setLoading(true)
    const params = filter ? { status: filter } : {}
    campaignsApi.list(params).then(setCampaigns).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [filter])

  const handleAction = async (action: string, id: string) => {
    try {
      if (action === 'launch') await campaignsApi.launch(id)
      if (action === 'pause') await campaignsApi.pause(id)
      if (action === 'resume') await campaignsApi.resume(id)
      if (action === 'clone') await campaignsApi.clone(id)
      if (action === 'delete') { await campaignsApi.delete(id) }
      load()
    } catch (e: any) {
      alert(e?.response?.data?.detail || 'Action failed')
    }
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Campaigns</h1>
          <p className="text-gray-500 text-sm mt-1">{campaigns.length} campaigns total</p>
        </div>
        <Link to="/campaigns/new" className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors">
          <Plus className="w-4 h-4" /> New Campaign
        </Link>
      </div>

      {/* Filter */}
      <div className="flex gap-2 flex-wrap">
        {['', 'draft', 'running', 'paused', 'completed', 'scheduled'].map(s => (
          <button key={s} onClick={() => setFilter(s)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${filter === s ? 'bg-blue-600 text-white' : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50'}`}>
            {s || 'All'}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" /></div>
      ) : campaigns.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 py-16 text-center">
          <Send className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">No campaigns found.</p>
          <Link to="/campaigns/new" className="text-blue-600 text-sm font-medium hover:underline mt-2 block">Create your first campaign →</Link>
        </div>
      ) : (
        <div className="grid gap-4">
          {campaigns.map(c => (
            <div key={c.id} className="bg-white rounded-xl border border-gray-200 p-5">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 flex-wrap">
                    <h3 className="font-semibold text-gray-900">{c.name}</h3>
                    <StatusBadge status={c.status} />
                  </div>
                  {c.description && <p className="text-sm text-gray-500 mt-1 truncate">{c.description}</p>}
                  <div className="flex flex-wrap gap-4 mt-3 text-sm text-gray-600">
                    <span><b>{c.stats?.total_contacts ?? 0}</b> contacts</span>
                    <span><b>{c.stats?.sent ?? 0}</b> sent</span>
                    <span><b>{(c.stats?.open_rate ?? 0).toFixed(1)}%</b> open</span>
                    <span><b>{(c.stats?.click_rate ?? 0).toFixed(1)}%</b> click</span>
                    <span><b>{(c.stats?.reply_rate ?? 0).toFixed(1)}%</b> reply</span>
                  </div>
                </div>

                <div className="flex items-center gap-1.5 flex-shrink-0">
                  <Link to={`/campaigns/${c.id}`} className="p-2 text-gray-500 hover:bg-gray-100 rounded-lg transition-colors" title="View">
                    <Eye className="w-4 h-4" />
                  </Link>
                  {c.status === 'draft' && (
                    <button onClick={() => handleAction('launch', c.id)} className="p-2 text-green-600 hover:bg-green-50 rounded-lg transition-colors" title="Launch">
                      <Play className="w-4 h-4" />
                    </button>
                  )}
                  {c.status === 'running' && (
                    <button onClick={() => handleAction('pause', c.id)} className="p-2 text-yellow-600 hover:bg-yellow-50 rounded-lg transition-colors" title="Pause">
                      <Pause className="w-4 h-4" />
                    </button>
                  )}
                  {c.status === 'paused' && (
                    <button onClick={() => handleAction('resume', c.id)} className="p-2 text-green-600 hover:bg-green-50 rounded-lg transition-colors" title="Resume">
                      <Play className="w-4 h-4" />
                    </button>
                  )}
                  <button onClick={() => handleAction('clone', c.id)} className="p-2 text-blue-500 hover:bg-blue-50 rounded-lg transition-colors" title="Clone">
                    <Copy className="w-4 h-4" />
                  </button>
                  <button onClick={() => { if (confirm('Delete this campaign?')) handleAction('delete', c.id) }} className="p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors" title="Delete">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
