---
name: confluence-notes
description: Claude Code 학습 내용을 Confluence에 페이지로 저장합니다
argument-hint: <제목> 또는 <제목> <간단한 설명>
---

# /confluence-notes 스킬

## 역할
현재 대화에서 작성된 내용을 Confluence 부모 페이지 아래에 하위 페이지로 저장합니다.

## 환경변수 (필수)
- `CONFLUENCE_EMAIL` — Atlassian 계정 이메일
- `CONFLUENCE_API_TOKEN` — Atlassian API 토큰
- `CONFLUENCE_SITE` — 사이트 URL (예: `https://mycompany.atlassian.net/wiki`)
- `CONFLUENCE_SPACE_KEY` — Space Key (예: `DEV`)
- `CONFLUENCE_PARENT_ID` — 노트를 저장할 부모 페이지 ID

## 스크립트 경로
이 스킬의 헬퍼 스크립트는 SKILL.md와 같은 폴더에 있습니다:
- `confluence_helper.py` — Confluence REST API 호출
- `md_to_confluence.py` — 마크다운 → Confluence Storage Format 변환

스크립트 경로는 `$(dirname "$0")` 또는 SKILL.md가 있는 디렉토리 기준으로 참조합니다.

## 처리 순서

사용자 입력: $ARGUMENTS

1. **$ARGUMENTS 해석**
   - 제목이 주어진 경우: 해당 제목으로 페이지 생성 대상 설정
   - 제목 없이 내용만 있는 경우: 적절한 한국어 제목을 제안하고 확인
   - 아무것도 없는 경우: 현재 대화에서 문서화할 내용이 있는지 확인

2. **기존 페이지 검색**
   - `python <스킬경로>/confluence_helper.py list` 실행하여 기존 페이지 목록 확인
   - 제목 기반으로 주제가 겹치는 페이지가 있는지 탐색
   - **유사 페이지 발견 시**: 사용자에게 "기존 페이지를 업데이트할까요, 새 페이지로 만들까요?" 확인
   - **없으면**: 새 페이지로 진행

3. **마크다운 → Confluence 변환**
   본문을 Confluence Storage Format (XHTML)으로 변환:
   - `## 제목` → `<h2>제목</h2>`
   - `**볼드**` → `<strong>볼드</strong>`
   - 코드블록 → `<ac:structured-macro ac:name="code">...</ac:structured-macro>`
   - 인라인 코드 → `<code>코드</code>`
   - 테이블 → `<table><tbody>...</tbody></table>`
   - 목록 → `<ul>/<ol><li>...</li></ul>/<ol>`
   - 인용구 → `<blockquote><p>내용</p></blockquote>`
   - 링크 → `<a href="URL">텍스트</a>`

4. **페이지 저장**
   - 변환된 HTML을 임시 파일에 저장 후 헬퍼 스크립트로 생성/업데이트
   - 헬퍼가 자동으로 전체 너비 설정과 `claude-code` 라벨을 추가
   - **새 페이지**:
     ```python
     import sys; sys.path.insert(0, '<스킬경로>')
     from confluence_helper import create_page
     body = open('/tmp/confluence_body.html', encoding='utf-8').read()
     create_page('제목', body)
     ```
   - **기존 페이지 업데이트**:
     ```python
     from confluence_helper import update_page
     body = open('/tmp/confluence_body.html', encoding='utf-8').read()
     update_page('페이지ID', '제목', body)
     ```

5. **결과 보고**
   - 새 페이지 생성인지, 기존 페이지 업데이트인지 명시
   - 페이지 URL을 사용자에게 표시
   - 주요 내용 요약

## 페이지 형식 규칙
- 제목: 한국어 (Confluence 페이지 제목)
- 본문: 한국어
- 라벨: `claude-code` 자동 추가
- 너비: 전체 너비 자동 적용

## 주의
- 기존 페이지 업데이트 시 내용을 덮어쓰지 않고 병합한다.
- Confluence Storage Format은 XHTML이므로 태그가 정확히 닫혀야 한다.
- `<`, `>`, `&` 등 특수문자는 코드블록 외부에서 이스케이프한다.
