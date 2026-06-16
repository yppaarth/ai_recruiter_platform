export interface User {
  id: string
  email: string
  username: string
  full_name?: string
  is_active: boolean
  created_at: string
}

export interface Campaign {
  id: string
  user_id: string
  name: string
  description?: string
  status: 'draft' | 'scheduled' | 'running' | 'completed' | 'paused'
  template_id?: string
  resume_path?: string
  sender_name?: string
  sender_email?: string
  emails_per_hour?: number
  emails_per_day?: number
  scheduled_at?: string
  started_at?: string
  completed_at?: string
  ai_summary?: string
  created_at: string
  updated_at: string
  stats?: CampaignStats
}

export interface CampaignStats {
  total_contacts: number
  pending: number
  sent: number
  opened: number
  clicked: number
  replied: number
  failed: number
  open_rate: number
  click_rate: number
  reply_rate: number
}

export interface Contact {
  id: string
  campaign_id: string
  name: string
  email: string
  company?: string
  title?: string
  extra_data: Record<string, string>
  status: string
  open_count: number
  click_count: number
  has_replied: boolean
  reply_at?: string
  created_at: string
}

export interface Email {
  id: string
  campaign_id: string
  contact_id: string
  subject: string
  body: string
  is_followup: boolean
  followup_number: number
  status: string
  sent_at?: string
  open_count: number
  click_count: number
  first_opened_at?: string
  created_at: string
}

export interface Template {
  id: string
  user_id: string
  name: string
  subject: string
  body: string
  is_ai_generated: boolean
  variables: string[]
  created_at: string
}

export interface DailyStats {
  date: string
  sent: number
  opened: number
  clicked: number
  replied: number
}

export interface OverallAnalytics {
  total_campaigns: number
  total_contacts: number
  total_sent: number
  total_opened: number
  total_clicked: number
  total_replied: number
  overall_open_rate: number
  overall_click_rate: number
  overall_reply_rate: number
  daily_stats: DailyStats[]
  top_companies: Array<{
    company: string
    total: number
    replied: number
    opened: number
    reply_rate: number
  }>
}

export interface Reply {
  id: string
  contact_id: string
  subject: string
  body_preview: string
  received_at: string
  detected_at: string
}

export interface AuditLog {
  id: string
  user_id: string
  action: string
  resource_type?: string
  resource_id?: string
  details: Record<string, unknown>
  timestamp: string
}
