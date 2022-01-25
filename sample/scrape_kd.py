import re
from pathlib import Path
from tqdm import tqdm
from bs4 import BeautifulSoup as bs
from article_ripper.main import get_document, html_to_md

START_CHAPTER = 1
LAST_CHAPTER = 248
FETCH_ONLY = False

LINK_KD = "https://rainingtl.org/kidnapped-dragons-"
DEST_DIR = Path(__file__).parent.joinpath("dst")

# TODO: add a parameter to remove those "Sponsered Ads"

# Scraping with some post-processing stuff.
# Keep in mind that the steps during the post-processing stuff
# is obviously very specific to this novel/format of article.

if __name__ == "__main__":
    head_not_found_err = []
    # this is temporary, will rid of the need for this later maybe?.

    html_dir = DEST_DIR.joinpath("html-src")
    html_dir.mkdir(parents=True, exist_ok=True)

    cached_html_chapters_path = []
    cached_html_chapters_num = []
    for i in html_dir.rglob("*html"):
        cached_html_chapters_num.append(
            int(re.search(r"ch(\d{1,3})", str(i), flags=re.I).group(1))
        )

    # ! Downloading chapters separately
    for i in tqdm(
        range(START_CHAPTER, LAST_CHAPTER + 1),
        "\033[0;1;91mFetching Chapters...\033[0m🚀️",
    ):
        if i in cached_html_chapters_num:
            continue
        doc_html = get_document(LINK_KD + f"{i}").summary()

        soup = bs(doc_html, "lxml")
        heading = soup.find("h3")

        chapter_number = "{0:03}".format(i)
        if heading is None:
            try:
                for j in soup.find_all("strong"):
                    # ! lazy workaround for when can't find Hx
                    _ep_num_find = re.search(
                        r"episode\s+(\d{2,3}):", str(j), flags=re.I
                    )
                    if _ep_num_find:
                        episode_number = _ep_num_find.group(1)
                        head_not_found_err.append(
                            f"ep{episode_number} ch{chapter_number}"
                        )
                        break
                if not _ep_num_find:
                    raise
            except Exception as e:
                episode_number = "ERR"
                tqdm.write("Error!", end=" ")
                tqdm.write(repr(e))
        else:
            episode_number = re.search(r"\d{1,3}", heading.text).group()
        episode_number = "{0:03}".format(int(episode_number))

        html_episode_dir = html_dir.joinpath(f"{episode_number}-episode")
        html_episode_dir.mkdir(parents=True, exist_ok=True)

        with open(
            html_episode_dir.joinpath(f"{episode_number}-ch{chapter_number}.html"), "w"
        ) as f:
            f.write(doc_html)

    if FETCH_ONLY:
        exit(0)

    # ! Updating cache
    """
    TODO(DONE✔️): sort this rglob & also need to fix ch num for that too.
    for eg. like 003, 063, 212...instead of 3, 63, 212
    """
    for i in sorted(html_dir.rglob("*html")):
        cached_html_chapters_path.append(i)

    md_dir = DEST_DIR.joinpath("md-proc")
    md_dir.mkdir(parents=True, exist_ok=True)

    episode_history = []
    # ! Post processing stuff and converting to MD
    if head_not_found_err:
        # initializing again for cases when fetch loop is skipped
        # due to cache being present otherwise this list would remain empty.
        head_not_found_err = []

    for i in tqdm(cached_html_chapters_path, "\033[0;1;94mProcessing...\033[0m⚙️"):
        episode_number = re.search(r"(\d{1,3})-episode", str(i), flags=re.I).group(1)
        chapter_number = re.search(r"ch(\d{1,3})", str(i), flags=re.I).group(1)
        # These should already be 3 digit ints so no need to do that again
        with open(i, "r") as f:
            # ! Removal of "next/prev chapter" elements.
            soup = bs(f, "lxml")
            for j in soup.find_all("p")[-10:]:
                if re.search(r"(previous|next)\s+chapter", j.text, flags=re.I):
                    j.extract()
            # ! h3 to h2
            heading = soup.find("h3")
            if heading is None:
                head_not_found_err.append(f"ep{episode_number} ch{chapter_number}")

                for k in soup.find_all("strong"):
                    # ! lazy workaround for when can't find Hx
                    if re.search(r"episode\s+\d{2,3}:", str(k), flags=re.I):
                        k.parent.name = "h2"
                        # !!! CHECK the episode via re
                        if episode_number not in episode_history:
                            k.parent.name = (
                                "h1"  # ! for chapter break when converting to epub
                            )
                            episode_history.append(episode_number)
            else:
                heading.name = "h2"
                if episode_number not in episode_history:
                    heading.name = "h1"  # ! for chapter break when converting to epub
                    episode_history.append(episode_number)

        doc_md = html_to_md(soup)
        episode_dir = md_dir.joinpath(f"{episode_number}-episode")
        episode_dir.mkdir(parents=True, exist_ok=True)

        with open(
            episode_dir.joinpath(f"{episode_number}-ch{chapter_number}.md"), "w"
        ) as f:
            f.write(doc_md)

    if head_not_found_err:
        print(
            f"⚠️  \033[0;1;93mThere might be issues with headings for chapters\033[0;1m {head_not_found_err}\033[0m"
        )
