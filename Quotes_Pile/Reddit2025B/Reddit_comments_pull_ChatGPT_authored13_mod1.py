import sys
import select
import termios
import tty
import time
import random
import requests
import argparse
from bs4 import BeautifulSoup, NavigableString, Tag
import datetime
from urllib.parse import urlparse
import os

HEADERS = {"User-Agent": "Mozilla/5.0"}


def pause_with_quit(total_seconds):
    print(f"\nPausing for {int(total_seconds)} seconds. Press 'Q' to quit.")
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)  # non-canonical mode
        elapsed = 0
        interval = 0.2
        while elapsed < total_seconds:
            time.sleep(interval)
            elapsed += interval
            if select.select([sys.stdin], [], [], 0)[0]:
                key = sys.stdin.read(1)
                if key.lower() == "q":
                    print("Quit requested. Exiting.")
                    sys.exit(0)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def parse_markdown_entries(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        lines = [line.rstrip("\n") for line in f]

    entries = []
    current_entry = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("http://old.reddit.com") or stripped.startswith("https://old.reddit.com"):
            if current_entry:
                url = current_entry[0]
                commentary = "\n".join(current_entry[1:]).strip()
                entries.append((url, commentary))
            current_entry = [stripped]
        else:
            current_entry.append(line)

    if current_entry:
        url = current_entry[0]
        commentary = "\n".join(current_entry[1:]).strip()
        entries.append((url, commentary))

    return entries


def convert_html_to_md(div):
    if div is None:
        return ""

    def recurse(node):
        if isinstance(node, NavigableString):
            return str(node)
        elif isinstance(node, Tag):
            inner = "".join(recurse(c) for c in node.children)
            if node.name in ["b", "strong"]:
                inner = f"**{inner}**"
            elif node.name in ["i", "em"]:
                inner = f"*{inner}*"
            if node.name in ["p", "div", "li", "blockquote"]:
                return inner.rstrip() + "\n\n"
            return inner
        return ""

    md_text = recurse(div).strip()
    lines = md_text.splitlines()
    for i in range(len(lines)):
        if lines[i].strip() and (i + 1 < len(lines) and not lines[i + 1].strip()):
            continue
        elif lines[i].strip() and not lines[i].endswith("  "):
            lines[i] += "  "
    return "\n".join(lines).rstrip()


def fetch_comment_data(url, fetch_user_info=True, use_hover=True, save_html_folder=None, check_saved_first=True, idx=None):
    path_parts = urlparse(url).path.strip("/").split("/")
    if len(path_parts) < 6:
        raise ValueError(f"URL does not appear to include a comment ID: {url}")
    comment_id = path_parts[-1]
    comment_div_id = f"t1_{comment_id}"
    
    
    
    html_text = None
    html_filename = None

    if save_html_folder and idx is not None:
        os.makedirs(save_html_folder, exist_ok=True)
        html_filename = os.path.join(save_html_folder, f"{idx}_{comment_id}.html")

        if check_saved_first and os.path.exists(html_filename):
            print(f"[cached] Using saved HTML for {url}")
            with open(html_filename, "r", encoding="utf-8") as f:
                html_text = f.read()

    if html_text is None:
		# no HTML loaded from local storage, do live Internet fetch
        res = requests.get(url, headers=HEADERS)
        res.raise_for_status()
        html_text = res.text

        if html_filename:
            with open(html_filename, "w", encoding="utf-8") as f:
                f.write(html_text)
            print(f"Saved fresh fetched HTML to {html_filename}")


    soup = BeautifulSoup(html_text, "html.parser")


    comment_div = soup.find("div", id=comment_div_id)
    if not comment_div:
        comment_div = soup.find("div", attrs={"data-fullname": f"t1_{comment_id}"})
    if not comment_div:
        raise ValueError(f"Could not find comment div with id t1_{comment_id} on page {url}")

    body_div = comment_div.select_one(".usertext-body .md")
    comment_md = convert_html_to_md(body_div) if body_div else "[comment not found]"

    author_tag = comment_div.select_one("a.author")
    author = author_tag.text.strip() if author_tag else "[deleted]"

    time_tag = comment_div.select_one(".tagline time")
    comment_age = time_tag.text.strip() if time_tag else None
    comment_timestamp = None
    if time_tag and "title" in time_tag.attrs:
        try:
            dt = datetime.datetime.strptime(time_tag["title"], "%a %b %d %H:%M:%S %Y UTC")
            comment_timestamp = dt.isoformat() + "Z"
        except ValueError:
            comment_timestamp = time_tag["title"]

    score_tag = comment_div.select_one(".score.unvoted")
    score_text = score_tag.text.strip() if score_tag else None

    account_date, bio, link_karma, comment_karma = None, None, None, None
    if fetch_user_info and author != "[deleted]":
        if use_hover:
            account_date, bio, link_karma, comment_karma = fetch_user_info_hover(author)
        else:
            account_date, bio = fetch_user_info_full(author)

    return {
        "url": url,
        "author": author,
        "comment_id": comment_id,
        "comment": comment_md,
        "comment_age": comment_age,
        "comment_timestamp": comment_timestamp,
        "score": score_text,
        "account_created": account_date,
        "bio": bio,
        "link_karma": link_karma,
        "comment_karma": comment_karma,
    }


def fetch_user_info_hover(username):
    url = f"https://old.reddit.com/user/{username}/about.json"
    res = requests.get(url, headers=HEADERS)
    if res.status_code != 200:
        return None, None, None, None
    data = res.json()["data"]

    created = datetime.datetime.utcfromtimestamp(data["created_utc"]).isoformat() + "Z"
    bio = data.get("subreddit", {}).get("public_description")
    link_karma = data.get("link_karma")
    comment_karma = data.get("comment_karma")
    return created, bio, link_karma, comment_karma


def fetch_user_info_full(username):
    url = f"https://old.reddit.com/user/{username}/"
    res = requests.get(url, headers=HEADERS)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")
    age = soup.select_one(".age")
    account_created = (
        age["title"] if age and "title" in age.attrs else age.text.strip() if age else None
    )
    bio_tag = soup.select_one(".usertext-body .md")
    bio = bio_tag.get_text("\n", strip=True) if bio_tag else None
    return account_created, bio


def main():
    parser = argparse.ArgumentParser(description="Parse Reddit comments from markdown list.")
    parser.add_argument("--file", required=True, help="Input markdown file containing Reddit comment URLs.")
    parser.add_argument("--output", help="Optional file to write fetched comment output (console pauses not included).")
    parser.add_argument("--no-user-info", action="store_true", help="Skip fetching user profile info (faster).")
    parser.add_argument("--skip-to", type=int, default=0, help="Number of entries to skip before starting (0 = start from first).")
    parser.add_argument("--stop-after", type=int, default=None, help="Stop after this many entries (default = process all).")
    parser.add_argument("--fetched-html-folder", default="fetched_pages", help="Folder to save HTML of all fetched pages.")
    parser.add_argument("--error-html-folder", default="error_pages", help="Folder to save HTML pages on error.")
    parser.add_argument("--check-saved-first", action="store_true", help="Use cached HTML if available")
    parser.add_argument("--compare-saved", action="store_true", help="Compare live fetch with saved HTML; save _N versions if changed/removed")
    args = parser.parse_args()

    entries = parse_markdown_entries(args.file)

    start = args.skip_to
    end = start + args.stop_after if args.stop_after else len(entries)
    entries = entries[start:end]

    total = len(entries)
    for idx, (url, commentary) in enumerate(entries, start=start + 1):
        print("=" * 80)
        print(f"Entry {idx} ({idx - start}/{total}) - URL to fetch:")
        print(url)

        try:
            data = fetch_comment_data(
                url,
                fetch_user_info=not args.no_user_info,
                save_html_folder=args.fetched_html_folder,
                check_saved_first=args.check_saved_first,
                idx=idx
            )
        except Exception as e:
            print(f"ERROR fetching comment: {e}")
            os.makedirs(args.error_html_folder, exist_ok=True)
            html_filename = os.path.join(args.error_html_folder, f"{idx}_{url.split('/')[-1]}.html")
            try:
                r = requests.get(url, headers=HEADERS)
                with open(html_filename, "w", encoding="utf-8") as f:
                    f.write(r.text)
                print(f"Saved HTML page to {html_filename}")
            except Exception as save_err:
                print(f"Failed to save HTML: {save_err}")
            continue

        output_lines = [
            "\n",
            "="*80,
            f"Entry {idx} ({idx - start}/{total}) - URL: {url}",
            f"Comment ID:      {data['comment_id']}",
            f"Author:          {data['author']}",
            f"Account Created: {data['account_created']}",
            f"Link Karma:      {data['link_karma']}",
            f"Comment Karma:   {data['comment_karma']}",
            f"Bio:             {data['bio']}",
            f"Comment Age:     {data['comment_age']}",
            f"Timestamp:       {data['comment_timestamp']}",
            f"Score:           {data['score']}",
            f":::::: Reddit User Comment: ======\n{data['comment']}"
        ]

        if commentary:
            output_lines.append(f":::::: RoundSparrow Commentary: ======\n{commentary}")

        # Console output
        print("\n".join(output_lines))

        # Write to file if requested
        if args.output:
            with open(args.output, "a", encoding="utf-8") as f:
                f.write("\n".join(output_lines) + "\n")

        # Pause between entries
        if idx - start < len(entries):
            sleep_time = random.uniform(2, 8)  # 2–8 seconds pause
            pause_with_quit(sleep_time)


if __name__ == "__main__":
    main()
