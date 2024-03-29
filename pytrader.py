import sys
import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic
from Kiwoom import *
from pandas import DataFrame
import time

TRADING_TIME = [[[8, 57], [15, 19]]]

form_class = uic.loadUiType("pytrader.ui")[0]

class MyWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.trade_stocks_done = False

        self.kiwoom = Kiwoom()
        self.kiwoom.comm_connect()

        self.run()
        self.currentTime = datetime.datetime.now()

        self.timer = QTimer(self)
        self.timer.start(1000)
        self.timer.timeout.connect(self.timeout)

        # Timer2 실시간 조회 체크박스 체크하면 10초에 한 번씩 데이터 자동 갱신
        self.timer2 = QTimer(self)
        self.timer2.start(1000*10)
        self.timer2.timeout.connect(self.timeout2)

        # 선정 종목 리스트
        self.load_buy_sell_list()

        accouns_num = int(self.kiwoom.get_login_info("ACCOUNT_CNT"))
        accounts = self.kiwoom.get_login_info("ACCNO")


        accounts_list = accounts.split(';')[0:accouns_num]
        self.comboBox.addItems(accounts_list)

        #self.pushButton_2.clicked.connect(self.check_balance)
        self.check_balance()
        self.kiwoom.OnReceiveRealData.connect(self.kiwoom._receive_real_data)
        self.check_chejan_balance()
        self.save_final_stock()


    def is_trading_time(self):
        vals = []
        current_time = self.currentTime.time()
        for start, end in TRADING_TIME:
            start_time = datetime.time(hour=start[0], minute=start[1])
            end_time = datetime.time(hour=end[0], minute=end[1])
            if(current_time >= start_time and current_time <= end_time):
                vals.append(True)
            else:
                vals.append(False)
                pass
        if vals.count(True):
            return True
        else:
            return False

    """def stock_name(self):
        f = open("buy_list.txt", 'rt')
        buy_list = f.readlines()
        f.close()
        account = self.comboBox.currentText()

        for row_data in buy_list:
            split_row_data = row_data.split(';')
            code = split_row_data[1]
"""



#주문을 들어가기 전에 파일에서 불러와서 종목을 확인, 종목의 전일 종가 확인 - 첫 번째 주문 시
#두 번째 주문부터는 이미 주문 들어간 파일에서 확인
    # 자동 주문
    def trade_stocks(self):
        #self.check_balance()
        auto_buy = []
        hoga_lookup = {'지정가': "00", '시장가': "03"}

        f = open("buy_list.txt", 'rt')
        buy_list = f.readlines()
        auto_buy += buy_list
        f.close()

        f = open("sell_list.txt", 'rt')
        sell_list = f.readlines()
        f.close()

        account = self.comboBox.currentText()
        close_rate, current_rate = self.run()
        #print("rate: ", rate[2][0])
        print(current_rate)
        # buy list
        for i in range(len(auto_buy)):
            split_row_data = auto_buy[i].split(';')
            hoga = split_row_data[2]
            code = split_row_data[1]
            num = split_row_data[3]
            price = split_row_data[4]
            bdr = split_row_data[5]
            pr = split_row_data[6]
            lr = split_row_data[7]


            #temp = self.kiwoom.opw00018_output['multi'][0][3]
            """for i in range(len(new)):
                price = bdr * new[i]
                price = int(price)
                temp = price % 10
                new_price = price - temp"""
            #print(self.final_stock[0])
            #price = bdr * self.final_stock[cnt]
            """price = int(price)
            temp = price % 10
            new_price = price - """
            print("bdr:", float(bdr))
            # 전날 종가
            new_price = close_rate[i][0] * float(bdr)
            print("cnt:", i)
            print("rate[cnt]", close_rate[i][0])
            print("new_price:", new_price)
            #temp = new_price % 10
            #new_price = new_price - temp
            hoga = "지정가"

            if split_row_data[-1].rstrip() == '매수전' and new_price <= current_rate[i][0]:
                self.kiwoom.send_order("send_order_req", "0101", account, 1, code, num, int(new_price), hoga_lookup[hoga], "")
                if self.kiwoom.orderNum:
                    for i, row_data in enumerate(buy_list):
                        buy_list[i] = buy_list[i].replace("매수전", "주문완료")
            elif split_row_data[-1].rstrip() == '매수전' and self.is_trading_time() == False:
                self.kiwoom.send_order("send_order_req", "0101", account, 1, code, num, price, hoga_lookup[hoga], "")
                if self.kiwoom.orderNum:
                    for i, row_data in enumerate(buy_list):
                        buy_list[i] = buy_list[i].replace("매수전", "주문완료")

        # sell list
        for row_data in sell_list:
            split_row_data = row_data.split(';')
            hoga = split_row_data[2]
            code = split_row_data[1]
            num = split_row_data[3]
            price = split_row_data[4]

            if split_row_data[-1].rstrip() == '매도전':
                self.kiwoom.send_order("send_order_req", "0101", account, 2, code, num, price, hoga_lookup[hoga], "")
                if self.kiwoom.orderNum:
                    for i, row_data in enumerate(buy_list):
                        sell_list[i] = sell_list[i].replace("매도전", "주문완료")
        #파일 정보 변경
        # buy list
        """for i, row_data in enumerate(buy_list):
            buy_list[i] = buy_list[i].replace("매수전", "주문완료")"""

        # file update
        f = open("buy_list.txt", 'wt')
        for row_data in buy_list:
            f.write(row_data)
        f.close()

        # sell list
        """for i, row_data in enumerate(sell_list):
            sell_list[i] = sell_list[i].replace("매도전", "주문완료")"""

        # file update
        f = open("sell_list.txt", 'wt')
        for row_data in sell_list:
            f.write(row_data)
        f.close()

    def load_buy_sell_list(self):
        f = open("buy_list.txt", 'rt')
        buy_list = f.readlines()
        f.close()

        f = open("sell_list.txt", 'rt')
        sell_list = f.readlines()
        f.close()

        row_count = len(buy_list) + len(sell_list)
        self.tableWidget_3.setRowCount(row_count)

        # buy list
        # j:행, i:열
        for j in range(len(buy_list)):
            row_data = buy_list[j]
            split_row_data = row_data.split(';')
            split_row_data[1] = self.kiwoom.get_master_code_name(split_row_data[1].rstrip())

            for i in range(len(split_row_data)):
                item = QTableWidgetItem(split_row_data[i].rstrip())
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                self.tableWidget_3.setItem(j, i, item)

        # sell list
        for j in range(len(sell_list)):
            row_data = sell_list[j]
            split_row_data = row_data.split(';')
            split_row_data[1] = self.kiwoom.get_master_code_name(split_row_data[1].rstrip())

            for i in range(len(split_row_data)):
                item = QTableWidgetItem(split_row_data[i].rstrip())
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                self.tableWidget_3.setItem(len(buy_list) + j, i, item)

        self.tableWidget_3.resizeRowsToContents()

    def save_final_stock(self):
        item_count = len(self.kiwoom.opw00018_output['multi'])
        if(self.is_trading_time() == False):
            self.final_stock = []
            for i in range(item_count):
                row = self.kiwoom.opw00018_output['multi'][i][3]
                self.final_stock.append(row)
            print(self.final_stock)
        #if(self.is_trading_time() == True):
            #종가 파일로 저장.



    def timeout(self):
        market_start_time = QTime(9, 0, 0)
        current_time = QTime.currentTime()

        if current_time > market_start_time and self.trade_stocks_done is False:
            self.trade_stocks()
            self.trade_stocks_done = True


        text_time = current_time.toString("hh:mm:ss")
        time_msg = "현재시간: " + text_time

        state = self.kiwoom.get_connect_state()
        if state == 1:
            state_msg = "서버 연결 중"
        else:
            state_msg = "서버 미 연결 중"

        self.statusbar.showMessage(state_msg + " | " + time_msg)

    # 체크 박스 체크?
    def timeout2(self):
        #if self.checkBox.isChecked():
        self.check_balance()
        self.check_chejan_balance()

    def check_chejan_balance(self):

        self.kiwoom.reset_opt10075_output()
        account_number = self.kiwoom.get_login_info("ACCNO")
        account_number = account_number.split(';')[0]

        self.kiwoom.set_input_value("계좌번호", account_number)
        self.kiwoom.comm_rq_data("opt10075_req", "opt10075", 0, "2000")

        while self.kiwoom.remained_data:
            time.sleep(0.2)
            self.kiwoom.set_input_value("계좌번호", account_number)
            self.kiwoom.comm_rq_data("opt10075_req", "opt10075", 0, "2000")

        item_count = len(self.kiwoom.opt10075_output['no_che'])
        self.tableWidget_4.setRowCount(item_count)

        for j in range(item_count):
            row = self.kiwoom.opt10075_output['no_che'][j]
            for i in range(len(row)):
                item = QTableWidgetItem(row[i])
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                self.tableWidget_4.setItem(j, i, item)

        self.tableWidget_4.resizeRowsToContents()

    def check_balance(self):
        self.kiwoom.reset_opw00018_output()
        account_number = self.kiwoom.get_login_info("ACCNO")
        account_number = account_number.split(';')[0]

        self.kiwoom.set_input_value("계좌번호", account_number)
        self.kiwoom.comm_rq_data("opw00018_req", "opw00018", 0, "2000")

        while self.kiwoom.remained_data:
            time.sleep(0.2)
            self.kiwoom.set_input_value("계좌번호", account_number)
            self.kiwoom.comm_rq_data("opw00018_req", "opw00018", 2, "2000")

        # opw0001TR (예수금 데이터)
        self.kiwoom.set_input_value("계좌번호", account_number)
        self.kiwoom.comm_rq_data("opw00001_req", "opw00001", 0, "2000")

        #balance
        item = QTableWidgetItem(self.kiwoom.d2_deposit)
        item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
        self.tableWidget.setItem(0, 0, item)

        # 나머지 칼럼 (table1)
        for i in range(1, 6):
            item = QTableWidgetItem(self.kiwoom.opw00018_output['single'][i-1])
            item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
            self.tableWidget.setItem(0, i, item)

        # 행 높이 조절
        self.tableWidget.resizeRowsToContents()

        # Item list (보유 종목별 평가 잔고)
        item_count = len(self.kiwoom.opw00018_output['multi'])
        self.tableWidget_2.setRowCount(item_count)

        for j in range(item_count):
            row = self.kiwoom.opw00018_output['multi'][j]
            for i in range(len(row)):
                item = QTableWidgetItem(row[i])
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                self.tableWidget_2.setItem(j, i, item)
        self.tableWidget_2.resizeRowsToContents()

    def get_ohlcv(self, code, start):
        #self.get_ohlcv("035720", "20190604")
        self.kiwoom.ohlcv = {'date': [], 'close': []}
        self.kiwoom.final = {'close': []}
        self.kiwoom.current = {'current': []}

        self.kiwoom.set_input_value("종목코드", code)
        self.kiwoom.set_input_value("기준일자", start)
        self.kiwoom.set_input_value("수정주가구분", 1)
        self.kiwoom.comm_rq_data("opt10081_req", "opt10081", 0, "0101")

        #time.sleep(0.2)
        #df = DataFrame(self.kiwoom.ohlcv, columns=['close'],
        #              index=self.kiwoom.ohlcv['date'])
        #return self.kiwoom.ohlcv

    def run(self):
        true_close = []
        true_current = []
        code = []
        today = datetime.datetime.today().strftime("%Y%m%d")
        f = open("buy_list.txt", 'rt')
        buy_list = f.readlines()

        for row_data in buy_list:
            split_row_data = row_data.split(';')
            code.append(split_row_data[1])
        for i in range(len(code)):
            print("code: ", code[i])
            self.get_ohlcv(code[i], today)
            true_close.append(self.kiwoom.final['close'])
            true_current.append(self.kiwoom.current['current'])
        print(true_close)

        f.close()
        return (true_close, true_current)
        #print("final: ", self.kiwoom.final_output)
      #  a = self.get_ohlcv("039490", "20190604")
       # print(a)



if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    app.exec_()