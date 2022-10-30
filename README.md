# calculate pnl for trades in angel broking for taxing purpose

## usage: angel_pnl.py [-h] -t TRADES_FILE/IN_FILE -p PNL_FILE/OUT_FILE -y FIN_YEAR -d DIVIDEND_FILE

> Calculate Angel Broking pnl based on trades
> 
> options:
>   -h, --help            show this help message and exit
>   -t IN_FILE, --trades-file IN_FILE
>                         Trades file
>   -p OUT_FILE, --pnl-file OUT_FILE
>                         File to capture pnl details
>   -d DIV_FILE, --div-file DIV_FILE
>                         File to capture dividend details
>   -y FIN_YEAR, --fin-year FIN_YEAR
>                         Financial Year as YYYY-YYYYY


## Terms Used in file
TRADES_FILE - Trades file obtained from angel broking
PNL_FILE - Calculated Pnl for the given FY. Captures pnl for individual trades. Captures Quarter wise too.
DIV_YEAR - Dividend Pnl file. Captures pnl for individual divs. Captures Quarter wise too.
FIN_YEAR - Financial year, as YYYY-YYYY format.
> Ex 01/04/2021 to 31/03/2022 should be given as 2021-2022
Other charges - Charges like brokerage, GST, STT etc
LTCG - Long term captial gains
STCG - Short term capital gains

## Sample arguments
```
python3 angel_pnl.py -t Equity_Transaction_till_140722.csv.safe -p pnl.csv  -y 2021-2022 -d div.csv
```

## Other charges calculation

> round(brokerage+stt+exch_trans_charges+sebi_fees+stamp_duty+gst+demat_tx_charges,2)
> BrokerageCharges(q,p,trd_type,exch)# 15 paise/100 rupees
> Stt(q,p,trd_type,exch) # 0.1% of turn over
> ExchTransactionCharges(q,p,trd_type,exch) ## nse 0.00335 % of turn over # bse 0.00345 % of turn over for a,b segment
> SebiTrunOverFees(q,p,trd_type,exch) # .0001 paise for every 100 rupees  or 10 rs / crore
> DematTxCharges(q,p,trd_type,exch)# flat 20 + gst @ 18
> StampDuty(q,p,trd_type,exch): # only on buy side(?) # Equity Delivery 0.015% (Rs 1500 per crore)
> Gst(brokerage,exch_trans_charges,sebi_to_fees): # gst 18%


## Sample Input Trades file
Below columns are mandatory
[ 'company', 'date', 'exchange', 'type', 'price', 'qty', 'brokerage', 'other_chrg', 'investment', 'mode', 'broker' ]

```
Company Name,Date,Exchange,Type,Price,Qty,Brokerage,Other Charges,Investment,Mode,Broker Name
Wheels India,04-Jul-2022,,Sell,0,0,0,0,16.6,CA,Angel
GAIL (India),15-Jun-2022,BSE,SELL,190,123,35.06,32.83,23302.11,Delivery,Angel
Strides Pharma,15-Mar-2022,NSE,Buy,312.05,320,149.79,140.63,"1,00,146.43",Delivery,Angel
NANDAN DENIM LIMITED,14-Jan-2022,NSE,SELL,153.11,788,180.98,169.92,"1,20,298.21",Delivery,Angel
NANDAN DENIM LIMITED,14-Jan-2022,NSE,SELL,153.11,728,167.2,156.98,"1,11,138.45",Delivery,Angel
NANDAN DENIM LIMITED,14-Jan-2022,NSE,SELL,153.11,1000,229.67,215.63,"1,52,662.70",Delivery,Angel
Aurobindo Pharma,16-Nov-2021,,Sell,0,0,0,0,900,CA,Angel
Sterlite Tech.,16-Nov-2021,NSE,SELL,304,250,114,107.03,75778.97,Delivery,Angel
Sterlite Tech.,16-Nov-2021,NSE,SELL,304,750,342,321.1,"2,27,336.90",Delivery,Angel
Sterlite Tech.,16-Nov-2021,NSE,SELL,304,356,162.34,152.42,"1,07,909.25",Delivery,Angel
AIRTEL-RE,28-Oct-2021,BSE,SELL,0,9,0,0,0,CA,Angel
Aurobindo Pharma,28-Oct-2021,NSE,Buy,681.5,300,306.69,287.94,"2,05,044.63",Delivery,Angel
IRB Infra.Devl.,22-Oct-2021,NSE,SELL,279,1000,418.5,392.93,"2,78,188.57",Delivery,Angel
IRB Infra.Devl.,21-Oct-2021,NSE,SELL,246.2,1000,369.3,346.74,"2,45,483.96",Delivery,Angel
IRB Infra.Devl.,21-Oct-2021,NSE,SELL,246.2,600,221.58,208.04,"1,47,290.38",Delivery,Angel
Aurobindo Pharma,20-Oct-2021,NSE,Buy,697.5,300,313.89,294.7,"2,09,858.59",Delivery,Angel
Hindustan Zinc,18-Oct-2021,NSE,SELL,392,500,294,276.04,"1,95,429.96",Delivery,Angel
Vedanta,18-Oct-2021,NSE,SELL,373,10,5.6,5.25,3719.15,Delivery,Angel
Vedanta,18-Oct-2021,NSE,SELL,373,990,553.91,520.06,"3,68,196.03",Delivery,Angel
Hindustan Copper,14-Oct-2021,NSE,SELL,134,500,100.5,94.36,66805.14,Delivery,Angel
Hindustan Copper,14-Oct-2021,NSE,SELL,134,1000,201,188.72,"1,33,610.28",Delivery,Angel
ITC,14-Oct-2021,NSE,SELL,255,700,267.75,251.39,"1,77,980.86",Delivery,Angel
Hindustan Copper,01-Oct-2021,NSE,Buy,109.9,1000,164.9,154.79,"1,10,219.69",Delivery,Angel
```

## Sample output Pnl file
Following fields are captured in pnl file
[ 'company', 'gain_type', 'quarter', 's_date', 'b_date', 's_qty', 's_price', 's_other_chrg', 's_value', 'b_qty', 'b_price', 'b_other_chrg', 'b_value','pnl' ]

**Data not accurate**

```
company,gain_type,quarter,s_date,b_date,s_qty,s_price,s_other_chrg,s_value,b_qty,b_price,b_other_chrg,b_value,pnl
NANDAN DENIM LIMITED,LTCG,4,2022-01-14,2018-03-06,198,153.11,113.49,30202.29,198,139.0,81.83,27603.83,2598.46
Sterlite Tech.,LTCG,3,2021-11-16,2018-12-21,356,304.0,343.57,107880.43,356,285.0,299.71,101759.71,6120.72
IRB Infra.Devl.,STCG,3,2021-10-22,2020-11-13,1000,279.0,849.79,278150.21,1000,109.0,322.37,109322.37,168827.84
Hindustan Zinc,LTCG,3,2021-10-18,2020-02-03,500,392.0,603.51,195396.49,500,190.5,281.48,95531.48,99865.01
Vedanta,LTCG,3,2021-10-18,2020-02-03,10,373.0,35.34,3694.66,10,133.5,3.41,1338.41,2356.25
Hindustan Copper,LTCG,3,2021-10-14,2020-02-03,500,134.0,221.92,66778.08,500,39.95,59.17,20034.17,46743.91
ITC,STCG,3,2021-10-14,2021-03-02,700,255.0,551.81,177948.19,700,209.5,434.55,147084.55,30863.64
Vodafone Idea,LTCG,2,2021-08-04,2020-07-27,10000,6.1,204.05,60795.95,10000,8.0,236.86,80236.86,-19440.91
Q1,LTCG,1,0,0,0,0,0,0.00,0,0,0,0.00,0.00
Q2,LTCG,2,0,0,0,0,0,182387.85,0,0,0,227672.04,-45284.19
Q3,LTCG,3,0,0,0,0,0,1437663.27,0,0,0,762629.95,675033.32
Q4,LTCG,4,0,0,0,0,0,414215.71,0,0,0,264552.00,149663.71
Q5,LTCG,5,0,0,0,0,0,0.00,0,0,0,0.00,0.00
Q1,STCG,1,0,0,0,0,0,0.00,0,0,0,0.00,0.00
Q2,STCG,2,0,0,0,0,0,0.00,0,0,0,0.00,0.00
Q3,STCG,3,0,0,0,0,0,589678.17,0,0,0,366631.92,223046.25
Q4,STCG,4,0,0,0,0,0,0.00,0,0,0,0.00,0.00
Q5,STCG,5,0,0,0,0,0,0.00,0,0,0,0.00,0.00
```

## Sample div pnl file
Following fields are captured in dividend pnl file
[ 'company', 'quarter', 'div_date', 'div_value']

**Date not accurate**

```
company,quarter,div_date,div_value
Aurobindo Pharma,4,2022-02-17,1650.00
CCL Products,4,2022-01-30,1134.00
GAIL (India),5,2022-03-20,2500.00
Hindustan Copper,2,2021-09-13,175.00
Huhtamaki India,1,2021-04-19,8757.00
ITC,1,2021-06-09,4025.00
IndusInd Bank,2,2021-08-16,550.00
Kalpataru Power,2,2021-07-06,750.00
Lupin,2,2021-07-26,812.50
NTPC,4,2022-02-02,8000.00
Petronet LNG,2,2021-06-30,1750.00
Prakash Pipes,2,2021-09-13,1034.40
Prince Pipes,3,2021-11-11,126.00
Sterlite Tech.,2,2021-08-19,11712.00
TVS Motor Co.,5,2022-03-24,3.75
Vedanta,4,2022-03-08,26000.00
Vedanta,4,2021-12-16,27000.00
Wheels India,2,2021-07-26,2.00
Zensar Tech.,4,2022-02-02,1500.00
Q1,1,0,21539.0
Q2,2,0,61009.9
Q3,3,0,4526.0
Q4,4,0,67284.0
Q5,5,0,2503.75
```
