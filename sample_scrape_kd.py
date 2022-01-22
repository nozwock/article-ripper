import re
from pathlib import Path
from tqdm import tqdm
from bs4 import BeautifulSoup as bs
from article_ripper import get_document, html_to_md

START_CHAPTER = 1
LAST_CHAPTER = 246
LINK_KD = "https://rainingtl.org/kidnapped-dragons-"
DEST_DIR = Path.cwd().joinpath("dst")

# Scraping with some post-processing stuff.
# Keep in mind that the steps during the post-processing stuff
# is obviously very specific to this novel/format of article.

episode_history = []
head_not_found_err = []

for i in tqdm(range(START_CHAPTER, LAST_CHAPTER+1), "processing...🐧️"):
    doc_html = get_document(LINK_KD + f"{i}").summary()
    soup = bs(doc_html, "lxml")
    # Removal of "next/prev chapter" elements.
    for j in soup.find_all("p")[-10:]:
        if re.search(r"(previous|next)\s+chapter", j.text, flags=re.IGNORECASE):
            j.extract()
    # h3 to h2
    if soup.find("h3") is None:
        head_not_found_err.append(i)
        try:
            episode_number = episode_history[-1]
        except Exception:
            episode_number = "err"
    else:
        soup.find("h3").name = "h2"
        heading = soup.find("h2").text
        episode_number = re.findall(r"\d+", heading)[0]
        if episode_number not in episode_history:
            # add_break = soup.new_tag("h1")
            # add_break.string = re.findall(r"[\w ]+:[\w ]+", heading)[0].strip()
            # soup.h2.insert_before(add_break)
            soup.find("h2").name = "h1"
            episode_history.append(episode_number)

    doc_md = html_to_md(soup)
    episode_dir = DEST_DIR.joinpath(f"{episode_number}-episode")
    episode_dir.mkdir(parents=True, exist_ok=True)

    with open(episode_dir.joinpath(f"{episode_number}-ch{i}.md"), "w") as f:
        f.write(doc_md)

if head_not_found_err:
    print(f"\033[0;1mNo heading found for chapters {head_not_found_err}💔️\033[0m")
