#!/usr/bin/env python3
"""
Bump version numbers in pyproject.toml and geemap/__init__.py

This script updates the version in two places in pyproject.toml:
1. [project] section: version = "..."
2. [tool.bumpversion] section: current_version = "..."

And updates __version__ in geemap/__init__.py:
__version__ = "..."

Usage:
    python scripts/bump_geemap_version.py NEW_VERSION

Example:
    python scripts/bump_geemap_version.py 0.36.5
"""

import sys
import re
from pathlib import Path


def update_pyproject_toml(file_path: Path, new_version: str) -> bool:
    """Update version in pyproject.toml (two occurrences)."""
    content = file_path.read_text()
    original_content = content
    
    # Pattern 1: [project] section version
    project_pattern = r'(^\[project\](?:.*?\n)*?version\s*=\s*)"([^"]+)"'
    # Pattern 2: [tool.bumpversion] section current_version
    bumpversion_pattern = r'(^\[tool\.bumpversion\](?:.*?\n)*?current_version\s*=\s*)"([^"]+)"'
    
    # Check if both patterns exist
    project_match = re.search(project_pattern, content, re.MULTILINE | re.DOTALL)
    bumpversion_match = re.search(bumpversion_pattern, content, re.MULTILINE | re.DOTALL)
    
    if not project_match:
        print("ERROR: Could not find 'version = \"...\"' in [project] section of pyproject.toml")
        return False
    
    if not bumpversion_match:
        print("ERROR: Could not find 'current_version = \"...\"' in [tool.bumpversion] section of pyproject.toml")
        return False
    
    old_project_version = project_match.group(2)
    old_bumpversion = bumpversion_match.group(2)
    
    print(f"Found project version: {old_project_version}")
    print(f"Found bumpversion: {old_bumpversion}")
    
    # Replace both occurrences
    # Use a more targeted approach to replace only the specific lines
    lines = content.split('\n')
    new_lines = []
    in_project = False
    in_bumpversion = False
    project_replaced = False
    bumpversion_replaced = False
    
    for line in lines:
        if line.strip() == '[project]':
            in_project = True
            in_bumpversion = False
        elif line.strip() == '[tool.bumpversion]':
            in_bumpversion = True
            in_project = False
        elif line.strip().startswith('['):
            in_project = False
            in_bumpversion = False
        
        # Replace in [project] section
        if in_project and not project_replaced and re.match(r'^version\s*=\s*"', line):
            new_lines.append(f'version = "{new_version}"')
            project_replaced = True
        # Replace in [tool.bumpversion] section
        elif in_bumpversion and not bumpversion_replaced and re.match(r'^current_version\s*=\s*"', line):
            new_lines.append(f'current_version = "{new_version}"')
            bumpversion_replaced = True
        else:
            new_lines.append(line)
    
    if not project_replaced or not bumpversion_replaced:
        print("ERROR: Failed to replace version strings in pyproject.toml")
        return False
    
    new_content = '\n'.join(new_lines)
    
    if new_content != original_content:
        file_path.write_text(new_content)
        print(f"✓ Updated pyproject.toml: {old_project_version} → {new_version}")
        return True
    else:
        print("ERROR: No changes made to pyproject.toml")
        return False


def update_init_py(file_path: Path, new_version: str) -> bool:
    """Update __version__ in geemap/__init__.py."""
    content = file_path.read_text()
    original_content = content
    
    # Pattern: __version__ = "..."
    pattern = r'^__version__\s*=\s*"([^"]+)"'
    
    match = re.search(pattern, content, re.MULTILINE)
    
    if not match:
        print("ERROR: Could not find '__version__ = \"...\"' in geemap/__init__.py")
        return False
    
    old_version = match.group(1)
    print(f"Found __version__: {old_version}")
    
    # Replace the version
    new_content = re.sub(pattern, f'__version__ = "{new_version}"', content, flags=re.MULTILINE)
    
    if new_content != original_content:
        file_path.write_text(new_content)
        print(f"✓ Updated geemap/__init__.py: {old_version} → {new_version}")
        return True
    else:
        print("ERROR: No changes made to geemap/__init__.py")
        return False


def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/bump_geemap_version.py NEW_VERSION")
        print("Example: python scripts/bump_geemap_version.py 0.36.5")
        sys.exit(1)
    
    new_version = sys.argv[1]
    
    # Validate version format (basic check)
    if not re.match(r'^\d+\.\d+\.\d+', new_version):
        print(f"ERROR: Invalid version format: {new_version}")
        print("Expected format: X.Y.Z or X.Y.Z-suffix (e.g., 0.36.5 or 0.36.5rc1)")
        sys.exit(1)
    
    print(f"\nBumping version to: {new_version}\n")
    
    # Get repository root (assuming script is in scripts/ directory)
    repo_root = Path(__file__).parent.parent
    
    pyproject_path = repo_root / "pyproject.toml"
    init_path = repo_root / "geemap" / "__init__.py"
    
    # Check files exist
    if not pyproject_path.exists():
        print(f"ERROR: pyproject.toml not found at {pyproject_path}")
        sys.exit(1)
    
    if not init_path.exists():
        print(f"ERROR: geemap/__init__.py not found at {init_path}")
        sys.exit(1)
    
    # Update files
    success = True
    success = update_pyproject_toml(pyproject_path, new_version) and success
    success = update_init_py(init_path, new_version) and success
    
    if success:
        print("\n✓ Version bump completed successfully!")
        sys.exit(0)
    else:
        print("\n✗ Version bump failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
