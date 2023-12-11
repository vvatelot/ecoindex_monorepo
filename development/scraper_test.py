import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed

from ecoindex.scraper import EcoindexScraper


def run_page_analysis(url: str, index: int):
    return index, asyncio.run(
        EcoindexScraper(url=url).init_chromedriver().get_page_analysis()
    )


with ThreadPoolExecutor(max_workers=8) as executor:
    future_to_analysis = {}

    url = "https://www.decathlon.fr"

    for i in range(10):
        print(f"Starting ecoindex {i} analysis")
        future_to_analysis[
            executor.submit(
                run_page_analysis,
                url,
                i,
            )
        ] = url

    for future in as_completed(future_to_analysis):
        try:
            index, result = future.result()
            print(f"Ecoindex {index}: {result}")
        except Exception as e:
            print(e)
