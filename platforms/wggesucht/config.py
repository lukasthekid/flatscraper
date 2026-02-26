"""WG-Gesucht.de platform configuration."""

PLATFORM_NAME = "wggesucht"

BASE_URL = "https://www.wg-gesucht.de/"
LOGIN_URL = "https://www.wg-gesucht.de/"

CITY = "München"
MAX_LISTING_AGE_HOURS = 24

EXCLUDED_PROVIDERS = [
    "M. Miethelden München",
    "Roomwise",
    "Spacest Team",
    "HousingAnywhere",
]

WG_SEARCH_URLS = [
    "https://www.wg-gesucht.de/wg-zimmer-in-Muenchen.90.0.1.0.html?offer_filter=1&city_id=90&sort_column=0&sort_order=0&noDeact=1&dTo=1775037600&categories%5B%5D=0&rent_types%5B%5D=2&sMin=20&rMax=1200&radAdd=Ludwigstra%C3%9Fe+21%2C+80539+M%C3%BCnchen%2C+Deutschland&radDis=3000&wgSea=2&wgMxT=2&wgArt%5B%5D=6&wgArt%5B%5D=12&wgArt%5B%5D=11&wgArt%5B%5D=0&wgArt%5B%5D=4&wgAge=26&exc=2",
    "https://www.wg-gesucht.de/1-zimmer-wohnungen-und-wohnungen-in-Muenchen.90.1+2.1.0.html?csrf_token=2d365091132db95d5a635584aacf065ce37eb630&offer_filter=1&city_id=90&sort_column=0&sort_order=0&noDeact=1&dTo=1774951200&radLat=48.1471575&radLng=11.5794281&categories%5B%5D=1&categories%5B%5D=2&rent_types%5B%5D=2&rMax=1500&radAdd=Ludwigstra%C3%9Fe+21%2C+M%C3%BCnchen%2C+Deutschland%2C+80539&radDis=5000",
    "https://www.wg-gesucht.de/1-zimmer-wohnungen-und-wohnungen-in-Muenchen.90.1+2.1.0.html?csrf_token=2d365091132db95d5a635584aacf065ce37eb630&offer_filter=1&city_id=90&sort_column=0&sort_order=0&noDeact=1&dTo=1774951200&radLat=48.1471575&radLng=11.5794281&categories%5B%5D=1&categories%5B%5D=2&rent_types%5B%5D=2&rMax=1200&radAdd=Ludwigstra%C3%9Fe+21%2C+M%C3%BCnchen%2C+Deutschland%2C+80539&radDis=10000",
]
