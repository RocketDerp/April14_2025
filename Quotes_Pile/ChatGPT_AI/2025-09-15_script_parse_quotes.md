please create a python shell program to process this file an verify the links have the specified comments. https://github.com/RocketDerp/April14_2025/blob/main/Quotes_Pile/Reddit2025A/Today_Reddit_Comment.md
ChatGPT said:

Here’s a Python shell/CLI program that will:

Read the Markdown file (Today_Reddit_Comment.md)

Parse out all links

For each link, check (via HTTP GET) that it is valid (status 200, etc.)

Also check that each link has the “specified comments” (you’ll need to clarify what “specified comments” means — e.g. some text after the link, or a comment in Reddit? I’ll assume you mean that after the link in the file there is a comment line matching some pattern)

Report any broken links or missing/incorrect comments

I’ll write a version that is modular so you can adjust the “specified comment” criteria.

#!/usr/bin/env python3

import re
import sys
import argparse
import requests

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.readlines()

def extract_links(lines):
    """
    Returns a list of (line_no, link, line_text) for Markdown links.
    Markdown link format: [text](url)
    Also handles bare URLs if needed.
    """
    link_pattern = re.compile(r'\[.*?\]\((https?://[^\s\)]+)\)')
    bare_url_pattern = re.compile(r'(https?://[^\s\)]+)')
    results = []
    for i, line in enumerate(lines, start=1):
        for m in link_pattern.finditer(line):
            url = m.group(1)
            results.append( (i, url, line.strip()) )
        # Optionally, detect bare URLs:
        # for m in bare_url_pattern.finditer(line):
        #     url = m.group(1)
        #     results.append( (i, url, line.strip()) )
    return results

def check_link(url, timeout=10):
    """
    Returns (ok, status_code or exception_str)
    """
    try:
        resp = requests.head(url, allow_redirects=True, timeout=timeout)
        # Some servers don't respond well to HEAD; optionally fallback to GET
        if resp.status_code >= 400 or resp.status_code < 200:
            # try GET
            resp2 = requests.get(url, allow_redirects=True, timeout=timeout)
            return (resp2.status_code == 200, resp2.status_code)
        return (True, resp.status_code)
    except Exception as e:
        return (False, str(e))

def check_specified_comment_after(lines, link_line_no, pattern, max_lookahead=3):
    """
    After the line containing the link, look in the next max_lookahead lines
    to see if there's a comment matching `pattern` (regex).
    Returns True if found, False otherwise.
    """
    pat = re.compile(pattern)
    for offset in range(1, max_lookahead+1):
        idx = link_line_no -1 + offset
        if idx < len(lines):
            if pat.search(lines[idx]):
                return True
    return False

def main():
    parser = argparse.ArgumentParser(description="Verify links in Markdown file have specified comments")
    parser.add_argument("mdfile", help="Path to the markdown file")
    parser.add_argument("--comment-pattern", help="Regex pattern that must appear after each link", required=True)
    parser.add_argument("--max-lookahead", type=int, default=3, help="How many lines after link to search for comment")
    parser.add_argument("--timeout", type=float, default=10.0, help="HTTP timeout for link checking")
    args = parser.parse_args()

    lines = read_file(args.mdfile)
    links = extract_links(lines)

    if not links:
        print("No links found.")
        sys.exit(0)

    bad_links = []
    missing_comments = []

    print(f"Found {len(links)} links. Checking...")

    for (lineno, url, line_text) in links:
        ok, status = check_link(url, timeout=args.timeout)
        if not ok:
            bad_links.append( (lineno, url, status) )

        has_comment = check_specified_comment_after(lines, lineno, args.comment_pattern, args.max_lookahead)
        if not has_comment:
            missing_comments.append( (lineno, url) )

    print("\n=== Results ===\n")

    if bad_links:
        print("Broken links or non-200 responses:")
        for (lineno, url, status) in bad_links:
            print(f"  Line {lineno}: {url} --> {status}")
    else:
        print("All links returned OK status.")

    if missing_comments:
        print("\nLinks missing specified comment pattern within next"
              f" {args.max_lookahead} lines:")
        for (lineno, url) in missing_comments:
            print(f"  Line {lineno}: {url}")
    else:
        print("All links have the specified comment pattern following.")

    # Exit code: non-zero if any errors
    if bad_links or missing_comments:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()

How to adapt/use:

Place this script in a file, e.g. verify_links.py

Make it executable (chmod +x verify_links.py)

Run it like:

./verify_links.py Today_Reddit_Comment.md --comment-pattern="YourRequiredPatternHere"


Replace "YourRequiredPatternHere" with the regex that defines what the “specified comments” should look like.
For example, if every link should be followed by a line starting with > Comment: then you might use ^> Comment: as the pattern.

You can adjust --max-lookahead to control how many lines after the link you want to search for the comment.

The script uses requests library so make sure you have it installed (pip install requests).

If you tell me exactly what “specified comments” means in your case (e.g. “every link must have the Reddit comment’s author & score in the next line”, or “must have a line with ‘Commented by: ...’ after link”, or something else), I can adjust this script to match that more precisely. Do you want me to build that specific version for your file?


&nbsp;

&nbsp;

&nbsp;

&nbsp;

To answer your question at the end.  there is a &nbsp , then a link to old.reddit.com line, then a line with Reddit username and Reddit account creation date, then the next lines are quoted (") of the comment. Then an optional RoundSparrow_Commentary section on a * bullet
ChatGPT said:

Thanks for the clarification. Based on your structure, here's how the file content appears to be formatted:

File Format Structure:

A line containing &nbsp;

Next line: A Reddit comment link (https://old.reddit.com/...)

Next line: A Reddit username and account creation date

Following lines: One or more lines starting with " — these are quoted Reddit comments

Optionally: A bullet point * line for RoundSparrow_Commentary

🎯 Goal:

Write a Python script that:

Finds each Reddit comment link

Verifies:

It's preceded by &nbsp; (or nearby)

Followed by:

A username and account creation date line

At least one line that starts with "

(Optional) A bullet line starting with * for RoundSparrow commentary

Validates the Reddit link works (e.g. responds with status 200)

✅ Here's the Python Shell Script:
#!/usr/bin/env python3

import re
import sys
import requests

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.readlines()

def is_reddit_link(line):
    return 'https://old.reddit.com/' in line

def check_reddit_link(url, timeout=10):
    try:
        r = requests.head(url, allow_redirects=True, timeout=timeout)
        return r.status_code == 200
    except:
        return False

def process_blocks(lines):
    i = 0
    errors = []

    while i < len(lines):
        line = lines[i].strip()

        # Look for the Reddit link
        if is_reddit_link(line):
            link = line
            context = {"link_line": i+1, "link": link}

            # Check for &nbsp; within the last 2 lines
            if i >= 1 and '&nbsp' in lines[i-1]:
                context["nbsp"] = True
            elif i >= 2 and '&nbsp' in lines[i-2]:
                context["nbsp"] = True
            else:
                context["nbsp"] = False

            # Check the username/date line
            if i+1 < len(lines):
                context["username_line"] = lines[i+1].strip()
                context["has_username_line"] = True
            else:
                context["has_username_line"] = False

            # Collect comment quote lines
            comment_lines = []
            j = i + 2
            while j < len(lines) and lines[j].strip().startswith('"'):
                comment_lines.append(lines[j].strip())
                j += 1
            context["quoted_lines"] = comment_lines
            context["has_comment"] = len(comment_lines) > 0

            # Optional: RoundSparrow commentary on a bullet line
            if j < len(lines) and lines[j].strip().startswith("*"):
                context["has_commentary"] = True
            else:
                context["has_commentary"] = False

            # Check if the link is valid
            context["link_ok"] = check_reddit_link(link)

            # Report any issues
            issues = []
            if not context["nbsp"]:
                issues.append("Missing &nbsp; before link")
            if not context["has_username_line"]:
                issues.append("Missing username/date line")
            if not context["has_comment"]:
                issues.append("Missing quoted comment lines")
            if not context["link_ok"]:
                issues.append("Reddit link not accessible (broken?)")

            if issues:
                errors.append((context["link_line"], link, issues))

            # Move to the next block
            i = j
        else:
            i += 1

    return errors

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 verify_reddit_md.py Today_Reddit_Comment.md")
        sys.exit(1)

    filepath = sys.argv[1]
    lines = read_file(filepath)
    errors = process_blocks(lines)

    if not errors:
        print("✅ All Reddit comment blocks look valid.")
    else:
        print("❌ Issues found in the following blocks:\n")
        for lineno, link, issues in errors:
            print(f"Line {lineno}: {link}")
            for issue in issues:
                print(f"  - {issue}")
            print()

if __name__ == "__main__":
    main()

🛠 How to Use

Save it as verify_reddit_md.py

Install dependencies:

pip install requests


Run:

python3 verify_reddit_md.py Today_Reddit_Comment.md

🔄 Example Output
Line 142: https://old.reddit.com/r/...
  - Missing &nbsp; before link
  - Reddit link not accessible (broken?)


Would you like this script to also download the Markdown directly from GitHub instead of needing a local file?

&nbsp;

&nbsp;

&nbsp;

Sure, please do
ChatGPT said:

Here’s a Python script that will download the Markdown file from GitHub (using its “raw” URL), then process it to verify that each Reddit‑comment block matches your structure (i.e. &nbsp;, link, username/date line, quoted lines, optional commentary). Feel free to adapt it further if needed.

#!/usr/bin/env python3

import re
import sys
import requests

def fetch_markdown_from_github(raw_url, timeout=10):
    """
    Download the raw markdown content from a GitHub raw URL.
    Returns the lines as a list.
    """
    resp = requests.get(raw_url, timeout=timeout)
    resp.raise_for_status()
    text = resp.text
    return text.splitlines()

def is_reddit_comment_link(line):
    """
    Return True if line contains a reddit old link of a comment.
    E.g. contains https://old.reddit.com/
    """
    return bool(re.search(r'https?://old\.reddit\.com/.*', line))

def check_reddit_link_accessible(url, timeout=10):
    """
    Check if the Reddit comment link returns a 200 status (or at least is reachable).
    """
    try:
        # HEAD first
        r = requests.head(url, allow_redirects=True, timeout=timeout)
        if r.status_code == 200:
            return True, r.status_code
        # fallback to GET
        r2 = requests.get(url, allow_redirects=True, timeout=timeout)
        return (r2.status_code == 200), r2.status_code
    except Exception as e:
        return False, str(e)

def process_markdown_blocks(lines):
    """
    Go through the lines looking for reddit comment blocks, verifying format.
    Returns a list of detected errors.
    """
    errors = []
    i = 0
    total_lines = len(lines)

    while i < total_lines:
        line = lines[i].rstrip('\n')
        # Look for the link line
        if is_reddit_comment_link(line.strip()):
            link_line_no = i + 1  # 1-based
            link = line.strip()

            context = {
                "link_line": link_line_no,
                "link": link,
            }

            # Check for &nbsp; in the preceding couple of lines
            nbsp_found = False
            if i >= 1 and '&nbsp' in lines[i-1]:
                nbsp_found = True
            elif i >= 2 and '&nbsp' in lines[i-2]:
                nbsp_found = True
            context["nbsp"] = nbsp_found

            # Username & date line (must exist and be the next line)
            if i + 1 < total_lines:
                username_date_line = lines[i+1].strip()
                context["username_date_line"] = username_date_line
                # Simple check: non-empty, maybe matches a pattern
                # Example pattern: u/username · Created: YYYY‑MM‑DD
                # You can adjust as needed
                # Here I’ll check it’s not empty and doesn’t start with a quote or bullet or the link again
                if username_date_line and not username_date_line.startswith('"') and not username_date_line.startswith('*') and not is_reddit_comment_link(username_date_line):
                    context["has_username_line"] = True
                else:
                    context["has_username_line"] = False
            else:
                context["has_username_line"] = False

            # Quoted comment lines: starting with '"' after that
            quoted_lines = []
            j = i + 2
            while j < total_lines:
                l = lines[j].lstrip()  # leading whitespace stripped for checking
                if l.startswith('"'):
                    quoted_lines.append(l)
                    j += 1
                else:
                    break
            context["quoted_lines"] = quoted_lines
            context["has_quoted"] = len(quoted_lines) > 0

            # Optional RoundSparrow commentary: bullet line starting with *
            if j < total_lines:
                if lines[j].lstrip().startswith('*'):
                    context["has_commentary"] = True
                else:
                    context["has_commentary"] = False
            else:
                context["has_commentary"] = False

            # Check link reachable
            ok_link, status = check_reddit_link_accessible(link)
            context["link_ok"] = ok_link
            context["link_status"] = status

            # Collect issues
            block_issues = []
            if not context["nbsp"]:
                block_issues.append("Missing &nbsp; in the lines before the link")
            if not context["has_username_line"]:
                block_issues.append("Missing or malformed username/date line after link")
            if not context["has_quoted"]:
                block_issues.append("Missing quoted comment lines after username/date line")
            if not context["link_ok"]:
                block_issues.append(f"Reddit link not accessible or not returning status 200 (got {status})")

            if block_issues:
                errors.append( (link_line_no, link, block_issues) )

            # Move i past this block to continue scanning
            # Skip ahead: after quoted lines and optional commentary
            # If commentary exists, skip it too
            i = j
            if context["has_commentary"]:
                i += 1
        else:
            i += 1

    return errors

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 verify_reddit_from_github.py <raw_markdown_url>")
        sys.exit(1)

    raw_url = sys.argv[1]
    print(f"Fetching Markdown from: {raw_url}")
    try:
        lines = fetch_markdown_from_github(raw_url)
    except Exception as e:
        print(f"Error fetching markdown: {e}")
        sys.exit(2)

    print(f"Fetched {len(lines)} lines. Processing...")
    errors = process_markdown_blocks(lines)

    if not errors:
        print("✅ All Reddit comment blocks look valid.")
        sys.exit(0)
    else:
        print("❌ Issues found in the following blocks:\n")
        for (lineno, link, issues) in errors:
            print(f"Block starting at line {lineno}: {link}")
            for issue in issues:
                print(f"  - {issue}")
            print()
        sys.exit(1)

if __name__ == "__main__":
    main()

🔧 How to use this

Determine the raw URL for your GitHub file.
For example, if the GitHub page is:

https://github.com/RocketDerp/April14_2025/blob/main/Quotes_Pile/Reddit2025A/Today_Reddit_Comment.md


Then replace the github.com/.../blob/main/... with raw.githubusercontent.com/.../main/....
So the raw URL will be something like:

https://raw.githubusercontent.com/RocketDerp/April14_2025/main/Quotes_Pile/Reddit2025A/Today_Reddit_Comment.md


Save the above script, e.g. as verify_reddit_from_github.py

Install dependencies if you don’t already have them:

pip install requests


Run the script:

python3 verify_reddit_from_github.py https://raw.githubusercontent.com/RocketDerp/April14_2025/main/Quotes_Pile/Reddit2025A/Today_Reddit_Comment.md


The script will fetch the file, then scan for reddit comment blocks, report any issues found.

If you like, I can run it on the current file and send you a report of what issues it finds (if any). Do you want me to do that?

&nbsp;

&nbsp;

&nbsp;

&nbsp;

sure, run it for testing
ChatGPT said:

I don't have the ability to execute scripts in real-time, especially with external web requests like downloading from GitHub. However, if you follow the instructions provided, you'll be able to run it on your local machine and test it with the GitHub URL.

Here's a recap of the steps to run the script on your machine:

Save the Python script to a file, e.g., verify_reddit_from_github.py.

Install the dependencies:

pip install requests


Run the script with the raw URL from GitHub:

python3 verify_reddit_from_github.py https://raw.githubusercontent.com/RocketDerp/April14_2025/main/Quotes_Pile/Reddit2025A/Today_Reddit_Comment.md


The script will:

Fetch the raw Markdown file from GitHub.

Process it line by line.

Check that Reddit comment links are properly formatted and accessible.

Ensure that they follow the required structure (e.g., &nbsp;, username/date, quoted comment, and optional RoundSparrow commentary).

If you run into any issues or need help with the results, feel free to share the output and I'll assist you further!

&nbsp;

&nbsp;

&nbsp;

&nbsp;
