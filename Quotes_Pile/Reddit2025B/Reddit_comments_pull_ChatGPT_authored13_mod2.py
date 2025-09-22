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
import json
import os
from bs4 import NavigableString, Tag
import traceback



HEADERS = {"User-Agent": "Mozilla/5.0"}


def pause_with_quit(total_seconds):
    print(f"\nPausing for {int(total_seconds)} seconds. Press 'Q' to quit app. [SPACE] to end pause.")
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
                    return True
                if key == " ":
                    print("Pause ended by operator.")
                    return False
        
        return False
 
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

    def recurse(node, in_list=False, list_type=None, index=1, in_blockquote=False):
        if isinstance(node, NavigableString):
            return str(node)
        elif isinstance(node, Tag):
            inner = "".join(
                recurse(
                    c,
                    in_list=in_list,
                    list_type=list_type,
                    index=index,
                    in_blockquote=in_blockquote,
                )
                for c in node.children
            )

            if node.name in ["b", "strong"]:
                inner = f"**{inner}**"
            elif node.name in ["i", "em"]:
                inner = f"*{inner}*"
            elif node.name == "a":
                href = node.get("href", "")
                if href:
                    return f"[{inner}]({href})"
                else:
                    return inner
            elif node.name == "li":
                if list_type == "ul":
                    return f"* {inner.strip()}\n"
                elif list_type == "ol":
                    return f"{index}. {inner.strip()}\n"
                else:
                    return f"{inner.strip()}\n"
            elif node.name == "ul":
                return "".join(
                    recurse(c, in_list=True, list_type="ul") for c in node.children
                ) + "\n"
            elif node.name == "ol":
                out, idx = [], 1
                for c in node.children:
                    out.append(recurse(c, in_list=True, list_type="ol", index=idx))
                    idx += 1
                return "".join(out) + "\n"
            elif node.name == "blockquote":
                content = recurse(node, in_blockquote=True)
                # Prefix each non-empty line with ">"
                quoted = "\n".join(
                    ["> " + line if line.strip() else ">" for line in content.splitlines()]
                )
                return quoted + "\n\n"
            elif node.name in ["p", "div"]:
                return inner.rstrip() + "\n\n"

            return inner
        return ""

    try:
        md_text = recurse(div).strip()

        # Tidy up line endings: force two-space at end of non-blank lines
        lines = md_text.splitlines()
        for i in range(len(lines)):
            if lines[i].strip() and (i + 1 < len(lines) and not lines[i + 1].strip()):
                continue
            elif lines[i].strip() and not lines[i].endswith("  "):
                lines[i] += "  "

        return "\n".join(lines).rstrip()
    except Exception as e:
        print(f"ERROR converting HTML to markdown. {e}")
        print(div)
        return f"ERROR\nERROR on HTML to markdown. Providing raw HTML:\n{div}";



def fetch_comment_data(url, idx=None, args=None):
	
    # params
    # save_html_folder=None, check_saved_first=True
    use_hover=True
    fetch_user_info=not args.no_user_info
    save_html_folder=args.fetched_html_folder
    check_saved_first=args.check_saved_first
	
	
    path_parts = urlparse(url).path.strip("/").split("/")
    if len(path_parts) < 6:
        raise ValueError(f"URL does not appear to include a comment ID: {url}")
    comment_id = path_parts[-1]
    comment_div_id = f"t1_{comment_id}"
    

    html_text = None
    html_filename = None
    live_fetch = False

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
        live_feetch = True

        if html_filename:
            with open(html_filename, "w", encoding="utf-8") as f:
                f.write(html_text)
            print(f"Saved fresh fetched HTML to {html_filename}")


    soup = BeautifulSoup(html_text, "html.parser")


    comment_div = soup.find("div", id=comment_div_id)
    if not comment_div:
        print("using fallback method to find comment")
        comment_div = soup.find("div", attrs={"data-fullname": f"t1_{comment_id}"})
            
    if not comment_div:
        raise ValueError(f"Could not find comment div with id t1_{comment_id} on page {url}")

    print("processing comment")
    try:
        body_div = comment_div.select_one(".usertext-body .md")
        comment_md = None
        if body_div:
            comment_md = convert_html_to_md(body_div)
        else:
            print("WARNING: comment not found")
            comment_md = "[comment not found]"

        author_tag = comment_div.select_one("a.author")
        author = author_tag.text.strip() if author_tag else "[deleted]"

        time_tag = comment_div.select_one(".tagline time")
        comment_age = time_tag.text.strip() if time_tag else None
        comment_timestamp = None
    except Exception as e:
        print(f"problem processing comment checkpoint A. {e}")
        #print(e)
        print(traceback.format_exc())
        raise ValueError(f"Could not process comment {comment_id} on page {url}")

    if time_tag and "title" in time_tag.attrs:
        try:
            dt = datetime.datetime.strptime(time_tag["title"], "%a %b %d %H:%M:%S %Y UTC")
            comment_timestamp = dt.isoformat() + "Z"
        except ValueError:
            comment_timestamp = time_tag["title"]

    score_tag = comment_div.select_one(".score.unvoted")
    score_text = score_tag.text.strip() if score_tag else None

    account_date, bio, link_karma, comment_karma, account_live_fetch = None, None, None, None, False
    if fetch_user_info and author != "[deleted]":
        if use_hover:
            account_date, bio, link_karma, comment_karma, account_live_fetch = fetch_user_info_hover(author, args)
            if account_live_fetch:
                live_fetch = True
        else:
            live_fetch = True
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
        "live_fetch": live_fetch,
    }


def fetch_user_info_hover(username, args=None):
    url = f"https://old.reddit.com/user/{username}/about.json"
    
    account_filename = None
    account_text = None
    data = None
    live_fetch = False
    
    if args.fetched_account_folder:
        os.makedirs(args.fetched_account_folder, exist_ok=True)
        account_filename = os.path.join(args.fetched_account_folder, f"{username}.json")

        if args.check_saved_first and os.path.exists(account_filename):
            print(f"[cached] Using saved account JSON for {username}")
            with open(account_filename, "r", encoding="utf-8") as f:
                # account_text = f.read()
                data = json.load(f)

    if data is None:
        print(f"live-fetch for user_info_hover {url}")
        res = requests.get(url, headers=HEADERS)
        if res.status_code != 200:
            return None, None, None, None, False
        data = res.json()["data"]
        live_fetch = True
    
        if account_filename:
            with open(account_filename, "w", encoding="utf-8") as f:
                # f.write(data)
                json.dump(data, f, indent=4) # indent=4 makes the JSON output more readable
                print(f"Saved fresh fetched account JSON to {account_filename}")

    created = datetime.datetime.utcfromtimestamp(data["created_utc"]).isoformat() + "Z"
    bio = data.get("subreddit", {}).get("public_description")
    user_title = data.get("subreddit", {}).get("title")
    if user_title:
        bio = user_title + " : " + bio
    link_karma = data.get("link_karma")
    comment_karma = data.get("comment_karma")
    return created, bio, link_karma, comment_karma, live_fetch


def fetch_user_info_full(username):
    url = f"https://old.reddit.com/user/{username}/"
    print(f"live-fetch for user_info_full {url}")
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
    parser.add_argument("--fetched-account-folder", default="fetched_accounts", help="Folder to save JSON of all fetched Reddit account info.")
    parser.add_argument("--error-html-folder", default="error_pages", help="Folder to save HTML pages on error.")
    parser.add_argument("--check-saved-first", action="store_true", help="Use cached HTML if available")
    parser.add_argument("--compare-saved", action="store_true", help="Compare live fetch with saved HTML; save _N versions if changed/removed")
    args = parser.parse_args()

    entries = parse_markdown_entries(args.file)

    start = args.skip_to
    end = start + args.stop_after if args.stop_after else len(entries)
    entries = entries[start:end]
    errorCountA = 0

    total = len(entries)
    for idx, (url, commentary) in enumerate(entries, start=start + 1):
        print("=" * 80)
        print(f"Entry {idx} ({idx - start}/{total}) - URL to fetch:")
        print(url)

        try:
            data = fetch_comment_data(
                url,
                idx=idx,
                args=args
            )
        except Exception as e:
            errorCountA += 1
            print(f"\n****** ERROR fetching comment: {e}. Error count: {errorCountA}")
            print(traceback.format_exc())
            quit_request = pause_with_quit(5)
            if quit_request:
                sys.exit(1)
            os.makedirs(args.error_html_folder, exist_ok=True)
            html_filename = os.path.join(args.error_html_folder, f"{idx}_{url.split('/')[-1]}.html")
            try:
                r = requests.get(url, headers=HEADERS)
                with open(html_filename, "w", encoding="utf-8") as f:
                    f.write(r.text)
                print(f"***** Saved HTML page on ERROR to {html_filename}")
            except Exception as save_err:
                print(f"***** ERROR Failed to save ERROR HTML: {save_err}")

            quit_request = pause_with_quit(30)
            if quit_request:
                sys.exit(1)
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
        if data['live_fetch']:
            if idx - start < len(entries):
                sleep_time = random.uniform(2, 8)  # 2–8 seconds pause
                quit_request = pause_with_quit(sleep_time)
                if quit_request:
                    print("Exiting after pause after live fetch")
                    sys.exit(0)

    if errorCountA > 0:
        print(f"\nERRORS encountered. Final error count: {errorCountA}")


if __name__ == "__main__":
    main()
