import { useState, FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { campaignsApi, uploadApi } from '../services/api'
import { ArrowLeft, Upload, FileText } from 'lucide-react'

export default function NewCampaignPage() {
  const navigate = useNavigate()
  const [step, setStep] = useState(1)
  const [campaignId, setCampaignId] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [contactsFile, setContactsFile] = useState<File | null>(null)
  const [resumeFile, setResumeFile] = useState<File | null>(null)
  const [uploadResult, setUploadResult] = useState<any>(null)
  const [candidateProfile, setCandidateProfile] = useState('')
  const [form, setForm] = useState({
    name: '',
    description: '',
    sender_name: '',
    sender_email: '',
    emails_per_hour: '',
    emails_per_day: '',
  })

  const handleCreateCampaign = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const data = await campaignsApi.create({
        ...form,
        emails_per_hour: form.emails_per_hour ? parseInt(form.emails_per_hour) : undefined,
        emails_per_day: form.emails_per_day ? parseInt(form.emails_per_day) : undefined,
      })
      setCampaignId(data.id)
      setStep(2)
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to create campaign')
    } finally {
      setLoading(false)
    }
  }

  const handleUpload = async () => {
    if (!campaignId || !contactsFile) return
    setLoading(true)
    setError('')
    try {
      const result = await uploadApi.contacts(campaignId, contactsFile)
      setUploadResult(result)
      if (resumeFile) await uploadApi.resume(campaignId, resumeFile)
      setStep(3)
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Upload failed')
    } finally {
      setLoading(false)
    }
  }

  const handleGenerateAndLaunch = async () => {
    if (!campaignId || !candidateProfile.trim()) return
    setLoading(true)
    setError('')
    try {
      await campaignsApi.generateEmails(campaignId, candidateProfile)
      navigate(`/campaigns/${campaignId}`)
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to generate emails')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <button onClick={() => navigate('/campaigns')} className="p-2 text-gray-500 hover:bg-gray-100 rounded-lg transition-colors">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <h1 className="text-2xl font-bold text-gray-900">New Campaign</h1>
      </div>

      {/* Steps */}
      <div className="flex items-center gap-2 mb-8">
        {['Campaign Details', 'Upload Contacts', 'Generate Emails'].map((s, i) => (
          <div key={s} className="flex items-center gap-2">
            <div className={`flex items-center gap-2 ${i + 1 <= step ? 'text-blue-600' : 'text-gray-400'}`}>
              <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold border-2 ${i + 1 < step ? 'bg-blue-600 border-blue-600 text-white' : i + 1 === step ? 'border-blue-600 text-blue-600' : 'border-gray-300 text-gray-400'}`}>
                {i + 1 < step ? '✓' : i + 1}
              </div>
              <span className="text-sm font-medium hidden sm:block">{s}</span>
            </div>
            {i < 2 && <div className={`flex-1 h-px w-8 ${i + 1 < step ? 'bg-blue-600' : 'bg-gray-200'}`} />}
          </div>
        ))}
      </div>

      {error && (
        <div className="bg-red-50 text-red-700 text-sm px-4 py-3 rounded-lg mb-5 border border-red-200">{error}</div>
      )}

      {/* Step 1 */}
      {step === 1 && (
        <form onSubmit={handleCreateCampaign} className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Campaign Name *</label>
            <input value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} required placeholder="e.g. Google Outreach Q3 2025" className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Candidate Profile (used for AI generation)</label>
            <textarea value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} rows={3} placeholder="e.g. AI/ML Engineer with 3 years of experience in NLP, LLMs, and building RAG pipelines at Samsung R&D..." className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Sender Name</label>
              <input value={form.sender_name} onChange={e => setForm(f => ({ ...f, sender_name: e.target.value }))} placeholder="Your Name" className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Sender Email</label>
              <input type="email" value={form.sender_email} onChange={e => setForm(f => ({ ...f, sender_email: e.target.value }))} placeholder="you@gmail.com" className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Emails/hour limit</label>
              <input type="number" value={form.emails_per_hour} onChange={e => setForm(f => ({ ...f, emails_per_hour: e.target.value }))} placeholder="50" min="1" max="200" className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Emails/day limit</label>
              <input type="number" value={form.emails_per_day} onChange={e => setForm(f => ({ ...f, emails_per_day: e.target.value }))} placeholder="200" min="1" max="1000" className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
          </div>
          <button type="submit" disabled={loading} className="w-full bg-blue-600 text-white py-2.5 rounded-lg font-medium text-sm hover:bg-blue-700 disabled:opacity-60 transition-colors">
            {loading ? 'Creating...' : 'Create Campaign →'}
          </button>
        </form>
      )}

      {/* Step 2 */}
      {step === 2 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-5">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Contacts File * (CSV or XLSX)</label>
            <div className="border-2 border-dashed border-gray-200 rounded-lg p-6 text-center hover:border-blue-400 transition-colors cursor-pointer" onClick={() => document.getElementById('contacts-file')?.click()}>
              <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
              <p className="text-sm text-gray-500">{contactsFile ? contactsFile.name : 'Click to upload CSV or XLSX'}</p>
              <p className="text-xs text-gray-400 mt-1">Required columns: name, email. Optional: company, title</p>
              <input id="contacts-file" type="file" accept=".csv,.xlsx,.xls" className="hidden" onChange={e => setContactsFile(e.target.files?.[0] || null)} />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Resume PDF (optional)</label>
            <div className="border-2 border-dashed border-gray-200 rounded-lg p-4 text-center hover:border-blue-400 transition-colors cursor-pointer" onClick={() => document.getElementById('resume-file')?.click()}>
              <FileText className="w-6 h-6 text-gray-400 mx-auto mb-1" />
              <p className="text-sm text-gray-500">{resumeFile ? resumeFile.name : 'Click to upload PDF resume'}</p>
              <input id="resume-file" type="file" accept=".pdf" className="hidden" onChange={e => setResumeFile(e.target.files?.[0] || null)} />
            </div>
          </div>
          <button onClick={handleUpload} disabled={!contactsFile || loading} className="w-full bg-blue-600 text-white py-2.5 rounded-lg font-medium text-sm hover:bg-blue-700 disabled:opacity-60 transition-colors">
            {loading ? 'Uploading...' : 'Upload & Continue →'}
          </button>
        </div>
      )}

      {/* Step 3 */}
      {step === 3 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-5">
          {uploadResult && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-sm text-green-800">
              ✓ Imported <b>{uploadResult.contacts_imported}</b> contacts
              {uploadResult.custom_columns.length > 0 && ` · Custom columns: ${uploadResult.custom_columns.join(', ')}`}
              {uploadResult.contacts_skipped > 0 && ` · ${uploadResult.contacts_skipped} duplicates skipped`}
            </div>
          )}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Your Candidate Profile *</label>
            <textarea
              value={candidateProfile}
              onChange={e => setCandidateProfile(e.target.value)}
              rows={5}
              placeholder="Describe yourself for AI email personalization. e.g.: AI/ML Engineer with 3+ years of experience. Ranked 4th globally at ICASSP 2025 Face-Voice Matching challenge. Built RAG pipelines at Samsung R&D with FAISS + BM25 hybrid retrieval. Published in Springer (Scopus indexed). M.Tech Data Science at DTU. Looking for GenAI/LLM Engineer roles."
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            />
            <p className="text-xs text-gray-400 mt-1">This is used by Grok AI to write personalized emails for each recruiter.</p>
          </div>
          <button onClick={handleGenerateAndLaunch} disabled={!candidateProfile.trim() || loading} className="w-full bg-blue-600 text-white py-2.5 rounded-lg font-medium text-sm hover:bg-blue-700 disabled:opacity-60 transition-colors">
            {loading ? 'Generating emails with AI...' : '✨ Generate Personalized Emails →'}
          </button>
        </div>
      )}
    </div>
  )
}
