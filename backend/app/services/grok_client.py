import httpx
import json
from typing import Dict, Any, Optional
from loguru import logger
from app.core.config import settings


class GrokClient:
    """Client for interacting with the Grok (xAI) API."""

    def __init__(self) -> None:
        self.api_key = settings.GROK_API_KEY
        self.model = settings.GROK_MODEL
        self.base_url = settings.GROK_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def _chat_completion(
        self,
        messages: list[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def generate_outreach_email(
        self,
        recruiter_name: str,
        company: str,
        title: str,
        candidate_profile: str,
        extra_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, str]:
        """Generate a personalized recruiter outreach email."""
        context_str = ""
        if extra_context:
            context_str = "\nAdditional context:\n" + "\n".join(
                f"- {k}: {v}" for k, v in extra_context.items() if v
            )

        system_prompt = (
            "You are an expert career coach specializing in writing highly effective, "
            "personalized recruiter outreach emails. Your emails are concise, professional, "
            "genuine, and non-spammy. You always respond ONLY with valid JSON."
        )

        user_prompt = f"""Generate a concise, professional recruiter outreach email.

Recruiter Details:
- Name: {recruiter_name}
- Company: {company}
- Title: {title}

Candidate Profile:
{candidate_profile}
{context_str}

Requirements:
- Personalize the email specifically to {company} and {recruiter_name}
- Make it concise (150-250 words for body)
- Sound genuine, not templated or spammy
- Include a specific reason why the candidate is interested in {company}
- Have a clear, polite call to action
- Professional but warm tone

Respond ONLY with a JSON object with exactly these two keys:
{{
  "subject": "email subject line here",
  "body": "full email body here with proper line breaks using \\n"
}}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            raw = await self._chat_completion(messages, temperature=0.8, max_tokens=600)
            # Strip markdown fences if present
            raw = raw.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            raw = raw.strip().rstrip("```").strip()
            result = json.loads(raw)
            return {"subject": result["subject"], "body": result["body"]}
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse Grok response: {e}")
            raise ValueError(f"Failed to parse AI response: {e}")

    async def generate_followup_email(
        self,
        recruiter_name: str,
        company: str,
        original_subject: str,
        followup_number: int,
        days_since_original: int,
        candidate_profile: str,
    ) -> Dict[str, str]:
        """Generate a follow-up email."""
        ordinals = {1: "first", 2: "second", 3: "third"}
        ordinal = ordinals.get(followup_number, f"{followup_number}th")

        system_prompt = (
            "You are an expert at writing polite, effective follow-up emails. "
            "Your follow-ups are brief, value-adding, and never pushy. "
            "Always respond ONLY with valid JSON."
        )

        user_prompt = f"""Generate a {ordinal} follow-up email to a recruiter who hasn't responded.

Details:
- Recruiter: {recruiter_name} at {company}
- Original email subject: {original_subject}
- Days since original email: {days_since_original}
- Follow-up number: {followup_number}
- Candidate Profile: {candidate_profile}

Requirements:
- Keep it very brief (50-100 words)
- Reference the original email naturally
- Add a small piece of new value or insight
- Be polite and understanding that they are busy
- Clear but gentle call to action
- If this is the 3rd follow-up, mention this will be the last follow-up

Respond ONLY with JSON:
{{
  "subject": "Re: {original_subject}",
  "body": "follow up email body"
}}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            raw = await self._chat_completion(messages, temperature=0.7, max_tokens=400)
            raw = raw.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            raw = raw.strip().rstrip("```").strip()
            result = json.loads(raw)
            return {"subject": result["subject"], "body": result["body"]}
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse Grok followup response: {e}")
            raise ValueError(f"Failed to parse AI followup response: {e}")

    async def generate_campaign_analytics_summary(
        self,
        campaign_name: str,
        stats: Dict[str, Any],
        company_breakdown: list[Dict[str, Any]],
    ) -> str:
        """Generate an AI-powered analytics summary for a campaign."""
        company_str = "\n".join(
            f"- {item['company']}: {item['reply_rate']:.1f}% reply rate, "
            f"{item['open_rate']:.1f}% open rate ({item['count']} contacts)"
            for item in company_breakdown[:10]
        )

        prompt = f"""Analyze these email campaign results and provide actionable insights.

Campaign: {campaign_name}
Overall Stats:
- Sent: {stats.get('sent', 0)}
- Open Rate: {stats.get('open_rate', 0):.1f}%
- Click Rate: {stats.get('click_rate', 0):.1f}%
- Reply Rate: {stats.get('reply_rate', 0):.1f}%

Company Breakdown:
{company_str}

Write 3-5 concise, data-driven insights in plain text. Be specific with numbers.
Examples of good insights:
- "Amazon recruiters respond 2.3x more often than startup recruiters."
- "Personalized subject lines improved open rates by 31%."
Focus on what worked, what didn't, and what to do differently."""

        messages = [{"role": "user", "content": prompt}]
        return await self._chat_completion(messages, temperature=0.5, max_tokens=400)


grok_client = GrokClient()
