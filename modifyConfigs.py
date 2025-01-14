import requests
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape
from collections import OrderedDict
import sys
import warnings
from requests.exceptions import RequestException
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from concurrent.futures import ThreadPoolExecutor, as_completed

warnings.simplefilter("ignore", InsecureRequestWarning)


def process_camera(camera, verify_url):
    camera_info = {
        'name': camera.get('name'),
        'type': camera.get('type'),
        'url': camera.get('url'),
        'camInstance': camera.get('camInstance'),
        'username': camera.get('username'),
        'password': camera.get('password'),
        'enabled': camera.get('enabled'),
        'setNames': camera.get('setNames'),
        'bitOptions': camera.get('bitOptions'),
    }
    identifier = (camera_info['name'], camera_info['url'])

    if verify_url and camera_info['type'].split()[0] != 'Traffic':
        successful_status = (200, 302, 301)
        try:
            response = requests.head(camera_info['url'], timeout=3, verify=False)
            successful_status = (200, 302, 301, 406)
            if response.status_code in successful_status:
                return identifier, camera_info
            else:
                raise RequestException("Non successful response from url")
        except RequestException as e:
            print(f"URL {camera_info['url']} request failed with: {e}")
            return None
    else:
        return identifier, camera_info


def parse_and_deduplicate_xml(file_path, verify_url):
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        unique_cameras = {}

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {
                executor.submit(process_camera, camera, verify_url): camera
                for camera in root.findall('camera')
                if (camera.get('name'), camera.get('url')) not in unique_cameras.keys()
            }

            for future in as_completed(futures):
                result = future.result()
                if result:
                    identifier, camera_info = result
                    unique_cameras[identifier] = camera_info

        return unique_cameras
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return []
    except ET.ParseError:
        print(f"Error: Failed to parse XML from file '{file_path}'.")
        return []


def write_to_xml(cameras, output_file):
    cameras = OrderedDict(sorted(cameras.items()))

    with open(output_file, 'w', encoding="utf-8") as f:
        f.write("<cameras>\n")
        for key, cam in cameras.items():
            attributes = " ".join(
                f'{key}="{escape(value if value is not None else "")}"'
                for key, value in cam.items()
            )
            f.write(f"<camera {attributes} />\n")
        f.write("</cameras>\n")


def main():
    if len(sys.argv) != 3:
        print('Usage: python modifyConfigs.py /path/to/cameras_config.xml/ verify(t/f)')
        sys.exit(1)

    file_path = sys.argv[1]
    verify_url = True if sys.argv[2] == 't' else False
    output_file = 'deduplicatedCameras.xml'

    unique_cameras = parse_and_deduplicate_xml(file_path, verify_url)

    if unique_cameras:
        write_to_xml(unique_cameras, output_file)
    else:
        print("No cameras found or an error occurred.")


if __name__ == "__main__":
    main()
