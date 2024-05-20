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

OUTPUT_DIR = "/tmp/downloads"

#  Create the output directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

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
    try:
        os.system(f'yt-dlp -f best -o "{OUTPUT_DIR}/{video_id}.mp4" {url}')
        if os.path.exists(f"{OUTPUT_DIR}/{video_id}.mp4"):
            return True
        else:
            print(f"Failed to download video {video_id}")
            return False
    except Exception as e:
        print(f"Error downloading video {video_id}: {e}")
        return False


def extract_segments(video_id, segments):
    input_file = f"{OUTPUT_DIR}/{video_id}.mp4"
    if not os.path.exists(input_file):
        print(f"Video file {input_file} does not exist.")
        return []

    output_files = []
    for idx, segment in enumerate(segments):
        start_time = segment["start"]
        duration = segment["duration"]
        output_file = f"{OUTPUT_DIR}/{video_id}_segment_{idx}.mp4"
        try:
            ffmpeg.input(input_file, ss=start_time, t=duration).output(
                output_file
            ).run()
            output_files.append(output_file)
        except ffmpeg.Error as e:
            print(f"FFmpeg error while processing {input_file}: {e}")
    return output_files


def compile_segments(output_files):
    if len(output_files) < 2:
        print("Not enough segments to concatenate.")
        return

    inputs = [ffmpeg.input(file) for file in output_files]
    joined = ffmpeg.concat(*inputs, v=1, a=1).output(
        f"{OUTPUT_DIR}/compiled_output.mp4"
    )
    try:
        joined.run()
    except ffmpeg.Error as e:
        print(f"FFmpeg error while compiling segments: {e}")


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


def main():
    quote = input("Enter the quote you want to search for: ")
    videos = search_youtube_videos(quote)
    for video in videos:
        video_id = video["videoId"]
        transcript = get_video_transcript(video_id)
        quote_segments = find_quote_in_transcript(transcript, quote)

        if quote_segments:
            if download_video(video_id):
                segment_files = extract_segments(video_id, quote_segments)
                if segment_files:
                    compile_segments(segment_files)
                    print(f"Compiled video for {video_id} is ready!")
            else:
                print(f"Failed to download video {video_id}")
        else:
            print(f"No matching segments found in video {video_id}")


if __name__ == "__main__":
    main()
