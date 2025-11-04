import requests, json
import os
import subprocess
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


if __name__ == '__main__':
    response = getAllChanges()
    urls =[]
    results_list = response.get("results")
    for data in results_list:
        urls.append(opswat_link + data["_links"]["webui"])
    
    for url in urls:
        command_list = [
            "python", 
            "confluenceDumpWithPython.py", 
            "--site", "opswat", 
            "--mode", "url", 
            "--url", url, 
        ]

        subprocess.run(command_list, check = True)
    process_all_files(
    r"C:\chatbot-sdk-implementations\Confluence Scrape\output",
    r"C:\chatbot-sdk-implementations\Confluence Scrape\processed confluence files"
    )



