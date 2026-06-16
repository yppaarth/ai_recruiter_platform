import { useEffect, useState } from 'react'
import { analyticsApi } from '../services/api'
import { OverallAnalytics } from '../types'
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend, BarChart, Bar
} from 'recharts'
import { TrendingUp, Send, Eye, MessageSquare, MousePointer } from 'lucide-react'

function StatCard({ label, value, icon: Icon, color }: { label: string; value: string; icon: any; color: string }) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5">
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm text-gray-500">{label}</span>
        <div className={`${color} rounded-lg p-2`}><Icon className="w-4 h-4 text-white" /></div>
      </div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
    </div>
  )
}

export default function AnalyticsPage() {
  const [data, setData] = useState<OverallAnalytics | null>(null)
  const [days, setDays] = useState(30)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    analyticsApi.overview(days).then(setData).finally(() => setLoading(false))
  }, [days])

  if (loading) return <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" /></div>
  if (!data) return null

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
          <p className="text-gray-500 text-sm mt-1">Campaign performance overview</p>
        </div>
        <select value={days} onChange={e => setDays(Number(e.target.value))} className="border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500">
          <option value={7}>Last 7 days</option>
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
        </select>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Total Sent" value={String(data.total_sent)} icon={Send} color="bg-blue-500" />
        <StatCard label="Open Rate" value={`${data.overall_open_rate.toFixed(1)}%`} icon={Eye} color="bg-emerald-500" />
        <StatCard label="Click Rate" value={`${data.overall_click_rate.toFixed(1)}%`} icon={MousePointer} color="bg-purple-500" />
        <StatCard label="Reply Rate" value={`${data.overall_reply_rate.toFixed(1)}%`} icon={MessageSquare} color="bg-orange-500" />
      </div>

      {/* Line Chart */}
      <div className="bg-white border border-gray-200 rounded-xl p-6">
        <h2 className="font-semibold text-gray-900 mb-4">Daily Activity</h2>
        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={data.daily_stats} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="date" tick={{ fontSize: 11 }} tickFormatter={d => d.slice(5)} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip labelFormatter={l => `Date: ${l}`} />
            <Legend />
            <Line type="monotone" dataKey="sent" stroke="#3b82f6" strokeWidth={2} dot={false} name="Sent" />
            <Line type="monotone" dataKey="opened" stroke="#10b981" strokeWidth={2} dot={false} name="Opened" />
            <Line type="monotone" dataKey="clicked" stroke="#8b5cf6" strokeWidth={2} dot={false} name="Clicked" />
            <Line type="monotone" dataKey="replied" stroke="#f59e0b" strokeWidth={2} dot={false} name="Replied" />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Top companies bar chart + table side by side */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white border border-gray-200 rounded-xl p-6">
          <h2 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-blue-500" />
            Top Companies by Reply Rate
          </h2>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={data.top_companies.slice(0, 8)} layout="vertical" margin={{ left: 10 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 11 }} unit="%" />
              <YAxis type="category" dataKey="company" tick={{ fontSize: 11 }} width={80} />
              <Tooltip formatter={(v: number) => `${v.toFixed(1)}%`} />
              <Bar dataKey="reply_rate" fill="#3b82f6" radius={[0, 4, 4, 0]} name="Reply Rate %" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white border border-gray-200 rounded-xl p-6">
          <h2 className="font-semibold text-gray-900 mb-4">Company Breakdown</h2>
          <div className="overflow-auto max-h-64">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100">
                  <th className="text-left pb-2 font-medium text-gray-500">Company</th>
                  <th className="text-right pb-2 font-medium text-gray-500">Contacts</th>
                  <th className="text-right pb-2 font-medium text-gray-500">Reply %</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {data.top_companies.map(c => (
                  <tr key={c.company}>
                    <td className="py-2 font-medium text-gray-800">{c.company}</td>
                    <td className="py-2 text-right text-gray-500">{c.total}</td>
                    <td className="py-2 text-right">
                      <span className={`font-medium ${c.reply_rate > 10 ? 'text-green-600' : c.reply_rate > 5 ? 'text-yellow-600' : 'text-gray-500'}`}>
                        {c.reply_rate.toFixed(1)}%
                      </span>
                    </td>
                  </tr>
                ))}
                {data.top_companies.length === 0 && (
                  <tr><td colSpan={3} className="py-8 text-center text-gray-400">No data yet</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}
