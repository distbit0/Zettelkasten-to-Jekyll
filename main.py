import os
import frontmatter
from datetime import datetime, timedelta
import shutil
import utils
from pathlib import Path
import os
import glob
import re


# path of the folder containing the notes
notes_folder = utils.getConfig()["notesFolderPath"]
# path of the folder containing the blog posts
blog_folder = utils.getConfig()["blogFolderPath"]
postPostfix = utils.getConfig()["blogPostIdentifierPostfix"]
contactInfo = utils.getConfig()["contactInfo"]


# function to check if a file has valid front matter
def has_valid_frontmatter(file_path):
    try:
        blogFM = frontmatter.load(file_path)
        if "headerImage" in blogFM:
            return True
        else:
            return False
    except frontmatter.exceptions.FrontMatterError:
        return False


def generateTitle(file_path):
    title = file_path.split("/")[-1]
    title = title.replace(".md", "").strip(" ")
    title = title[0].upper() + title[1:]

    return title


# function to add front matter to a file
def add_frontmatter(file_path, date=None, description="", articleUrl=""):
    filename = file_path.split("/")[-1]
    # get the current date
    yesterday = datetime.now() - timedelta(1)
    date = yesterday.strftime("%Y-%m-%d") if date is None else date
    # get the title from the file name

    postObject = frontmatter.load(file_path)
    hashtags = remove_hashtags(postObject.content)[1]

    title = generateTitle(file_path)

    if articleUrl == "":
        articleUrl = (
            utils.getConfig()["blogUrl"] + "/" + title.replace(" ", "-").lower()
        )

    frontMatterObject = {
        "title": title,
        "layout": "post",
        "date": date + " 00:00",
        "headerImage": False,
        "category": "blog",
        "author": utils.getConfig()["author"],
        "description": description,
        "articleUrl": articleUrl,
        "tag": hashtags,
    }

    for key, value in frontMatterObject.items():
        postObject[key] = value

    # save file
    outputText = frontmatter.dumps(postObject)
    currentText = open(file_path).read()
    if currentText == outputText:
        return
    frontmatter.dump(postObject, file_path)


def addNewLinesBeforeBlockQuoteReply(md_string):
    modified_md_string = []
    indentOfLastLine = 0
    for line in md_string.split("\n"):
        try:
            indent = line.strip().split(" ")[0].count(">")
        except:
            indent = 0
        if line.strip().startswith(">"):
            lineNotBlank = line.strip().replace(">", "").strip() != ""
            if indent < indentOfLastLine and lineNotBlank:
                modified_md_string.append(">" * indent)
        modified_md_string.append(line)
        indentOfLastLine = indent

    return "\n".join(modified_md_string)


def formatPostContents(file_path, allFileNames):
    post = frontmatter.load(file_path)
    content = post.content

    content = remove_link_only_lines(content)
    content = convert_md_links(content, allFileNames)
    content += "\n\n" + contactInfo
    content = content.replace(postPostfix, "")
    content = remove_hashtags(content)[0]
    contentWithDoubleSpaces = ""
    for line in content.split("\n"):
        contentWithDoubleSpaces += line
        if not line.endswith("  ") and line.strip() != "":
            contentWithDoubleSpaces += "  "  # markdown requires two spaces after a line for it to be recognised as such
        contentWithDoubleSpaces += "\n"
    content = str(contentWithDoubleSpaces)

    content = addNewLinesBeforeBlockQuoteReply(content)
    post.content = content
    frontmatter.dump(post, file_path)


def convert_md_links(md_string, allFileNames):
    # Regex pattern to match the markdown links
    pattern = r"\[\[(?P<filename>[^|\]]+)(?:\|(?P<linkText>[^]]+))?\]\]"

    # Function to replace matched markdown links
    def replace_func(match):
        # Extract the filename and title from the matched object
        filename = match.group("filename").split("/")[-1]  # Only take the file name
        linkText = match.group("linkText") if match.group("linkText") else filename

        linkText = linkText.replace(".md", "")
        if filename + ".md" not in allFileNames:
            return linkText

        filename = "/" + generateTitle(filename).replace(" ", "-").lower()
        # Return the replacement link format
        return f"[{linkText}]({filename})"

    # Use re.sub to replace the markdown links
    return re.sub(pattern, replace_func, md_string)


def remove_link_only_lines(md_string):
    # Regex pattern to match lines with only markdown links and whitespaces
    pattern = r"^\s*(\[\[[^|\]]+\|?[^\]]*\]\]\s*)+$"

    # Filter out lines that match the pattern
    lines = md_string.split("\n")
    filtered_lines = [
        line
        for line in lines
        if not re.match(
            pattern, line.replace(",", "").replace(".", "").replace("+", "")
        )
    ]

    # Join and return the filtered lines
    return "\n".join(filtered_lines)


def find_files_containing_string(root_folder, target_string):
    matching_files = []

    # Walk through each directory
    for dirpath, _, filenames in os.walk(root_folder):
        for filename in filenames:
            if filename.endswith(".md"):  # Check if it's a text file
                filepath = os.path.join(dirpath, filename)
                with open(filepath, "r", encoding="utf-8", errors="ignore") as file:
                    # Read the file line-by-line and search for the target_string
                    for line in file:
                        if target_string in line:
                            matching_files.append(filepath)
                            break  # Exit once target_string is found to avoid redundant checking

    return matching_files


def remove_hashtags(md_string):
    # Regular expression pattern to detect #hashtags
    hashtag_pattern = r"\s(#[\w-]+)"

    md_string = "\n" + md_string
    # Find all hashtags in the markdown string
    hashtags = re.findall(hashtag_pattern, md_string)

    # Remove all found hashtags from the markdown string
    cleaned_md = re.sub(hashtag_pattern, "", md_string)

    hashtags = [tag.strip("#") for tag in hashtags if tag != postPostfix]

    return cleaned_md, hashtags


def generateBlogPostFileName(title, date):
    title = title.replace(" ", "-")

    fileName = date + "-" + generateTitle(title) + ".md"
    fileName = fileName.lower()

    return fileName


def main():
    files = glob.glob(blog_folder + "/*")
    for f in files:
        os.remove(f)
    # find all files in the notes folder
    file_paths = find_files_containing_string(notes_folder, postPostfix)
    allFileNames = [str(file_path).split("/")[-1] for file_path in file_paths]

    for file_path in file_paths:
        file_path = str(file_path)
        filename = file_path.split("/")[-1]
        if has_valid_frontmatter(file_path):
            # extract the date from the front matter
            post = frontmatter.load(file_path)
            description = post["description"] if "description" in post else ""
            articleUrl = post["articleUrl"] if "articleUrl" in post else ""
            filename = articleUrl.split("/")[-1] if "articleUrl" in post else filename
            date = (
                datetime.strptime(post["date"], "%Y-%m-%d  %H:%M")
                .date()
                .strftime("%Y-%m-%d")
            )
            add_frontmatter(
                file_path, date=date, description=description, articleUrl=articleUrl
            )
        else:
            print("not valid frontmatter")
            # add front matter to the file
            add_frontmatter(file_path)
            yesterday = datetime.now() - timedelta(1)
            date = yesterday.strftime("%Y-%m-%d")
        # copy the file to the blog folder with the new name

        blogPostFileName = generateBlogPostFileName(filename, date)
        new_file_path = os.path.join(blog_folder, blogPostFileName)
        print("copied", file_path, "\nto", new_file_path, "\n\n")
        shutil.copy(file_path, new_file_path)
        formatPostContents(new_file_path, allFileNames)


if __name__ == "__main__":
    gitAutoPath = utils.getConfig()["gitAutoPath"]
    main()
    gitFolder = "/".join(blog_folder.split("/")[:-1])
    os.system(gitAutoPath + " " + gitFolder)
