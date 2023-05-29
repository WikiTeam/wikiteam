from lxml import etree
from lxml.builder import E

from wikiteam3.dumpgenerator.exceptions import PageMissingError

def makeXmlPageFromRaw(xml, arvcontinue) -> str:
    """Discard the metadata around a <page> element in <mediawiki> string"""
    root = etree.XML(xml)
    find = etree.XPath("//*[local-name() = 'page']")
    page = find(root)[0]
    if arvcontinue is not None:
        page.attrib['arvcontinue'] = arvcontinue
    # The tag will inherit the namespace, like:
    # <page xmlns="http://www.mediawiki.org/xml/export-0.10/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    # FIXME: pretty_print doesn't seem to work, only adds a newline
    return etree.tostring(page, pretty_print=True, encoding="unicode")


def makeXmlFromPage(page: dict, arvcontinue) -> str:
    """Output an XML document as a string from a page as in the API JSON"""
    try:
        p = E.page(
            E.title(str(page["title"])),
            E.ns(str(page["ns"])),
            E.id(str(page["pageid"])),
        )
        if arvcontinue is not None:
            p.attrib['arvcontinue'] = arvcontinue
        for rev in page["revisions"]:
            # Older releases like MediaWiki 1.16 do not return all fields.
            if "userid" in rev:
                userid = rev["userid"]
            else:
                userid = 0
            if "size" in rev:
                size = rev["size"]
            else:
                size = 0

            # Create rev object
            revision = [E.id(str(rev["revid"])),
                E.timestamp(rev["timestamp"]),]

            # The text, user, comment, sha1 may be deleted/suppressed
            if (('texthidden' in rev) or ('textmissing' in rev)):
                print("Warning: text missing/hidden in pageid %d revid %d" % (page['pageid'], rev['revid']))
                revision.append(E.text(**{
                    'bytes': str(size),
                    'deleted': 'deleted',
                }))
            else:
                text = str(rev["*"])
                revision.append(E.text(text, **{
                    'bytes': str(size),
                    '{http://www.w3.org/XML/1998/namespace}space': 'preserve',
                }))

            if not "user" in rev:
                if not "userhidden" in rev:
                    print("Warning: user not hidden but missing user in pageid %d revid %d" % (page['pageid'], rev['revid']))
                revision.append(E.contributor(deleted="deleted"))
            else:
                revision.append(
                    E.contributor(
                        E.username(str(rev["user"])),
                        E.id(str(userid)),
                    )
                )

            if not "sha1" in rev:
                if "sha1hidden" in rev:
                    revision.append(E.sha1()) # stub
                else:
                    # The sha1 may not have been backfilled on older wikis or lack for other reasons (Wikia).
                    pass
            elif "sha1" in rev:
                revision.append(E.sha1(rev["sha1"]))


            if 'commenthidden' in rev:
                revision.append(E.comment(deleted="deleted"))
            elif "comment" in rev and rev["comment"]:
                revision.append(E.comment(str(rev["comment"])))

            if "contentmodel" in rev:
                revision.append(E.model(rev["contentmodel"]))
            if "contentformat" in rev:
                revision.append(E.format(rev["contentformat"]))
            # Sometimes a missing parentid is not replaced with a 0 as it should.
            if "parentid" in rev:
                revision.append(E.parentid(str(rev["parentid"])))

            if "minor" in rev:
                revision.append(E.minor())

            # mwcli's dump.xml order
            revisionTags = ['id', 'parentid', 'timestamp', 'contributor', 'minor', 'comment', 'origin', 'model', 'format', 'text', 'sha1']
            revisionElementsDict = {elem.tag: elem for elem in revision}
            _revision = E.revision()
            for tag in revisionTags:
                if tag in revisionElementsDict:
                    _revision.append(revisionElementsDict.pop(tag))
            for elem in revisionElementsDict.values():
                _revision.append(elem)
            p.append(_revision)
    except KeyError as e:
        print(e)
        raise PageMissingError(page["title"], e)
    return etree.tostring(p, pretty_print=True, encoding="unicode")

