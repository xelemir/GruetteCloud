import requests
from bs4 import BeautifulSoup

class ApartmentHelper:
    def __init__(self):
        pass
    
    def search_product(self, url):
        request = requests.get(url).text
        soup = BeautifulSoup(request, 'html.parser')
        product = {"name": None, "price": None, "description": None, "images": None, "url": None}
        
        product_images = []
        images = soup.find_all('img', {'class': 'pip-image'})
        for image in images:
            product_images.append(image['src'])
        product["images"] = product_images
        
        name = soup.find('span', {'class': 'pip-header-section__title--big notranslate'})
        product["name"] = name.text
        
        price = soup.find('span', {'class': 'pip-temp-price__sr-text'})
        price = price.text.replace("€", "")
        price = price.replace("Preis", "")
        product["price"] = price.strip()
        
        description = soup.find('span', {'class': 'pip-header-section__description-text'})
        product["description"] = description.text
        
        product["url"] = url
        
        return product

    def get_items_(self):
        return  {"bedroom": [
                    {
                        "name": "MALM",
                        "price": "329€",
                        "description": "Bettgestell hoch mit 2 Schubladen, 140cm x 200cm, weiß",
                        "img": "https://www.ikea.com/de/de/images/products/malm-bettgestell-hoch-mit-2-schubkaesten-weiss-lindbaden__1101597_pe866769_s5.jpg",
                        "url": "https://www.ikea.com/de/de/p/malm-bettgestell-hoch-mit-2-schubkaesten-weiss-lindbaden-s59494995/",
                    },
                    {
                        "name": "ÅKREHAMN",
                        "price": "349€",
                        "description": "Matratze, mittelfest, weiß, 140cm x 200cm",
                        "img": "https://www.ikea.com/de/de/images/products/akrehamn-schaummatratze-mittelfest-weiss__1062618_pe851029_s5.jpg",
                        "url": "https://www.ikea.com/de/de/p/akrehamn-schaummatratze-mittelfest-weiss-30481644/",
                    },
                    {
                        "name": "2x RUMSMALVA",
                        "price": "26€",
                        "description": "Kissen, ergonomisch, 40cm x 80cm, weiß, 2 Stück",
                        "img": "https://www.ikea.com/de/de/images/products/rumsmalva-kissen-erg-seiten-rueckenschlaefer__0778781_pe759130_s5.jpg",
                        "url": "https://www.ikea.com/de/de/p/rumsmalva-kissen-erg-seiten-rueckenschlaefer-60446753/",
                    },
                    {
                        "name": "SMÅSPORRE",
                        "price": "23€",
                        "description": "Bettdecke, mittelwarm, 140cm x 200cm",
                        "img": "https://www.ikea.com/de/de/images/products/smasporre-decke-mittelwarm__0776665_pe758186_s5.jpg",
                        "url": "https://www.ikea.com/de/de/p/smasporre-decke-mittelwarm-00457004/",
                    },
                    {
                        "name": "BERGPALM",
                        "price": "40€",
                        "description": "Bettwäscheset, 2-teilig, grün, Streifen, 140cm x 200cm",
                        "img": "https://www.ikea.com/de/de/images/products/bergpalm-bettwaesche-set-2-teilig-gruen-streifen__0718512_pe731562_s5.jpg",
                        "url": "https://www.ikea.com/de/de/p/bergpalm-bettwaesche-set-2-teilig-gruen-streifen-20423211/",
                    },
                    {
                        "name": "NORDKISA",
                        "price": "299€",
                        "description": "Kleiderschrank offen, Schiebetür, Bambus",
                        "img": "https://www.ikea.com/de/de/images/products/nordkisa-kleiderschrank-offen-schiebetuer-bambus__0813677_ph165857_s5.jpg",
                        "url": "https://www.ikea.com/de/de/p/nordkisa-kleiderschrank-offen-schiebetuer-bambus-00439468/",
                    },
                    {
                        "name": "KALLAX 2x3",
                        "price": "65€",
                        "description": "Regal, weiß",
                        "img": "https://www.ikea.com/de/de/images/products/kallax-regal-weiss__1143200_pe881437_s5.jpg",
                        "url": "https://www.ikea.com/de/de/p/kallax-regal-weiss-90522420/",
                    },
                    {
                        "name": "IKORNNES",
                        "price": "149€",
                        "description": "Standspiegel, Esche",
                        "img": "https://www.ikea.com/de/de/images/products/ikornnes-standspiegel-esche__0858773_pe658292_s5.jpg",
                        "url": "https://www.ikea.com/de/de/p/ikornnes-standspiegel-esche-30298396/",
                    },
                    {
                        "name": "LAUTERS",
                        "price": "70€",
                        "description": "Standleuchte, Esche, weiß, E27 (nicht enthalten)",
                        "img": "https://www.ikea.com/de/de/images/products/lauters-standleuchte-esche-weiss__0879908_pe714870_s5.jpg",
                        "url": "https://www.ikea.com/de/de/p/lauters-standleuchte-esche-weiss-30405042/",
                    },
                    {
                        "name": "3x BRANÄS",
                        "price": "54€",
                        "description": "Korb, Rattan, passend für KALLAX, 3 Stück",
                        "img": "https://www.ikea.com/de/de/images/products/branaes-korb-rattan__0418392_pe575458_s5.jpg",
                        "url": "https://www.ikea.com/de/de/p/branaes-korb-rattan-00138432/",
                    },
                ],
                "livingroom": [
                    {
                        "name": "LANDSKRONA",
                        "price": "599€",
                        "description": "2er-Sofa, Gunnared hellgrün, Holz",
                        "img": "https://www.ikea.com/de/de/images/products/landskrona-2er-sofa-gunnared-hellgruen-holz__0828967_pe680176_s5.jpg",
                        "url": "https://www.ikea.com/de/de/p/landskrona-2er-sofa-gunnared-hellgruen-holz-s39270289/",
                    },
                    {
                        "name": "DAGLYSA",
                        "price": "199€",
                        "description": "Esstisch, Eichenfurnier",
                        "img": "https://www.ikea.com/de/de/images/products/daglysa-tisch-eichenfurnier__0871261_pe680260_s5.jpg",
                        "url": "https://www.ikea.com/de/de/p/daglysa-tisch-eichenfurnier-50402288/",
                    },
                    {
                        "name": "4x JOKKMOKK",
                        "price": "120€",
                        "description": "Stuhl, Antikbeize, 4 Stück",
                        "img": "https://www.ikea.com/de/de/images/products/jokkmokk-stuhl-antikbeize__0870916_pe716638_s5.jpg",
                        "url": "https://www.ikea.com/de/de/p/jokkmokk-stuhl-antikbeize-90342688/",
                    },
                    {
                        "name": "LAUTERS",
                        "price": "70€",
                        "description": "Standleuchte, Esche, weiß, E27 (nicht enthalten)",
                        "img": "https://www.ikea.com/de/de/images/products/lauters-standleuchte-esche-weiss__0879908_pe714870_s5.jpg",
                        "url": "https://www.ikea.com/de/de/p/lauters-standleuchte-esche-weiss-30405042/",
                    },
                    {
                        "name": "BESTÅ",
                        "price": "204€",
                        "description": "TV-Bank mit Türen, weiß, Lappviken weiß",
                        "img": "https://www.ikea.com/de/de/images/products/besta-tv-bank-mit-tueren-weiss-lappviken-weiss__0995908_pe821978_s5.jpg",
                        "url": "https://www.ikea.com/de/de/p/besta-tv-bank-mit-tueren-weiss-lappviken-weiss-s89330691/",
                    },
                    {
                        "name": "4x MALINDA",
                        "price": "28€",
                        "description": "Stuhlkissen, dunkelgrün, 4 Stück",
                        "img": "https://www.ikea.com/de/de/images/products/malinda-stuhlkissen-dunkelgruen__1138169_pe879870_s5.jpg",
                        "url": "https://www.ikea.com/de/de/p/malinda-stuhlkissen-dunkelgruen-50551061/",
                    },
                    {
                        "name": "KALLAX 2x4",
                        "price": "70€",
                        "description": "Regal, weiß",
                        "img": "https://www.ikea.com/de/de/images/products/kallax-regal-weiss__1084790_pe859876_s5.jpg",
                        "url": "https://www.ikea.com/de/de/p/kallax-regal-weiss-80275887/",
                    },
                    {
                        "name": "4x GNABBAS",
                        "price": "40€",
                        "description": "Korb, passend für KALLAX, 4 Stück",
                        "img": "https://www.ikea.com/de/de/images/products/gnabbas-korb__0945515_pe797708_s5.jpg?f=xl",
                        "url": "https://www.ikea.com/de/de/p/gnabbas-korb-60400298/",
                    },
                ],
                "sanitary": [
                    {
                        "name": "RÅGRUND",
                        "price": "50€",
                        "description": "Regal, Bambus",
                        "img": "https://www.ikea.com/de/de/images/products/ragrund-regal-bambus__0250172_pe379441_s5.jpg",
                        "url": "https://www.ikea.com/de/de/p/ragrund-regal-bambus-30253067/",
                    },
                ],
                "other": [
                    {
                        "name": "TJUSIG",
                        "price": "40€",
                        "description": "Schuhaufbewahrung, weiß",
                        "img": "https://www.ikea.com/de/de/images/products/tjusig-schuhaufbewahrung-weiss__0391790_pe560011_s5.jpg",
                        "url": "https://www.ikea.com/de/de/p/tjusig-schuhaufbewahrung-weiss-30152638/",
                    },
                    {
                        "name": "BAGGMUCK",
                        "price": "5€",
                        "description": "Schuhmatte, drinnen/draußen, graugrün",
                        "img": "https://www.ikea.com/de/de/images/products/baggmuck-schuhmatte-drinnen-draussen-graugruen__1164519_pe890593_s5.jpg",
                        "url": "https://www.ikea.com/de/de/p/baggmuck-schuhmatte-drinnen-draussen-graugruen-60550891/",
                    },
                    {
                        "name": "KULLEN",
                        "price": "69€",
                        "description": "Kommode mit 6 Schubladen, weiß",
                        "img": "https://www.ikea.com/de/de/images/products/kullen-kommode-mit-6-schubladen-weiss__0778050_pe758820_s5.jpg",
                        "url": "https://www.ikea.com/de/de/p/kullen-kommode-mit-6-schubladen-weiss-90309245/",
                    },
                    {
                        "name": "SKRUVBY",
                        "price": "40€",
                        "description": "Beistelltisch, weiß",
                        "img": "https://www.ikea.com/de/de/images/products/skruvby-beistelltisch-weiss__1123688_pe874847_s5.jpg",
                        "url": "https://www.ikea.com/de/de/p/skruvby-beistelltisch-weiss-80532009/",
                    },
                ],
            }
        

if __name__ == "__main__":
    pass

