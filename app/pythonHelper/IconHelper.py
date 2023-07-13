import requests

class IconHelper:
    def __init__(self):
        pass

    def get_icon(self, filename):
        extension = filename.split(".")[-1]
        
        if extension in ["jpg", "jpeg", "png", "gif", "bmp", "ico", "webp"]:
            return "https://jan.gruettefien.com/static/icons/image.svg"
        
        elif extension in ["mp3", "wav", "ogg", "flac", "aac", "wma", "m4a"]:
            return "https://jan.gruettefien.com/static/icons/audio.svg"
        
        elif extension in ["mp4", "webm", "ogg", "flv", "avi", "mov", "wmv", "mkv"]:
            return "https://jan.gruettefien.com/static/icons/video.svg"
        
        elif extension in ["doc", "docx", "odt", "rtf", "txt", "ppt", "pptx", "odp", "xls", "xlsx", "ods", "csv"]:
            return "https://jan.gruettefien.com/static/icons/document.svg"
        
        elif extension == "py":
            return "https://jan.gruettefien.com/static/icons/python.svg"
    
        if requests.get("https://jan.gruettefien.com/static/icons/" + extension + ".svg").status_code == 200:
            return "https://jan.gruettefien.com/static/icons/" + extension + ".svg"
        else: 
            return "https://jan.gruettefien.com/static/icons/search.svg"

if __name__ == "__main__":
    icon = IconHelper()
    print(icon.get_icon("test.audio"))