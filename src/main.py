import sys
import time
import clipboard
import youtube_dl
import hashlib
from dataclasses import dataclass


VIDEO_PATH = '../videos/'

class DownloadFailedException(Exception):
    def __init__(self, download_url):
        self.download_url = download_url

@dataclass
class Video:
    url: str
    title: str
    extension: str

    def url_hash(self) -> str:
        return hashlib.sha256(self.url.encode()).hexdigest()

    def filename(self) -> str:
        return f'{self.url_hash()}.{self.extension}'

def get_clipboard_content():
    return clipboard.paste()

def is_url(s):
    return 'https://' in s

def download_video(url):
    def is_video_supported(url):
        extractors = youtube_dl.extractor.gen_extractors()
        for e in extractors:
            if e.suitable(url):
                return True
        return False

    if not is_video_supported(url):
        print('Video is not supported')
        raise DownloadFailedException(url)
    options = {
            'quiet': True,
            'outtmpl': '%(id)s.$(ext)s'
    }

    ydl = youtube_dl.YoutubeDL(options)
    with ydl:
        try:
            result = ydl.extract_info(url, download=False)
        except youtube_dl.utils.DownloadError:
            raise DownloadFailedException(url)
        except youtube_dl.utils.UnsupportedError:
            raise DownloadFailedException(url)
        except Exception as e:
            print(f'new error: {type(e)}')

    if 'entries' in result:
        video = result['entries'][0]
    else:
        video = result


    title = video['title']
    extension = video['ext']
    video = Video(url, video['title'], video['ext'])
    return video

def listen_for_changes(sleep_amount = 1):
    print('Listening for clipboard content...')
    active_clipboard_content = ''

    def get_new_clipboard_content():
        nonlocal active_clipboard_content
        current_clipboard_content = get_clipboard_content()

        if active_clipboard_content == current_clipboard_content:
            return None

        active_clipboard_content = current_clipboard_content
        return current_clipboard_content

    while True:
        content = get_new_clipboard_content()
        if content != None and is_url(content):
            print(f'New content: {content}')
            try:
                video = download_video(content)
                print(video.filename())
            except DownloadFailedException as e:
                print(f'Failed to download "{(e.download_url)}"')
        time.sleep(sleep_amount)

def main():
    listen_for_changes()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit()

