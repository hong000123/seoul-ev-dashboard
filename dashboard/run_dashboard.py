"""Portable Streamlit launcher; no local geospatial runtime required."""
from pathlib import Path
import sys

try:
    from streamlit.web import cli
except ImportError as exc:
    raise SystemExit("Streamlit이 없습니다. README.md의 설치 명령을 먼저 실행하세요. " + str(exc))
sys.argv = ["streamlit", "run", str(Path(__file__).with_name("app.py")), "--theme.base=light", *sys.argv[1:]]
raise SystemExit(cli.main())
