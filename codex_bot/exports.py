from __future__ import annotations

import csv
import io
import json


def messages_to_markdown(title: str, messages: list[dict]) -> str:
    sections = [f"# {title}", ""]
    for message in messages:
        sections.extend((f"## {message['role'].title()}", "", message["content"], ""))
    return "\n".join(sections).rstrip() + "\n"


def messages_to_csv(messages: list[dict]) -> str:
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(("role", "content", "created_at"))
    for message in messages:
        writer.writerow((message["role"], message["content"], message.get("created_at", "")))
    return output.getvalue()


def marketing_content_to_markdown(records: list[dict]) -> str:
    sections = ["# Marketing content library", ""]
    for record in records:
        sections.extend(
            (
                f"## {record['title']}",
                "",
                f"- Type: {record['content_type']}",
                f"- Status: {record['status']}",
                f"- Created: {record.get('created_at', '')}",
                "",
                record["body"],
                "",
            )
        )
    return "\n".join(sections).rstrip() + "\n"


def marketing_content_to_csv(records: list[dict]) -> str:
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(("id", "content_type", "title", "status", "body", "brief", "created_at"))
    for record in records:
        writer.writerow(
            (
                record.get("id", ""),
                record["content_type"],
                record["title"],
                record["status"],
                record["body"],
                record.get("brief", ""),
                record.get("created_at", ""),
            )
        )
    return output.getvalue()


def records_to_json(records: list[dict]) -> str:
    return json.dumps(records, indent=2, ensure_ascii=False, default=str)

