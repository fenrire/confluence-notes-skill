#!/usr/bin/env python3
"""Confluence API helper for Claude Code skills.

Usage:
    python confluence_helper.py create --title "제목" --body "<h1>HTML내용</h1>"
    python confluence_helper.py update --page-id 123456 --title "제목" --body "<h1>HTML내용</h1>"
    python confluence_helper.py list
    python confluence_helper.py delete --page-id 123456

Environment variables required:
    CONFLUENCE_EMAIL        - Atlassian account email
    CONFLUENCE_API_TOKEN    - Atlassian API token
    CONFLUENCE_SITE         - Site URL (e.g. https://mycompany.atlassian.net/wiki)
    CONFLUENCE_SPACE_KEY    - Space key (e.g. DEV)
    CONFLUENCE_FOLDER_ID    - Parent folder/page ID for notes
"""

import argparse
import base64
import json
import os
import sys
import urllib.request
import urllib.error


def get_config():
    """Load configuration from environment variables."""
    required = {
        "CONFLUENCE_EMAIL": os.environ.get("CONFLUENCE_EMAIL", ""),
        "CONFLUENCE_API_TOKEN": os.environ.get("CONFLUENCE_API_TOKEN", ""),
        "CONFLUENCE_SITE": os.environ.get("CONFLUENCE_SITE", ""),
        "CONFLUENCE_SPACE_KEY": os.environ.get("CONFLUENCE_SPACE_KEY", ""),
        "CONFLUENCE_FOLDER_ID": os.environ.get("CONFLUENCE_FOLDER_ID", ""),
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        print(f"ERROR: Missing environment variables: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)
    return required


def get_auth(config):
    return base64.b64encode(
        f"{config['CONFLUENCE_EMAIL']}:{config['CONFLUENCE_API_TOKEN']}".encode()
    ).decode()


def api_request(config, path, method="GET", data=None):
    url = f"{config['CONFLUENCE_SITE']}{path}"
    headers = {
        "Authorization": f"Basic {get_auth(config)}",
        "Content-Type": "application/json; charset=utf-8",
    }
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(req)
        if resp.status == 204:
            return None
        return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        print(f"ERROR {e.code}: {error_body[:500]}", file=sys.stderr)
        sys.exit(1)


def create_page(title, body_html, config=None):
    if config is None:
        config = get_config()

    result = api_request(config, "/rest/api/content", method="POST", data={
        "type": "page",
        "title": title,
        "ancestors": [{"id": config["CONFLUENCE_FOLDER_ID"]}],
        "space": {"key": config["CONFLUENCE_SPACE_KEY"]},
        "body": {
            "storage": {
                "value": body_html,
                "representation": "storage",
            }
        },
    })
    page_id = result["id"]

    # Set full-width
    api_request(config, f"/rest/api/content/{page_id}/property", method="POST", data={
        "key": "content-appearance-published",
        "value": "full-width",
    })

    # Add label
    api_request(config, f"/rest/api/content/{page_id}/label", method="POST", data=[
        {"prefix": "global", "name": "claude-code"},
    ])

    web_url = f"{config['CONFLUENCE_SITE']}{result['_links']['webui']}"
    print(json.dumps({"id": page_id, "title": title, "url": web_url}))


def update_page(page_id, title, body_html, config=None):
    if config is None:
        config = get_config()

    current = api_request(config, f"/rest/api/content/{page_id}?expand=version")
    version = current["version"]["number"] + 1

    result = api_request(config, f"/rest/api/content/{page_id}", method="PUT", data={
        "type": "page",
        "title": title,
        "version": {"number": version},
        "body": {
            "storage": {
                "value": body_html,
                "representation": "storage",
            }
        },
    })

    web_url = f"{config['CONFLUENCE_SITE']}{result['_links']['webui']}"
    print(json.dumps({"id": page_id, "title": title, "url": web_url, "version": version}))


def list_pages(config=None):
    if config is None:
        config = get_config()

    result = api_request(
        config,
        f"/rest/api/content/{config['CONFLUENCE_FOLDER_ID']}/child/page"
        f"?limit=50&expand=version"
    )
    pages = []
    for page in result.get("results", []):
        pages.append({
            "id": page["id"],
            "title": page["title"],
            "version": page["version"]["number"],
        })
    print(json.dumps(pages, ensure_ascii=False))


def delete_page(page_id, config=None):
    if config is None:
        config = get_config()

    api_request(config, f"/rest/api/content/{page_id}", method="DELETE")
    print(json.dumps({"deleted": page_id}))


def main():
    parser = argparse.ArgumentParser(description="Confluence API helper")
    sub = parser.add_subparsers(dest="command", required=True)

    p_create = sub.add_parser("create")
    p_create.add_argument("--title", required=True)
    p_create.add_argument("--body", required=True)

    p_update = sub.add_parser("update")
    p_update.add_argument("--page-id", required=True)
    p_update.add_argument("--title", required=True)
    p_update.add_argument("--body", required=True)

    p_list = sub.add_parser("list")

    p_delete = sub.add_parser("delete")
    p_delete.add_argument("--page-id", required=True)

    args = parser.parse_args()

    if args.command == "create":
        create_page(args.title, args.body)
    elif args.command == "update":
        update_page(args.page_id, args.title, args.body)
    elif args.command == "list":
        list_pages()
    elif args.command == "delete":
        delete_page(args.page_id)


if __name__ == "__main__":
    main()
