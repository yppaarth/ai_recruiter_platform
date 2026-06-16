from app.services.email_service import EmailService


def test_text_to_html_linkifies_plain_urls():
    service = EmailService()

    html = service._text_to_html("Please review https://example.com/jobs?team=ai&level=senior.")

    assert (
        '<a href="https://example.com/jobs?team=ai&amp;level=senior">'
        'https://example.com/jobs?team=ai&amp;level=senior</a>.'
    ) in html


def test_wrap_links_uses_tracking_base_url(monkeypatch):
    monkeypatch.setattr("app.services.email_service.settings.TRACKING_BASE_URL", "https://track.example.com")
    service = EmailService()

    html = service._wrap_links('<a href="https://example.com/jobs">Jobs</a>', "email-123")

    assert 'href="https://track.example.com/api/v1/tracking/click/email-123?url=https%3A%2F%2Fexample.com%2Fjobs"' in html


def test_tracking_pixel_uses_tracking_base_url(monkeypatch):
    monkeypatch.setattr("app.services.email_service.settings.TRACKING_BASE_URL", "https://track.example.com/")
    service = EmailService()

    html = service._inject_tracking_pixel("<body>Hello</body>", "track-123")

    assert 'src="https://track.example.com/api/v1/tracking/open/track-123"' in html
