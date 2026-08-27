# Jewelry SW — PyQt6

주얼리 입출고 대장을 위한 Windows 네이티브 PyQt6 애플리케이션입니다.

## 설치 및 실행

Python 3.10 이상이 필요합니다.

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m jewelry.main
```

## 주요 UI 구조

- `jewelry/ui/window/main_window.py`: 창 프레임, 타이틀바, 페이지 전환
- `jewelry/ui/pages/main_page.py`: 요약 카드, 탭, 액션 바 및 기능 연결
- `jewelry/ui/widgets/entry_grid.py`: 2단 헤더, 데이터 행, 합계 행
- `jewelry/ui/widgets/stat_card.py`: 월/통계/추이 카드
- `jewelry/ui/sidebar/sidebar.py`: SVG 자산 없이 QPainter로 그린 탐색 아이콘
- `jewelry/ui/resources/styles/theme.qss`: 공통 디자인 토큰과 상태 스타일

## Windows EXE 만들기

```powershell
.\build_desktop.ps1
```

완성된 단일 실행 파일은 `dist\Jewelry SW.exe`에 생성됩니다.
