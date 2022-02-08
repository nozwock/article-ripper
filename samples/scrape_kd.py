import re
from pathlib import Path
from tqdm import tqdm
from bs4 import BeautifulSoup as bs
from article_ripper import get_document, html_to_md

START_CHAPTER = 1
LAST_CHAPTER = 253
FETCH_ONLY = False

LINK_KD = "https://rainingtl.org/kidnapped-dragons-"
DEST_DIR = Path(__file__).parent.joinpath("dst")

FILTER_IMG = [
    "https://i0.wp.com/rainingtl.org/wp-content/uploads/2021/07/Levi-Ad-1.png",
]


# Ad segments & stuff
# TODO(DONE✔️): add a parameter to remove those "Sponsered Ads"

# Scraping with some post-processing stuff.
# Keep in mind that the steps during the post-processing stuff
# is obviously very specific to this novel/"format of article".

html_dir = DEST_DIR.joinpath("html-src")
html_dir.mkdir(parents=True, exist_ok=True)
md_dir = DEST_DIR.joinpath("md-proc")
md_dir.mkdir(parents=True, exist_ok=True)


def fetch_chapters() -> None:
    cached_html_chapters_num = [
        int(re.search(r"ch(\d{1,3})", str(i), flags=re.I).group(1))
        for i in html_dir.rglob("*html")
    ]

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
                        # head_not_found_err.append(
                        #     f"ep{episode_number} ch{chapter_number}"
                        # )
                        break
                if not _ep_num_find:
                    raise
            except Exception as e:
                episode_number = "ERR"
                tqdm.write("Error!", end=" ")
                tqdm.write(f"{e!r}")
        else:
            episode_number = re.search(r"\d{1,3}", heading.text).group()
        episode_number = "{0:03}".format(int(episode_number))

        html_episode_dir = html_dir.joinpath(f"{episode_number}-episode")
        html_episode_dir.mkdir(parents=True, exist_ok=True)

        with open(
            html_episode_dir.joinpath(f"{episode_number}-ch{chapter_number}.html"), "w"
        ) as f:
            f.write(doc_html)


def convert_chapters_to_md() -> None:
    cached_html_chapters_path = [i for i in sorted(html_dir.rglob("*html"))]
    """
    TODO(DONE✔️): sort this rglob & also need to fix ch num for that too.
    for eg. like 003, 063, 212...instead of 3, 63, 212
    """

    head_not_found_err = []
    # this is temporary, will rid of the need for this later maybe?.

    episode_history = []
    # if head_not_found_err:
    #     # initializing again for cases when fetch loop is skipped
    #     # due to cache being present otherwise this list would remain empty.
    #     head_not_found_err = []

    # ! Post processing stuff
    for i in tqdm(cached_html_chapters_path, "\033[0;1;94mProcessing...\033[0m⚙️"):
        episode_number = re.search(r"(\d{1,3})-episode", str(i), flags=re.I).group(1)
        chapter_number = re.search(r"ch(\d{1,3})", str(i), flags=re.I).group(1)
        # These should already be 3 digit ints so no need to do that again

        # tqdm.write(f"🗃 {str(i)}")

        with open(i, "r") as f:
            soup = bs(f, "lxml")

            # ! Filtering out Ad images
            for j in soup.find_all("img"):
                for k in FILTER_IMG:
                    # tqdm.write(f"📄 {j['src']}")
                    if re.search(rf"{k}", j["src"], flags=re.I):
                        # tqdm.write(f"🔱 check\n{k}")
                        _temp_elem = j
                        # just iterating 3 times just because I feel that should be enough
                        # for our use case here
                        for _ in range(3):
                            # we want to move up in the hierarchy until we include
                            # the <figure> tag
                            if (
                                len(_temp_elem.parent.get_text(strip=True)) == 0
                                or _temp_elem.parent.name == "figure"
                            ):
                                _temp_elem = _temp_elem.parent
                                # tqdm.write(f"\n✅success {str(_temp_elem)[:300]}...\n")
                            else:
                                # tqdm.write(
                                #     f"\n❌️fail {str(_temp_elem.parent)[:350]}...\n"
                                # )
                                _temp_elem.extract()
                                break
                        # j.extract()
                        # print(len(j.parent.get_text(strip=True)))\
                    else:
                        # tqdm.write(f"{j['src']}")
                        pass
                    # if re.search(rf"{k}", k, flags=re.I):
                    #     break

            # ! Removal of "next/prev chapter" elements.
            # tqdm.write(f"😎 {[str(j)[:150] for j in soup.find_all('p')[:-11:-1]]}")
            for j in soup.find_all("p")[:-11:-1]:
                if re.search(r"(previous|next)\s+chapter", j.text, flags=re.I):
                    # tqdm.write(f"📥 deleted {str(j)}")
                    j.extract()

            # ! h3 to h2
            # hmm maybe this is unnecessary we could instead just have epub chapters break at h2
            heading = soup.find("h3")
            if heading is None:
                head_not_found_err.append(f"ep{episode_number} ch{chapter_number}")

                for j in soup.find_all("strong"):
                    # ! lazy workaround for when can't find Hx
                    if re.search(r"episode\s+\d{2,3}:", str(j), flags=re.I):
                        j.parent.name = "h2"
                        # !!! CHECK the episode via re
                        if episode_number not in episode_history:
                            j.parent.name = (
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


if __name__ == "__main__":
    fetch_chapters()
    if FETCH_ONLY:
        exit(0)
    convert_chapters_to_md()
