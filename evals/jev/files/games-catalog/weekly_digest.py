"""Ask Claude to write the weekly email digest of catalogue changes (demo project)."""
import anthropic

client = anthropic.Anthropic()


def digest(changes):
    msg = client.messages.create(
        model="<model>", max_tokens=1200,
        messages=[{"role": "user", "content": "Write a friendly 200-word weekly digest of these catalogue changes:\n" + changes}],
    )
    return msg.content[0].text


if __name__ == "__main__":
    print(digest(open("data/catalog.csv").read()))
