import logging
import os
import pandas as pd
import traceback
import json
from datetime import datetime, timedelta, timezone
from matplotlib import pyplot as plt


class PnlVisualizer(object):
    """
    PNLをグラフ化します.
    save_pnl.pyで1分ごとに書き出したファイルを利用します.
    こちらのプログラムは1時間おきや1日おきに定期的に実行してください.
    """
    def __init__(self, exchange_name, bot_name, year, month, day, logger):
        """
        コンストラクタです.
        :param exchange_name: 取引所名. ログファイルの指定に使います.
        :param bot_name: ボット名. ログファイルの指定に使います.
        :param year: 対象年.
        :param month: 対象月.
        :param day: 対象日.
        :param logger: ロガー.
        """
        self.exchange_name = exchange_name
        self.bot_name = bot_name
        self.timezone = timezone(timedelta(hours=9), "JST")
        self.request_limit = 5
        self.start_timestamp = datetime(year, month, day, 0, 0, tzinfo=self.timezone).timestamp()
        self.start_datetime = datetime.fromtimestamp(self.start_timestamp, tz=self.timezone).astimezone(self.timezone)
        self.dir_name = ""
        self.file_name = f"pnl_{exchange_name}_{bot_name}_{self.start_datetime.strftime('%y%m%d')}.csv"
        self.file_encoding = "shift-jis"
        self.output_dir_name = ""
        self.output_file_name = f"pnl_{exchange_name}_{bot_name}_{self.start_datetime.strftime('%y%m%d')}.png"
        self.pnl = None
        self.logger = logger

    def _load_pnl(self):
        """
        損益ファイルをロードします.
        """
        if not os.path.isfile(self.dir_name + self.file_name):
            message = f"Pnl file is not found. {self.file_name}"
            self.logger.error(message)
            raise FileNotFoundError(message)
        self.pnl = pd.read_csv(self.dir_name + self.file_name, encoding=self.file_encoding)
        if len(self.pnl) == 0:
            message = f"Pnl data does not exist in {self.file_name}"
            self.logger.error(message)
            raise FileNotFoundError(message)

    def _draw_price(self, ax):
        """
        価格チャートを描きます.
        :param ax: matplotlibの座標軸.
        """
        if self.pnl is None or len(self.pnl) == 0:
            return
        x = [index for index, item in enumerate(self.pnl.datetime_jst.values)]
        y = self.pnl.ltp.values
        ax.plot(x, y, color="blue", linewidth=1)

    def _draw_balance(self, ax):
        """
        損益チャートを描きます.
        :param ax: matplotlibの座標軸.
        """
        if self.pnl is None or len(self.pnl) == 0:
            return
        x = [index for index, item in enumerate(self.pnl.datetime_jst.values)]
        # x = [item[11:16] for item in self.pnl.datetime_jst.values]  # 時刻をx軸に書くならこちら.
        pnl = self.pnl.pnl.values
        first = pnl[0]
        y = [price - first for price in pnl]
        ax.plot(x, y, color="red", linewidth=1)

    def initialize(self):
        """
        初期化処理です.
        """
        self._load_pnl()

    def draw_chart(self):
        """
        チャートを描きます.
        """
        title = f"{self.exchange_name} {self.bot_name} PnL {self.start_datetime.strftime('%Y/%m/%d')}"
        fig = plt.figure(figsize=(10, 4))
        fig.suptitle(title)
        ax1 = fig.add_subplot(211)
        ax2 = fig.add_subplot(212)
        self._draw_price(ax1)
        self._draw_balance(ax2)
        ax1.grid(which="major", axis="x", color="gray", alpha=0.5, linestyle="dotted", linewidth=1)
        ax1.grid(which="major", axis="y", color="gray", alpha=0.5, linestyle="dotted", linewidth=1)
        ax2.grid(which="major", axis="x", color="gray", alpha=0.5, linestyle="dotted", linewidth=1)
        ax2.grid(which="major", axis="y", color="gray", alpha=0.5, linestyle="dotted", linewidth=1)

    def save(self):
        """
        ファイルに保存します.
        :return: ファイルパス.
        """
        file_path = self.output_dir_name + self.output_file_name
        plt.savefig(file_path)
        return file_path


if __name__ == "__main__":
    import argparse
    import pytz
    import requests
    # ロガー.
    logger = logging.getLogger(__name__)
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.DEBUG)
    # パラメータ.
    my_exchange_name = "ftx"
    my_bot_name = "vix"
    with open('config.json', 'r', encoding="utf-8") as f:
        config = json.load(f)
    # TODO Discord通知する際はここにHook URLを指定してください.
    hook = config["discordWebhook"]
    # 引数読み込み.
    parser = argparse.ArgumentParser()
    jst = timezone(timedelta(hours=9), "JST")
    now = datetime.now(pytz.UTC).replace(tzinfo=pytz.UTC).astimezone(jst)
    parser.add_argument("year", type=int, help=u"年", nargs="?", default=int(now.strftime("%Y")))
    parser.add_argument("month", type=int, help=u"月", nargs="?", default=int(now.strftime("%m")))
    parser.add_argument("day", type=int, help=u"日", nargs="?", default=int(now.strftime("%d")))
    args = parser.parse_args()
    try:
        visualizer = PnlVisualizer(my_exchange_name, my_bot_name, args.year, args.month, args.day, logger)
        visualizer.initialize()
        visualizer.draw_chart()
        output = visualizer.save()
        if hook:
            with open(output, "rb") as f:
                file_data = f.read()
                files = {'uploadFile': (visualizer.output_file_name, file_data, "image/png")}
                requests.post(hook, files=files)
    except Exception as e:
        logger.error(traceback.format_exc())
        raise e
