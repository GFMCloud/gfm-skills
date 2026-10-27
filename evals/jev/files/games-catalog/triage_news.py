"""For each news link, ask Claude whether the article announces a new edition of a catalogued
game (demo project). Claude fetches and reads each article itself, then checks our catalogue."""
import anthropic

client = anthropic.Anthropic()
PROMPT = """Fetch the article at {url}. Read it, then search our catalogue (catalog.csv is attached)
and decide: does it announce a NEW EDITION of a game we already list? Follow any links in the
article to the publisher's site if the article is unclear. Answer yes or no and the catalog_id."""


def triage(url, catalog_text):
    msg = client.messages.create(
        model="<model>", max_tokens=400,
        tools=[{"type": "web_fetch", "name": "web_fetch"}],
        messages=[{"role": "user", "content": PROMPT.format(url=url) + "\n\n" + catalog_text}],
    )
    return msg.content[-1].text


if __name__ == "__main__":
    catalog_text = open("data/catalog.csv").read()
    for url in open("data/news_links.txt").read().split():
        print(url, triage(url, catalog_text))
