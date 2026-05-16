#!/usr/bin/env python3
import os
import subprocess
import sys
from datetime import datetime

def generate_release_notes():
    print("Generating release notes...")
    
    try:
        # Get the latest tag
        latest_tag = subprocess.check_output(
            ["git", "describe", "--tags", "--abbrev=0"], 
            stderr=subprocess.DEVNULL
        ).decode().strip()
        revision_range = f"{latest_tag}..HEAD"
    except subprocess.CalledProcessError:
        # No tags exist yet
        latest_tag = "Initial"
        revision_range = "HEAD"
    
    try:
        log_output = subprocess.check_output(
            ["git", "log", revision_range, "--pretty=format:- %s (%h)"]
        ).decode().strip()
    except subprocess.CalledProcessError as e:
        print(f"Error fetching git log: {e}")
        sys.exit(1)
        
    date_str = datetime.now().strftime("%Y-%m-%d")
    version = os.environ.get("NEW_VERSION", "Unreleased")
    
    changelog_entry = f"## [{version}] - {date_str}\n\n"
    if log_output:
        changelog_entry += log_output + "\n\n"
    else:
        changelog_entry += "- No new changes.\n\n"
        
    changelog_path = "CHANGELOG.md"
    existing_content = ""
    if os.path.exists(changelog_path):
        with open(changelog_path, "r") as f:
            existing_content = f.read()
            
    with open(changelog_path, "w") as f:
        f.write("# Changelog\n\n")
        f.write(changelog_entry)
        # Strip the old header if it exists
        if existing_content.startswith("# Changelog\n\n"):
            f.write(existing_content[len("# Changelog\n\n"):])
        else:
            f.write(existing_content)
            
    print(f"Updated {changelog_path}")

if __name__ == "__main__":
    generate_release_notes()
