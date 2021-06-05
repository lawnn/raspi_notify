import ccxt
import csv
import logging
import os
import sys
import pytz
import json
import time
import traceback
from datetime import datetime, timedelta, timezone


def balance():
    return ftx.fetch_balance()


def last_price():
    tic = ftx.fetch_ticker(symbol)
    return tic['last']


if __name__ == "__main__":
    # ロガー.
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())
    # パラメータ.
    with open('config.json', 'r', encoding="utf-8") as f:
        config = json.load(f)
    ftx = ccxt.ftx()
    ftx.apiKey = config['ftx_apiKey']
    ftx.secret = config['ftx_secret']
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
            balances = balance()
            break
        except Exception as e:
            failed_counter += 1
            if failed_counter > request_limit:
                logger.error("API request failed and request limit exceeded.")
                logger.error(traceback.format_exc())
                raise e
            time.sleep(1)

    if not balances['info']['success']:
        sys.exit()
    usdValue = 0
    for result in balances["info"]["result"]:
        usdValue += float(result["usdValue"])
    pnl = round(usdValue, 2)

    last_price = last_price()
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
