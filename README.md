# confluence-notes-skill

Claude Code에서 학습 내용을 Confluence 페이지로 저장하는 스킬입니다.

## 기능

- `/confluence-notes` 명령으로 현재 대화 내용을 Confluence 페이지로 저장
- 마크다운 → Confluence Storage Format 자동 변환
- 기존 페이지 검색 및 업데이트 지원
- 전체 너비 + `claude-code` 라벨 자동 적용

## 설치

### 1. 스킬 폴더 복사

```bash
cp -r confluence-notes-skill ~/.claude/skills/confluence-notes
```

### 2. 환경변수 설정

Atlassian API 토큰: https://id.atlassian.com/manage-profile/security/api-tokens

```bash
# ~/.bashrc 또는 ~/.zshrc에 추가
export CONFLUENCE_EMAIL="your-email@company.com"
export CONFLUENCE_API_TOKEN="your-api-token"
export CONFLUENCE_SITE="https://yourcompany.atlassian.net/wiki"
export CONFLUENCE_SPACE_KEY="YOUR_SPACE"
export CONFLUENCE_FOLDER_ID="1234567890"
```

- `CONFLUENCE_SITE`: Confluence Cloud 사이트 URL (`/wiki` 포함)
- `CONFLUENCE_SPACE_KEY`: Space 설정에서 확인 가능
- `CONFLUENCE_FOLDER_ID`: 노트를 저장할 폴더의 URL에서 확인 (예: `.../folder/1234567890`)

### 3. 확인

Claude Code에서:
```
/confluence-notes 테스트 페이지
```

## 사용법

```
/confluence-notes                          # 현재 대화에서 문서화할 내용 확인
/confluence-notes Claude 인증 방식 정리     # 제목을 지정하여 새 페이지 생성
```

## 파일 구조

```
confluence-notes-skill/
├── SKILL.md                # 스킬 정의 (Claude Code 프롬프트)
├── confluence_helper.py    # Confluence REST API 호출
├── md_to_confluence.py     # 마크다운 → Confluence HTML 변환
└── README.md               # 이 파일
```

## 요구사항

- Claude Code
- Python 3.6+
- Confluence Cloud (Atlassian API 토큰)
