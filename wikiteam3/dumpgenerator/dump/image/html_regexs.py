R_NEXT = r"(?<!&amp;dir=prev)&amp;offset=(?P<offset>\d+)&amp;"

REGEX_CANDIDATES = [
    # [0]
    # archiveteam 1.15.1 <td class="TablePager_col_img_name"><a href="/index.php?title=File:Yahoovideo.jpg" title="File:Yahoovideo.jpg">Yahoovideo.jpg</a> (<a href="/images/2/2b/Yahoovideo.jpg">file</a>)</td>
    # wikanda 1.15.5 <td class="TablePager_col_img_user_text"><a
    # href="/w/index.php?title=Usuario:Fernandocg&amp;action=edit&amp;redlink=1"
    # class="new" title="Usuario:Fernandocg (página no
    # existe)">Fernandocg</a></td>
    r'(?im)<td class="TablePager_col_img_name"><a href[^>]+title="[^:>]+:(?P<filename>[^>]+)">[^<]+</a>[^<]+<a href="(?P<url>[^>]+/[^>/]+)">[^<]+</a>[^<]+</td>\s*<td class="TablePager_col_img_user_text"><a[^>]+>(?P<uploader>[^<]+)</a></td>'

    # [1]
    # wikijuegos 1.9.5
    # http://softwarelibre.uca.es/wikijuegos/Especial:Imagelist old
    # mediawiki version
    ,r'(?im)<td class="TablePager_col_links"><a href[^>]+title="[^:>]+:(?P<filename>[^>]+)">[^<]+</a>[^<]+<a href="(?P<url>[^>]+/[^>/]+)">[^<]+</a></td>\s*<td class="TablePager_col_img_timestamp">[^<]+</td>\s*<td class="TablePager_col_img_name">[^<]+</td>\s*<td class="TablePager_col_img_user_text"><a[^>]+>(?P<uploader>[^<]+)</a></td>'

    # [2]
    # gentoowiki 1.18
    ,r'(?im)<td class="TablePager_col_img_name"><a[^>]+title="[^:>]+:(?P<filename>[^>]+)">[^<]+</a>[^<]+<a href="(?P<url>[^>]+)">[^<]+</a>[^<]+</td><td class="TablePager_col_thumb"><a[^>]+><img[^>]+></a></td><td class="TablePager_col_img_size">[^<]+</td><td class="TablePager_col_img_user_text"><a[^>]+>(?P<uploader>[^<]+)</a></td>'

    # [3]
    # http://www.memoryarchive.org/en/index.php?title=Special:Imagelist&sort=byname&limit=50&wpIlMatch=
    # (<a href="/en/Image:109_0923.JPG" title="Image:109 0923.JPG">desc</a>) <a href="/en/upload/c/cd/109_0923.JPG">109 0923.JPG</a> . . 885,713 bytes . . <a href="/en/User:Bfalconer" title="User:Bfalconer">Bfalconer</a> . . 18:44, 17 November 2005<br />
    ,'(?ism)<a href=[^>]+ title="[^:>]+:(?P<filename>[^>]+)">[^<]+</a>[^<]+<a href="(?P<url>[^>]+)">[^<]+</a>[^<]+<a[^>]+>(?P<uploader>[^<]+)</a>'

    # [4]
    ,(
        r'(?im)<td class="TablePager_col_img_name">\s*<a href[^>]*?>(?P<filename>[^>]+)</a>[^<]*?<a href="(?P<url>[^>]+)">[^<]*?</a>[^<]*?</td>\s*'
        r'<td class="TablePager_col_thumb">[^\n\r]*?</td>\s*'
        r'<td class="TablePager_col_img_size">[^<]*?</td>\s*'
        r'<td class="(?:TablePager_col_img_user_text|TablePager_col_img_actor)">\s*(<a href="[^>]*?" title="[^>]*?">)?(?P<uploader>[^<]+?)(</a>)?\s*</td>'
    )
]
