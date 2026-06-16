import { useState, FormEvent } from 'react'
import { authApi } from '../services/api'
import { useAuth } from '../hooks/useAuth'
import { Save, Mail, Server, AlertCircle, CheckCircle } from 'lucide-react'

export default function SettingsPage() {
  const { user } = useAuth()
  const [form, setForm] = useState({
    smtp_host: 'smtp.gmail.com',
    smtp_port: '587',
    smtp_username: '',
    smtp_password: '',
    smtp_from_name: user?.full_name || '',
    smtp_use_tls: true,
    imap_host: 'imap.gmail.com',
    imap_port: '993',
    imap_username: '',
    imap_password: '',
  })
  const [status, setStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle')
  const [error, setError] = useState('')

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setStatus('saving')
    setError('')
    try {
      await authApi.updateSMTP({
        ...form,
        smtp_port: parseInt(form.smtp_port),
        imap_port: parseInt(form.imap_port),
      })
      setStatus('saved')
      setTimeout(() => setStatus('idle'), 3000)
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to save settings')
      setStatus('error')
    }
  }

  const f = (key: keyof typeof form) => ({
    value: form[key] as string,
    onChange: (e: React.ChangeEvent<HTMLInputElement>) =>
      setForm(prev => ({ ...prev, [key]: e.target.value })),
  })

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-500 text-sm mt-1">Configure your email sending and receiving settings</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* SMTP */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
          <div className="flex items-center gap-2 mb-2">
            <Mail className="w-5 h-5 text-blue-500" />
            <h2 className="font-semibold text-gray-900">SMTP Settings (Outgoing Email)</h2>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">SMTP Host</label>
              <input {...f('smtp_host')} className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="smtp.gmail.com" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">SMTP Port</label>
              <input {...f('smtp_port')} type="number" className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="587" />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">From Name</label>
            <input {...f('smtp_from_name')} className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Your Name" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Email / Username</label>
            <input {...f('smtp_username')} type="email" className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="you@gmail.com" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">App Password</label>
            <input {...f('smtp_password')} type="password" className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Gmail App Password (not your account password)" />
            <p className="text-xs text-gray-400 mt-1">For Gmail: enable 2FA → generate App Password at myaccount.google.com/security</p>
          </div>
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="use_tls"
              checked={form.smtp_use_tls}
              onChange={e => setForm(f => ({ ...f, smtp_use_tls: e.target.checked }))}
              className="rounded border-gray-300"
            />
            <label htmlFor="use_tls" className="text-sm text-gray-700">Use TLS (recommended)</label>
          </div>
        </div>

        {/* IMAP */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
          <div className="flex items-center gap-2 mb-2">
            <Server className="w-5 h-5 text-purple-500" />
            <h2 className="font-semibold text-gray-900">IMAP Settings (Reply Detection)</h2>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">IMAP Host</label>
              <input {...f('imap_host')} className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="imap.gmail.com" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">IMAP Port</label>
              <input {...f('imap_port')} type="number" className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="993" />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">IMAP Username</label>
            <input {...f('imap_username')} type="email" className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="you@gmail.com" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">IMAP Password</label>
            <input {...f('imap_password')} type="password" className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="App Password" />
          </div>
        </div>

        {error && (
          <div className="flex items-center gap-2 text-red-700 bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-sm">
            <AlertCircle className="w-4 h-4" />{error}
          </div>
        )}
        {status === 'saved' && (
          <div className="flex items-center gap-2 text-green-700 bg-green-50 border border-green-200 rounded-lg px-4 py-3 text-sm">
            <CheckCircle className="w-4 h-4" />Settings saved successfully!
          </div>
        )}

        <button
          type="submit"
          disabled={status === 'saving'}
          className="flex items-center gap-2 bg-blue-600 text-white px-6 py-2.5 rounded-lg font-medium text-sm hover:bg-blue-700 disabled:opacity-60 transition-colors"
        >
          <Save className="w-4 h-4" />
          {status === 'saving' ? 'Saving...' : 'Save Settings'}
        </button>
      </form>

      {/* Info box */}
      <div className="bg-amber-50 border border-amber-200 rounded-xl p-5 text-sm text-amber-800">
        <b>Gmail Setup:</b> Go to Google Account → Security → 2-Step Verification → App passwords → Generate one for "Mail". Use that as your password here. Enable IMAP in Gmail Settings → Forwarding and POP/IMAP.
      </div>
    </div>
  )
}
