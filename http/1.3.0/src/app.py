import time
import json
import ast
import random
import socket
import uncurl
import asyncio
import requests
import subprocess

from walkoff_app_sdk.app_base import AppBase

class HTTP(AppBase):
    __version__ = "1.3.0"
    app_name = "http"  

    def __init__(self, redis, logger, console_logger=None):
        print("INIT")
        """
        Each app should have this __init__ to set up Redis and logging.
        :param redis:
        :param logger:
        :param console_logger:
        """
        super().__init__(redis, logger, console_logger)

    # This is dangerously fun :)
    # Do we care about arbitrary code execution here?
    def curl(self, statement):
        process = subprocess.Popen(statement, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
        stdout = process.communicate()
        item = ""
        if len(stdout[0]) > 0:
            print("Succesfully ran bash!")
            item = stdout[0]
        else:
            print("FAILED to run bash!")
            item = stdout[1]

        try:
            return item.decode("utf-8")
        except:
            return item

        return item
        #try: 
        #    if not statement.startswith("curl "):
        #        statement = "curl %s" % statement

        #    data = uncurl.parse(statement)
        #    request = eval(data)
        #    if isinstance(request, requests.models.Response):
        #        return request.text
        #    else:
        #        return "Unable to parse the curl parameter. Remember to start with curl "
        #except:
        #    return "An error occurred during curl parsing"

    def splitheaders(self, headers):
        parsed_headers = {}
        if headers:
            split_headers = headers.split("\n")
            self.logger.info(split_headers)
            for header in split_headers:
                if ": " in header:
                    splititem = ": "
                elif ":" in header:
                    splititem = ":"
                elif "= " in header:
                    splititem = "= "
                elif "=" in header:
                    splititem = "="
                else:
                    self.logger.info(f"Skipping header {header} as its invalid")
                    continue

                splitheader = header.split(splititem)
                if len(splitheader) == 2:
                    parsed_headers[splitheader[0]] = splitheader[1]
                else:
                    self.logger.info(
                        f"Skipping header {header} with split {splititem} cus only one item"
                    )

                    continue

        return parsed_headers

    def checkverify(self, verify):
        if str(verify).lower().strip() == "false":
            return False
        elif verify is None:
            return False
        elif verify:
            return True
        else:
            return False 

    def checkbody(self, body):
        # Indicates json
        if isinstance(body, str):
            if body.strip().startswith("{"):
                body = json.dumps(ast.literal_eval(body))


            # Not sure if loading is necessary
            # Seemed to work with plain string into data=body too, and not parsed json=body
            #try:
            #    body = json.loads(body)
            #except json.decoder.JSONDecodeError as e:
            #    return body

            return body
        if isinstance(body, (dict, list)):
            try:
                body = json.dumps(body)
            except:
                return body

        return body

    def fix_url(self, url):
        # Random bugs seen by users
        if "hhttp" in url:
            url = url.replace("hhttp", "http")

        if "http:/" in url and "http://" not in url:
            url = url.replace("http:/", "http://", -1)
        if "https:/" in url and "https://" not in url:
            url = url.replace("https:/", "https://", -1)
        if "http:///" in url:
            url = url.replace("http:///", "http://", -1)
        if "https:///" in url:
            url = url.replace("https:///", "https://", -1)
        if "http://" not in url and "http" not in url:
            url = f"http://{url}" 

        return url

    def return_file(self, requestdata):
        filedata = {
            "filename": "response.txt",
            "data": requestdata,
        }
        fileret = self.set_files([filedata])
        if len(fileret) == 1:
            return {"success": True, "file_id": fileret[0]}

        return fileret
            
    def prepare_response(self, request):
        try:
            parsedheaders = dict(request.headers.items())
            cookies = {}
            if request.cookies:
                for key, value in request.cookies.items():
                    cookies[key] = value


            jsondata = request.text
            try:
                jsondata = json.loads(jsondata)
            except:
                pass

            return json.dumps({
                "success": True,
                "status": request.status_code,
                "url": request.url,
                "headers": parsedheaders,
                "body": jsondata,
                "cookies":cookies,
            })
        except Exception as e:
            print(f"[WARNING] Failed in request: {e}")
            return request.text

    def GET(self, url, headers="", username="", password="", verify=True, http_proxy="", https_proxy="", timeout=5, to_file=False):
        url = self.fix_url(url)

        parsed_headers = self.splitheaders(headers)
        parsed_headers["User-Agent"] = "Shuffle Automation"
        verify = self.checkverify(verify)
        proxies = None
        if http_proxy: 
            proxies["http"] = http_proxy
        if https_proxy: 
            proxies["https"] = https_proxy

        if username or password:
            auth = requests.auth.HTTPBasicAuth(username, password)
        else:
            auth = None
        if not timeout:
            timeout = 5
        if timeout:
            timeout = int(timeout)

        to_file = to_file == "true"
        request = requests.get(url, headers=parsed_headers, auth=auth, verify=verify, proxies=proxies, timeout=timeout)
        return (
            self.return_file(request.text)
            if to_file
            else self.prepare_response(request)
        )

    def POST(self, url, headers="", body="", username="", password="", verify=True, http_proxy="", https_proxy="", timeout=5, to_file=False):
        url = self.fix_url(url)

        parsed_headers = self.splitheaders(headers)
        parsed_headers["User-Agent"] = "Shuffle Automation"
        verify = self.checkverify(verify)
        body = self.checkbody(body)
        proxies = None
        if http_proxy: 
            proxies["http"] = http_proxy
        if https_proxy: 
            proxies["https"] = https_proxy

        if username or password:
            auth = requests.auth.HTTPBasicAuth(username, password)
        else:
            auth = None
        if not timeout:
            timeout = 5
        if timeout:
            timeout = int(timeout)

        to_file = to_file == "true"
        request = requests.post(url, headers=parsed_headers, auth=auth, data=body, verify=verify, proxies=proxies, timeout=timeout)
        return (
            self.return_file(request.text)
            if to_file
            else self.prepare_response(request)
        )

    # UNTESTED BELOW HERE
    def PUT(self, url, headers="", body="", username="", password="", verify=True, http_proxy="", https_proxy="", timeout=5, to_file=False):
        url = self.fix_url(url)

        parsed_headers = self.splitheaders(headers)
        parsed_headers["User-Agent"] = "Shuffle Automation"
        verify = self.checkverify(verify)
        body = self.checkbody(body)
        proxies = None
        if http_proxy: 
            proxies["http"] = http_proxy
        if https_proxy: 
            proxies["https"] = https_proxy


        if username or password:
            auth = requests.auth.HTTPBasicAuth(username, password)
        else:
            auth = None
        if not timeout:
            timeout = 5
        if timeout:
            timeout = int(timeout)

        to_file = to_file == "true"
        request = requests.put(url, headers=parsed_headers, auth=auth, data=body, verify=verify, proxies=proxies, timeout=timeout)
        return (
            self.return_file(request.text)
            if to_file
            else self.prepare_response(request)
        )

    def PATCH(self, url, headers="", body="", username="", password="", verify=True, http_proxy="", https_proxy="", timeout=5, to_file=False):
        url = self.fix_url(url)

        parsed_headers = self.splitheaders(headers)
        parsed_headers["User-Agent"] = "Shuffle Automation"
        verify = self.checkverify(verify)
        body = self.checkbody(body)
        proxies = None
        if http_proxy: 
            proxies["http"] = http_proxy
        if https_proxy: 
            proxies["https"] = https_proxy

        if username or password:
            auth = requests.auth.HTTPBasicAuth(username, password)
        else:
            auth = None
        if not timeout:
            timeout = 5
        if timeout:
            timeout = int(timeout)

        to_file = to_file == "true"
        request = requests.patch(url, headers=parsed_headers, data=body, auth=auth, verify=verify, proxies=proxies, timeout=timeout)
        return (
            self.return_file(request.text)
            if to_file
            else self.prepare_response(request)
        )

    def DELETE(self, url, headers="", body="", username="", password="", verify=True, http_proxy="", https_proxy="", timeout=5, to_file=False):
        url = self.fix_url(url)

        parsed_headers = self.splitheaders(headers)
        parsed_headers["User-Agent"] = "Shuffle Automation"
        verify = self.checkverify(verify)
        proxies = None
        if http_proxy: 
            proxies["http"] = http_proxy
        if https_proxy: 
            proxies["https"] = https_proxy

        if username or password:
            auth = requests.auth.HTTPBasicAuth(username, password)
        else:
            auth = None
        if not timeout:
            timeout = 5
        if timeout:
            timeout = int(timeout)

        to_file = to_file == "true"
        request = requests.delete(url, headers=parsed_headers, auth=auth, verify=verify, proxies=proxies, timeout=timeout)
        return (
            self.return_file(request.text)
            if to_file
            else self.prepare_response(request)
        )

    def HEAD(self, url, headers="", body="", username="", password="", verify=True, http_proxy="", https_proxy="", timeout=5, to_file=False):
        url = self.fix_url(url)

        parsed_headers = self.splitheaders(headers)
        parsed_headers["User-Agent"] = "Shuffle Automation"
        verify = self.checkverify(verify)
        body = self.checkbody(body)
        proxies = None
        if http_proxy: 
            proxies["http"] = http_proxy
        if https_proxy: 
            proxies["https"] = https_proxy

        if username or password:
            auth = requests.auth.HTTPBasicAuth(username, password)
        else:
            auth = None
        if not timeout:
            timeout = 5
        if timeout:
            timeout = int(timeout)

        to_file = to_file == "true"
        request = requests.head(url, headers=parsed_headers, auth=auth, verify=verify, proxies=proxies, timeout=timeout)
        return (
            self.return_file(request.text)
            if to_file
            else self.prepare_response(request)
        )

    def OPTIONS(self, url, headers="", body="", username="", password="", verify=True, http_proxy="", https_proxy="", timeout=5, to_file=False):
        url = self.fix_url(url)

        parsed_headers = self.splitheaders(headers)
        parsed_headers["User-Agent"] = "Shuffle Automation"
        verify = self.checkverify(verify)
        body = self.checkbody(body)
        proxies = None
        if http_proxy: 
            proxies["http"] = http_proxy
        if https_proxy: 
            proxies["https"] = https_proxy

        if username or password:
            auth = requests.auth.HTTPBasicAuth(username, password)
        else:
            auth = None
        if not timeout:
            timeout = 5

        if timeout:
            timeout = int(timeout)

        to_file = to_file == "true"
        request = requests.options(url, headers=parsed_headers, auth=auth, verify=verify, proxies=proxies, timeout=timeout)
        return (
            self.return_file(request.text)
            if to_file
            else self.prepare_response(request)
        )


# Run the actual thing after we've checked params
def run(request):
    print("Starting cloud!")
    action = request.get_json()
    print(action)
    print(type(action))
    authorization_key = action.get("authorization")
    current_execution_id = action.get("execution_id")

    if action and "name" in action and "app_name" in action:
        HTTP.run(action)
        return f'Attempting to execute function {action["name"]} in app {action["app_name"]}'
    else:
        return 'Invalid action'

if __name__ == "__main__":
    HTTP.run()
