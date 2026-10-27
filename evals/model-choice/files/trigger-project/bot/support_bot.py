"""Shop support bot (Demo material for a skill eval; not a real project.)"""
import anthropic

client = anthropic.Anthropic()


def answer(question):
    msg = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=400,
        messages=[{"role": "user", "content": question}],
    )
    return msg.content[0].text
