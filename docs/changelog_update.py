import re

# Copy the release notes from the GitHub release page
markdown_text = """
## What's Changed
* Add installation CI by @giswqs in https://github.com/gee-community/geemap/pull/1656
* Fix vis control error by @giswqs in https://github.com/gee-community/geemap/pull/1660

## New Contributors
* @bengalin made their first contribution in https://github.com/gee-community/geemap/pull/1664
* @sufyanAbbasi made their first contribution in https://github.com/gee-community/geemap/pull/1666
* @kirimaru-jp made their first contribution in https://github.com/gee-community/geemap/pull/1669
* @schwehr made their first contribution in https://github.com/gee-community/geemap/pull/1673

**Full Changelog**: https://github.com/gee-community/geemap/compare/v0.25.0...v0.26.0
"""

# Regular expression pattern to match the Markdown hyperlinks
pattern = r"https://github\.com/gee-community/geemap/pull/(\d+)"


# Function to replace matched URLs with the desired format
def replace_url(match):
    pr_number = match.group(1)
    return f"[#{pr_number}](https://github.com/gee-community/geemap/pull/{pr_number})"


# Use re.sub to replace URLs with the desired format
formatted_text = re.sub(pattern, replace_url, markdown_text)

for line in formatted_text.splitlines():
    if "Full Changelog" in line:
        prefix = line.split(": ")[0]
        link = line.split(": ")[1]
        version = line.split("/")[-1]
        formatted_text = (
            formatted_text.replace(line, f"{prefix}: [{version}]({link})")
            .replace("## What's Changed", "**What's Changed**")
            .replace("## New Contributors", "**New Contributors**")
        )


with open("docs/changelog_update.md", "w") as f:
    f.write(formatted_text)

# Print the formatted text
print(formatted_text)

# Copy the formatted text and paste it to the CHANGELOG.md file
