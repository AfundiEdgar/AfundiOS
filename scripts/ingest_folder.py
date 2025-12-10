import argparse
import requests
from pathlib import Path

API_URL_DEFAULT = "http://localhost:8000/ingest"


def main(folder: str, api_url: str):
    folder_path = Path(folder)
    for path in folder_path.rglob("*"):
        if path.is_file():
            files = {"file": (path.name, path.read_bytes())}
            data = {"source_url": ""}
            resp = requests.post(api_url, data=data, files=files)
            print(path, resp.status_code, resp.text)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("folder")
    parser.add_argument("--api-url", default=API_URL_DEFAULT)
    args = parser.parse_args()
    main(args.folder, args.api_url)
