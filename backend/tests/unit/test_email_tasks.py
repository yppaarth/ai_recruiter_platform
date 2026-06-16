from app.models.models import Contact
from app.tasks.email_tasks import render_contact_template


def test_render_contact_template_basic_placeholders():
    contact = Contact(
        name="Priya",
        email="priya@example.com",
        company="OpenAI",
        title="Recruiter",
        extra_data={},
    )

    rendered = render_contact_template(
        "Hi {{name}}, I am reaching out about roles at {{company}} for a {{title}} contact.",
        contact,
    )

    assert rendered == "Hi Priya, I am reaching out about roles at OpenAI for a Recruiter contact."


def test_render_contact_template_custom_columns_and_spaced_tokens():
    contact = Contact(
        name="Sam",
        email="sam@example.com",
        company="Example Corp",
        title="Talent Partner",
        extra_data={"team": "Platform", "location": "Bengaluru"},
    )

    rendered = render_contact_template(
        "Hi {{ name }}, I saw the {{team}} opening in {{ location }} at {{company}}.",
        contact,
    )

    assert rendered == "Hi Sam, I saw the Platform opening in Bengaluru at Example Corp."
