Google Reader Python API Client
===============================

This project is a Python client library for feed readers that utilize the [Google Reader](https://en.wikipedia.org/wiki/Google_Reader) API.
Although [Google Reader was discontinued in 2013](https://en.wikipedia.org/wiki/Google_Reader#Discontinuation), many feed readers continue to rely on this API.

Note that this library is not fully implemented. It has been tested with [Miniflux](https://miniflux.app) and [FreshRSS](https://freshrss.github.io/).

There is no official Google Reader API documentation. This library has been developed by analyzing existing software implementations.

Installation
------------

```bash
python3 -m pip install google-reader
```

Usage Example
-------------

```python
>>> import google_reader

>>> client = google_reader.Client("https://reader.example.org/")
>>> auth_token = client.login("my_username", "my_password")

>>> client.get_user_info(auth_token)
UserInfo(user_id='1', user_name='admin', user_email='admin@example.org', user_profile_id='1')

>>> client.list_subscriptions(auth_token)
[Subscription(id='feed/6', title='Feed Title', url='https://example.org/feed', html_url='https://example.org/', icon_url='https://reader.example.org/feed/icon/846d0be14a9676baabfb7fbb69a1fbca8bb9dad3', categories=[Category(id='user/1/label/My Test', label='My Test', type='folder')])]
```

Documentation
-------------

### Item IDs Format

Item IDs can be returned in short or long form depending on the API method.

- Long form: The prefix `tag:google.com,2005:reader/item/` followed by the ID as an unsigned base 16 number that is 0-padded so that it's always 16 characters wide.
- Short form: The ID as a signed base 10 number.

Examples:

```
tag:google.com,2005:reader/item/00000000148b9369	344691561
tag:google.com,2005:reader/item/00000000148b383e	344668222
tag:google.com,2005:reader/item/00000000148b3841	344668225
```

### Stream IDs

Streams can be feeds, tags (labels/folders) or states.

- Feed: `feed/http://example.org/feed` or `feed/123456`
- Tag: `user/-/label/Some Text`
- Read articles: `user/-/state/com.google/read`
- Starred articles: `user/-/state/com.google/starred`
- Broadcasted articles: `user/-/state/com.google/broadcast`
- Annotated articles: `user/-/state/com.google/annotated`
- Likes articles: `user/-/state/com.google/like`
- Saved web pages: `user/-/state/com.google/saved-web-pages`

### Client Login

Request:

- URL: `/accounts/ClientLogin`
- Method: `GET`

Querystring parameters:

* `Email`: the user's email
* `Passwd`: the user's account password

The plain text response contains 3 lines:

```
SID=...
LSID=...
Auth=<token>
```

The access token can be retrieved from the third line of the response and should be included in the `Authorization` header for each request:

```
Authorization: GoogleLogin auth=<token>
```

Some endpoints require the `POST` parameter `T` to include the access token.

Python example:

```python
>>> import google_reader

>>> client = google_reader.Client("https://reader.example.org/")

>>> client.login("my_username", "my_password")
AuthToken(TokenType='GoogleLogin', AccessToken='test/8eec3f60a23a5b5464245054f60eb9ced8d5655c')
```

### User Information

Request:

- URL: `/reader/api/0/user-info`
- Method: `GET`
- Supported formats: JSON

Response:

```json
{
  "userId": "1234",
  "userName": "test",
  "userProfileId": "1234",
  "userEmail": "test@example.org",
  "isBloggerUser": true,
  "signupTimeSec": 1163850013,
  "isMultiLoginEnabled": false
}
```

Python example:

```python
>>> import google_reader

>>> client = google_reader.Client("https://reader.example.org/")
>>> auth_token = client.login("my_username", "my_password")

>>> client.get_user_info(auth_token)
UserInfo(user_id='1234', user_name='test', user_email='test@example.org', user_profile_id='1234')
```

### Subscriptions List

Request:

- URL: `/reader/api/0/subscription/list`
- Method: `GET`
- Supported formats: JSON

Response:

```json
{
    "subscriptions": [
        "id": "feed/2",
        "title": "Kanboard Release Notes",
        "url": "https://kanboard.org/releases.xml"
        "htmlUrl": "https://kanboard.org/releases.html",
        "iconUrl": "http://localhost/feed/icon/d8276d41bd515db917b46a38d743932d0d02da51",
        "categories": [
            {
                "id": "user/1/label/All",
                "label": "All",
                "type": "folder"
            }
        ]
    ]
}
```

Python Example:

```python
>>> import google_reader

>>> client = google_reader.Client("https://reader.example.org/")
>>> auth_token = client.login("my_username", "my_password")

>>> client.list_subscriptions(auth_token)
[Subscription(id='feed/1', title='FreshRSS releases', url='https://github.com/FreshRSS/FreshRSS/releases.atom', html_url='https://github.com/FreshRSS/FreshRSS/', icon_url='http://127.0.0.1:8082/f.php?516d4293', categories=[Tag(id='user/-/label/Uncategorized', label='Uncategorized', type=None)])]
```

### Edit Subscription

Request:

- URL: `/reader/api/0/subscription/edit`
- Method: `POST`
- Supported formats: Returns "OK" in plain text
- POST token required: Yes

Creation:

- `ac`: the string `subscribe`
- `s`: the stream ID to create (`feed/<feed url>`)
- `t`: the name for this subscription
- `a`: the stream ID of a category. If the category doesn’t exist, it will be created (optional)

Edition:

- `ac`: the string `edit`
- `s`: the stream ID to edit (`feed/<feed url>`)
- `r` or `a`: the stream ID of a category. `r` moves the feed out of the category, `a` adds the feed to the category
- `t`: a new title for the feed

Deletion:

- `ac`: the string `unsubscribe`
- `s`: the stream ID to delete (`feed/<feed url>`)

Python Example:

```python
>>> import google_reader

>>> client = google_reader.Client("https://reader.example.org/")
>>> auth_token = client.login("my_username", "my_password")

>>> client.edit_subscription(auth_token, subscription_id="feed/1", action="edit", add_label_id=google_reader.get_label_id("Test"))
True

>>> c.edit_subscription(auth_token, subscription_id="feed/1", action="edit", title="FreshRSS Releases")
True
```

### Quick Add Subscription

Request:

- URL: `/reader/api/0/subscription/quickadd`
- Method: `POST`
- Supported formats: JSON
- POST token required: Yes

Response:

```json
{
  "query": "feed/http://feeds.arstechnica.com/arstechnica/science",
  "numResults": 1,
  "streamId": "feed/http://arstechnica.com/",
  "streamName": "Ars Technica » Scientific Method"
}
```

Python Example:

```python
>>> import google_reader

>>> client = google_reader.Client("https://reader.example.org/")
>>> auth_token = client.login("my_username", "my_password")

>>> client.quick_add_subscription(auth_token, url="https://lemonde.fr")
QuickAddSubscription(query='https://www.lemonde.fr/rss/une.xml', num_results=1, stream_id='feed/2', stream_name='Le Monde.fr - Actualités et Infos en France et dans le monde'
```

### Get Stream Items IDs

Request:

- URL: `/reader/api/0/stream/items/ids`
- Method: `GET`
- Supported formats: JSON
- POST token required: Yes

Querystring parameters:

- `s`: Stream ID
- `n`: Number of items to return
- `r`: Order direction. By default, it is newest first. You can pass the value `o` here to get oldest first.
- `ot`: Start time (unix timestamp) from which to start to get items.
- `xt`: Exclude Target. For example, set to `user/-/state/com.google/read` to exclude all read items.
- `it`: Include Target. For example, set to `user/-/state/com.google/starred` to include starred items.
- `c`: Continuation (pagination cursor).

Response:

```json
{
    "itemRefs": [
        {"id": "123"},
        {"id": "456"}
    ],
    "continuation": "abcde"
}
```

Python example:

```python
>>> import google_reader

>>> client = google_reader.Client("https://reader.example.org/")
>>> auth_token = client.login("my_username", "my_password")

>>> client.get_stream_items_ids(auth_token, stream_id="feed/1", limit=2)
StreamIDs(item_refs=[ItemRef(id='1746307865812560'), ItemRef(id='1746307865812559')], continuation='1746307865812559')
```

### Get Stream Items Contents

Request:

- URL: `/reader/api/0/stream/items/contents`
- Methods: `GET`
- Supported formats: JSON
- POST token required: Yes

Parameter:

- `i`: Item ID (can be repeated)

Response:

```json
{
    "alternate": [
        {
            "href": "https://miniflux.app/",
            "type": "text/html"
        }
    ],
    "author": "admin",
    "direction": "ltr",
    "id": "feed/22",
    "items": [
        {
            "alternate": [
                {
                    "href": "https://miniflux.app/releases/2.2.8.html",
                    "type": "text/html"
                }
            ],
            "author": "Myself",
            "canonical": [
                {
                    "href": "https://miniflux.app/releases/2.2.8.html"
                }
            ],
            "categories": [
                "user/1/state/com.google/reading-list",
                "user/1/label/All"
            ],
            "content": {
                "content": "long text",
                "direction": "ltr"
            },
            "crawlTimeMsec": "1746310821141",
            "enclosure": [

                {
                    "type": "application/octet-stream",
                    "url": "https://github.com/miniflux/v2/releases/download/2.2.8/miniflux-linux-amd64"
                },
                {
                    "type": "application/octet-stream",
                    "url": "https://github.com/miniflux/v2/releases/download/2.2.8/miniflux-linux-amd64.sha256"
                }
            ],
            "id": "tag:google.com,2005:reader/item/0000000000000468",
            "origin": {
                "htmlUrl": "https://miniflux.app/",
                "streamId": "feed/22",
                "title": "Miniflux"
            },
            "published": 1745280000,
            "summary": {
                "content": "long text",
                "direction": "ltr"
            },
            "timestampUsec": "1745280000000000",
            "title": "Miniflux 2.2.8",
            "updated": 1746310821
        }
    ],
    "self": [
        {
            "href": "http://localhost/reader/api/0/stream/items/contents"
        }
    ],
    "title": "Miniflux",
    "updated": 1746311274
}
```

Python example:

```python
>>> import google_reader

>>> client = google_reader.Client("https://reader.example.org/")
>>> auth_token = client.login("my_username", "my_password")

>>> c.get_stream_items_contents(auth_token, item_ids=[google_reader.get_long_item_id(1128)])
StreamContentItems(...)
```

### Edit Tags

Request:

- URL: `/reader/api/0/edit-tag`
- Method: `POST`
- Supported formats: Returns "OK" in plain text
- POST token required: Yes

Parameters:

- `i`: Item ID (can be repeated)
- `a`: tag to add to the items (can be repeated)
- `r`: tag to remove from the items (can be repeated)

Possible tags are:

- `user/-/state/com.google/kept-unread`
- `user/-/state/com.google/starred`
- `user/-/state/com.google/broadcast`
- `user/-/state/com.google/read`
- `user/-/state/com.google/like`
- `user/-/label/tag_name`

Python example:

```python
>>> import google_reader

>>> client = google_reader.Client("https://reader.example.org/")
>>> auth_token = client.login("my_username", "my_password")

>>> client.edit_tags(auth_token, item_ids=[google_reader.get_long_item_id(1128)], add_tags=[google_reader.STREAM_STARRED])
True
```

### Delete Tag

Request:

- URL: `/reader/api/0/disable-tag`
- Method: `POST`
- Supported formats: Returns "OK" in plain text
- POST token required: Yes

Parameters:

- `s`: Stream ID

Python example:

```python
>>> import google_reader

>>> client = google_reader.Client("https://reader.example.org/")
>>> auth_token = client.login("my_username", "my_password")

>>> client.disable_tag(auth_token, tag_id='user/-/label/Test')
True

>>> client.delete_tag(auth_token, tag_id='user/-/label/Test')
True
```

### Rename Tag

Request:

- URL: `/reader/api/0/rename-tag`
- Method: `POST`
- Supported formats: Returns "OK" in plain text
- POST token required: Yes

Parameters:

- `s`: Tag stream ID
- `dest`: New label name, for example: `user/-/label/<new label>`

Python example:

```python
>>> import google_reader

>>> client = google_reader.Client("https://reader.example.org/")
>>> auth_token = client.login("my_username", "my_password")

>>> client.rename_tag(auth_token, tag_id='user/-/label/All', new_label_name="Something Else")
True
```

### List Tags

Request:

- URL: `/reader/api/0/disable-tag`
- Method: `GET`
- Supported formats: JSON

Response:

```json
{
    "tags": [
        {"id": "user/1005921515/state/com.google/starred"},
        {"id": "user/1/label/My Test", "label": "My Test", "type": "folder"}
    ]
}

```

Python example:

```python
>>> import google_reader

>>> client = google_reader.Client("https://reader.example.org/")
>>> auth_token = client.login("my_username", "my_password")

>>> client.list_tags(auth_token)
[Tag(id='user/-/state/com.google/starred', label=None, type=None), Tag(id='user/-/label/Test', label=None, type='folder'), Tag(id='user/-/label/Uncategorized', label=None, type='folder')]

>>> client.list_tags(auth_token)
[Tag(id='user/1/state/com.google/starred', label=None, type=None), Tag(id='user/1/label/All', label='All', type='folder'), Tag(id='user/1/label/My Test', label='My Test', type='folder')]
```

### Resources

- https://www.inoreader.com/developers/
- https://feedhq.readthedocs.io/en/latest/api/
- https://github.com/bazqux/bazqux-api
- https://freshrss.github.io/FreshRSS/en/developers/06_GoogleReader_API.html
