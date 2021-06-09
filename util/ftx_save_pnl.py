import pybotters
import csv
import logging
import os
import sys
import pytz
import time
import traceback
from datetime import datetime, timedelta, timezone


if __name__ == "__main__":
    # ロガー.
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())
    # パラメータ.
    symbol = 'ETH-PERP'

    exchange_name = "ftx"
    bot_name = "vix"
    output_filename_base = "pnl_{}_{}_{}.csv"
    output_dir = ""
    output_file_encoding = "shift-jis"
    header = ["timestamp", "datetime_jst", "pnl", "ltp"]

    # バランスとオープンオーダー取得.
    request_limit = 5
    failed_counter = 0
    while True:
        try:
            balances = pybotters.get('https://ftx.com/api/wallet/all_balances', apis='apis.json').json()
            break
        except Exception as e:
            failed_counter += 1
            if failed_counter > request_limit:
                logger.error("API request failed and request limit exceeded.")
                logger.error(traceback.format_exc())
                raise e
            time.sleep(1)

    if not balances['success']:
        sys.exit()
    usdValue = 0
    for result in balances["result"]['main']:
        usdValue += float(result["usdValue"])
    pnl = round(usdValue, 2)

    last_price = pybotters.get(f'https://ftx.com/api/futures/{symbol}').json()['result']['last']
    # ファイル出力.
    jst = timezone(timedelta(hours=9), "JST")
    now = datetime.now(pytz.UTC).replace(tzinfo=pytz.UTC).astimezone(jst)
    filename = output_filename_base.format(exchange_name, bot_name, now.strftime("%y%m%d"))
    output_file = None
    try:
        file_exists = os.path.isfile(filename)
        output_file = open(filename, "a", encoding=output_file_encoding)
        writer = csv.writer(output_file)
        if not file_exists:
            writer.writerow(header)
        # 桁はそのまま出力. 使う側で加工する.
        writer.writerow([now.timestamp(), now.strftime("%Y-%m-%dT%H:%M:%S"), pnl, last_price])
    except Exception as e:
        logger.error(f"Cannot write file {filename}.")
        logger.error(traceback.format_exc())
        raise e
    finally:
        if output_file is not None:
            output_file.close()
