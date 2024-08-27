import requests

def test():
    response = requests.get('http://localhost:5000/nan')
    print(response.status_code)
    
if __name__ == "__main__":
    test()