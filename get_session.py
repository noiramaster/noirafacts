"""Extract Instagram sessionid from Chrome cookies"""

import os
import sqlite3

cookie_path = os.path.expanduser(
    '~') + '/AppData/Local/Google/Chrome/User Data/Default/Network/Cookies'

try:
    conn = sqlite3.connect(f'file:{cookie_path}?mode=ro', uri=True)
    conn.text_factory = bytes
    c = conn.cursor()
    c.execute("SELECT name, value FROM cookies WHERE host_key LIKE '%instagram.com%' AND name='sessionid'")
    row = c.fetchone()
    conn.close()

    if row and row[1]:
        value = row[1].decode('utf-8') if isinstance(row[1], bytes) else row[1]
        print(value)
    else:
        print('NOTFOUND')
except Exception as e:
    print(f'ERROR: {e}')
