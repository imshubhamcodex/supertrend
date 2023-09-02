import numpy as np
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import mplfinance as mpl
from datetime import datetime, time as datetime_time
import time

from mercury_Bot import send_message, send_img

# Fetch data
def fetch_data(ticker="^NSEI", time_interval="15m"):
    end_date = datetime.today().date()
    start_date = end_date - timedelta(days=50)
    data = yf.download(ticker, start=start_date, end=end_date, interval=time_interval)
    return data


def atr(DF,n):
    df=DF.copy()
    df['High-Low']=abs(df['High']-df['Low'])
    df['High-PreviousClose']=abs(df['High']-df['Close'].shift(1))
    df['Low-PreviousClose']=abs(df['Low']-df["Close"].shift(1))
    df['TrueRange']=df[['High-Low','High-PreviousClose','Low-PreviousClose']].max(axis=1,skipna=False)
    df['ATR']=df['TrueRange'].ewm(com=n,min_periods=n).mean()
    return df['ATR']


def supertrend(DF,n,m):
    df = DF.copy()
    df['ATR'] = atr(df,n)
    df["BASIC_UPPERBAND"]=((df['High']+df['Low'])/2) + m*df['ATR'] 
    df["BASIC_LOWERBAND"]=((df['High']+df['Low'])/2) - m*df['ATR']
    df["FINAL_UPPERBAND"]=df["BASIC_UPPERBAND"]
    df["FINAL_LOWERBAND"]=df["BASIC_LOWERBAND"]
    ind = df.index
    for i in range(n,len(df)):
        if df['Close'][i-1]<=df['FINAL_UPPERBAND'][i-1]:
            df.loc[ind[i],'FINAL_UPPERBAND']=min(df['BASIC_UPPERBAND'][i],df['FINAL_UPPERBAND'][i-1])
        else:
            df.loc[ind[i],'FINAL_UPPERBAND']=df['BASIC_UPPERBAND'][i]    
    for i in range(n,len(df)):
        if df['Close'][i-1]>=df['FINAL_LOWERBAND'][i-1]:
            df.loc[ind[i],'FINAL_LOWERBAND']=max(df['BASIC_LOWERBAND'][i],df['FINAL_LOWERBAND'][i-1])
        else:
            df.loc[ind[i],'FINAL_LOWERBAND']=df['BASIC_LOWERBAND'][i]  
    df['Strend']=np.nan
    for test in range(n,len(df)):
        if df['Close'][test-1]<=df['FINAL_UPPERBAND'][test-1] and df['Close'][test]>df['FINAL_UPPERBAND'][test]:
            df.loc[ind[test],'Strend']=df['FINAL_LOWERBAND'][test]
            break
        if df['Close'][test-1]>=df['FINAL_LOWERBAND'][test-1] and df['Close'][test]<df['FINAL_LOWERBAND'][test]:
            df.loc[ind[test],'Strend']=df['FINAL_UPPERBAND'][test]
            break
    for i in range(test+1,len(df)):
        if df['Strend'][i-1]==df['FINAL_UPPERBAND'][i-1] and df['Close'][i]<=df['FINAL_UPPERBAND'][i]:
            df.loc[ind[i],'Strend']=df['FINAL_UPPERBAND'][i]
        elif  df['Strend'][i-1]==df['FINAL_UPPERBAND'][i-1] and df['Close'][i]>=df['FINAL_UPPERBAND'][i]:
            df.loc[ind[i],'Strend']=df['FINAL_LOWERBAND'][i]
        elif df['Strend'][i-1]==df['FINAL_LOWERBAND'][i-1] and df['Close'][i]>=df['FINAL_LOWERBAND'][i]:
            df.loc[ind[i],'Strend']=df['FINAL_LOWERBAND'][i]
        elif df['Strend'][i-1]==df['FINAL_LOWERBAND'][i-1] and df['Close'][i]<=df['FINAL_LOWERBAND'][i]:
            df.loc[ind[i],'Strend']=df['FINAL_UPPERBAND'][i]
    return df['Strend']


def st_changes(data):
    data.index = pd.to_datetime(data.index)
    style = mpl.make_mpf_style(base_mpf_style='yahoo', gridstyle=':')
    fig, axes = mpl.plot(data, type='candle', style=style, addplot=[mpl.make_addplot(data['supertrend'], color='blue')],figsize=(16, 8) ,returnfig=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"mplfinance_chart_{timestamp}.png"
    fig.savefig(filename)  
    send_img(filename)
    send_message("*ALERT: SuperTrend Direction Changed on NSEI [15 min]*")
    

def check_dates(data_frame, st_changes, data):
    today = datetime.now().date()

    yesterday = today - timedelta(days=1)
    day_before_yesterday = today - timedelta(days=2)

    if today in data_frame.index or yesterday in data_frame.index in data_frame.index:
        st_changes(data)


def main():
    data = fetch_data()
    n=4
    m=18
    data['supertrend']=supertrend(data,n,m)
    add=mpl.make_addplot(data["supertrend"],color='blue')
    #mpl.plot(data,addplot=add,type='candle',style="yahoo")


    data['supertrend_diff'] = data['supertrend'].diff().abs()
    threshold = 300  # For example, a change of 100
    sharp_change_df = data[data['supertrend_diff'] > threshold]
    print(sharp_change_df)
    check_dates(sharp_change_df, st_changes, data)


# Looper
def check_and_call_function():
    current_time = datetime.now().time()
    
    print("\r" +"Time: "+ str(current_time), end='', flush=True)
    
    hour = 9
    
    start_timek = datetime_time(hour, 30)
    end_timek = datetime_time(hour, 32)
            
    if start_timek <= current_time <= end_timek:
        print(" ")
        main()
        print("Re-Run at " + str(current_time))
        time.sleep(2 * 60)


while True:
    check_and_call_function()
    time.sleep(60)  # 60-second wait





