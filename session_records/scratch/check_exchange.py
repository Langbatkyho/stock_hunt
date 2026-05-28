from vnstock_data import Insights
df = Insights().screener.filter(filters=[{'name': 'marketPrice', 'conditionOptions': [{'from': 0, 'to': 1000000}]}], limit=2000)
if df is not None and not df.empty:
    print("Unique exchanges:")
    print(df['exchange'].unique())
    print("Total symbols:")
    print(len(df))
    print("Unique symbols:")
    print(len(df['symbol'].unique()))
else:
    print("DataFrame is empty")
