"""kubectl-application-shell package"""

import sys
from typing import List


def run_cli():
    """Entry point that handles default command behavior"""
    from .cli import app
    
    # If we have arguments and the first one is not a known command
    known_commands = ["main", "list-sessions", "resume-session", "terminate-session", "--help", "-h"]
    
    if len(sys.argv) > 1 and sys.argv[1] not in known_commands:
        # Check if the first argument starts with -- (it's an option)
        if not sys.argv[1].startswith("-"):
            # Insert "main" as the command
            sys.argv.insert(1, "main")
    
    app(prog_name="kubeas")