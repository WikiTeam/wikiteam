# Publishing the dump

Publishing your dumps to the [Internet Archive's wikiteam collection](https://archive.org/details/wikiteam) is easily done. First [sign up](https://archive.org/account/signup) or [login](http://archive.org/account/login.php).

## Launcher and uploader

Instructions on using the scripts `launcher` and `uploader` are in the file [Usage](./USAGE.md).

## Automatic publishing

Just use `uploader` (especially if you have multiple wikis): the script takes the filename of a list of wikis as argument and uploads their dumps to archive.org. You only need to:

- Check the 7z compressed dumps are in the same directory as `listfile`. The file `listfile` contains a list of the api.php URLs of the wikis to upload, one per line.
- [Retrieve your S3 keys](http://www.archive.org/account/s3.php), save them one per line (in the order provided) in a keys.txt file in same directory as `uploader`.
- Run the script `uploader listfile`.

## Manual publishing

- After running dumpgenerator, in each dump folder, select all files, right-click on the selection, click 7-Zip, click `Add to archive...` and click OK.
- At Archive.org, for each wiki [create a new item](http://archive.org/create/).
- Click `Upload files`. Then either drag and drop the 7-Zip archive onto the box or click `Choose files` and select the 7-Zip archive.
- `Page Title` and `Page URL` will be filled in by the uploader.
- Add a short `Description`, such as a descriptive name fopr the wiki.
- Add `Subject Tags`, separated by commas, these are the keywords that will help the archive to show up in a Internet Archive search, e.g. wikiteam,wiki,subjects of the wiki, and so on.
- `Creator`, can be left blank.
- `Date`, can be left blank.
- `Collection`, select `Community texts`.
- `Language`, select the language of the wiki.
- `License`, click to expand and select Creative Commons, Allow Remixing, Require Share-Alike for a CC-BY-SA licence.
- Click `Upload and Create Your Item`.

With the subject tag of wikiteam and collection of community texts, your uploads should appear in a search for [subject:"wikiteam" AND collection:opensource](https://archive.org/search?query=subject%3A%22wikiteam%22+AND+collection%3Aopensource).

## Info for developers

- [Internet Archive’s S3 like server API](https://archive.org/developers/ias3.html).
