import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { analyticsApi, campaignsApi } from '../services/api'
import { OverallAnalytics, Campaign } from '../types'
import { Send, Eye, MousePointer, MessageSquare, Plus, TrendingUp, Users, Mail } from 'lucide-react'

function StatCard({ label, value, icon: Icon, color, sub }: {
  label: string; value: string | number; icon: any; color: string; sub?: string
}) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 flex items-start gap-4">
      <div className={`${color} rounded-lg p-2.5`}>
        <Icon className="w-5 h-5 text-white" />
      </div>
      <div>
        <p className="text-sm text-gray-500">{label}</p>
        <p className="text-2xl font-bold text-gray-900 mt-0.5">{value}</p>
        {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
      </div>
    </div>
  )
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    draft: 'bg-gray-100 text-gray-600',
    running: 'bg-green-100 text-green-700',
    paused: 'bg-yellow-100 text-yellow-700',
    completed: 'bg-blue-100 text-blue-700',
    scheduled: 'bg-purple-100 text-purple-700',
  }
  return (
    <span className={`text-xs font-medium px-2.5 py-1 rounded-full ${colors[status] || 'bg-gray-100 text-gray-600'}`}>
      {status}
    </span>
  )
}

export default function DashboardPage() {
  const [analytics, setAnalytics] = useState<OverallAnalytics | null>(null)
  const [campaigns, setCampaigns] = useState<Campaign[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      analyticsApi.overview(30),
      campaignsApi.list({ limit: 5 }),
    ]).then(([a, c]) => {
      setAnalytics(a)
      setCampaigns(c)
    }).finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
    </div>
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-500 text-sm mt-1">Overview of your outreach performance</p>
        </div>
        <Link to="/campaigns/new" className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors">
          <Plus className="w-4 h-4" />
          New Campaign
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Total Contacts" value={analytics?.total_contacts ?? 0} icon={Users} color="bg-blue-500" />
        <StatCard label="Emails Sent" value={analytics?.total_sent ?? 0} icon={Send} color="bg-indigo-500" />
        <StatCard
          label="Open Rate"
          value={`${(analytics?.overall_open_rate ?? 0).toFixed(1)}%`}
          icon={Eye}
          color="bg-emerald-500"
          sub={`${analytics?.total_opened ?? 0} opened`}
        />
        <StatCard
          label="Reply Rate"
          value={`${(analytics?.overall_reply_rate ?? 0).toFixed(1)}%`}
          icon={MessageSquare}
          color="bg-orange-500"
          sub={`${analytics?.total_replied ?? 0} replied`}
        />
      </div>

      {/* Recent campaigns */}
      <div className="bg-white rounded-xl border border-gray-200">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <h2 className="font-semibold text-gray-900">Recent Campaigns</h2>
          <Link to="/campaigns" className="text-sm text-blue-600 hover:underline">View all</Link>
        </div>
        <div className="divide-y divide-gray-50">
          {campaigns.length === 0 ? (
            <div className="px-6 py-10 text-center">
              <Mail className="w-10 h-10 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500 text-sm">No campaigns yet.</p>
              <Link to="/campaigns/new" className="text-blue-600 text-sm font-medium hover:underline mt-1 block">
                Create your first campaign →
              </Link>
            </div>
          ) : campaigns.map(c => (
            <Link key={c.id} to={`/campaigns/${c.id}`} className="flex items-center justify-between px-6 py-4 hover:bg-gray-50 transition-colors">
              <div>
                <p className="font-medium text-gray-900 text-sm">{c.name}</p>
                <p className="text-xs text-gray-400 mt-0.5">{c.stats?.total_contacts ?? 0} contacts</p>
              </div>
              <div className="flex items-center gap-4">
                <div className="text-right hidden sm:block">
                  <p className="text-sm font-medium text-gray-700">{(c.stats?.open_rate ?? 0).toFixed(1)}% open</p>
                  <p className="text-xs text-gray-400">{(c.stats?.reply_rate ?? 0).toFixed(1)}% reply</p>
                </div>
                <StatusBadge status={c.status} />
              </div>
            </Link>
          ))}
        </div>
      </div>

      {/* Top companies */}
      {analytics && analytics.top_companies.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-100">
            <h2 className="font-semibold text-gray-900 flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-blue-500" />
              Top Performing Companies
            </h2>
          </div>
          <div className="px-6 py-4 space-y-3">
            {analytics.top_companies.slice(0, 5).map((c) => (
              <div key={c.company} className="flex items-center gap-3">
                <span className="text-sm text-gray-700 w-32 truncate font-medium">{c.company}</span>
                <div className="flex-1 bg-gray-100 rounded-full h-2">
                  <div
                    className="bg-blue-500 h-2 rounded-full"
                    style={{ width: `${Math.min(c.reply_rate, 100)}%` }}
                  />
                </div>
                <span className="text-sm text-gray-500 w-16 text-right">{c.reply_rate.toFixed(1)}%</span>
                <span className="text-xs text-gray-400 w-16 text-right">{c.total} contacts</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
