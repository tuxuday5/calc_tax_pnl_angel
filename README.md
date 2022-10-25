# canculate pnl for trades in angel broking for taxing purpose

#### usage: angel_pnl.py [-h] -t IN_FILE -p OUT_FILE -y FIN_YEAR

Calculate Angel Broking pnl based on trades

options:
  -h, --help            show this help message and exit
  -t IN_FILE, --trades-file IN_FILE
                        Trades file
  -p OUT_FILE, --pnl-file OUT_FILE
                        Out/Pnl file
  -y FIN_YEAR, --fin-year FIN_YEAR
                        Financial Year as YYYY-YYYYY

```
python3 -m pdb angel_pnl.py -t trades.csv -p pnl.csv -y 2021-2022
```
