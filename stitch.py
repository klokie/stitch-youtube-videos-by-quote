import os
import re
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
import ffmpeg

# YouTube API setup
# YOUTUBE_API_KEY = "YOUR_YOUTUBE_API_KEY"

from dotenv import load_dotenv

# load YOUTUBE_API_KEY from .env
load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")


youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)


def search_youtube_videos(query, max_results=5):
    search_response = (
        youtube.search()
        .list(q=query, part="id,snippet", maxResults=max_results, type="video")
        .execute()
    )

    videos = []
    for item in search_response["items"]:
        videos.append(
            {"videoId": item["id"]["videoId"], "title": item["snippet"]["title"]}
        )
    return videos


def get_video_transcript(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return transcript
    except Exception as e:
        print(f"Could not retrieve transcript for {video_id}: {e}")
        return []


def download_video(video_id):
    url = f"https://www.youtube.com/watch?v={video_id}"
    os.system(f'youtube-dl -f best -o "downloads/{video_id}.mp4" {url}')


def extract_segments(video_id, segments):
    input_file = f"downloads/{video_id}.mp4"
    for idx, segment in enumerate(segments):
        start_time = segment["start"]
        duration = segment["duration"]
        output_file = f"downloads/{video_id}_segment_{idx}.mp4"
        ffmpeg.input(input_file, ss=start_time, t=duration).output(output_file).run()


def compile_segments(video_id, segment_count):
    inputs = [
        ffmpeg.input(f"downloads/{video_id}_segment_{i}.mp4")
        for i in range(segment_count)
    ]
    joined = ffmpeg.concat(*inputs, v=1, a=1).output(
        f"downloads/{video_id}_compiled.mp4"
    )
    joined.run()


def find_quote_in_transcript(transcript, quote):
    quote_segments = []
    quote_words = re.findall(r"\w+", quote.lower())
    for i, entry in enumerate(transcript):
        entry_words = re.findall(r"\w+", entry["text"].lower())
        if all(word in entry_words for word in quote_words):
            quote_segments.append(
                {"start": entry["start"], "duration": entry["duration"]}
            )
    return quote_segments


def main(quote="let's go"):
    videos = search_youtube_videos(quote)
    for video in videos:
        video_id = video["videoId"]
        transcript = get_video_transcript(video_id)
        quote_segments = find_quote_in_transcript(transcript, quote)

        if quote_segments:
            download_video(video_id)
            extract_segments(video_id, quote_segments)
            compile_segments(video_id, len(quote_segments))
            print(f"Compiled video for {video_id} is ready!")
        else:
            print(f"No matching segments found in video {video_id}")


if __name__ == "__main__":
    quote = input("Enter the quote you want to search for: ")
    main(quote=quote)
