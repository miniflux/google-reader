from dataclasses import dataclass
from typing import Literal
import requests

# Streams can be feeds, tags (folders) or system types.
STREAM_FEED = "feed/{feed_id}"
STREAM_TAG = "user/-/label/{label_title}"
STREAM_READ = "user/-/state/com.google/read"
STREAM_STARRED = "user/-/state/com.google/starred"
STREAM_KEPT_UNREAD = "user/-/state/com.google/kept-unread"
STREAM_BROADCAST = "user/-/state/com.google/broadcast"


class ClientError(Exception):
    """Base class for Google Reader API errors."""

    pass


class AuthenticationError(ClientError):
    """Raised when authentication fails."""

    def __init__(self, message: str):
        super().__init__(message)


@dataclass(frozen=True)
class AuthToken:
    TokenType: str
    AccessToken: str


@dataclass(frozen=True)
class UserInfo:
    user_id: str
    user_name: str
    user_email: str
    user_profile_id: str


@dataclass(frozen=True)
class Tag:
    id: str
    label: str | None = None
    type: str | None = None


@dataclass(frozen=True)
class Subscription:
    id: str
    title: str
    url: str
    html_url: str
    icon_url: str
    categories: list[Tag]


@dataclass(frozen=True)
class ItemRef:
    id: str


@dataclass(frozen=True)
class StreamIDs:
    item_refs: list[ItemRef]
    continuation: str | None


@dataclass(frozen=True)
class ContentHREF:
    href: str


@dataclass(frozen=True)
class ContentHREFType:
    href: str
    type: str


@dataclass(frozen=True)
class ContentItemEnclosure:
    url: str
    type: str


@dataclass(frozen=True)
class ContentItemContent:
    direction: str
    content: str


@dataclass(frozen=True)
class ContentItemOrigin:
    stream_id: str
    title: str
    html_url: str


@dataclass(frozen=True)
class ContentItem:
    id: str
    categories: list[str]
    title: str
    crawl_time_msec: str
    timestamp_usec: str
    published: int
    updated: int
    author: str
    alternate: list[ContentHREFType]
    summary: ContentItemContent
    content: ContentItemContent
    origin: ContentItemOrigin
    enclosure: list[ContentItemEnclosure]
    canonical: list[ContentHREF]


@dataclass(frozen=True)
class StreamContentItems:
    direction: str
    id: str
    title: str
    self: list[ContentHREF]
    alternate: list[ContentHREFType]
    updated: int
    items: list[ContentItem]
    author: str


@dataclass(frozen=True)
class QuickAddSubscription:
    query: str
    num_results: int
    stream_id: str
    stream_name: str


class Client:
    """
    Client for interacting with the Google Reader API.
    """

    def __init__(
        self, base_url: str, session: requests.Session | None = None, user_agent: str = "Google Reader Python Client"
    ):
        """
        Initialize a new Google Reader API Client.

        Args:
            base_url: Base URL of the Miniflux instance (e.g., "https://reader.miniflux.app")
            session: Optional requests.Session object for making HTTP requests.
            user_agent: User agent string for the HTTP requests.
        """
        self._base_url = base_url.rstrip("/")
        self._session = session or requests.Session()
        self._session.headers.update({"User-Agent": user_agent})

    def login(self, username: str, password: str) -> AuthToken:
        """
        Log in to the Google Reader API.

        Args:
            username: Username for the Google Reader account.
            password: Password for the Google Reader account.
        """
        response = self._session.post(
            f"{self._base_url}/accounts/ClientLogin", data={"Email": username, "Passwd": password}
        )
        if response.status_code != 200:
            raise AuthenticationError("Authentication failed")

        auth_data = {}
        for line in response.text.strip().split("\n"):
            key, value = line.split("=", 1)
            auth_data[key] = value

        auth_token = auth_data.get("Auth")
        if not auth_token:
            raise AuthenticationError("No Auth token found in response")
        return AuthToken(TokenType="GoogleLogin", AccessToken=auth_token)

    def get_user_info(self, auth: AuthToken) -> UserInfo:
        """
        Get user information from the Google Reader API.

        Args:
            auth(AuthToken): Authentication token obtained from the login process.
        Returns:
            UserInfo: User information object containing user ID, name, email, and profile ID.
        Raises:
            ClientError: If the request fails or the response is not valid.
            AuthenticationError: If the authentication token is invalid.
        """
        response = self._session.get(
            f"{self._base_url}/reader/api/0/user-info",
            headers={"Authorization": f"{auth.TokenType} auth={auth.AccessToken}"},
            params={"output": "json"},
        )
        if response.status_code == 401:
            raise AuthenticationError("Authentication failed")
        elif response.status_code != 200:
            raise ClientError("Failed to get user info")

        user_info = response.json()
        return UserInfo(
            user_id=user_info.get("userId", ""),
            user_name=user_info.get("userName", ""),
            user_email=user_info.get("userEmail", ""),
            user_profile_id=user_info.get("userProfileId", ""),
        )

    def list_subscriptions(self, auth: AuthToken) -> list[Subscription]:
        """
        Get the list of subscriptions from the Google Reader API.

        Args:
            auth(AuthToken): Authentication token obtained from the login process.
        Returns:
            List of Subscription objects.
        Raises:
            ClientError: If the request fails or the response is not valid.
            AuthenticationError: If the authentication token is invalid.
        """
        response = self._session.get(
            f"{self._base_url}/reader/api/0/subscription/list",
            headers={"Authorization": f"{auth.TokenType} auth={auth.AccessToken}"},
            params={"output": "json"},
        )
        if response.status_code == 401:
            raise AuthenticationError("Authentication failed")
        elif response.status_code != 200:
            raise ClientError("Failed to get subscriptions")

        return [
            Subscription(
                id=sub.get("id", ""),
                title=sub.get("title", ""),
                url=sub.get("url", ""),
                html_url=sub.get("htmlUrl", ""),
                icon_url=sub.get("iconUrl", ""),
                categories=[Tag(**cat) for cat in sub.get("categories", [])],
            )
            for sub in response.json().get("subscriptions", [])
        ]

    def edit_subscription(
        self,
        auth: AuthToken,
        subscription_id: str,
        action: Literal["edit", "subscribe", "unsubscribe"],
        remove_label_id: str | None = None,
        add_label_id: str | None = None,
        title: str | None = None,
    ) -> bool:
        """
        Edit a subscription.

        Args:
            auth(AuthToken): Authentication token obtained from the login process.
            subscription_id(str): ID of the subscription to edit.
            action(str): Action to perform on the subscription (edit, subscribe, unsubscribe).
            remove_label_id(str): Label to remove from the subscription.
            add_label_id(str): Label to add to the subscription.
            title(str): New title for the subscription.
        Returns:
            bool: True if the operation was successful, False otherwise.
        Raises:
            ClientError: If the request fails or the response is not valid.
            AuthenticationError: If the authentication token is invalid.
        """
        data = {"s": subscription_id, "ac": action, "T": auth.AccessToken}
        if remove_label_id:
            data["r"] = remove_label_id
        if add_label_id:
            data["a"] = add_label_id
        if title:
            data["t"] = title
        response = self._session.post(
            f"{self._base_url}/reader/api/0/subscription/edit",
            headers={"Authorization": f"{auth.TokenType} auth={auth.AccessToken}"},
            params={"output": "json"},
            data=data,
        )
        if response.status_code == 401:
            raise AuthenticationError("Authentication failed")
        elif response.status_code != 200:
            raise ClientError("Failed to edit subscription")
        return True

    def quick_add_subscription(self, auth: AuthToken, url: str) -> QuickAddSubscription:
        """
        Quick add a subscription.

        Args:
            auth(AuthToken): Authentication token obtained from the login process.
            url(str): URL of the subscription to add.
        Returns:
            QuickAddSubscription: Object containing the result of the quick add operation.
        Raises:
            ClientError: If the request fails or the response is not valid.
            AuthenticationError: If the authentication token is invalid.
        """
        response = self._session.post(
            f"{self._base_url}/reader/api/0/subscription/quickadd",
            headers={"Authorization": f"{auth.TokenType} auth={auth.AccessToken}"},
            params={"output": "json"},
            data={"quickadd": url, "T": auth.AccessToken},
        )
        if response.status_code == 401:
            raise AuthenticationError("Authentication failed")
        elif response.status_code != 200:
            raise ClientError("Failed to quick add subscription")

        response = response.json()
        return QuickAddSubscription(
            query=response.get("query", ""),
            num_results=response.get("numResults", 0),
            stream_id=response.get("streamId", ""),
            stream_name=response.get("streamName", ""),
        )

    def get_stream_items_ids(
        self,
        auth: AuthToken,
        stream_id: str,
        limit: int = 1000,
        direction: Literal["asc", "desc"] = "desc",
        start_time: int | None = None,
        continuation: str | None = None,
        exclude_target: Literal["user/-/state/com.google/read"] | None = None,
        include_target: Literal[
            "user/-/state/com.google/read", "user/-/state/com.google/starred", "user/-/state/com.google/like"
        ]
        | None = None,
    ) -> StreamIDs:
        """
        Get item IDs for a given stream.

        Args:
            stream_id(str): ID of the stream to retrieve item IDs from.
            limit(int): Maximum number of items to retrieve.
            direction(Literal["asc", "desc"]): Direction to retrieve items (ascending or descending).
            start_time(int | None): Optional start time for retrieving items.
            continuation(str | None): Optional continuation token for pagination.
            exclude_target(str | None): Optional target to exclude from results.
            include_target(str | None): Optional target to include in results.
        Returns:
            List of item IDs.
        """
        params = {"output": "json", "s": stream_id, "n": limit}
        if direction == "asc":
            params["r"] = "o"
        if start_time:
            params["ot"] = start_time
        if exclude_target:
            params["xt"] = exclude_target
        if include_target:
            params["it"] = include_target
        if continuation:
            params["c"] = continuation

        response = self._session.get(
            f"{self._base_url}/reader/api/0/stream/items/ids",
            headers={"Authorization": f"{auth.TokenType} auth={auth.AccessToken}"},
            params=params,
        )
        if response.status_code == 401:
            raise AuthenticationError("Authentication failed")
        elif response.status_code != 200:
            raise ClientError("Failed to get item IDs")

        data = response.json()
        return StreamIDs(
            item_refs=[ItemRef(id=item["id"]) for item in data.get("itemRefs", [])],
            continuation=data.get("continuation", ""),
        )

    def get_stream_items_contents(self, auth: AuthToken, item_ids: list[str]) -> StreamContentItems:
        """
        Get the contents of items

        Args:
            auth(AuthToken): Authentication token obtained from the login process.
            item_ids(list[str]): List of item IDs to retrieve.
        Returns:
            StreamContentItems: List of item contents.
        Raises:
            ClientError: If the request fails or the response is not valid.
            AuthenticationError: If the authentication token is invalid.
        """
        response = self._session.post(
            f"{self._base_url}/reader/api/0/stream/items/contents",
            headers={"Authorization": f"{auth.TokenType} auth={auth.AccessToken}"},
            params={"output": "json"},
            data={"i": item_ids, "T": auth.AccessToken},
        )
        if response.status_code == 401:
            raise AuthenticationError("Authentication failed")
        elif response.status_code != 200:
            raise ClientError("Failed to get item contents")

        data = response.json()
        return StreamContentItems(
            direction=data.get("direction", ""),
            id=data.get("id", ""),
            title=data.get("title", ""),
            self=[ContentHREF(**item) for item in data.get("self", [])],
            alternate=[ContentHREFType(**item) for item in data.get("alternate", [])],
            updated=data.get("updated", 0),
            items=[
                ContentItem(
                    id=item.get("id", ""),
                    categories=item.get("categories", []),
                    title=item.get("title", ""),
                    crawl_time_msec=item.get("crawlTimeMsec", ""),
                    timestamp_usec=item.get("timestampUsec", ""),
                    published=item.get("published", 0),
                    updated=item.get("updated", 0),
                    author=item.get("author", ""),
                    alternate=[
                        ContentHREFType(href=alt.get("href", ""), type=alt.get("type", ""))
                        for alt in item.get("alternate", [])
                    ],
                    summary=ContentItemContent(
                        direction=item.get("summary", {}).get("direction", ""),
                        content=item.get("summary", {}).get("content", ""),
                    ),
                    content=ContentItemContent(
                        direction=item.get("content", {}).get("direction", ""),
                        content=item.get("content", {}).get("content", ""),
                    ),
                    origin=ContentItemOrigin(
                        stream_id=item.get("origin", {}).get("streamId", ""),
                        title=item.get("origin", {}).get("title", ""),
                        html_url=item.get("origin", {}).get("htmlUrl", ""),
                    ),
                    enclosure=[ContentItemEnclosure(**enc) for enc in item.get("enclosure", [])],
                    canonical=[ContentHREF(**can) for can in item.get("canonical", [])],
                )
                for item in data.get("items", [])
            ],
            author=data.get("author", ""),
        )

    def edit_tags(
        self,
        auth: AuthToken,
        item_ids: list[str],
        add_tags: list[str] | None = None,
        remove_tags: list[str] | None = None,
    ) -> bool:
        """
        Edit tags for a list of items.

        Args:
            auth(AuthToken): Authentication token obtained from the login process.
            item_ids(list[str]): List of item IDs to edit tags for.
            add_tags(list[str]): List of tags to add.
            remove_tags(list[str]): List of tags to remove.
        Returns:
            bool: True if the operation was successful, False otherwise.
        Raises:
            ClientError: If the request fails or the response is not valid.
            AuthenticationError: If the authentication token is invalid.
        """
        data = {"i": item_ids, "T": auth.AccessToken}
        if add_tags:
            data["a"] = add_tags
        if remove_tags:
            data["r"] = remove_tags
        if not add_tags and not remove_tags:
            raise ClientError("No tags to add or remove")
        response = self._session.post(
            f"{self._base_url}/reader/api/0/edit-tag",
            headers={"Authorization": f"{auth.TokenType} auth={auth.AccessToken}"},
            params={"output": "json"},
            data=data,
        )
        if response.status_code == 401:
            raise AuthenticationError("Authentication failed")
        elif response.status_code != 200:
            raise ClientError("Failed to edit tags")
        return True

    def disable_tag(self, auth: AuthToken, tag_id: str) -> bool:
        """
        Deletes a category or a tag.

        Args:
            auth(AuthToken): Authentication token obtained from the login process.
            tag_id(str): ID of the tag to delete.
        Returns:
            bool: True if the operation was successful, False otherwise.
        Raises:
            ClientError: If the request fails or the response is not valid.
            AuthenticationError: If the authentication token is invalid.
        """
        response = self._session.post(
            f"{self._base_url}/reader/api/0/disable-tag",
            headers={"Authorization": f"{auth.TokenType} auth={auth.AccessToken}"},
            params={"output": "json"},
            data={"s": tag_id, "T": auth.AccessToken},
        )
        if response.status_code == 401:
            raise AuthenticationError("Authentication failed")
        elif response.status_code != 200:
            raise ClientError("Failed to disable tags")
        return True

    def delete_tag(self, auth: AuthToken, tag_id: str) -> bool:
        """
        Deletes a category or a tag.

        Args:
            auth(AuthToken): Authentication token obtained from the login process.
            tag_id(str): ID of the tag to delete.
        Returns:
            bool: True if the operation was successful, False otherwise.
        Raises:
            ClientError: If the request fails or the response is not valid.
            AuthenticationError: If the authentication token is invalid.
        """
        return self.disable_tag(auth, tag_id)

    def rename_tag(self, auth: AuthToken, tag_id: str, new_label_name: str) -> bool:
        """
        Rename a category or a tag.

        Args:
            auth(AuthToken): Authentication token obtained from the login process.
            tag_id(str): ID of the tag to rename.
            new_label_name(str): New name for the category or tag.
        Returns:
            bool: True if the operation was successful, False otherwise.
        Raises:
            ClientError: If the request fails or the response is not valid.
            AuthenticationError: If the authentication token is invalid.
        """
        response = self._session.post(
            f"{self._base_url}/reader/api/0/rename-tag",
            headers={"Authorization": f"{auth.TokenType} auth={auth.AccessToken}"},
            params={"output": "json"},
            data={"s": tag_id, "dest": get_label_id(new_label_name), "T": auth.AccessToken},
        )
        if response.status_code == 401:
            raise AuthenticationError("Authentication failed")
        elif response.status_code != 200:
            raise ClientError("Failed to rename tags")
        return True

    def list_tags(self, auth: AuthToken) -> list[Tag]:
        """
        Get the list of tags from the Google Reader API.

        Args:
            auth(AuthToken): Authentication token obtained from the login process.
        Returns:
            List of Tag objects.
        Raises:
            ClientError: If the request fails or the response is not valid.
            AuthenticationError: If the authentication token is invalid.
        """
        response = self._session.get(
            f"{self._base_url}/reader/api/0/tag/list",
            headers={"Authorization": f"{auth.TokenType} auth={auth.AccessToken}"},
            params={"output": "json"},
        )
        if response.status_code == 401:
            raise AuthenticationError("Authentication failed")
        elif response.status_code != 200:
            raise ClientError("Failed to get tags")

        return [Tag(**tag) for tag in response.json().get("tags", [])]


def get_long_item_id(item_id: int) -> str:
    """
    Convert a short item ID to a long item ID.

    Args:
        item_id(int): Short item ID.
    Returns:
        Long item ID.
    """
    return f"tag:google.com,2005:reader/item/{item_id:016x}"


def get_label_id(label_title: str) -> str:
    """
    Convert a label to a label ID.

    Args:
        label_title(str): Label name.
    Returns:
        Label stream ID.
    """
    return STREAM_TAG.format(label_title=label_title)
