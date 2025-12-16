#!/usr/bin/env python3
"""
Commit Message Validator for TDD Evidence.

Validates that commit messages follow the format:
  [SCOPE] Description

Where SCOPE is one of:
  - M1, M2, M3, M4, M5 (Milestones)
  - SETUP, REFACTOR, FIX, DOCS, TEST, CHORE
  - VT-01, VT-02, ST-01, ST-02, ST-03, ST-04 (Tracks)

Examples:
  [M1-SETUP] Add pyproject.toml configuration
  [VT-01] Implement ChatAgent.chat() method
  [FIX] Correct token estimation overflow
  [DOCS] Update README with examples
"""
import re
import sys

# Valid scopes
VALID_SCOPES = [
    # Milestones
    "M1", "M2", "M3", "M4", "M5",
    # General
    "SETUP", "REFACTOR", "FIX", "DOCS", "TEST", "CHORE", "REVIEW",
    # Tracks
    "VT-01", "VT-02", "ST-01", "ST-02", "ST-03", "ST-04",
    # Combinations
    "M1-SETUP", "M1-ST04", "M2-VT01", "M3-ST01", "M3-ST02",
    "M4-ST03", "M5-VT02",
]

# Regex pattern: [SCOPE] Description (at least 10 chars)
PATTERN = r"^\[([A-Z0-9\-]+)\]\s+.{10,}"


def validate_commit_message(message: str) -> tuple[bool, str]:
    """Validate commit message format."""
    # Skip merge commits
    if message.startswith("Merge"):
        return True, "Merge commit - skipping validation"

    # Skip if message contains special markers (e.g., from tools)
    if "Generated with" in message or "Co-Authored-By:" in message:
        # Check only the first line
        first_line = message.split("\n")[0]
        message = first_line

    # Check pattern
    match = re.match(PATTERN, message)
    if not match:
        return False, (
            "Commit message must follow format: [SCOPE] Description\n"
            f"Valid scopes: {', '.join(VALID_SCOPES[:10])}...\n"
            "Example: [M1-SETUP] Add ProviderConfig entity"
        )

    # Check scope
    scope = match.group(1)
    if scope not in VALID_SCOPES:
        # Allow compound scopes like M1-SETUP
        parts = scope.split("-")
        if not all(p in VALID_SCOPES or p in ["SETUP", "ST04", "VT01", "VT02", "ST01", "ST02", "ST03"] for p in parts):
            return False, (
                f"Invalid scope: [{scope}]\n"
                f"Valid scopes: {', '.join(VALID_SCOPES[:10])}..."
            )

    return True, "OK"


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: commit-msg-check.py <commit-msg-file>")
        sys.exit(1)

    commit_msg_file = sys.argv[1]

    try:
        with open(commit_msg_file) as f:
            message = f.read().strip()
    except FileNotFoundError:
        print(f"Error: File not found: {commit_msg_file}")
        sys.exit(1)

    valid, reason = validate_commit_message(message)

    if not valid:
        print("=" * 50)
        print("COMMIT MESSAGE VALIDATION FAILED")
        print("=" * 50)
        print(f"\nYour message:\n  {message[:100]}...")
        print(f"\nError:\n  {reason}")
        print("\n" + "=" * 50)
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
