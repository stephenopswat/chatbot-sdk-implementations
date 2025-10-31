import os
import argparse
import myModules
import re
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv

load_dotenv()

# We still need this helper function here to get the page_id
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
# Argument Parser Setup
# --------------------------
parser = argparse.ArgumentParser()
parser.add_argument(
    "--mode", "-m", dest="mode",
    choices=["space", "url"],
    help="Choose a download mode", required=True
)
parser.add_argument("--site", "-S", type=str, help="Atlassian Site", required=True)
parser.add_argument("--space", "-s", type=str, help="Space Key (for 'space' mode)")
parser.add_argument("--url", type=str, help="Full Confluence URL (for 'url' mode)")
parser.add_argument("--outdir", "-o", type=str, default="output",
                    help="Folder for export", required=False)
# --- All other arguments (html, rst, sphinx, etc.) are removed ---

args = parser.parse_args()

# --- Validation ---
if args.mode == "url" and not args.url:
    parser.error("--url <URL> is required when mode is 'url'")
if args.mode == "space" and not args.space:
    parser.error("--space <SPACE_KEY> is required when mode is 'space'")

# --------------------------
# Initialization
# --------------------------
atlassian_site = args.site
user_name = os.environ["atlassianUserEmail"]
api_token = os.environ["atlassianAPIToken"]
my_outdir_base = args.outdir # This is just "output" by default

# --- THIS IS THE ONLY FOLDER CREATION ---
# Ensure the base output directory (e.g., "output") exists
os.makedirs(my_outdir_base, exist_ok=True)
# ----------------------------------------

# --------------------------
# URL MODE
# --------------------------
if args.mode == "url":
    print(f"Exporting a single page from URL...")
    page_id = extract_page_id_from_url(args.url)

    if not page_id:
        print("Could not get Page ID from URL. Exiting.")
    else:
        print(f"  |-> Extracted Page ID: {page_id}")
        
        # Get page content
        my_body_export_view = myModules.get_body_export_view(atlassian_site, page_id, user_name, api_token).json()
        my_body_export_view_html = my_body_export_view["body"]["export_view"]["value"]
        my_body_export_view_title = my_body_export_view["title"]

        # --- Pass the FLAT output directory to the module ---
        # Both 'base' and 'content' are just "output"
        myModules.dump_html(
            arg_site=atlassian_site,
            arg_html=my_body_export_view_html,
            arg_title=my_body_export_view_title,
            arg_page_id=page_id,
            arg_outdir_base=my_outdir_base,    # Passes "output"
            arg_outdir_content=my_outdir_base, # Passes "output"
            arg_page_labels=None,
            arg_page_parent=None,
            arg_username=user_name,
            arg_api_token=api_token
        )

    print("Done!")

# --------------------------
# SPACE MODE
# --------------------------
elif args.mode == 'space':
    print(f"Exporting a whole space...")
    space_key = args.space
    
    all_spaces_full = myModules.get_spaces_all(atlassian_site,user_name,api_token)
    space_id = ""
    for n in all_spaces_full:
        if (n['key'].lower() == space_key.lower()):
            print("Found space: " + n['key'])
            space_id = n['id']
            break

    if space_id == "":
        print(f"Could not find Space Key '{space_key}' in this site.")
    else:
        all_pages_full = myModules.get_pages_from_space(atlassian_site,space_id,user_name,api_token)
        print(f"{len(all_pages_full)} pages to export")

        for p in all_pages_full:
            # Get page content
            my_body_export_view = myModules.get_body_export_view(atlassian_site,p['id'],user_name,api_token).json()
            my_body_export_view_html = my_body_export_view['body']['export_view']['value']
            my_body_export_view_title = p['title']
            
            print(f"\nGetting page {my_body_export_view_title}, {p['id']}")

            # --- Pass the FLAT output directory to the module ---
            # Both 'base' and 'content' are just "output"
            myModules.dump_html(
                arg_site=atlassian_site,
                arg_html=my_body_export_view_html,
                arg_title=my_body_export_view_title,
                arg_page_id=p['id'],
                arg_outdir_base=my_outdir_base,    # Passes "output"
                arg_outdir_content=my_outdir_base, # Passes "output"
                arg_page_labels=None,
                arg_page_parent=p['parentId'],
                arg_username=user_name,
                arg_api_token=api_token
            )

    print("Done!")

else:
    print("No script mode defined in the command line")