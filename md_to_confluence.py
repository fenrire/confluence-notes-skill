#!/usr/bin/env python3
"""Convert markdown files to Confluence storage format and upload."""

import re
import html


def md_to_confluence(md_text):
    """Convert markdown to Confluence XHTML storage format."""
    # Remove YAML frontmatter
    md_text = re.sub(r'^---\n.*?\n---\n*', '', md_text, flags=re.DOTALL)

    lines = md_text.split('\n')
    result = []
    i = 0
    in_list = None  # 'ul' or 'ol'
    list_stack = []  # track nested lists

    def close_lists():
        nonlocal list_stack
        output = []
        while list_stack:
            output.append(f'</{list_stack.pop()}>')
        return output

    while i < len(lines):
        line = lines[i]

        # Code block
        if line.strip().startswith('```'):
            result.extend(close_lists())
            lang_match = re.match(r'```(\w*)', line.strip())
            lang = lang_match.group(1) if lang_match else ''
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code_lines.append(lines[i])
                i += 1
            code_content = '\n'.join(code_lines)
            if lang:
                result.append(
                    f'<ac:structured-macro ac:name="code">'
                    f'<ac:parameter ac:name="language">{lang}</ac:parameter>'
                    f'<ac:plain-text-body><![CDATA[{code_content}]]></ac:plain-text-body>'
                    f'</ac:structured-macro>'
                )
            else:
                result.append(
                    f'<ac:structured-macro ac:name="code">'
                    f'<ac:plain-text-body><![CDATA[{code_content}]]></ac:plain-text-body>'
                    f'</ac:structured-macro>'
                )
            i += 1
            continue

        # Table
        if '|' in line and line.strip().startswith('|'):
            result.extend(close_lists())
            table_lines = []
            while i < len(lines) and '|' in lines[i] and lines[i].strip().startswith('|'):
                table_lines.append(lines[i])
                i += 1
            result.append(convert_table(table_lines))
            continue

        # Headings
        heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if heading_match:
            result.extend(close_lists())
            level = len(heading_match.group(1))
            text = convert_inline(heading_match.group(2))
            result.append(f'<h{level}>{text}</h{level}>')
            i += 1
            continue

        # Blockquote
        if line.strip().startswith('>'):
            result.extend(close_lists())
            quote_lines = []
            while i < len(lines) and lines[i].strip().startswith('>'):
                quote_lines.append(re.sub(r'^>\s*', '', lines[i]))
                i += 1
            quote_text = convert_inline(' '.join(quote_lines))
            result.append(f'<blockquote><p>{quote_text}</p></blockquote>')
            continue

        # Horizontal rule
        if re.match(r'^---+$', line.strip()):
            result.extend(close_lists())
            result.append('<hr />')
            i += 1
            continue

        # Unordered list
        ul_match = re.match(r'^(\s*)[-*]\s+(.+)$', line)
        if ul_match:
            if not list_stack:
                result.append('<ul>')
                list_stack.append('ul')
            text = convert_inline(ul_match.group(2))
            result.append(f'<li>{text}</li>')
            i += 1
            continue

        # Ordered list
        ol_match = re.match(r'^(\s*)\d+\.\s+(.+)$', line)
        if ol_match:
            if not list_stack:
                result.append('<ol>')
                list_stack.append('ol')
            text = convert_inline(ol_match.group(2))
            result.append(f'<li>{text}</li>')
            i += 1
            continue

        # Empty line
        if not line.strip():
            result.extend(close_lists())
            i += 1
            continue

        # Regular paragraph
        result.extend(close_lists())
        para_lines = [line]
        i += 1
        while i < len(lines) and lines[i].strip() and not lines[i].startswith('#') \
                and not lines[i].startswith('```') and not lines[i].startswith('>') \
                and not re.match(r'^[-*]\s+', lines[i]) and not re.match(r'^\d+\.\s+', lines[i]) \
                and not (lines[i].strip().startswith('|') and '|' in lines[i]) \
                and not re.match(r'^---+$', lines[i].strip()):
            para_lines.append(lines[i])
            i += 1
        text = convert_inline(' '.join(para_lines))
        result.append(f'<p>{text}</p>')

    result.extend(close_lists())
    return '\n'.join(result)


def convert_inline(text):
    """Convert inline markdown to HTML."""
    # Escape HTML entities first (but preserve existing tags)
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    # Bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # Italic
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    # Inline code
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    # Links [text](url)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    # Obsidian wiki links [[text]]
    text = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', r'\2', text)
    text = re.sub(r'\[\[([^\]]+)\]\]', r'\1', text)

    return text


def convert_table(table_lines):
    """Convert markdown table to Confluence HTML table."""
    rows = []
    for line in table_lines:
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        rows.append(cells)

    if len(rows) < 2:
        return ''

    # Check if second row is separator
    is_separator = all(re.match(r'^[-:]+$', c.strip()) for c in rows[1] if c.strip())

    result = ['<table><tbody>']

    if is_separator and len(rows) >= 2:
        # Header row
        result.append('<tr>')
        for cell in rows[0]:
            result.append(f'<th>{convert_inline(cell)}</th>')
        result.append('</tr>')
        # Data rows
        for row in rows[2:]:
            result.append('<tr>')
            for cell in row:
                result.append(f'<td>{convert_inline(cell)}</td>')
            result.append('</tr>')
    else:
        for row in rows:
            result.append('<tr>')
            for cell in row:
                result.append(f'<td>{convert_inline(cell)}</td>')
            result.append('</tr>')

    result.append('</tbody></table>')
    return ''.join(result)


def get_title_from_md(md_text):
    """Extract H1 title from markdown."""
    md_text = re.sub(r'^---\n.*?\n---\n*', '', md_text, flags=re.DOTALL)
    match = re.search(r'^#\s+(.+)$', md_text, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return None


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python md_to_confluence.py <file.md>")
        sys.exit(1)

    with open(sys.argv[1], encoding='utf-8') as f:
        md = f.read()

    title = get_title_from_md(md)
    body = md_to_confluence(md)
    print(f"TITLE: {title}")
    print(f"BODY_LENGTH: {len(body)}")
    print("---")
    print(body)
