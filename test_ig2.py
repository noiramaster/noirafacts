from instagram_private_api import Client
import json

api = Client('shadow4stories', 'aissarah')
print(f'Login: {api.authenticated}')
user_id = api.user_id
print(f'User ID: {user_id}')

# Look up natubeac
result = api.username_info('natubeac')
print(f'natubeac info: {result.get("user", {}).get("full_name", "not found")}')

user_pk = result.get('user', {}).get('pk')
print(f'PK: {user_pk}')

if user_pk:
    feed = api.user_feed(str(user_pk))
    items = feed.get('items', [])
    print(f'Found {len(items)} posts')
    for item in items[:5]:
        print(f'  - {item.get("code")} media_type={item.get("media_type")} has_video={item.get("media_type") == 2}')
