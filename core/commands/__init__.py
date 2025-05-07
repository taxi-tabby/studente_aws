"""
클라이언트-서버 명령어 모듈
이 패키지는 클라이언트와 서버 간의 통신에 사용되는 명령어 정의 및 처리를 담당합니다.
"""

from core.commands.command_registry import register_command_handlers
from core.commands.command_definitions import *

# 명령어 핸들러 등록을 자동으로 수행
register_command_handlers()