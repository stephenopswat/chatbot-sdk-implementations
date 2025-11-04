import requests, json
import os
import sys
import subprocess
import concurrent.futures
from group import group
from preprocess_docs import process_all_files
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv()

opswat_link = "https://opswat.atlassian.net/wiki"

def getAllChanges():
    host = "https://opswat.atlassian.net"
    user_name = os.environ["atlassianUserEmail"]
    api_key = os.environ["atlassianAPIToken"]

    #Use this url to filter changes the last 10 days, with limit of up to 500 changes
    url = f"{host}/wiki/rest/api/content/search?cql=type%20in%20(page,blogpost)%20AND%20space%20%3D%20\"OES\"%20AND%20lastmodified%20%3E%20now(\"-10d\")%20order%20by%20lastmodified%20desc&limit=500"

    auth = HTTPBasicAuth(user_name, api_key)

    headers = {"Accept" : "application/json"}
    response = requests.request("GET", url, headers = headers, auth  =auth)

    data = response.json()
    return data

def runDownloadScript(url, python_exe, dump_script_path):
    command_list = [
        python_exe, 
        dump_script_path, 
        "--site", "opswat", 
        "--mode", "url", 
        "--url", url,
    ]
    
    try:
        result = subprocess.run(
            command_list, 
            check=True, 
            capture_output=True, 
            text=True, 
            encoding='utf-8'
        )
        # If successful, return the URL
        return f"[SUCCESS] {url}"
    except subprocess.CalledProcessError as e:
        # If it fails, return the error
        return f"[FAILED] {url} | Error: {e.stderr[:150]}..." # Show first 150 chars of error
    except FileNotFoundError:
        return f"[FAILED] {url} | Error: 'python' or 'confluenceDumpWithPython.py' not found."
    except Exception as e:
        return f"[FAILED] {url} | Error: {str(e)}"

if __name__ == '__main__':
    response = getAllChanges()
    urls =[]
    results_list = response.get("results")
    
    if not results_list:
        print("No changes made for the past 10 days, pausing the program")
        sys.exit()
    
    for data in results_list:
        urls.append(opswat_link + data["_links"]["webui"])
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dump_script_path = os.path.join(script_dir, "confluenceDumpWithPython.py")
    python_exe = sys.executable

    MAX_CONCURRENT_DOWNLOADS = 20

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT_DOWNLOADS) as executor:
        futures = {
            executor.submit(runDownloadScript, url, python_exe, dump_script_path): url for url in urls
        }

        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            print(result) # Print the "[SUCCESS]..." or "[FAILED]..." message


    process_all_files(
    r"C:\chatbot-sdk-implementations\Confluence Scrape\output",
    r"C:\chatbot-sdk-implementations\Confluence Scrape\processed confluence files"
    )
    group(r"C:\chatbot-sdk-implementations\Confluence Scrape\processed confluence files")



