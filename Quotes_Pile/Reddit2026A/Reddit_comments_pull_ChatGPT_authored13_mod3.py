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
import glob
import traceback
from html_to_markdown import convert_to_markdown

# ToDo:
#
#   1. NSFW postings comment links error the code. I've just been interactively ending the error timing.
#
#   2. My Python is incredibly rusty. I don't know standard convention for variable names and camel case
#      vs. underscore. And this app source code mixes both.
#      Variable name renaming all across the board
#   3. Pass the whole arg to functions / methods as is done with the JSON page fetch
#      the HTML page fetch doesn't use app args variables the same way
#

# Global variables

# The Python standard (defined in PEP 8, the official style guide) for variable names is to use lowercase with words separated by underscores (known as snake_case)

HEADERS = {"User-Agent": "Pluribus TV project version 0.1.0"}
error_count_b = 0
error_fetch_count = 0
error_parse_a_count = 0
fetch_reddit_count_a = 0
replies_users_fetch = 0
replies_users_max = 16
# every slowdown_every fetches kick in delay
slowdown_every = 2
age18_count = 0
args = {}


# agenda here is to not need global in every function
# ToDo: utilize this code. Here to note future rework
def increment_error_for(error_index):
    global error_count_b
    global error_fetch_count
    global error_parse_a_count

    # ToDo: a switch case or even use an array instead of unique variables?
    # ToDo: remove the globals in the functions and call this



def live_fetch_error(res, call_spot):
    exitcode = 0
    
    if res.status_code == 429:
        print(f"detected http 429 error, immediate app exit. Call identifier {call_spot}")
        exitcode = 3
    if 500 <= res.status_code <= 599:
        print(f"detected http 5xx error, immediate app exit. Call identifier {call_spot}")
        exitcode = 4

    if exitcode > 0:
        print(f"HTTP Status: {res.status_code} {res.reason}")
        print(f"Response Time: {res.elapsed.total_seconds()}s")
        sys.exit(exitcode)



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


# alternates
#   https://old.reddit.com/r/Python/comments/1igtrtp/htmltomarkdown_12_modern_html_to_markdown/
#   https://github.com/Goldziher/html-to-markdown
def convert_html_to_md(div):
    global error_count_b
    
    if div is None:
        print("got empty div, missing comment?")
        error_count_b += 1
        return ""

    if "You must be at least eighteen years old to view this content." in div:
         print("over age 18, missing comment?")
         error_count_b += 1
         return ""

    try:
        md_text = convert_to_markdown(div);
        return md_text;
    except Exception as e:
        error_count_b += 1
        print(f"ERROR converting HTML to markdown. {e}")
        print(div)
        return f"ERROR\nERROR on HTML to markdown. Providing raw HTML:\n{div}";


def comment_do_one (comment_div):
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

    return {
        "author_tag": author_tag,
        "author": author,
        "time_tag": time_tag,
        "comment_age": comment_age,
        "comment_timestamp": comment_timestamp,
        "comment_md": comment_md,
        "score_tag": score_tag,
        "score_text": score_text,
    }




# Since the entire source list is comment links...
#    some replies are already covered.
#    check if in another tree we already processed comment.

comment_id_already = set()

def check_comment_seen(comment_id):
    # Use the 'in' operator for membership testing
    if comment_id in comment_id_already:
        return True
    else:
        comment_id_already.add(comment_id)
        return False


def walk_comment_tree(comment_div, level=0):
    global args
    global replies_users_fetch
    global replies_users_max

    # level 0 already printed
    if level == 0:
        print("--- SKIP level 0 ")

    else:
        
        # ToDo: throw aapp rgs into global and check global args?
        fetch_user_info = True
        use_hover=True

        # Old Reddit uses 'thing' class for the container
        entry = comment_div.find("div", class_="entry", recursive=False)
        #  entry = comment_div
        
        if entry:
            
            comment_id = comment_div.get('data-fullname')
            
            # has the comment been previously seen in this source batch?
            # will also note this as a new entry if unseen.
            if check_comment_seen(comment_id) == False:
                # Extract metadata
                author = None
                author_tag = entry.find("a", class_="author")
                if author_tag:
                    author = author_tag.get_text()

                    replies_users_fetch += 1
                    if replies_users_fetch > replies_users_max:
                        print(f"skip fetch user info, already got {replies_users_max}, on {replies_users_fetch}")
                        fetch_user_info = False
                    
                    account_date, bio, link_karma, comment_karma, account_live_fetch = None, None, None, None, False
                    if fetch_user_info:
                        if author != "[deleted]":
                        # if onec["author"] != "[deleted]":
                            if use_hover:
                                account_date, bio, link_karma, comment_karma, account_live_fetch = fetch_user_info_hover(author, args)
                                if account_live_fetch:
                                    live_fetch = True
                            else:
                                live_fetch = True
                                account_date, bio = fetch_user_info_full(author)
   
                else:
                    author = "[deleted]"
                
                # 'md' class contains the user's markdown text
                text_div = entry.find("div", class_="md")
                text = text_div.get_text(strip=True) if text_div else ""
                
                print("{0}- {1}: {2}...".format("  " * level, author, text[:120]))
            else:
                print(f"skip, already processed comment {comment_id}")
        else:
            print("entry not found")

    # Target the container for nested replies
    replies_container = comment_div.find("div", class_="child", recursive=False)
    if replies_container:
        # Nested comments are inside another 'sitetable' within 'child'
        nested_table = replies_container.find("div", class_="sitetable", recursive=False)
        if nested_table:
            child_comments = nested_table.find_all("div", class_="thing", recursive=False)
            for child in child_comments:
                walk_comment_tree(child, level + 1)
    else:
        print("no replies_container")



def fetch_comment_data(url, idx=None, args=None):
    global fetch_reddit_count_a
    global replies_users_fetch
    global age18_count

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

    if save_html_folder is not None:
        os.makedirs(save_html_folder, exist_ok=True)

        if check_saved_first:
            # Reddit comment id are system-wide for all subreddits
            # filename_pattern = f"{comment_id}_*.html"
            filename_pattern = os.path.join(save_html_folder, f"{comment_id}_*.html")
            existing_files_all = glob.glob(filename_pattern)

            if existing_files_all:

                found_count = len(existing_files_all)
                # epoc number filenames should sort highest (freshest, most recent)
                html_filename = max(existing_files_all)

                print(f"[cached] Using saved HTML for {url} file {html_filename} found count: {found_count}")
                with open(html_filename, "r", encoding="utf-8") as f:
                    html_text = f.read()

            else:
                print(f"found no existing files, pattern {filename_pattern}")


    if html_text is None:
        # no HTML loaded from local storage, do live Internet fetch
        fetch_reddit_count_a += 1
        res = requests.get(url, headers=HEADERS)
        fetch_time_epoch = int(time.time())
        if res.status_code != 200:
            live_fetch_error(res, 3)
        res.raise_for_status()
        html_text = res.text
        live_fetch = True

        html_filename = os.path.join(save_html_folder, f"{comment_id}_{fetch_time_epoch}.html")

        if html_filename:
            with open(html_filename, "w", encoding="utf-8") as f:
                f.write(html_text)
            print(f"Saved fresh fetched HTML to {html_filename}")


    soup = BeautifulSoup(html_text, "html.parser")

    comment_div = soup.find("div", attrs={"data-fullname": f"t1_{comment_id}"})
                    
    if not comment_div:
        age18_content = soup.find('button', attrs={'name': 'over18'})
        if age18_content:
            print("age 18 content detected")
            age18_count += 1
        # Abandoning exceptions for known predictable failures
        # raise ValueError(f"Could not find comment div with id t1_{comment_id} on page {url}")
        return {
            "parsed": 1,
            "live_fetch": live_fetch,
        }

    print(f"processing comment {comment_id}")

    # Find the nested div that contains all child/reply comments and remove it
    replies = comment_div.find("div", class_="child")
    if replies:
        print("!!!!!!!!!!!!!")
        print("!!!!!!!!!!!!! replies found")
        # Locate the 'expand' link which contains the child count text when collapsed
        expand_link = comment_div.find("a", class_="expand")

        if expand_link:
            num_children_tag = comment_div.find("a", class_="numchildren")
            if num_children_tag:
                child_count_text = num_children_tag.get_text(strip=True)
                print(f"!!!!!!!!!!!!! number of replies child count text: {child_count_text}")

        # reset global variable
        replies_users_fetch = 0
        walk_comment_tree(comment_div, 0)
        print("!!!!!!!!!!!!! replies processed")
        replies.decompose()


    # onec = one_comment
    onec = comment_do_one(comment_div)


    account_date, bio, link_karma, comment_karma, account_live_fetch = None, None, None, None, False
    if fetch_user_info:
        if onec["author"] != "[deleted]":
            if use_hover:
                account_date, bio, link_karma, comment_karma, account_live_fetch = fetch_user_info_hover(onec["author"], args)
                if account_live_fetch:
                    live_fetch = True
            else:
                live_fetch = True
                account_date, bio = fetch_user_info_full(author)
   
    # ToDo: post when time         
    post_title, post_account, post_body = None, None, None
    # for now, there is no application param to control, so hard-wire to true
    if 1:
        # 1. Get the Posting Title
        # On old.reddit, the post title is typically an <a> tag with class "title"
        title_tag = soup.find("a", class_="title")

        if title_tag:
            post_title = title_tag.get_text()
        else:
            post_title = "Title not found"

        # 2. Get the Posting Body (Self-text)
        # The main post text is usually inside a 'usertext-body' div within 'topmatter'
        top_matter = soup.find("div", class_="topmatter")
        body_div = None

        if top_matter:
            body_div = top_matter.find("div", class_="usertext-body")

            if body_div:
                post_body = body_div.get_text(strip=True)
            else:
                # leave as "None" ... post_body = "No body text (link-only post)"
                print("no post body top_matter usertext-body found")

            # ToDo: Unfinished
            post_account = top_matter.find("a", class_="author")
            post_author_name = post_account.get_text() if post_account else "[deleted]"
    

        else:
            print("no post body top_matter found")
        
            # wget of comment specific URL reveals that the posting text is absent.
            #   https://old.reddit.com/r/c64/comments/1q7asvi/cli_for_c64_ultimate_rest_api/nye0maj/
            #   only if you fetch the posting URL directly do you get the posting text
            #   https://old.reddit.com/r/c64/comments/1q7asvi/cli_for_c64_ultimate_rest_api/


    return {
        "parsed": 0,
        "url": url,
        "author": onec["author"],
        "comment_id": comment_id,
        "comment": onec["comment_md"],
        "comment_age": onec["comment_age"],
        "comment_timestamp": onec["comment_timestamp"],
        "score": onec["score_text"],
        "account_created": account_date,
        "bio": bio,
        "link_karma": link_karma,
        "comment_karma": comment_karma,
        "live_fetch": live_fetch,
        "post_title": post_title,
        "post_body": post_body,
    }


def fetch_user_info_hover(username, args=None):
    global fetch_reddit_count_a
    global error_fetch_count
    global slowdown_every
    global error_parse_a_count

    url = f"https://old.reddit.com/user/{username}/about.json"
    
    account_filename = None
    account_text = None
    reddit_account_data = None
    live_fetch = False
    
    if args.fetched_account_folder:
        os.makedirs(args.fetched_account_folder, exist_ok=True)

        if args.check_saved_first:
            # WARNING
            #  The Reddit message comment identifier is machine generated and follows a
            #  non-creative pattern. Usernames, on the other hand, serve the end-suer more
            #  and allow underscores in the filenames.
            #  Personally I think a unique unicode character should be designated
            #     1. spaces in filenames should have a UNIQUE Unicode value that allow console rendering
            #         to distinguish from space between parameters. Such a filename-space character
            #         could even be rendered visibliy in computer system console fonts.
            #     2.  Same goes with URL links with spaces
            #     3.  Maybe tabs too?
            #     4.  Underscore in filenames too?
            #     5.  All these conventions for filenames also make standard for source code
            #         variable and function / method names. And source code editing tools
            #         and viewing tools could use fonts to render them as visible
            #     6.  The essential idea is that "space" and "underscore" be returned to the common
            #         human language use. And that "spaces in filenames" and "space in variable names"
            #         get their own special Unicode character for all the technical reasonsons of clarity
            #         of technical usage and mistakes in parsing /etc.
            #     7.  While we are at it... a new set of Unicode characters for made-up quotations of people
            #         In USA culture / English speakers tend to use "quoted phrases" as a way to express
            #         sound-alike write-alike mockery and sarcasm of the thinking of someone. But it is bad.
            #         It is bad, because it is represented in the same way as if you are factaully qooting
            #         another person or organization and isn't clealry marked as a "fbricated quote" usage.
            #         Since year 2013, the Internet has been overrun with misinformation and disinformation
            #         And having a convention of "this quote is a fiction representation of an idea"
            #         emphasizes the importance of quoting other people or organizes sincerely. 
            #     8.  Similar to number 7 on this list. A new set of Unicode values for begin and end of a quote
            #         that is used for EMPHASIS, "Air Quotes". Like bold or italics or underline, but a convention
            #         of English speakers using "QUOTE THIS MOTHER FUCCKER" as a way to "SO CALLED" draw extra
            #         attention to emphasize a word. It's a usage like ALL CAPS on a word or MiXedCaps mocking.
            #     9.  Happy New Year 2026. All of Us, We The People, Pale Blue Dot Pride, Pluribus! go Earth!
            #     Thank you.
            #
            #  I've decided △ - Great Seal Pyramid. CURRENTLY as of January 1, 2026 - Reddit doesn't allow this
            #      character in a username. Also note that path such as "/" isn't allowed in username either
            #      so there isn't any defense against ".." attacks or "/" root path start of a username.
            #
            filename_pattern = os.path.join(args.fetched_account_folder, f"{username}△*.json")
            existing_files_all = glob.glob(filename_pattern)

            if existing_files_all:

                found_count = len(existing_files_all)
                # epoc number filenames should sort highest (freshest, most recent)
                account_filename = max(existing_files_all)
            
                # reference above print(f"[cached] Using saved HTML for {url} file {html_filename} found count: {found_count}")
                print(f"[cached] Using saved JSON for {username} file {account_filename} found count: {found_count}")
                with open(account_filename, "r", encoding="utf-8") as f:
                    # account_text = f.read()
                    reddit_account_data = json.load(f)


    if reddit_account_data is None:
        print(f"live-fetch for user_info_hover {url}")
        fetch_reddit_count_a += 1

        if fetch_reddit_count_a % slowdown_every == 0:
            print(f"fetch_reddit_count_a {fetch_reddit_count_a} is a multiple of {slowdown_every}.")
            sleep_time = random.uniform(11, 22)
            quit_request = pause_with_quit(sleep_time)
            if quit_request:
                sys.exit(1)
        
        res = requests.get(url, headers=HEADERS)
        fetch_time_epoch = int(time.time())
        if res.status_code == 404:
            # user account deleted
            reddit_account_data = res.json()
            print(f"User account 404 deleted? {url}")
            print(f"account data: {reddit_account_data}")
            quit_request = pause_with_quit(24)
            if quit_request:
                sys.exit(1)
        else:
            if res.status_code != 200:
                live_fetch_error(res, 1)
                error_fetch_count += 1
                print("Error encountered on Reddit account data fetch")
                print(res)
                quit_request = pause_with_quit(3)
                if quit_request:
                    sys.exit(1)
                return None, None, None, None, False
            reddit_account_data = res.json()["data"]
        
        live_fetch = True

        # account_filename = os.path.join(args.fetched_account_folder, f"{username}.json")
        account_filename = os.path.join(args.fetched_account_folder, f"{username}△{fetch_time_epoch}.json")

        if account_filename:
            with open(account_filename, "w", encoding="utf-8") as f:
                # f.write(data)
                json.dump(reddit_account_data, f, indent=4) # indent=4 makes the JSON output more readable
                print(f"Saved fresh fetched account JSON to {account_filename}")

    skip_condition = 0

    # ToDo: are both of these redundant?
    if "is_suspended" in reddit_account_data:
        if reddit_account_data["is_suspended"]:
             print("suspended account encountered")
             skip_condition = 1

    if "error" in reddit_account_data:
        if reddit_account_data["error"] == 404:
             # since the time of the comment capture, account now deleted
             print("since-deleted account encountered")
             skip_condition = 1

    if skip_condition > 0:
        # only pause if the first time, live fetch to Reddit
        if live_fetch:
            quit_request = pause_with_quit(3)
            if quit_request:
                sys.exit(1)
        return None, None, None, None, False

    try:
        created = datetime.datetime.utcfromtimestamp(reddit_account_data["created_utc"]).isoformat() + "Z"
        bio = ""
        user_title = ""
        account_subreddit = reddit_account_data.get("subreddit", {})
        if (account_subreddit):
            bio = account_subreddit.get("public_description")
            user_title = account_subreddit.get("title")
        else:
            error_parse_a_count += 1
            print("WARNING: account subreddit JSON absent")
            print(reddit_account_data)
            quit_request = pause_with_quit(10)
            if quit_request:
                sys.exit(1)

        # currently user_title is not returned, so merge with bio
        if user_title:
            bio = user_title + " : " + bio
        link_karma = reddit_account_data.get("link_karma")
        comment_karma = reddit_account_data.get("comment_karma")
        return created, bio, link_karma, comment_karma, live_fetch
    except Exception as e:
        print("error parsing account information", e)
        print(reddit_account_data)
        error_parse_a_count += 1
        quit_request = pause_with_quit(15)
        if quit_request:
            sys.exit(1)


def fetch_user_info_full(username):
    global fetch_reddit_count_a

    url = f"https://old.reddit.com/user/{username}/"
    print(f"live-fetch for user_info_full {url}")
    fetch_reddit_count_a += 1
    res = requests.get(url, headers=HEADERS)
    if res.status_code != 200:
        live_fetch_error(res, 2)
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
    global args
    global error_fetch_count
    global age18_count
    global error_parse_a_count

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
                # ToDo: is this doing a new http live-fetch?
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

        # currently matches here if age18 required
        if data["parsed"] > 0:
            print(f"PARSING returned matched skip, {data['parsed']}")
            continue

        # Markdown formatted output
        output_lines = [
            "\n",
            "="*13,
            "  ",
            f"## Reddit comment {data['comment_id']}\n",
            f"    entry {idx} ({idx - start}/{total})\n",
            f"Comment URL: {url}  ",
            f"Comment ID:      {data['comment_id']}  ",
            f"Author:          {data['author']}  ",
            f"Bio:             {data['bio']}  ",
            f"Account Created: {data['account_created']}  ",
            f"Link Karma:      {data['link_karma']}  ",
            f"Comment Karma:   {data['comment_karma']}  ",
            f"Comment Age:     {data['comment_age']}  ",
            f"Timestamp:       {data['comment_timestamp']}  ",
            f"Score:           {data['score']}  ",
            f"Post Title:      {data['post_title']}  ",
            f":::::: Reddit User Comment: ======  \n{data['comment']}"
        ]

        if commentary:
            output_lines.append(f":::::: Analysis_Thoughts Commentary: ======  \n{commentary}")

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

    endtime_dt_object = datetime.datetime.now(datetime.timezone.utc)
    # Format the datetime object into an ISO 8601 string with milliseconds
    endtime_iso_with_ms = endtime_dt_object.isoformat(timespec='milliseconds')

    with open('Output/run_summary0.txt', 'a') as summaryfile:
        summaryfile.write(f"{args.output}\n")
        summaryfile.write(f"    end {endtime_iso_with_ms}\n")

        if errorCountA + error_count_b + error_fetch_count + error_parse_a_count > 0:
            print(f"\nERRORS encountered! Final error counts, A: {errorCountA} B: {error_count_b} error_fetch_count: {error_fetch_count} error_parse_a_count: {error_parse_a_count}")
            summaryfile.write(f"\nERRORS encountered! Final error counts, A: {errorCountA} B: {error_count_b} error_fetch_count: {error_fetch_count} error_parse_a_count: {error_parse_a_count}\n")

        if fetch_reddit_count_a > 0:
            print(f"Live fetch to Reddit count: {fetch_reddit_count_a}")
            summaryfile.write(f"Live fetch to Reddit count: {fetch_reddit_count_a}\n")

        if age18_count > 0:
            print(f"Could not parse, age 18 required: {age18_count}")
            summaryfile.write(f"Could not parse, age 18 required: {age18_count}\n")


if __name__ == "__main__":
    main()
