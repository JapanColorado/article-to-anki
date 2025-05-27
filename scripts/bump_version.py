#!/usr/bin/env python3
"""Script to bump version numbers across the project and create releases."""

import re
import sys
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

def get_current_version():
    """Get current version from __init__.py."""
    init_file = Path("articles_to_anki") / "__init__.py"
    if not init_file.exists():
        raise FileNotFoundError("articles_to_anki/__init__.py not found")

    content = init_file.read_text()
    match = re.search(r'__version__ = "([^"]+)"', content)
    if not match:
        raise ValueError("Version not found in __init__.py")

    return match.group(1)

def bump_version(current_version, bump_type="patch"):
    """Bump version number based on type."""
    try:
        major, minor, patch = map(int, current_version.split('.'))
    except ValueError:
        raise ValueError(f"Invalid version format: {current_version}")

    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "patch":
        patch += 1
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")

    return f"{major}.{minor}.{patch}"

def update_version_files(new_version):
    """Update version in all relevant files."""
    files_to_update = [
        {
            "path": "articles_to_anki/__init__.py",
            "pattern": r'__version__ = "([^"]+)"',
            "replacement": f'__version__ = "{new_version}"'
        },
        {
            "path": "pyproject.toml",
            "pattern": r'version = "([^"]+)"',
            "replacement": f'version = "{new_version}"'
        }
    ]

    updated_files = []
    for file_info in files_to_update:
        path = Path(file_info["path"])
        if path.exists():
            content = path.read_text()
            new_content = re.sub(file_info["pattern"], file_info["replacement"], content)
            if new_content != content:
                path.write_text(new_content)
                updated_files.append(str(path))
                print(f"✓ Updated {path}")
            else:
                print(f"⚠ No changes needed in {path}")
        else:
            print(f"⚠ File not found: {path}")

    return updated_files

def update_changelog(new_version):
    """Update CHANGELOG.md with new version."""
    changelog_path = Path("CHANGELOG.md")
    current_date = datetime.now().strftime("%Y-%m-%d")

    if not changelog_path.exists():
        # Create new changelog
        changelog_content = f"""# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [{new_version}] - {current_date}

### Added
- Initial PyPI release
- Core functionality for generating Anki cards from articles
- Support for URLs and local files (PDF, EPUB, DOCX, TXT, etc.)
- Smart duplicate detection with semantic similarity
- AnkiConnect integration for direct card export
- Custom prompts and flexible configuration

### Changed

### Deprecated

### Removed

### Fixed

### Security
"""
        changelog_path.write_text(changelog_content)
        print(f"✓ Created CHANGELOG.md")
    else:
        # Update existing changelog
        content = changelog_path.read_text()

        # Find the [Unreleased] section and add new version after it
        unreleased_pattern = r"(## \[Unreleased\]\s*\n)"
        new_section = f"\\1\n## [{new_version}] - {current_date}\n\n### Added\n\n### Changed\n\n### Fixed\n\n"

        if re.search(unreleased_pattern, content):
            new_content = re.sub(unreleased_pattern, new_section, content)
            changelog_path.write_text(new_content)
            print(f"✓ Updated CHANGELOG.md")
        else:
            print("⚠ Could not find [Unreleased] section in CHANGELOG.md")

def run_git_commands(new_version, commit=True, tag=True, push=True):
    """Run git commands to commit, tag, and push changes."""
    try:
        # Check if we're in a git repository
        subprocess.run(["git", "status"], check=True, capture_output=True)

        if commit:
            # Add all changes
            subprocess.run(["git", "add", "."], check=True)

            # Commit changes
            commit_message = f"Bump version to {new_version}"
            subprocess.run(["git", "commit", "-m", commit_message], check=True)
            print(f"✓ Committed changes: {commit_message}")

        if tag:
            # Create tag
            tag_name = f"v{new_version}"
            tag_message = f"Release version {new_version}"
            subprocess.run(["git", "tag", "-a", tag_name, "-m", tag_message], check=True)
            print(f"✓ Created tag: {tag_name}")

        if push:
            # Push changes and tags
            subprocess.run(["git", "push"], check=True)
            subprocess.run(["git", "push", "--tags"], check=True)
            print("✓ Pushed changes and tags to remote")

        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Git command failed: {e}")
        return False
    except FileNotFoundError:
        print("✗ Git not found. Please install git.")
        return False

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Bump version and create release")
    parser.add_argument(
        "bump_type",
        choices=["major", "minor", "patch"],
        help="Type of version bump"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--no-commit",
        action="store_true",
        help="Don't commit changes to git"
    )
    parser.add_argument(
        "--no-tag",
        action="store_true",
        help="Don't create git tag"
    )
    parser.add_argument(
        "--no-push",
        action="store_true",
        help="Don't push to remote repository"
    )

    args = parser.parse_args()

    try:
        # Get current version
        current_version = get_current_version()
        print(f"Current version: {current_version}")

        # Calculate new version
        new_version = bump_version(current_version, args.bump_type)
        print(f"New version: {new_version}")

        if args.dry_run:
            print("\n🔍 DRY RUN - No changes will be made")
            print(f"Would bump version from {current_version} to {new_version}")
            print("Would update:")
            print("  - articles_to_anki/__init__.py")
            print("  - pyproject.toml")
            print("  - CHANGELOG.md")
            if not args.no_commit:
                print(f"Would commit changes")
            if not args.no_tag:
                print(f"Would create tag v{new_version}")
            if not args.no_push:
                print(f"Would push to remote")
            return

        # Update version files
        print(f"\n📝 Updating version files...")
        updated_files = update_version_files(new_version)

        # Update changelog
        print(f"\n📋 Updating changelog...")
        update_changelog(new_version)

        # Git operations
        if not args.no_commit or not args.no_tag or not args.no_push:
            print(f"\n🔧 Running git operations...")
            success = run_git_commands(
                new_version,
                commit=not args.no_commit,
                tag=not args.no_tag,
                push=not args.no_push
            )

            if not success:
                print("✗ Git operations failed. Version files were updated but not committed.")
                sys.exit(1)

        print(f"\n🎉 Successfully bumped version to {new_version}!")
        print(f"\nNext steps:")
        print(f"1. GitHub Actions will automatically publish to PyPI when the tag is pushed")
        print(f"2. Check the Actions tab in your GitHub repository")
        print(f"3. Verify the package is published: https://pypi.org/project/articles-to-anki/")

    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
