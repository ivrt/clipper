import requests
import json
import time
import asyncio
import sys
import concurrent.futures

# from clipper_admin import ClipperConnection, KubernetesContainerManager

# Connect to clipper
# clipper_conn = ClipperConnection(KubernetesContainerManager())
# clipper_conn.connect()

# Get query address
# addr = clipper_conn.get_query_addr()
# print('Got query endpoint address: ', addr)

# Just set the current query address
addr = 'ec2-54-169-144-111.ap-southeast-1.compute.amazonaws.com:32211'

# Setup data for the requests
req_json = json.dumps({
    "input": "Each Party shall promptly notify the other Party of any unauthorized release of the Confidential Information."
})
headers = {"Content-type": "application/json"}
apps = ['dright-ownership-info', 'term-survival-clause','boiler-severability', 'rpo-stof-care', 'rpo-return', 'nda-right-to-indep-dev', 'boiler-waiver', 'boiler-ent-agmt', 'ci-def-list', 'rpo-notify-breach', 'disputes-remedy', 'rpo-disc-limits', 'term-definite', 'ci-std-except', 'rpo-non-use', 'boiler-variation', 'disputes-disp-reso', 'boiler-counterparts', 'boiler-no-partner']

def predict(index, app):
    try:
        t1 = time.time()
        endpoint = "http://" + addr + "/{0}/predict".format(app)
        print(endpoint, headers, req_json)
        response = requests.post(endpoint, headers=headers, data=req_json)
        print(response.content)
        print('{0} Query successful for {1} endpoint and completed in {2} seconds'.format(index, app, time.time() - t1))
    except requests.exceptions.RequestException as e:
        print(e)
        print('{0} Query failed for {1} endpoint.'.format(index, app))

async def getStuff():
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        loop = asyncio.get_event_loop()
        futures = [
            loop.run_in_executor(
                executor,
                predict,
                index,
                app
            )
            for index, app in enumerate(apps)
        ]
        for response in await asyncio.gather(*futures):
            pass


t0 = time.time()
loop = asyncio.get_event_loop()
loop.run_until_complete(getStuff())
t1 = time.time()
print("Analysis complete. ASYNC Query of {0} endpoints completed in {1} seconds.".format(len(apps), t1 - t0))
