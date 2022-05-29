import base64
import json
from pprint import pprint

import requests

from pywidevine.decrypt.wvdecryptcustom import WvDecrypt

url = "https://lic.staging.drmtoday.com/license-proxy-widevine/cenc/?assetId=agent-327"


init_data = "AAAAaXBzc2gAAAAA7e+LqXnWSs6jyCfc1R0h7QAAAEkIARIQb2sbmIT4PQuGahvYrKOQ0hoIY2FzdGxhYnMiIGV5SmhjM05sZEVsa0lqb2lZV2RsYm5RdE16STNJbjA9MgdkZWZhdWx0"
# wvdecrypt = WvDecrypt(init_data_b64=init_data, cert_data_b64=None,
#                       device=deviceconfig.device_LenovoTB_X605L_9404_l1)
# data = wvdecrypt.get_challenge()
# print(base64.b64encode(data).decode("utf8"))

# data = base64.b64decode("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")

client_id_file = open("device_client_id_blob", 'rb')
client_id = client_id_file.read()
client_id_file.close()

private_key_file = open("device_private_key", 'rb')
private_key = private_key_file.read()
private_key_file.close()

wvdecrypt = WvDecrypt(init_data_b64=init_data, cert_data_b64=None,
                      device_client_id=client_id, device_private_key=private_key)

data = wvdecrypt.get_challenge()
print(base64.b64encode(data).decode("utf8"))

HEADERS = {
    "dt-custom-data":  base64.b64encode(json.dumps({
        "userId": "purchase",
        "sessionId": "default",
        "merchant": "client_dev",
    }).encode()).decode()
}
response = requests.post(url, data=data, headers=HEADERS)
if not response.ok:
    print(response.headers.get("x-dt-resp-code"))
    raise Exception(f"Failed: [{response.status_code}] {response.text}")

data = response.json()
pprint(data, indent=4)
print(response.headers.get("x-dt-resp-code"))
