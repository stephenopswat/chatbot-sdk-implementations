'''
Usage command: 
    for url specific: python confluenceDumpWithPython.py --site <site-name only> --mode url --url "<put your url here>" --text
    for all spaces: python confluenceDumpWithPython.py --site <site-name only> --mode space --space SPACENAME --text
'''
import os
import argparse
import myModules
import re
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv
from bs4 import BeautifulSoup

load_dotenv()

"""
Dump Confluence content using Python

Args:
    mode: Download mode (space or url)
    site: Site to export from
    space: Space to export from (for space mode)
    url: URL to export from (for url mode)
    outdir: Folder to export to (optional)
    sphinx: Sphinx compatible folder structure (optional)
    notags: Do not add tags to rst files (optional)

Returns:
    HTML and RST files inside the default or custom output folder
"""


def save_plain_text(html_content, output_filepath):
    """
    Extracts plain text from an HTML string using BeautifulSoup
    and saves it to a file.
    """
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        plain_text = soup.get_text(separator=" ", strip=True)

        lines = (line.strip() for line in plain_text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        cleaned_text = "\n".join(chunk for chunk in chunks if chunk)


        with open(output_filepath, "w", encoding="utf-8") as f:
            f.write(cleaned_text)
        print(f"  |-> Saved plain text to {output_filepath}")
    except Exception as e:
        print(f"  [!] Could not save plain text file: {e}")


# --------------------------
# Argument Parser Setup
# --------------------------
parser = argparse.ArgumentParser()
parser.add_argument(
    "--mode", "-m", dest="mode",
    choices=["space", "url"],  # Cleaned choices
    help="Choose a download mode", required=True
)
parser.add_argument("--site", "-S", type=str, help="Atlassian Site", required=True)
parser.add_argument("--space", "-s", type=str, help="Space Key (for 'space' mode)")
parser.add_argument("--url", type=str, help="Full Confluence URL (for 'url' mode)")
parser.add_argument("--outdir", "-o", type=str, default="output",
                    help="Folder for export", required=False)
parser.add_argument("--sphinx", "-x", action="store_true", default=False,
                    help="Sphinx compatible folder structure", required=False)
parser.add_argument("--tags", action="store_true", default=False,
                    help="Add labels as .. tags::", required=False)
parser.add_argument("--html", action="store_true", default=False,
                    help="Include .html file in export (default is only .rst)", required=False)
parser.add_argument("--no-rst", action="store_false", dest="rst", default=True,
                    help="Disable .rst file in export", required=False)
parser.add_argument('--text-only', action='store_true', default=False,
                    help='Only export a plain .txt file for each page; suppress .rst and .html output.', required=False)
parser.add_argument("--text", action="store_true", default=False,
                    help="Include .txt file (plain text) in export", required=False)

args = parser.parse_args()

# Cleaned up validation
if args.mode == "url" and not args.url:
    parser.error("--url <URL> is required when mode is 'url'")
if args.mode == "space" and not args.space:
    parser.error("--space <SPACE_KEY> is required when mode is 'space'")

# Helper: sanitize a title into a filename-friendly token used elsewhere in the script
def _sanitize_title_for_filename(title: str) -> str:
    return title.replace("/", "-").replace(",", "").replace("&", "And").replace(":", "-").replace(" ", "_")



def extract_page_id_from_url(url: str) -> int | None:
    """
    Extracts the Confluence Page ID from various URL formats.
    """
    try:
        parsed_url = urlparse(url)
        path = parsed_url.path
        
        # Format 1: /wiki/spaces/SPACE/pages/<page_id>/Page+Title
        match = re.search(r'/pages/(\d+)', path)
        if match:
            return int(match.group(1))
            
        # Format 2: /wiki/pages/viewpage.action?pageId=<page_id>
        if "viewpage.action" in path:
            query_params = parse_qs(parsed_url.query)
            if "pageId" in query_params:
                return int(query_params["pageId"][0])
                
        print(f"  [!] Could not parse Page ID from URL: {url}")
        return None
    except Exception as e:
        print(f"  [!] Error parsing URL: {e}")
        return None

# --------------------------
# Initialization
# --------------------------
atlassian_site = args.site
my_attachments = []
my_embeds = []
my_embeds_externals = []
my_emoticons = []
my_emoticons_list = []

user_name = os.environ["atlassianUserEmail"]
api_token = os.environ["atlassianAPIToken"]

sphinx_compatible = args.sphinx
sphinx_tags = args.tags
print("Sphinx set to " + str(sphinx_compatible))

my_outdir_base = args.outdir

# --------------------------
# URL MODE
# --------------------------
if args.mode == "url":
    print(f"Exporting a single page from URL (Sphinx set to {args.sphinx})")
    page_id = extract_page_id_from_url(args.url)

    if not page_id:
        print("Could not get Page ID from URL. Exiting.")
    else:
        print(f"  |-> Extracted Page ID: {page_id}")
        
        page_name = myModules.get_page_name(atlassian_site, page_id, user_name, api_token)
        my_body_export_view = myModules.get_body_export_view(atlassian_site, page_id, user_name, api_token).json()
        my_body_export_view_html = my_body_export_view["body"]["export_view"]["value"]
        my_body_export_view_title = my_body_export_view["title"].replace("/", "-").replace(",", "").replace("&", "And").replace(":", "-").replace("|", "-").replace("[", "").replace("]", "")

        page_parent = myModules.get_page_parent(atlassian_site, page_id, user_name, api_token)
        my_outdir_base = os.path.join(my_outdir_base, f"{page_id}-{my_body_export_view_title}")
        my_outdir_content = my_outdir_base

        myModules.mk_outdirs(my_outdir_base)
        my_page_labels = myModules.get_page_labels(atlassian_site, page_id, user_name, api_token)
        print(f'Base export folder is "{my_outdir_base}" and the Content goes to "{my_outdir_content}"')

        exts = []
        if args.rst:
            exts.append('.rst')
        if args.html:
            exts.append('.html')
        if args.text:
            exts.append('.txt')

        myModules.dump_html(
            atlassian_site,
            my_body_export_view_html,
            my_body_export_view_title,
            page_id,
            my_outdir_base,
            my_outdir_content,
            my_page_labels,
            page_parent,
            user_name,
            api_token,
            sphinx_compatible,
            sphinx_tags,
            arg_html_output=args.html,
            arg_rst_output=args.rst,
        )

        if args.text:
            text_filepath = os.path.join(my_outdir_base, f"{my_body_export_view_title}.txt")
            save_plain_text(my_body_export_view_html, text_filepath)

        print("Done!")

# --------------------------
# SPACE MODE
# --------------------------
elif args.mode == 'space':
    print(f"Exporting a whole space (Sphinx set to {args.sphinx})")
    space_key = args.space
    
    all_spaces_full = myModules.get_spaces_all(atlassian_site,user_name,api_token)
    space_id = ""
    space_name = ""
    for n in all_spaces_full:
        if (n['key'].lower() == space_key.lower()):
            print("Found space: " + n['key'])
            space_id = n['id']
            space_name = n['name']
            break

    my_outdir_content = os.path.join(my_outdir_base,f"{space_id}-{space_name}")
    if not os.path.exists(my_outdir_content):
        os.mkdir(my_outdir_content)
    
    if not args.sphinx:
        my_outdir_base = my_outdir_content

    # This creates the main directories (_images, _static) once.
    myModules.mk_outdirs(my_outdir_base)

    if space_id == "":
        print(f"Could not find Space Key '{space_key}' in this site.")
    else:
        all_pages_full = myModules.get_pages_from_space(atlassian_site,space_id,user_name,api_token)
        print(f"{len(all_pages_full)} pages to export")
        page_counter = 0

        for p in all_pages_full:
            page_counter += 1
            # First, we always need to get the page content, regardless of output mode
            my_body_export_view = myModules.get_body_export_view(atlassian_site,p['id'],user_name,api_token).json()
            my_body_export_view_html = my_body_export_view['body']['export_view']['value']
            my_body_export_view_title = p['title'].replace("/","-").replace(",","").replace("&","And").replace(" ","_").replace("|", "-").replace("[", "").replace("]", "")
            
            print(f"\nGetting page #{page_counter}/{len(all_pages_full)}, {my_body_export_view_title}, {p['id']}")

            if args.text_only:
                # This block runs for "Plain Text Only" mode
                print("  --text-only flag set. Saving plain text and downloading attachments.")
                
                # 1. Download attachments
                attach_dir = myModules.set_dirs(my_outdir_base)[0]
                myModules.get_attachments(atlassian_site, p['id'], attach_dir, user_name, api_token)

                # 2. Save the plain text file
                text_filepath = os.path.join(my_outdir_content, f"{my_body_export_view_title}.txt")
                save_plain_text(my_body_export_view_html, text_filepath)
            else:
                # This is the normal mode (when --text-only is NOT used)
                my_body_export_view_labels = myModules.get_page_labels(atlassian_site,p['id'],user_name,api_token)

                # Checkpoint: skip if outputs already exist for this page
                exts = []
                if args.rst:
                    exts.append('.rst')
                if args.html:
                    exts.append('.html')
                if args.text:
                    exts.append('.txt')

                myModules.dump_html(atlassian_site,my_body_export_view_html,my_body_export_view_title,p['id'],my_outdir_base,my_outdir_content,my_body_export_view_labels,p['parentId'],user_name,api_token,sphinx_compatible,sphinx_tags,arg_html_output=args.html,arg_rst_output=args.rst)
                
                # The --text flag can still be used to add a .txt file to the normal export
                if args.text:
                    text_filepath = os.path.join(my_outdir_content, f"{my_body_export_view_title}.txt")
                    save_plain_text(my_body_export_view_html, text_filepath)

    print("Done!")

# --------------------------
# NO MODE
# --------------------------
else:
    print("No script mode defined in the command line")