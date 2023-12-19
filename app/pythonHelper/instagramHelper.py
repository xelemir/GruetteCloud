from bs4 import BeautifulSoup

counterA = 0
counterB = 0
counterC = 0
counterD = 0
counterE = 0
counterOther = 0
users_recorded = []

# open the file
with open('post.html') as html_file:
    soup = BeautifulSoup(html_file, 'html.parser')
    
    # find the comments
    biggest_div = soup.find_all('div', class_='x9f619 xjbqb8w x78zum5 x168nmei x13lgxp2 x5pf9jr xo71vjh x1yztbdb x1uhb9sk x1plvlek xryxfnj x1c4vz4f x2lah0s xdt5ytf xqjyukv x1qjc9v5 x1oa3qoh x1nhvcw1')
    
    for div in biggest_div:
        # find comment within the biggest div
        comment = div.find('span', class_='_ap3a _aaco _aacu _aacx _aad7 _aade').text.lower()
        
        # find username within the biggest div
        username = div.find('a', class_='x1i10hfl xjqpnuy xa49m3k xqeqjp1 x2hbi6w xdl72j9 x2lah0s xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r x2lwn1j xeuugli x1hl2dhg xggy1nq x1ja2u2z x1t137rt x1q0g3np x1lku1pv x1a2a7pz x6s0dn4 xjyslct x1ejq31n xd10rxx x1sy0etr x17r0tee x9f619 x1ypdohk x1f6kntn xwhw2v2 xl56j7k x17ydfre x2b8uid xlyipyv x87ps6o x14atkfc xcdnw81 x1i0vuye xjbqb8w xm3z3ea x1x8b98j x131883w x16mih1h x972fbf xcfux6l x1qhh985 xm0m39n xt0psk2 xt7dq6l xexx8yu x4uap5 x18d9i69 xkhd6sd x1n2onr6 x1n5bzlp xqnirrm xj34u2y x568u83').text
        
        print(f"Username: {username} Comment: {comment}")

        if comment == 'a':
            if username not in users_recorded:
                users_recorded.append(username)
                counterA += 1
        elif comment == 'b':
            if username not in users_recorded:
                users_recorded.append(username)
                counterB += 1
        elif comment == 'c':
            if username not in users_recorded:
                users_recorded.append(username)
                counterC += 1
        elif comment == 'd':
            if username not in users_recorded:
                users_recorded.append(username)
                counterD += 1
        elif comment == 'e':
            if username not in users_recorded:
                users_recorded.append(username)
                counterE += 1
        else:
            counterOther += 1
            
    
    print()
    print(f"Counter A: {counterA}")
    print(f"Counter B: {counterB}")
    print(f"Counter C: {counterC}")
    print(f"Counter D: {counterD}")
    print(f"Counter E: {counterE}")
    
    print(f"Total: {counterA + counterB + counterC + counterD + counterE + counterOther}")