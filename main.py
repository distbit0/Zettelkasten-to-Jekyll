import os
import frontmatter
from datetime import datetime, timedelta
import shutil
import utils
from pathlib import Path
import os
import glob


# path of the folder containing the notes
notes_folder = utils.getConfig()["notesFolderPath"]
# path of the folder containing the blog posts
blog_folder = utils.getConfig()["blogFolderPath"]
postPostfix = utils.getConfig()["blogPostIdentifierPostfix"]


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


def remove_frontmatter(file_name):
    try:
        # Load the file
        post = frontmatter.load(file_name)
        # Get the content of the file
        content = post.content
        print(content)
        # Overwrite the file with the content only
        with open(file_name, "w") as f:
            f.write(content)

    except frontmatter.exceptions.FrontMatterError:
        # If the file does not have front matter, do nothing
        pass


# function to add front matter to a file
def add_frontmatter(file_path, date=None, description=""):
    filename = file_path.split("/")[-1]
    # get the current date
    yesterday = datetime.now() - timedelta(1)
    date = yesterday.strftime("%Y-%m-%d") if date is None else date
    # get the title from the file name
    title = (
        os.path.basename(file_path)
        .replace(postPostfix, "")
        .replace("-", " ")
        .replace(".md", "")
    )
    title = title.capitalize()
    articleurl = utils.getConfig()["blogUrl"] + "/" + title.replace(" ", "-")

    # create front matter
    frontMatterText = """---
title: "{}"
layout: post
date: {} 00:00
headerImage: false
category: blog
author: {}
description: {}
articleUrl: {}
---

""".format(
        title, date, utils.getConfig()["author"], description, articleurl
    )
    # add front matter to the file

    fileContents = open(file_path).read()
    with open(file_path, "w") as fileToEdit:
        fileToEdit.write(frontMatterText + fileContents)


def main():
    files = glob.glob(blog_folder + "/*")
    for f in files:
        os.remove(f)
    # find all files in the notes folder
    for file_path in Path(notes_folder).rglob("*" + postPostfix + ".md"):
        file_path = str(file_path)
        filename = file_path.split("/")[-1]
        if has_valid_frontmatter(file_path):
            # extract the date from the front matter
            post = frontmatter.load(file_path)
            description = post["description"]
            date = (
                datetime.strptime(post["date"], "%Y-%m-%d  %H:%M")
                .date()
                .strftime("%Y-%m-%d")
            )
            remove_frontmatter(file_path)
            add_frontmatter(file_path, date=date, description=description)
        else:
            print("not valid frontmatter")
            # add front matter to the file
            remove_frontmatter(file_path)
            add_frontmatter(file_path)
            yesterday = datetime.now() - timedelta(1)
            date = yesterday.strftime("%Y-%m-%d")
        # copy the file to the blog folder with the new name

        new_filename = "{}-{}".format(date, filename.replace(postPostfix, "")).replace(
            " ", "-"
        )
        new_file_path = os.path.join(blog_folder, new_filename)
        print("copied", file_path, "\nto", new_file_path, "\n\n")
        shutil.copy(file_path, new_file_path)


if __name__ == "__main__":
    gitAutoPath = utils.getConfig()["gitAutoPath"]
    main()
    os.system(gitAutoPath + " -d " + blog_folder + " -o -p")
