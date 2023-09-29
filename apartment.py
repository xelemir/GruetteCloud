from bs4 import BeautifulSoup
import requests

request = requests.get('https://www.ikea.com/de/de/p/nordkisa-kleiderschrank-offen-schiebetuer-bambus-00439468/').text
soup = BeautifulSoup(request, 'html.parser')

images = soup.find_all('img', {'class': 'pip-image'})

print(images)