#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
import time
import random
import requests
import urllib3
import json 

from walkoff_app_sdk.app_base import AppBase

class Splunk(AppBase):
    """
    Splunk integration for WALKOFF with some basic features
    """
    __version__ = "1.0.0"
    app_name = "splunk"

    def __init__(self, redis, logger, console_logger=None):
        """
        Each app should have this __init__ to set up Redis and logging.
        :param redis:
        :param logger:
        :param console_logger:
        """
        self.verify = False
        self.timeout = 10
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        super().__init__(redis, logger, console_logger)

    def echo(self, input_data):
        return input_data 

    def run_search(self, auth, url, query):
        url = f'{url}/services/search/jobs?output_mode=json'
        return requests.post(
            url, auth=auth, data=query, timeout=self.timeout, verify=False
        )

    def get_search(self, auth, url, search_sid):
        # Wait for search to be done?
        firsturl = f'{url}/services/search/jobs/{search_sid}?output_mode=json'
        print(f"STARTED FUNCTION WITH URL {firsturl}")
        time.sleep(0.2)
        maxrunduration = 30
        ret = "No results yet"
        while True:
            try:
                ret = requests.get(firsturl, auth=auth, timeout=self.timeout, verify=False)
            except requests.exceptions.ConnectionError:
                print("Sleeping for 1 second")
                time.sleep(1)
                continue

            try:
                content = ret.json()["entry"][0]["content"]
            except KeyError as e:
                print("\nKEYERROR: %s\n" % content)
                time.sleep(1)
                continue

            try:
                if content["resultCount"] > 0 or content["isDone"] or content["isFinalized"] or content["runDuration"] > maxrunduration:
                    print("CONTENT PRE EVENTS: ", content)
                    eventsurl = f'{url}/services/search/jobs/{search_sid}/events'
                    print(f"Running events check towards {eventsurl}")
                    try:
                        newret = requests.get(eventsurl, auth=auth, timeout=self.timeout, verify=False)
                        if ret.status_code < 300 and ret.status_code >= 200:
                            return newret.text
                        else:
                            return "Bad status code for events: %sd", ret.status_code
                    except requests.exceptions.ConnectionError:
                        return f"Events requesterror: {e}"
            except KeyError:
                try:
                    return ret.json()["messages"]
                except KeyError as e:
                    return f"KeyError: {e}"

            time.sleep(1)

        return ret

    def SplunkQuery(self, url, username, password, query, result_limit=100, earliest_time="-24h", latest_time="now"):
        auth = (username, password)

        # "latest_time": "now"
        query = {
            "search": f"| search {query}",
            "exec_mode": "normal",
            "count": result_limit,
            "earliest_time": earliest_time,
            "latest_time": latest_time,
        }


        print(f'Current search: {query["search"]}')

        try:
            ret = self.run_search(auth, url, query)
        except requests.exceptions.ConnectTimeout as e:
            print(f"Timeout: {e}")
            return f"Timeout: {e}"

        if ret.status_code != 201:
            print("Bad status code: %d" % ret.status_code)
            return "Bad status code: %d" % ret.status_code

        search_id = ret.json()["sid"]

        print(f"Search ID: {search_id}")

        ret = self.get_search(auth, url, search_id)
        return ret
        #if len(ret.json()["entry"]) == 1:
        #    count = ret.json()["entry"][0]["content"]["resultCount"]
        #    print("Result: %d" % count)
        #    return str(count)

        #print("No results (or wrong?): %d" % (len(ret.json()["entry"])))
        #return "No results"
        
if __name__ == "__main__":
    Splunk.run()
