#!/usr/bin/python
import csv
import datetime
import pprint
import re
import locale
import argparse

class ValidateFinYear(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        f_y = values
        f_y_split = f_y.split('-')

        if len(f_y_split) != 2:
            raise ValueError(f"Financial Year improper argument {f_y}")

        if (int(f_y_split[0]) < 2000) and (int(f_y_split[0]) < 2050):
            raise ValueError(f"Financial Year improper argument {f_y}")

        if (int(f_y_split[1]) < 2000) and (int(f_y_split[1]) < 2050):
            raise ValueError(f"Financial Year improper argument {f_y}")

        setattr(namespace,'start_date',datetime.date(int(f_y_split[0]),4,1))
        setattr(namespace,'end_date',datetime.date(int(f_y_split[1]),3,31))


argParser = argparse.ArgumentParser(description='Calculate Angel Broking pnl based on trades')
argParser.add_argument('-t','--trades-file',dest='in_file',type=str,required=True,help='Trades file')
argParser.add_argument('-p','--pnl-file',dest='out_file',type=str,required=True,help='Out/Pnl file')
argParser.add_argument('-y','--fin-year',action=ValidateFinYear,required=True,help='Financial Year as YYYY-YYYYY')

parsedArgs = vars(argParser.parse_args())


#in_file='/home/uday/Downloads/Equity_Transaction_till_140722.csv'
#in_file='/home/uday/lang/python/tax_pnl_calc/tst1.csv'
#out_file='/home/uday/lang/python/tax_pnl_calc/tax_pnl.csv'
in_file = parsedArgs['in_file']
out_file = parsedArgs['out_file']
#map_file= '/home/uday/Downloads/EQUITY_L.csv'
#map_fields = [ "SYMBOL", "NAME OF COMPANY", "SERIES", "DATE OF LISTING", "PAID UP VALUE", "MARKET LOT", "ISIN NUMBER", "FACE VALUE" ]

#setlocale(locale.LC_NUMERIC,'')
locale.setlocale(locale.LC_ALL, 'en_IN')
OTHER_CHARGES_PERCENTAGE = 0.0015
in_fields = [ "company", "date", "exchange", "type", "price", "qty", "brokerage", "other_chrg", "investment", "mode", "broker" ]
in_float_fields = [ "price", "brokerage", "other_chrg", "investment" ]
in_int_fields = [ "qty" ]
in_date_fields = [ "date" ]

pnl_fields  = [ "company",  "s_date", "s_qty", "s_price", "s_other_chrg", "s_value", "b_date", "b_qty", "b_price", "b_other_chrg", "b_value","pnl" ]

scrip_wise_buys = {}
sells_of_interest = {}
sells_till_start_of_period = {}
cax = []
cax_not_divs = []
pnl  = []
#
#start_date =  datetime.date(2020,4,1)
#end_date = datetime.date(2021,3,31)
#
#start_date =  datetime.date(2021,4,1)
#end_date = datetime.date(2022,3,31)

start_date = parsedArgs['start_date']
end_date = parsedArgs['end_date']

def ShouldIgnore(r):
    return False

def NormalizeRecord(r):
#in_fields = [ "Company Name", "Date", "Exchange", "Type", "Price", "Qty", "Brokerage", "Other Charges", "Investment", "Mode", "Broker Name" ]
    for f in in_float_fields:
        r[f] = locale.atof(r[f])

    for f in in_int_fields:
        r[f] = locale.atoi(r[f])

    for f in in_date_fields:
        r[f] = datetime.datetime.strptime(r[f],"%d-%b-%Y").date()

    if re.match('buy',r['type'],re.I):
        r['type'] = 'buy'
    elif re.match('sell',r['type'],re.I):
        r['type'] = 'sell'


def SumAllSells(s):
    total = 0
    for a_s in s:
        total += a_s['qty']

    return total

#pnl_fields  = [ "company",  "s_date", "s_qty", "s_price", "s_other_chrg", "s_value", "b_date", "b_qty", "b_price", "b_other_chrg", "b_value","pnl" ]
#  1 Company Name│Date│Exchange│Type│Price│Qty│Brokerage│Other Charges│Investment│Mode│Broker Name
#  2 GAIL (India)│15-Jun-2022│BSE│SELL│190│123│35.06│32.83│23302.11│Delivery│Angel
#  3 GAIL (India)│20-Mar-2022││Sell│0│0│0│0│2500│CA│Angel

def WriteDivPnl(cax,h):
    for c in cax:
        pnl_record = dict.fromkeys(pnl_fields,0)

        pnl_record['company'] = c['company']
        pnl_record['s_date'] = c['date']
        pnl_record['s_price'] = c['investment']
        pnl_record['s_qty'] = 1
        pnl_record['s_other_chrg'] = 0
        pnl_record['s_value']      = c['investment']

        pnl_record['b_date'] = c['date']
        pnl_record['b_qty'] = 1
        pnl_record['b_price'] = 0
        pnl_record['b_other_chrg'] = 0
        pnl_record['b_value']      = 0
        pnl_record['pnl']          = pnl_record['s_value']

        for k in ( 's_other_chrg', 's_value', 'b_other_chrg', 'b_value', 'pnl'):
            pnl_record[k] = "{0:.2f}".format(pnl_record[k])

        h.writerow(pnl_record)

def CalculatePnlForScripSells(s_prev,s,b):
    """ adjust total_sells from s_prev in buys
    then for every s, can straight away map remaining b.
    should adjust for partial qty in b, adjusted for s_prev
    """
    scrip_first_sell = True
    pnls = []

    for a_sell in s:

        if scrip_first_sell: #adjust prev year sells
            scrip_first_sell = False
            prev_yr_sells = SumAllSells(s_prev)

            for a_buy in b:
                if prev_yr_sells >= a_buy['qty']:
                    prev_yr_sells -= a_buy['qty']
                    a_buy['qty'] = 0
                else:
                    a_buy['qty'] -= prev_yr_sells

        for a_buy in b:
            if a_buy['qty'] == 0:
                continue

            out_qty = a_buy['qty'] if a_buy['qty'] <= a_sell['qty'] else a_sell['qty']

            pnl_record = dict.fromkeys(pnl_fields,0)
            pnl_record['company'] = a_sell['company']
            pnl_record['s_date'] = a_sell['date']
            pnl_record['s_price'] = a_sell['price']
            pnl_record['s_qty'] = out_qty
            pnl_record['s_other_chrg'] = a_sell['price'] * out_qty * OTHER_CHARGES_PERCENTAGE
            pnl_record['s_value']      = (a_sell['price'] * out_qty) - pnl_record['s_other_chrg']

            pnl_record['b_date'] = a_buy['date']
            pnl_record['b_qty'] = out_qty
            pnl_record['b_price'] = a_buy['price']
            pnl_record['b_other_chrg'] = a_buy['price'] * out_qty * OTHER_CHARGES_PERCENTAGE
            pnl_record['b_value']      = (a_buy['price'] * out_qty) + pnl_record['b_other_chrg']
            pnl_record['pnl']          = pnl_record['s_value'] - pnl_record['b_value']

            for k in ( 's_other_chrg', 's_value', 'b_other_chrg', 'b_value', 'pnl'):
                pnl_record[k] = "{0:.2f}".format(pnl_record[k])

            pnls.append(pnl_record)

            if a_sell['qty'] <= out_qty:
                a_buy['qty'] -= out_qty
                break
            else:
                a_sell['qty'] -= out_qty
                a_buy['qty'] -= out_qty
                continue

    return pnls

with open(in_file) as trade_history, open(out_file,'w') as pnl_file:
    trade_history_hand = csv.DictReader(trade_history,in_fields, delimiter=',', quotechar='"')
    trade_history.readline()

    pnl_hand = csv.DictWriter(pnl_file,pnl_fields, delimiter=',', quotechar='"')
    pnl_hand.writeheader()

    for record in trade_history_hand:
        NormalizeRecord(record)
        #if ShouldIgnore(record):
        #    print("Ignoring record ", pprint.pprint(record))
        #    continue

        scrip = record['company']

        if record['mode'] == 'Delivery': ## trades
            if record['type'] == 'buy':
                if scrip not in scrip_wise_buys:
                    scrip_wise_buys[scrip] = []

                scrip_wise_buys[scrip].append(record)
            elif record['type'] == 'sell':
                if scrip not in sells_till_start_of_period:
                    sells_till_start_of_period[scrip] = []
                if scrip not in sells_of_interest:
                    sells_of_interest[scrip] = []

                if record['date']  < start_date:
                    sells_till_start_of_period[scrip].append(record)
                elif record['date']  >= start_date and record['date']  <= end_date:
                    sells_of_interest[scrip].append(record)
        elif record['mode'] == 'CA': ## cax
            if record['date']  >= start_date and record['date']  <= end_date:
                if record['price'] == 0  and record['qty'] == 0: ## not rights or swaps
                    cax.append(record)
                else:
                    cax_not_divs.append(record)

    for scrip in sells_of_interest:
        if len(sells_of_interest[scrip]) == 0: ## no sells for this financial year
            continue

        sells_prev_sorted = sorted(sells_till_start_of_period[scrip], key=lambda r:r['date'])
        sells_of_interest_sorted = sorted(sells_of_interest[scrip], key=lambda r:r['date'])
        scrip_wise_buys_sorted = sorted(scrip_wise_buys[scrip],key=lambda r:r['date'])
        pnls = CalculatePnlForScripSells(sells_prev_sorted,sells_of_interest_sorted,scrip_wise_buys_sorted)

        for r in pnls:
            pnl_hand.writerow(r) 

    WriteDivPnl(cax,pnl_hand)
