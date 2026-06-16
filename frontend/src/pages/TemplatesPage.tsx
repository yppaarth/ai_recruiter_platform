import { useEffect, useState } from 'react'
import { templatesApi } from '../services/api'
import { Template } from '../types'
import { Plus, Trash2, Edit2, FileText, X, Check } from 'lucide-react'

export default function TemplatesPage() {
  const [templates, setTemplates] = useState<Template[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState<Template | null>(null)
  const [form, setForm] = useState({ name: '', subject: '', body: '' })
  const [saving, setSaving] = useState(false)

  const load = () => {
    templatesApi.list().then(setTemplates).finally(() => setLoading(false))
  }
  useEffect(() => { load() }, [])

  const openNew = () => { setEditing(null); setForm({ name: '', subject: '', body: '' }); setShowForm(true) }
  const openEdit = (t: Template) => { setEditing(t); setForm({ name: t.name, subject: t.subject, body: t.body }); setShowForm(true) }

  const handleSave = async () => {
    if (!form.name || !form.subject || !form.body) return
    setSaving(true)
    try {
      if (editing) await templatesApi.update(editing.id, form)
      else await templatesApi.create(form)
      setShowForm(false)
      load()
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this template?')) return
    await templatesApi.delete(id)
    load()
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Email Templates</h1>
          <p className="text-gray-500 text-sm mt-1">Reusable templates with Jinja2 variable support</p>
        </div>
        <button onClick={openNew} className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors">
          <Plus className="w-4 h-4" /> New Template
        </button>
      </div>

      {/* Template form modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
              <h2 className="font-semibold text-gray-900">{editing ? 'Edit Template' : 'New Template'}</h2>
              <button onClick={() => setShowForm(false)} className="p-1 text-gray-400 hover:text-gray-600"><X className="w-5 h-5" /></button>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Template Name</label>
                <input value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} placeholder="e.g. FAANG Outreach" className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Subject Line</label>
                <input value={form.subject} onChange={e => setForm(f => ({ ...f, subject: e.target.value }))} placeholder="e.g. ML Engineer opportunity at {{company}}" className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Body</label>
                <textarea value={form.body} onChange={e => setForm(f => ({ ...f, body: e.target.value }))} rows={10} placeholder="Hi {{name}},&#10;&#10;I came across {{company}} and was impressed by...&#10;&#10;Supported variables: {{name}}, {{company}}, {{title}}, and any custom columns" className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none font-mono" />
              </div>
              <div className="bg-blue-50 rounded-lg px-4 py-3 text-xs text-blue-700">
                <b>Supported variables:</b> {'{{name}}'}, {'{{company}}'}, {'{{title}}'}, {'{{email}}'}, and any custom columns from your uploaded CSV/XLSX.
              </div>
              <div className="flex justify-end gap-2">
                <button onClick={() => setShowForm(false)} className="px-4 py-2 border border-gray-200 rounded-lg text-sm text-gray-600 hover:bg-gray-50">Cancel</button>
                <button onClick={handleSave} disabled={saving || !form.name || !form.subject || !form.body} className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-60">
                  <Check className="w-4 h-4" />{saving ? 'Saving...' : 'Save Template'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {loading ? (
        <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" /></div>
      ) : templates.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 py-16 text-center">
          <FileText className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500 mb-2">No templates yet.</p>
          <button onClick={openNew} className="text-blue-600 text-sm font-medium hover:underline">Create your first template →</button>
        </div>
      ) : (
        <div className="grid gap-4">
          {templates.map(t => (
            <div key={t.id} className="bg-white rounded-xl border border-gray-200 p-5">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <h3 className="font-semibold text-gray-900">{t.name}</h3>
                    {t.is_ai_generated && <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full">AI Generated</span>}
                  </div>
                  <p className="text-sm text-gray-500 mt-1"><b>Subject:</b> {t.subject}</p>
                  <p className="text-sm text-gray-400 mt-1.5 line-clamp-2">{t.body}</p>
                  {t.variables.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mt-2">
                      {t.variables.map(v => (
                        <span key={v} className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded font-mono">{`{{${v}}}`}</span>
                      ))}
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-1.5 flex-shrink-0">
                  <button onClick={() => openEdit(t)} className="p-2 text-blue-500 hover:bg-blue-50 rounded-lg transition-colors"><Edit2 className="w-4 h-4" /></button>
                  <button onClick={() => handleDelete(t.id)} className="p-2 text-red-400 hover:bg-red-50 rounded-lg transition-colors"><Trash2 className="w-4 h-4" /></button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
