import sys
import time
import clipboard
import youtube_dl
import hashlib
from dataclasses import dataclass
import requests
from bs4 import BeautifulSoup


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
        return f'{self.url_hash()}__{self.title}.{self.extension}'

def get_clipboard_content():
    return clipboard.paste()

def is_url(s):
    return 'https://' in s

def try_get_alternative_video_url(url):
    # print(url)
    req = requests.get(url)
    soup = BeautifulSoup(req.text, 'html.parser')
    iframes = soup.select('div.responsive-player > iframe[src]')
    if iframes is None or len(iframes) == 0:
        return None
    meta_title = soup.findAll('meta', {'itemprop': 'name'})
    title = None
    if meta_title is not None and len(meta_title) > 0:
        title = meta_title[0]['content']
        print('title is', title)
    player_url = iframes[0]['src']
    # print(player_url)

    player_request = requests.get(player_url)
    player_soup = BeautifulSoup(player_request.text, 'html.parser')
    video_sources = player_soup.select('video#video > source')
    print('found sources:')
    for video_source in video_sources:
        print('-', video_source['title'], video_source['src'])

    alternative_url = video_sources[0]['src']
    alternative_url_size = video_sources[0]['title']
    # print(alternative_url)
    return alternative_url, title, alternative_url_size


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
    alternative_title = None
    with ydl:
        try:
            result = ydl.extract_info(url, download=False)
        except youtube_dl.utils.DownloadError:
            alternative_url, alternative_title, size = try_get_alternative_video_url(url)
            if alternative_url is None:
                raise DownloadFailedException(url)

            print('alternative url', alternative_url)
            result = ydl.extract_info(alternative_url, download=False)
            url = alternative_url
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

    if alternative_title is not None:
        print('changing title')
        title = alternative_title
    video = Video(url, title, extension)

    return video

videos_to_download = []

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
                print('title is', video.title)
                print('filename is', video.filename())
                print('download url is', video.url)
                videos_to_download.append(video)
            except DownloadFailedException as e:
                print(f'Failed to download "{(e.download_url)}"')
        time.sleep(sleep_amount)

def main():
    # .responsive-player > iframe
    listen_for_changes()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        for video in videos_to_download:
            print('will now download', video.title, 'from', video.url)
            print(video)
            options = {
                # 'quiet': True,
                'outtmpl': f'videos/{video.filename()}'
            }
            ydl = youtube_dl.YoutubeDL(options)
            ydl.download([video.url])
        sys.exit()

