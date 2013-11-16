MediaWiki XML Schema Descriptions
=================================

This folder stores all the MediaWiki XML Schema Descriptions (XSD) and the differences between versions. This is useful for ensuring the compatibility of DumpGenerator to create dumps following the format of what MediaWiki provides via Special:Export.

DumpGenerator currently supports Schema versions 0.3 till 0.8.

Below is a list of the MediaWiki version that each XSD was introduced:

| Schema version |  MediaWiki version |
| -------------- | ------------------ |
|      0.8       |        1.21        |
|      0.7       |        1.20        |
|      0.6       |        1.19        |
|      0.5       |        1.18        |
|      0.4       |        1.16        |
|      0.3       |        1.5         |
|      0.2       |        unknown     |
|      0.1       |        1.5         |

*Note: It is unknown whether version 0.2 of the XSD was actually used by MediaWiki in exporting, since 0.3 followed immediately after 0.1*

For versions before MediaWiki 1.5, it is possible that no XML Schema Description was provided during the export, and since the backend database was changed at MediaWiki 1.5, DumpGenerator hence will not provide support for downloading an XML export of wikis before that version.

We **strongly encourage** system administrators who are still using MediaWiki 1.4 and earlier to upgrade so that DumpGenerator can create a proper dump of the wiki using XML. If it is not possible, we advice using [wget-warc][1] and downloading a complete copy of the wiki in HTML form in the Web ARChive format.

[1]: http://www.archiveteam.org/index.php?title=Wget_with_WARC_output
