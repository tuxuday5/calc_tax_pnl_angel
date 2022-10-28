#!/usr/bin/python
import csv
import datetime
import pprint
import re
import locale
import argparse

locale.setlocale(locale.LC_ALL, 'en_IN')
TRANSACTION_CHARGES_DEFAULT_PERCENT = 0.00345
DEFAULT_TT = 'BUY'
LTCG = 'LTCG'
STCG = 'STCG'

IN_FIELDS = [ 'company', 'date', 'exchange', 'type', 'price', 'qty', 'brokerage', 'other_chrg', 'investment', 'mode', 'broker' ]
IN_FLOAT_FIELDS = [ 'price', 'brokerage', 'other_chrg', 'investment' ]
IN_INT_FIELDS = [ 'qty' ]
IN_DATE_FIELDS = [ 'date' ]

PNL_FIELDS  = [ 'company', 'gain_type', 'quarter', 's_date', 'b_date', 's_qty', 's_price', 's_other_chrg', 's_value', 'b_qty', 'b_price', 'b_other_chrg', 'b_value','pnl' ]

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

        if (int(f_y_split[0])+1 != int(f_y_split[1])):
            raise ValueError(f"Financial Year improper argument {f_y}")

        setattr(namespace,'start_date',datetime.date(int(f_y_split[0]),4,1))
        setattr(namespace,'end_date',datetime.date(int(f_y_split[1]),3,31))


argParser = argparse.ArgumentParser(description='Calculate Angel Broking pnl based on trades')
argParser.add_argument('-t','--trades-file',dest='in_file',type=str,required=True,help='Trades file')
argParser.add_argument('-p','--pnl-file',dest='out_file',type=str,required=True,help='Out/Pnl file')
argParser.add_argument('-y','--fin-year',action=ValidateFinYear,required=True,help='Financial Year as YYYY-YYYYY')
#in_file='/home/uday/Downloads/Equity_Transaction_till_140722.csv'
#in_file='/home/uday/lang/python/tax_pnl_calc/tst1.csv'
#out_file='/home/uday/lang/python/tax_pnl_calc/tax_pnl.csv'
#map_file= '/home/uday/Downloads/EQUITY_L.csv'
#map_fields = [ "SYMBOL", "NAME OF COMPANY", "SERIES", "DATE OF LISTING", "PAID UP VALUE", "MARKET LOT", "ISIN NUMBER", "FACE VALUE" ]

parsedArgs = vars(argParser.parse_args())
IN_FILE = parsedArgs['in_file']
OUT_FILE = parsedArgs['out_file']
START_DATE = parsedArgs['start_date']
END_DATE = parsedArgs['end_date']


def IsBuy(x):
    return x == 'buy'

def IsSell(x):
    return x == 'sell'

def IsDelivery(x):
    return x == 'delivery'

def IsCax(x):
    return x == 'ca'

def IsBse(x):
    return x == 'bse'

def IsNse(x):
    return x == 'nse'

def Gst(brokerage,exch_trans_charges,sebi_to_fees):
    ## gst 18%
    taxable_value = round(brokerage+exch_trans_charges+sebi_to_fees,2)
    return round(taxable_value*0.18,2)

def StampDuty(q,p,trd_type,exch):
    ### only on buy side(?)
    ## Equity Delivery 0.015% (Rs 1500 per crore)
    ## Equity Intraday 0.003% (Rs 300 per crore)
    ## Futures (equity and commodity) 0.002% (Rs 200 per crore)
    ## Options (equity and commodity) 0.003% (Rs 300 per crore)
    ## Currency (F&O) 0.0001% (Rs 10 per crore) on buy-side
    ## Mutual Fund 0.005% (Rs 500 per crore)

    #if not IsBuy(trd_type):
    #    return 0

    turn_over = q * p
    return round(turn_over * 0.00015)

def ExchTransactionCharges(q,p,trd_type,exch):
    ## nse 0.00335 % of turn over
    ### bse 0.00345 % of turn over for a,b segment
    ### bse 0.00275 % of turn over for E, F, FC, G, GC, I, IF, IT, M, MS, MT, T, TS, W
    ### bse 0.1% of turn over for XC, XD, XT, Z, ZP
    ### bse 1% of turn over for P, R, SS, ST

    turn_over = q * p
    charges = 0.0
    if IsBse(exch):
        charges = turn_over * 0.0000345
    elif IsNse(exch):
        charges = turn_over * 0.0000335
    else:
        print(f"Exch {exch} not handled for ExchTransactionCharges. {TRANSACTION_CHARGES_DEFAULT_PERCENT}% used")
        charges = turn_over * TRANSACTION_CHARGES_DEFAULT_PERCENT

    return round(charges,2)

def Stt(q,p,trd_type,exch):
    ### 0.1% of turn over
    turn_over = q * p
    return round(turn_over * 0.001)


def SebiTrunOverFees(q,p,trd_type,exch):
    # .0001 paise for every 100 rupees
    # or 10 rs / crore
    turn_over = q * p
    hunds_in_turn_over = turn_over/100.0
    sebi_fees_in_paise = hunds_in_turn_over * 0.0001

    return round(sebi_fees_in_paise,2)

def BrokerageCharges(q,p,trd_type,exch):
    ## 15 paise/100 rupees
    p_s_brokerage_charges = p * 0.0015
    return round(p_s_brokerage_charges*q,2)

def DematTxCharges(q,p,trd_type,exch):
    # flat 20 + gst @ 18
    if IsBuy(trd_type):
        return 0
    return round(20*1.18,2)

def CalculateOtherCharges(q,p,trd_type,exch):
    brokerage = BrokerageCharges(q,p,trd_type,exch)
    stt = Stt(q,p,trd_type,exch)
    exch_trans_charges = ExchTransactionCharges(q,p,trd_type,exch)
    sebi_fees = SebiTrunOverFees(q,p,trd_type,exch)
    stamp_duty = StampDuty(q,p,trd_type,exch)
    gst = Gst(brokerage,exch_trans_charges,sebi_fees)
    demat_tx_charges = DematTxCharges(q,p,trd_type,exch)

    return round(brokerage+stt+exch_trans_charges+sebi_fees+stamp_duty+gst+demat_tx_charges,2)

def AddPnlToQuarter(p,r):
    g_t = r['gain_type']
    q = r['quarter']
    for f in ['s_value','b_value','pnl']:
        p[g_t][q][f] +=  locale.atof(r[f])

def GetQuarterOfDate(d):
    fy = START_DATE.year
    fy_p1 = END_DATE.year
    if (d > datetime.date(year=fy,month=4,day=1)) and (d <= datetime.date(year=fy,month=6,day=15)):
        return 1
    elif (d > datetime.date(year=fy,month=6,day=15)) and (d <= datetime.date(year=fy,month=9,day=15)):
        return 2
    elif (d > datetime.date(year=fy,month=9,day=15)) and (d <= datetime.date(year=fy,month=12,day=15)):
        return 3
    elif (d > datetime.date(year=fy_p1,month=3,day=15)) and (d <= datetime.date(year=fy_p1,month=3,day=31)):
        return 5
    elif (d > datetime.date(year=fy,month=12,day=15)) and (d <= datetime.date(year=fy_p1,month=3,day=15)):
        return 4

def GetGainType(b_d,s_d):
    day_diff = abs((s_d-b_d).days)
    if day_diff > 365:
        return LTCG
    else:
        return STCG

def ShouldIgnore(r):
    return False

def NormalizeRecord(r):
#IN_FIELDS = [ "Company Name", "Date", "Exchange", "Type", "Price", "Qty", "Brokerage", "Other Charges", "Investment", "Mode", "Broker Name" ]
    for f in IN_FLOAT_FIELDS:
        r[f] = locale.atof(r[f])

    for f in IN_INT_FIELDS:
        r[f] = locale.atoi(r[f])

    for f in IN_DATE_FIELDS:
        r[f] = datetime.datetime.strptime(r[f],"%d-%b-%Y").date()

    if re.match('buy',r['type'],re.I):
        r['type'] = 'buy'
    elif re.match('sell',r['type'],re.I):
        r['type'] = 'sell'

    if re.match('delivery',r['mode'],re.I):
        r['mode'] = 'delivery'
    elif re.match('ca',r['mode'],re.I):
        r['mode'] = 'ca'
    elif re.match('intraday',r['mode'],re.I):
        r['mode'] = 'intraday'
    else:
        print(f"Unknown trade mode :{r['mode']}: for record")

    if re.match('nse',r['exchange'],re.I):
        r['exchange'] = 'nse'
    elif re.match('bse',r['exchange'],re.I):
        r['exchange'] = 'bse'
    elif IsCax(r['mode']) and (r['exchange'] == ''):
        pass
    else:
        print(f"Unknown exchange :{r['exchange']}: for record")


def SumAllSells(s):
    total = 0
    for a_s in s:
        total += a_s['qty']

    return total

#PNL_FIELDS  = [ "company",  "s_date", "s_qty", "s_price", "s_other_chrg", "s_value", "b_date", "b_qty", "b_price", "b_other_chrg", "b_value","pnl" ]
#  1 Company Name│Date│Exchange│Type│Price│Qty│Brokerage│Other Charges│Investment│Mode│Broker Name
#  2 GAIL (India)│15-Jun-2022│BSE│SELL│190│123│35.06│32.83│23302.11│Delivery│Angel
#  3 GAIL (India)│20-Mar-2022││Sell│0│0│0│0│2500│CA│Angel

def WriteDivPnl(cax,h):
    for c in cax:
        pnl_record = dict.fromkeys(PNL_FIELDS,0)

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

            pnl_record = dict.fromkeys(PNL_FIELDS,0)
            pnl_record['company'] = a_sell['company']
            pnl_record['quarter'] = GetQuarterOfDate(a_sell['date'])
            pnl_record['gain_type'] = GetGainType(a_sell['date'],a_buy['date'])

            pnl_record['s_date'] = a_sell['date']
            pnl_record['s_price'] = a_sell['price']
            pnl_record['s_qty'] = out_qty
            #pnl_record['s_other_chrg'] = a_sell['price'] * out_qty * OTHER_CHARGES_PERCENTAGE
            pnl_record['s_other_chrg'] = CalculateOtherCharges(out_qty,a_sell['price'],a_sell['type'],a_sell['exchange'])
            pnl_record['s_value']      = (a_sell['price'] * out_qty) - pnl_record['s_other_chrg']

            pnl_record['b_date'] = a_buy['date']
            pnl_record['b_qty'] = out_qty
            pnl_record['b_price'] = a_buy['price']
            #pnl_record['b_other_chrg'] = a_buy['price'] * out_qty * OTHER_CHARGES_PERCENTAGE
            pnl_record['b_other_chrg'] = CalculateOtherCharges(out_qty,a_buy['price'],a_buy['type'],a_buy['exchange'])
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


def GetPnlsByQuarterTemplate():
    pnls_by_q = {}
    for g_t in [LTCG,STCG]:
        pnls_by_q[g_t] = {}
        for q in [1,2,3,4,5]:
            pnls_by_q[g_t][q] = c_q = dict.fromkeys(PNL_FIELDS,0)
            c_q['company'] = "Q{0:1d}".format(q)
            c_q['quarter'] = q
            c_q['gain_type'] =  g_t

    return pnls_by_q

with open(IN_FILE) as trade_history, open(OUT_FILE,'w') as pnl_file:
    scrip_wise_buys = {}
    sells_of_interest = {}
    sells_till_start_of_fy = {}
    cax_divs = []
    cax_not_divs = []
    pnls_by_q = {}

    trade_history_hand = csv.DictReader(trade_history,IN_FIELDS, delimiter=',', quotechar='"')
    trade_history.readline()

    pnl_hand = csv.DictWriter(pnl_file,PNL_FIELDS, delimiter=',', quotechar='"')
    pnl_hand.writeheader()

    for record in trade_history_hand:
        NormalizeRecord(record)
        #if ShouldIgnore(record):
        #    print("Ignoring record ", pprint.pprint(record))
        #    continue

        scrip = record['company']

        if IsDelivery(record['mode']):
            if IsBuy(record['type']):
                if scrip not in scrip_wise_buys:
                    scrip_wise_buys[scrip] = []

                scrip_wise_buys[scrip].append(record)
            elif IsSell(record['type']):
                if scrip not in sells_till_start_of_fy:
                    sells_till_start_of_fy[scrip] = []
                if scrip not in sells_of_interest:
                    sells_of_interest[scrip] = []

                if record['date']  < START_DATE:
                    sells_till_start_of_fy[scrip].append(record)
                elif record['date']  >= START_DATE and record['date']  <= END_DATE:
                    sells_of_interest[scrip].append(record)
        elif IsCax(record['mode']): # cax
            if record['date']  >= START_DATE and record['date']  <= END_DATE:
                if record['price'] == 0  and record['qty'] == 0: ## not rights or swaps
                    cax_divs.append(record)
                else:
                    cax_not_divs.append(record)

    pnls_by_q = GetPnlsByQuarterTemplate()

    for scrip in sells_of_interest:
        if len(sells_of_interest[scrip]) == 0: ## no sells for this financial year
            continue

        sells_prev_sorted = sorted(sells_till_start_of_fy[scrip], key=lambda r:r['date'])
        sells_of_interest_sorted = sorted(sells_of_interest[scrip], key=lambda r:r['date'])
        scrip_wise_buys_sorted = sorted(scrip_wise_buys[scrip],key=lambda r:r['date'])
        pnls = CalculatePnlForScripSells(sells_prev_sorted,sells_of_interest_sorted,scrip_wise_buys_sorted)

        if len(pnls) > 0:
            for r in pnls:
                pnl_hand.writerow(r)
                AddPnlToQuarter(pnls_by_q,r)

    for g_t in [LTCG,STCG]:
        for q in [1,2,3,4,5]:
            for k in ['s_value', 'b_value', 'pnl']:
                pnls_by_q[g_t][q][k] = "{0:.2f}".format(pnls_by_q[g_t][q][k])
            pnl_hand.writerow(pnls_by_q[g_t][q])

    if len(cax_divs) > 0:
        WriteDivPnl(cax_divs,pnl_hand)
