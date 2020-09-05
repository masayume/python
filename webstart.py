# webbrowser.py
import webbrowser

websites = [
            'https://mail.google.com/',
            'https://pinterest.co.uk',
            'https://tympanus.net/codrops/collective/collective-419/',
            'http://localhost:8989'
            ]

for website in websites:
    webbrowser.get(using='google-chrome').open_new_tab(website)