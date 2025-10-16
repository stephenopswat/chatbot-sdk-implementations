import os
import argparse
import myModules
from dotenv import load_dotenv
from bs4 import BeautifulSoup  # ADDED STEP 1: Import BeautifulSoup

load_dotenv()

"""
Dump Confluence content using Python

Args:
    mode: Download mode
    site: Site to export from
    space: Space to export from
    page: Page to export
    outdir: Folder to export to (optional)
    sphinx: Sphinx compatible folder structure (optional)
    notags: Do not add tags to rst files (optional)

Returns:
    HTML and RST files inside the default or custom output folder
"""


# ADDED STEP 2: Define a function to extract and save plain text
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
    choices=["single", "space", "bylabel", "pageprops"],
    help="Choose a download mode", required=True
)
parser.add_argument("--site", "-S", type=str, help="Atlassian Site", required=True)
parser.add_argument("--space", "-s", type=str, help="Space Key")
parser.add_argument("--page", "-p", type=int, help="Page ID")
parser.add_argument("--label", "-l", type=str, help="Page label")
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
parser.add_argument("--showlabels", action="store_true", default=False,
                    help="Export .rst files with the page labels at the bottom", required=False)
parser.add_argument('--text-only', action='store_true', default=False,
                    help='Only export a plain .txt file for each page; suppress .rst and .html output.', required=False)
# ADDED STEP 3: Add new command-line argument for text output
parser.add_argument("--text", action="store_true", default=False,
                    help="Include .txt file (plain text) in export", required=False)

args = parser.parse_args()

# --------------------------
# Mode Handling
# --------------------------
atlassian_site = args.site

if args.mode == "single":
    print(f"Exporting a single page (Sphinx set to {args.sphinx})")
    page_id = args.page
elif args.mode == "space":
    print(f"Exporting a whole space (Sphinx set to {args.sphinx})")
    space_key = args.space
elif args.mode == "bylabel":
    print(f"Exporting all pages with a common label (Sphinx set to {args.sphinx})")
elif args.mode == "pageprops":
    print(f"Exporting a Page Properties page with all its children (Sphinx set to {args.sphinx})")

# --------------------------
# Initialization
# --------------------------
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
# SINGLE PAGE MODE
# --------------------------
if args.mode == "single":
    page_id = args.page
    page_name = myModules.get_page_name(atlassian_site, page_id, user_name, api_token)
    my_body_export_view = myModules.get_body_export_view(atlassian_site, page_id, user_name, api_token).json()
    my_body_export_view_html = my_body_export_view["body"]["export_view"]["value"]
    my_body_export_view_title = my_body_export_view["title"].replace("/", "-").replace(",", "").replace("&", "And").replace(":", "-")

    page_parent = myModules.get_page_parent(atlassian_site, page_id, user_name, api_token)
    my_outdir_base = os.path.join(my_outdir_base, f"{page_id}-{my_body_export_view_title}")
    my_outdir_content = my_outdir_base

    myModules.mk_outdirs(my_outdir_base)
    my_page_labels = myModules.get_page_labels(atlassian_site, page_id, user_name, api_token)
    print(f'Base export folder is "{my_outdir_base}" and the Content goes to "{my_outdir_content}"')

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

    # ADDED STEP 4: Call the text extraction function if requested
    if args.text:
        text_filepath = os.path.join(my_outdir_base, f"{my_body_export_view_title}.txt")
        save_plain_text(my_body_export_view_html, text_filepath)

    print("Done!")

# --------------------------
# SPACE MODE
# --------------------------
elif args.mode == 'space':
    ###########
    ## SPACE ##
    ###########
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
            my_body_export_view_title = p['title'].replace("/","-").replace(",","").replace("&","And").replace(" ","_")
            
            print(f"\nGetting page #{page_counter}/{len(all_pages_full)}, {my_body_export_view_title}, {p['id']}")

            ### CORRECTED LOGIC SECTION FOR 'space' MODE ###
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
                # It will create .rst and/or .html files as requested
                my_body_export_view_labels = myModules.get_page_labels(atlassian_site,p['id'],user_name,api_token)
                myModules.dump_html(atlassian_site,my_body_export_view_html,my_body_export_view_title,p['id'],my_outdir_base,my_outdir_content,my_body_export_view_labels,p['parentId'],user_name,api_token,sphinx_compatible,sphinx_tags,arg_html_output=args.html,arg_rst_output=args.rst)
                
                # The --text flag can still be used to add a .txt file to the normal export
                if args.text:
                    text_filepath = os.path.join(my_outdir_content, f"{my_body_export_view_title}.txt")
                    save_plain_text(my_body_export_view_html, text_filepath)

    print("Done!")

# --------------------------
# PAGEPROPS MODE
# --------------------------
elif args.mode == "pageprops":
    page_id = args.page
    print("Getting Page Properties Report Details")

    report = myModules.get_body_export_view(atlassian_site, page_id, user_name, api_token).json()
    report_title = report["title"].replace("/", "-").replace(",", "").replace("&", "And").replace(":", "-")
    report_html = report["body"]["export_view"]["value"]

    my_outdir_content = os.path.join(my_outdir_base, f"{page_id}-{report_title}")
    if not args.sphinx:
        my_outdir_base = my_outdir_content

    myModules.mk_outdirs(my_outdir_base)
    children, children_dict = myModules.get_page_properties_children(atlassian_site, report_html, my_outdir_content, user_name, api_token)

    for i, child_id in enumerate(children, start=1):
        child = myModules.get_body_export_view(atlassian_site, child_id, user_name, api_token).json()
        child_html = child["body"]["export_view"]["value"]
        child_title = child["title"]

        print(f"Getting Child page #{i}/{len(children)}: {child_title} ({child_id})")

        if not args.no_output:
            # This block runs normally to create page files
            myModules.dump_html(
                arg_site=atlassian_site,
                arg_html=child_html,
                arg_title=child_title,
                arg_page_id=child_id,
                arg_outdir_base=my_outdir_base,
                arg_outdir_content=my_outdir_content,
                arg_page_labels=myModules.get_page_labels(atlassian_site, child_id, user_name, api_token),
                arg_page_parent=myModules.get_page_parent(atlassian_site, child_id, user_name, api_token),
                arg_username=user_name,
                arg_api_token=api_token,
                arg_sphinx_compatible=sphinx_compatible,
                arg_sphinx_tags=sphinx_tags,
                arg_type="reportchild",
                arg_html_output=args.html,
                arg_rst_output=args.rst,
                arg_show_labels=args.showlabels,
            )

            if args.text:
                text_filename = f"{child_title}.txt".replace(":", "-").replace(" ", "_")
                text_filepath = os.path.join(my_outdir_content, text_filename)
                save_plain_text(child_html, text_filepath)
        else:
            # This block runs in --no-output mode to download attachments only
            print("  --no-output flag set. Downloading attachments only.")
            attach_dir = myModules.set_dirs(my_outdir_base)[0] # Get the attachment dir path
            myModules.get_attachments(atlassian_site, child_id, attach_dir, user_name, api_token)


    # Process the main report page after the loop
    print(f"\nProcessing main report page: {report_title}")

    ### MODIFIED SECTION FOR THE MAIN REPORT PAGE ###
    if not args.no_output:
        # This block runs normally to create the report's page files
        myModules.dump_html(
            arg_site=atlassian_site,
            arg_html=report_html,
            arg_title=report_title,
            arg_page_id=page_id,
            arg_outdir_base=my_outdir_base,
            arg_outdir_content=my_outdir_content,
            arg_page_labels=myModules.get_page_labels(atlassian_site, page_id, user_name, api_token),
            arg_page_parent=myModules.get_page_parent(atlassian_site, page_id, user_name, api_token),
            arg_username=user_name,
            arg_api_token=api_token,
            arg_sphinx_compatible=sphinx_compatible,
            arg_sphinx_tags=sphinx_tags,
            arg_type="report",
            arg_html_output=args.html,
            arg_rst_output=args.rst,
            arg_show_labels=args.showlabels,
        )

        if args.text:
            text_filepath = os.path.join(my_outdir_content, f"{report_title}.txt")
            save_plain_text(report_html, text_filepath)
    else:
        # This block runs in --no-output mode for the main report page
        print("  --no-output flag set. Downloading attachments only for the report page.")
        attach_dir = myModules.set_dirs(my_outdir_base)[0] # Get the attachment dir path
        myModules.get_attachments(atlassian_site, page_id, attach_dir, user_name, api_token)

    print("Done!")

# --------------------------
# NO MODE
# --------------------------
else:
    print("No script mode defined in the command line")
