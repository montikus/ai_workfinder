import json


def capture_network_response_to_file(page, url, filename):
    page.listen.start(url)
    packet = page.listen.wait(timeout=30, fit_count=2)

    with open(f'account_ads_data/{filename}.json', 'w', encoding='utf-8') as file:
        json.dump(packet.response.body, file, ensure_ascii=False, indent=2)

    page.listen.stop()
