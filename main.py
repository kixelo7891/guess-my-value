import requests
from bs4 import BeautifulSoup
import pandas as pd
import random
import time

headers = {'User-Agent':
               'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36'}

#pages = ["https://www.transfermarkt.com/slovan-bratislava/startseite/verein/540/saison_id/2025",
#         "https://www.transfermarkt.com/msk-zilina/startseite/verein/1443/saison_id/2025",
#         "https://www.transfermarkt.com/spartak-trnava/startseite/verein/365/saison_id/2025",
#        "https://www.transfermarkt.com/mfk-dukla-banska-bystrica/startseite/verein/20758/saison_id/2025",
#        "https://www.transfermarkt.com/dac-dunajska-streda/startseite/verein/4529/saison_id/2025",
#         "https://www.transfermarkt.com/as-trencin/startseite/verein/7918/saison_id/2025",
#         "https://www.transfermarkt.com/fk-zeleziarne-podbrezova/startseite/verein/20063/saison_id/2025",
#         "https://www.transfermarkt.com/mfk-ruzomberok/startseite/verein/7087/saison_id/2025",
#         "https://www.transfermarkt.com/mfk-skalica/startseite/verein/35488/saison_id/2025",
#         "https://www.transfermarkt.com/fc-kosice/startseite/verein/51316/saison_id/2025",
#         "https://www.transfermarkt.com/zemplin-michalovce/startseite/verein/13744/saison_id/2025",
#         "https://www.transfermarkt.com/1-fc-tatran-presov/startseite/verein/4531/saison_id/2025",
#         "https://www.transfermarkt.com/kfc-komarno/startseite/verein/32314"]

page = 'https://www.transfermarkt.com/fortuna-liga/startseite/wettbewerb/SLO1'
tree = requests.get(page, headers = headers)
soup = BeautifulSoup(tree.content, 'html.parser')
#print(soup)

pages = []
links = soup.find_all("td", class_="hauptlink no-border-links") #.find("a")['href']
for link in links:
    #print(f"https://www.transfermarkt.com{link.a['href']}")
    pages.append(f"https://www.transfermarkt.com{link.a['href']}")


def scrape_data():
    all_players = []
    all_values = []
    all_clubs = []
    all_logos = []
    all_images = []

    for page in pages:
        pageTree = requests.get(page, headers=headers)
        pageSoup = BeautifulSoup(pageTree.content, 'html.parser')

        club_name = page.split("/")[3].replace("-", " ").title()

        logo_tag = pageSoup.select_one("img.tiny_wappen")
        logo_url = logo_tag["src"] if logo_tag else ""
        logo_url = logo_url.replace("/tiny/", "/head/")

        print(f"Scraping: {club_name} | logo: {'✓' if logo_url else '✗'}")

        # logo_tag = pageSoup.find("img", {"class": "tm-clubs-list__club-image"})
        # if not logo_tag:
        #     logo_tag = pageSoup.find("img", {"class": "data-header__club-link"})
        # if not logo_tag:
        #     # fallback - hľadaj podľa alt textu v hlavičke
        #     logo_tag = pageSoup.select_one("div.data-header img")
        # logo_url = logo_tag["src"] if logo_tag else ""
        #
        # club_tag = pageSoup.select_one("h1.data-header__headline-wrapper")
        # if not club_tag:
        #     club_tag = pageSoup.select_one("h1")
        # club_name = club_tag.text.strip() if club_tag else "Unknown"
        #
        # img_tag = row.find("img", {"class": "bilderrahmen-fixed"})
        # img_url = ""
        #
        # if img_tag:
        #     img_url = (img_tag.get("data-src") or img_tag.get("src") or "")
        #     img_url = img_url.split("?lm")[0]
        # all_images.append(img_url)

        rows = pageSoup.find_all("tr", {"class": ["odd", "even"]})
        for row in rows:
            name_cell = row.find("td", {"class": "hauptlink"})
            value_cell = row.find("td", {"class": "rechts hauptlink"})

            if not name_cell or not name_cell.a:
                continue
            if not value_cell:
                continue

            name = name_cell.text.strip().replace("\n", "").replace("\xa0", "")
            raw_value = value_cell.text.strip()

            # if name_cell and value_cell:
            #     name = name_cell.text.strip().replace("\n", "").replace("\xa0", "")
            #     raw_value = value_cell.text.strip()

            if raw_value in ["-", ""]:
                continue

            value = (raw_value
                    .replace("€", "")
                    .replace(".", "")
                    .replace("k", "000")
                    .replace("m", "0000")
                    .strip())

            img_tag = row.find("img", {"class": "bilderrahmen-fixed"})
            img_url = ""
            if img_tag:
                img_url = img_tag.get("data-src") or img_tag.get("src") or ""
                if "silhouette" in img_url:
                    img_url = ""
                else:
                    img_url = img_url.split("?lm")[0]
                    img_url = img_url.replace("/medium/", "/big/")

            all_players.append(name)
            all_values.append(value)
            all_clubs.append(club_name)
            all_logos.append(logo_url)
            all_images.append(img_url)

        time.sleep(random.uniform(1.5, 3.0))  # be polite to the server

    return all_players, all_values, all_clubs, all_logos, all_images

def football_player_guess_game(df):
    x = 10
    success = 0
    while x > 0:
        # Randomly select two different indices
        indices = random.sample(range(len(df)), 2)

        # Display the names and ask for the guess
        print(f"Football Player Value Guessing Game, you have {x} attempt(s):")
        user_guess = input(
            f"{df['Players'][indices[0]]} market value is €{int(df['Values'][indices[0]]) / 1000000}m.\n Does {df['Players'][indices[1]]} have a HIGHER or LOWER market value than {df['Players'][indices[0]]}?\n  Type 'H' for HIGHER and type 'L' for LOWER: ")

        # Check the answer
        user_guess = user_guess.lower()
        if user_guess == "h":
            if int(df['Values'][indices[1]]) > int(df['Values'][indices[0]]) and not int(df['Values'][indices[0]]) == int(df['Values'][indices[1]]):
                print(
                    f"Correct! You guessed it right. {df['Players'][indices[1]]} value is €{int(df['Values'][indices[1]]) / 1000000}m.\n")
                x -= 1
                success += 1
                time.sleep(2)

            elif int(df['Values'][indices[1]]) < int(df['Values'][indices[0]]) and not int(df['Values'][indices[0]]) == int(df['Values'][indices[1]]):
                print(
                    f"Wrong! because {df['Players'][indices[1]]} value is only €{int(df['Values'][indices[1]]) / 1000000}m.\n")
                x -= 1
                time.sleep(2)

        elif user_guess == "l":
            if int(df['Values'][indices[0]]) > int(df['Values'][indices[1]]) and not int(df['Values'][indices[0]]) == int(df['Values'][indices[1]]):
                print(
                    f"Yes you are right, {df['Players'][indices[1]]} value is lower --->>> €{int(df['Values'][indices[1]]) / 1000000}m.\n")
                x -= 1
                success += 1
                time.sleep(2)

            elif int(df['Values'][indices[0]]) < int(df['Values'][indices[1]]) and not int(df['Values'][indices[0]]) == int(df['Values'][indices[1]]):
                print(
                    f"Wrong answer! because {df['Players'][indices[1]]} value is higher --->>> €{int(df['Values'][indices[1]]) / 1000000}m.\n")
                x -= 1
                time.sleep(2)

        else:
            print("I do not understand your query...\n")
            x -= 1
            time.sleep(1)

    if success > 8:
        print(f"Excellent! You're master of Niké Liga, because your success rate is {success*10}%.")
    elif success >= 1 and success <= 8:
        print(f"Not great not terrible... your success rate is {success*10}%.")
    else:
        print(f"You should watch more 'Bavme sa o lige.' magazine... because your success rate is {success*10}%.")


# Run the game
#football_player_guess_game()
if __name__ == "__main__":
    players, values, clubs, logos, players_images = scrape_data()
    print(f"Scraped {len(players)} players")

    #print(f"Players: {len(all_players)}, Values: {len(all_values)}")  # should match now
    #df = pd.DataFrame({"Players": all_players, "Values": all_values})
    df = pd.DataFrame({"Players": players,
                       "Values": values,
                       "Clubs": clubs,
                       "Logos": logos,
                       "PlayerImages": players_images
                       })
    df.to_csv("nike_liga_data.csv", index=True)
    football_player_guess_game(df)