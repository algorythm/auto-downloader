import sys
import time
import clipboard


def get_clipboard_content():
    return clipboard.paste()

def is_url(s):
    return 'https://' in s

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
        time.sleep(sleep_amount)

def main():
    listen_for_changes()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit()
