#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path('/Users/kuruth/work/yt-core')
VERSIONS_DIR = ROOT / 'alembic' / 'cmp' / 'versions'

CREATE_TABLE_RE = re.compile(r"op\.create_table\(\s*['\"]([^'\"]+)['\"]", re.S)
DROP_TABLE_RE = re.compile(r"op\.drop_table\(\s*['\"]([^'\"]+)['\"]")
ADD_COLUMN_RE = re.compile(r"op\.add_column\(\s*['\"]([^'\"]+)['\"]\s*,\s*sa\.Column\(\s*['\"]([^'\"]+)['\"]", re.S)
DROP_COLUMN_RE = re.compile(r"op\.drop_column\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"]([^'\"]+)['\"]")
ALTER_COLUMN_RE = re.compile(r"op\.alter_column\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"]([^'\"]+)['\"](.*?)\)", re.S)
REVISION_RE = re.compile(r"revision:\s*str\s*=\s*['\"]([^'\"]+)['\"]")
MESSAGE_RE = re.compile(r'^"""(.*?)\n', re.S)
UPGRADE_BLOCK_RE = re.compile(r"def upgrade\(\) -> None:\n(.*?)(?:\n\ndef downgrade\(\) -> None:|\Z)", re.S)


def parse_args():
    parser = argparse.ArgumentParser(description='Summarize DB table/column changes from Alembic migration files by date.')
    parser.add_argument('--date', help='Target date in YYYY-MM-DD. Defaults to yesterday in local time.')
    parser.add_argument('--dir', default=str(VERSIONS_DIR), help='Alembic versions directory')
    return parser.parse_args()


def target_date(value: str | None) -> dt.date:
    if value:
        return dt.date.fromisoformat(value)
    return dt.date.today() - dt.timedelta(days=1)


def extract_upgrade_block(text: str) -> str:
    match = UPGRADE_BLOCK_RE.search(text)
    return match.group(1) if match else text


def parse_file(path: Path):
    text = path.read_text(encoding='utf-8')
    upgrade_text = extract_upgrade_block(text)
    message_match = MESSAGE_RE.search(text)
    revision_match = REVISION_RE.search(text)
    summary = {
        'file': path.name,
        'revision': revision_match.group(1) if revision_match else path.stem.split('_', 1)[0],
        'message': message_match.group(1).strip() if message_match else path.stem,
        'created_tables': CREATE_TABLE_RE.findall(upgrade_text),
        'dropped_tables': DROP_TABLE_RE.findall(upgrade_text),
        'added_columns': ADD_COLUMN_RE.findall(upgrade_text),
        'dropped_columns': DROP_COLUMN_RE.findall(upgrade_text),
        'altered_columns': [],
    }

    for table, column, tail in ALTER_COLUMN_RE.findall(upgrade_text):
        changes = []
        if 'existing_type=' in tail or 'type_=' in tail:
            changes.append('type')
        if 'nullable=' in tail:
            changes.append('nullable')
        if 'server_default=' in tail:
            changes.append('server_default')
        if not changes:
            changes.append('other')
        summary['altered_columns'].append((table, column, ', '.join(sorted(set(changes)))))
    return summary


def collect(date_value: dt.date, versions_dir: Path):
    files = []
    for path in sorted(versions_dir.glob('*.py')):
        file_date = dt.datetime.fromtimestamp(path.stat().st_mtime).date()
        if file_date == date_value:
            files.append(path)
    return files


def format_report(date_value: dt.date, summaries: list[dict]) -> str:
    lines = []
    lines.append(f'# DB 变更统计 - {date_value.isoformat()}')
    lines.append('')
    if not summaries:
        lines.append('当天没有匹配到 Alembic 迁移文件。')
        return '\n'.join(lines)

    created_tables = []
    dropped_tables = []
    table_changes = defaultdict(lambda: {'add': [], 'drop': [], 'alter': []})

    for item in summaries:
        created_tables.extend(item['created_tables'])
        dropped_tables.extend(item['dropped_tables'])
        for table, column in item['added_columns']:
            table_changes[table]['add'].append((column, item['file']))
        for table, column in item['dropped_columns']:
            table_changes[table]['drop'].append((column, item['file']))
        for table, column, change in item['altered_columns']:
            table_changes[table]['alter'].append((column, change, item['file']))

    lines.append('## 迁移文件')
    for item in summaries:
        lines.append(f"- `{item['file']}`: `{item['message']}` (revision `{item['revision']}`)")
    lines.append('')

    lines.append('## 新增表')
    if created_tables:
        for table in created_tables:
            lines.append(f'- `{table}`')
    else:
        lines.append('- 无')
    lines.append('')

    lines.append('## 删除表')
    if dropped_tables:
        for table in dropped_tables:
            lines.append(f'- `{table}`')
    else:
        lines.append('- 无')
    lines.append('')

    lines.append('## 表字段变更')
    if not table_changes:
        lines.append('- 无')
    else:
        for table in sorted(table_changes.keys()):
            lines.append(f'- `{table}`')
            for column, file_name in table_changes[table]['add']:
                lines.append(f'  - 新增字段: `{column}` (`{file_name}`)')
            for column, change, file_name in table_changes[table]['alter']:
                lines.append(f'  - 修改字段: `{column}` ({change}, `{file_name}`)')
            for column, file_name in table_changes[table]['drop']:
                lines.append(f'  - 删除字段: `{column}` (`{file_name}`)')
    lines.append('')
    return '\n'.join(lines)


def main():
    args = parse_args()
    date_value = target_date(args.date)
    versions_dir = Path(args.dir)
    files = collect(date_value, versions_dir)
    summaries = [parse_file(path) for path in files]
    print(format_report(date_value, summaries))


if __name__ == '__main__':
    main()
