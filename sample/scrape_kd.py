import re
from pathlib import Path
from tqdm import tqdm
from bs4 import BeautifulSoup as bs
from article_ripper.main import get_document, html_to_md

START_CHAPTER = 1
LAST_CHAPTER = 246
LINK_KD = "https://rainingtl.org/kidnapped-dragons-"
DEST_DIR = Path.cwd().joinpath("dst")

# TODO: improve the headings pattern matching
# TODO: add a parameter to remove those "Sponsered Ads"

# Scraping with some post-processing stuff.
# Keep in mind that the steps during the post-processing stuff
# is obviously very specific to this novel/format of article.

episode_history = []
head_not_found_err = []

html_dir = DEST_DIR.joinpath("html-src")
html_dir.mkdir(parents=True, exist_ok=True)

cached_html_chapters_path = []
cached_html_chapters_num = []
for i in html_dir.rglob("*html"):
    cached_html_chapters_num.append(
        int(re.search(r"(ch(\d{1,3}))", str(i), flags=re.I).groups()[-1])
    )

# Downloading chapters separately
for i in tqdm(range(START_CHAPTER, LAST_CHAPTER + 1), "\033[0;1;91mFetching Chapters...\033[0m🚀️"):
    if i in cached_html_chapters_num:
        continue
    doc_html = get_document(LINK_KD + f"{i}").summary()

    soup = bs(doc_html, "lxml")
    heading = soup.find("h3")
    if heading is None:
        try:
            head_not_found_err.append(f"ep{episode_history[-1]} ch{i}")
            episode_number = episode_history[-1]
        except Exception:
            episode_number = "err"
    else:
        episode_number = re.findall(r"\d{1,3}", heading.text)[0]
        if len(episode_number) == 1:
            episode_number = "0"+episode_number
        if episode_number not in episode_history:
            episode_history.append(episode_number)

    html_episode_dir = html_dir.joinpath(f"{episode_number}-episode")
    html_episode_dir.mkdir(parents=True, exist_ok=True)

    with open(html_episode_dir.joinpath(f"{episode_number}-ch{i}.html"), "w") as f:
        f.write(doc_html)

# Updating cache
for i in html_dir.rglob("*html"):
    cached_html_chapters_path.append(i)

md_dir = DEST_DIR.joinpath("md-proc")
md_dir.mkdir(parents=True, exist_ok=True)

# Post processing stuff and converting to md
if head_not_found_err:
    # initializing again for cases when fetch loop is skipped
    # due to cache being present otherwise this list would remain empty.
    head_not_found_err = []

for i in tqdm(cached_html_chapters_path, "\033[0;1;94mProcessing...\033[0m⚙️"):
    episode_number = re.search(r"((\d{1,3})-episode)", str(i), flags=re.I).groups()[-1]
    if len(episode_number) == 1:
        episode_number = "0"+episode_number
    chapter_number = re.search(r"(ch(\d{1,3}))", str(i), flags=re.I).groups()[-1]
    with open(i, "r") as f:
        # Removal of "next/prev chapter" elements.
        soup = bs(f, "lxml")
        for j in soup.find_all("p")[-10:]:
            if re.search(r"(previous|next)\s+chapter", j.text, flags=re.IGNORECASE):
                j.extract()
        # h3 to h2
        heading = soup.find("h3")
        if heading is None:
            head_not_found_err.append(f"ep{episode_history[-1]} ch{chapter_number}")
            try:
                episode_number = episode_history[-1]
            except Exception:
                episode_number = "err"
        else:
            heading.name = "h2"
            # episode_number = re.findall(r"\d+", heading)[0]
            if episode_number not in episode_history:
                heading.name = "h1" # for chapter break when converting to epub
                episode_history.append(episode_number)

    doc_md = html_to_md(soup)
    episode_dir = md_dir.joinpath(f"{episode_number}-episode")
    episode_dir.mkdir(parents=True, exist_ok=True)

    with open(episode_dir.joinpath(f"{episode_number}-ch{chapter_number}.md"), "w") as f:
        f.write(doc_md)


if head_not_found_err:
    print(f"\033[0;1;93mNo headings found for chapters\033[0;1m {head_not_found_err}💔️\033[0m")
