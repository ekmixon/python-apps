import asyncio
import time
import random
import json
import requests
import json

from walkoff_app_sdk.app_base import AppBase

class Subflow(AppBase):
    """
    An example of a Walkoff App.
    Inherit from the AppBase class to have Redis, logging, and console logging set up behind the scenes.
    """
    __version__ = "1.0.0"
    app_name = "subflow"  # this needs to match "name" in api.yaml

    def __init__(self, redis, logger, console_logger=None):
        """
        Each app should have this __init__ to set up Redis and logging.
        :param redis:
        :param logger:
        :param console_logger:
        """
        super().__init__(redis, logger, console_logger)

    #def run_userinput(self, sms, email, subflow, argument):
    #    url = "%s/api/v1/workflows/%s/execute" % (self.url, workflow)

    #    if len(sms) > 0:

    def run_subflow(self, user_apikey, workflow, argument, source_workflow="", source_execution="", source_node="", source_auth="", startnode=""):
        print(f"STARTNODE: {startnode}")
        url = f"{self.url}/api/v1/workflows/{workflow}/execute"

        params = {}
        if str(source_workflow) != "":
            params["source_workflow"] = source_workflow
        else:
            print("No source workflow")

        if str(source_auth) != "":
            params["source_auth"] = source_auth
        else:
            print("No source auth")

        if str(source_node) != "":
            params["source_node"] = source_node
        else:
            print("No source node")

        if str(source_execution) != "":
            params["source_execution"] = source_execution
        else:
            print("No source execution")

        if str(startnode) != "":
            params["start"] = startnode
        else:
            print("No startnode")

        headers = {"Authorization": f"Bearer {user_apikey}"}

        if not str(argument):
            ret = requests.post(url, headers=headers, params=params)
        else:
            if not isinstance(argument, list) and not isinstance(argument, object) and not isinstance(argument, dict):
                try:
                    argument = json.loads(argument)
                except:
                    pass

            try:
                ret = requests.post(url, headers=headers, params=params, json=argument)
                print(f"Successfully sent argument of length {len(str(argument))} as JSON")
            except:
                try:
                    ret = requests.post(url, headers=headers, json=argument, params=params)
                    print("Successfully sent as JSON (2)")
                except:
                    ret = requests.post(url, headers=headers, data=argument, params=params)
                    print("Successfully sent as data (3)")

        print("Status: %d" % ret.status_code)
        print(f"RET: {ret.text}")

        return ret.text

if __name__ == "__main__":
    Subflow.run()
