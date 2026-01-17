import os
import re
from googleapiclient.discovery import build
from fastapi import HTTPException

# ambil API key dari environment
API_KEY = os.getenv("YOUTUBE_API_KEY")

if not API_KEY:
    raise RuntimeError("YOUTUBE_API_KEY belum diset")

youtube = build("youtube", "v3", developerKey=API_KEY)


def extract_video_id(url: str) -> str:
    pattern = r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})"
    match = re.search(pattern, url)
    if not match:
        raise HTTPException(status_code=400, detail="URL YouTube tidak valid")
    return match.group(1)


def get_top_level_comments(video_id: str) -> list:
    comments = []
    next_page_token = None

    while True:
        response = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=100,
            textFormat="plainText",
            pageToken=next_page_token
        ).execute()

        for item in response["items"]:
            snippet = item["snippet"]["topLevelComment"]["snippet"]
            comments.append({
                "comment_id": item["id"],
                "author": snippet["authorDisplayName"],
                "text": snippet["textDisplay"],
                "published_at": snippet["publishedAt"],
                "like_count": snippet["likeCount"]
            })

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

    return comments


def get_replies(parent_id: str) -> list:
    replies = []
    next_page_token = None

    while True:
        response = youtube.comments().list(
            part="snippet",
            parentId=parent_id,
            maxResults=100,
            textFormat="plainText",
            pageToken=next_page_token
        ).execute()

        for item in response["items"]:
            snippet = item["snippet"]
            replies.append({
                "comment_id": item["id"],
                "author": snippet["authorDisplayName"],
                "text": snippet["textDisplay"],
                "published_at": snippet["publishedAt"],
                "like_count": snippet["likeCount"]
            })

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

    return replies


def fetch_all_comments(video_url: str) -> list:
    video_id = extract_video_id(video_url)
    top_comments = get_top_level_comments(video_id)

    all_comments = []
    for comment in top_comments:
        all_comments.append(comment)
        replies = get_replies(comment["comment_id"])
        all_comments.extend(replies)

    return all_comments
