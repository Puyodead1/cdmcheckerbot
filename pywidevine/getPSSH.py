import requests
import xmltodict
import json
import os
import subprocess
import binascii
import base64
from pywidevine.cdm.formats import widevine_pssh_data_pb2


def get_pssh(mpd_url):
    r = requests.get(url=mpd_url)
    r.raise_for_status()
    xml = xmltodict.parse(r.text)
    mpd = json.loads(json.dumps(xml))
    tracks = mpd['MPD']['Period']['AdaptationSet']
    for video_tracks in tracks:
        if video_tracks['@mimeType'] == 'video/mp4':
            for t in video_tracks["ContentProtection"]:
                if t['@schemeIdUri'].lower() == "urn:uuid:edef8ba9-79d6-4ace-a3c8-27dcd51d21ed":
                    pssh = t["cenc:pssh"]
    return pssh


def get_pssh_from_file(mp4_file):
    currentFile = __file__
    realPath = os.path.realpath(currentFile)
    dirPath = os.path.dirname(realPath)
    dirName = os.path.basename(dirPath)
    mp4dump = "mp4dump"
    WV_SYSTEM_ID = '[ed ef 8b a9 79 d6 4a ce a3 c8 27 dc d5 1d 21 ed]'
    pssh = None
    data = subprocess.check_output(
        [mp4dump, '--format', 'json', '--verbosity', '1', mp4_file])
    data = json.loads(data)
    for atom in data:
        if atom['name'] == 'moov':
            for child in atom['children']:
                if child['name'] == 'pssh' and child['system_id'] == WV_SYSTEM_ID:
                    pssh = child['data'][1:-1].replace(' ', '')
                    pssh = binascii.unhexlify(pssh)
                    # if pssh.startswith('\x08\x01'):
                    #   pssh = pssh[0:]
                    pssh = pssh[0:]
                    pssh = base64.b64encode(pssh).decode('utf-8')
                    return pssh


def extract_kid(pssh_data):
    pssh = widevine_pssh_data_pb2.WidevinePsshData()
    pssh.ParseFromString(pssh_data)

    content_id = base64.b16encode(pssh.key_id[0])
    return content_id.decode("utf-8").lower()
