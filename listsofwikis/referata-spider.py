# -*- coding: utf-8 -*-

import random
import re
import requests
import time

def main():
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux i686; rv:24.0) Gecko/20100101 Firefox/24.0',
    }
    
    keyword = 'site:referata.com'
    for start in range(0, 1000, 10):
        url = 'https://www.google.es/search?q=%s&start=%d' % (re.sub(' ', '%20', keyword), start)
        r = requests.get(url, headers=headers)
        raw = r.text
        
        m = re.findall(ur'(?im)<h3 class="r"><a href=\"([^ ]+?)" onmouse', raw)
        for i in m:
            print i
        
        if re.search(ur'id="ofr"', raw): #resultados omitidos, final
            break
        
        time.sleep(random.randint(3,10))
    
if __name__ == '__main__':
    main()
