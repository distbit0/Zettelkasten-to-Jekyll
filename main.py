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


# function to add front matter to a file
def add_frontmatter(file_path, date=None, description="", tag=[""]):
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
    title = title[0].upper() + title[1:]
    articleurl = utils.getConfig()["blogUrl"] + "/" + title.replace(" ", "-")

    post = frontmatter.loads("")

    frontMatterObject = {
        "title": title,
        "layout": "post",
        "date": date + " 00:00",
        "headerImage": False,
        "category": "blog",
        "author": utils.getConfig()["author"],
        "description": description,
        "articleUrl": articleurl,
        "tag": tag,
    }

    for key, value in frontMatterObject.items():
        post[key] = value

    # create front matter
    frontMatterText = frontmatter.dumps(post)
    # add front matter to the file

    fileContents = frontmatter.load(file_path).content

    with open(file_path, "w") as fileToEdit:
        fileToEdit.write(frontMatterText + "\n\n" + fileContents)


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
            description = post["description"] if "description" in post else ""
            tag = post["tag"] if "tag" in post else [""]
            date = (
                datetime.strptime(post["date"], "%Y-%m-%d  %H:%M")
                .date()
                .strftime("%Y-%m-%d")
            )
            add_frontmatter(file_path, date=date, description=description, tag=tag)
        else:
            print("not valid frontmatter")
            # add front matter to the file
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
    gitFolder = "/".join(blog_folder.split("/")[:-1])
    os.system(gitAutoPath + " -d " + gitFolder + " -o -p")
