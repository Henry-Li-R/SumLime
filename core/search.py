import time
import requests
from bs4 import BeautifulSoup

def search_snippets(claim):
    """
    Query DuckDuckGo HTML search and return a list of snippet texts.
    This method scrapes result summaries from the DDG HTML interface.
    """
    headers = {"User-Agent": "Mozilla/5.0"}
    query = {"q": claim}
    url = "https://html.duckduckgo.com/html/"

    for attempt in range(3): # Retry search 3 times max
        try:
            response = requests.post(url, data=query, headers=headers, timeout=10)
            response.raise_for_status()
            break
        except requests.exceptions.RequestException:
            if attempt == 2:
                raise
            time.sleep(1)

    soup = BeautifulSoup(response.text, "html.parser")
    snippets = []

    results = soup.find_all("a", class_="result__snippet")
    print(results)
    print("\n\n")
    if not results:
        raise RuntimeError("No result snippets found in DuckDuckGo HTML response")
    for result in results: # Store up to 5 snippets
        text = result.get_text(strip=True)
        print("result " + text + "\n\n")

        if text:
            snippets.append(text)
        if len(snippets) >= 5:
            break

    return snippets
