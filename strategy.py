#pip install ccxt

import config
import pandas as pd
import ccxt
from smtplib import SMTP

# SETTİNGS
symbolName = input("Symbol (BTC, ETH, LTC...): ").upper()
leverage = float(input("Leverage: "))
baseOrderSize = float(input("Base Order Size: "))
safetyOrderSize = float(input("Safety Order Size: "))
maxSafetyTradesCount = float(input("Max Safety Trades Count: "))
priceDeviation = float(input("Price Deviation %: "))
safetyOrderStepScale = float(input("Safety Order Step Scale: "))
safetyOrderVolumeScale = float(input("Safety Order Volume Scale: "))
takeProfitType = float(input("Take Profit Type (Classic TP(1) - Trailing TP(2)): "))
if takeProfitType == 1:
    takeProfit = float(input("Take Profit %: "))
if takeProfitType == 2:
    takeProfitTrigger = float(input("Trailing Take Profit Trigger %: "))
    takeProfitTrailing = float(input("Trailing Take Profit %: "))
SLselection = float(input("Do you want stop loss? = YES(1) - NO(2): "))
if SLselection == 1:
    stopLossType = float(input("Stop Loss Type = Classic SL(1) - Trailing SL(2): "))
    if stopLossType == 1:
        stopLoss = float(input("Stop Loss %: "))
    if stopLossType == 2:
        stopLossTrailing = float(input("Trailing Stop Loss %: "))
positionSide = float(input("Position Side = Only Long(1) - Only Short(2) - Long and Short(3): "))
profitAmount = float(input("Profit Amount: "))
mail = float(input("Bot Send e-mail? (YES(1) - NO(2)): "))


#ATTRIBUTES
first = True
longTPtrigger = False
shortTPtrigger = False
lastOrderPrice = 0
tradeCount = 0
symbol = symbolName+"/USDT"
mainSafetyOrderSize = safetyOrderSize
mainPriceDeviation = priceDeviation
takeProfitCount = 0
highestPrice = 0
lowestPrice = 0

# API CONNECT
exchange = ccxt.binance({
"apiKey": config.apiKey,
"secret": config.secretKey,

'options': {
'defaultType': 'future'
},
'enableRateLimit': True
})

while True:
    try:
        
        balance = exchange.fetch_balance()
        free_balance = exchange.fetch_free_balance()
        positions = balance['info']['positions']
        newSymbol = symbolName+"USDT"
        current_positions = [position for position in positions if float(position['positionAmt']) != 0 and position['symbol'] == newSymbol]
        position_info = pd.DataFrame(current_positions, columns=["symbol", "entryPrice", "unrealizedProfit", "isolatedWallet", "positionAmt", "positionSide"])
        
        # in position?
        if not position_info.empty and position_info["positionAmt"][len(position_info.index) - 1] != 0:
            inPosition = True
        else: 
            inPosition = False
            longPosition = False
            shortPosition = False
            
        # in long position?
        if not position_info.empty and float(position_info["positionAmt"][len(position_info.index) - 1]) > 0:
            longPosition = True
            shortPosition = False
        # in short position?
        if not position_info.empty and float(position_info["positionAmt"][len(position_info.index) - 1]) < 0:
            shortPosition = True
            longPosition = False
        
        
        # LOAD BARS
        bars = exchange.fetch_ohlcv(symbol, timeframe="1m", since = None, limit = 1)
        df = pd.DataFrame(bars, columns=["timestamp", "open", "high", "low", "close", "volume"])
        
        # Get current price
        currentPrice = float(df["close"][len(df.index) - 1])

        # Starting price
        if first:
            firstPrice = float(df["close"][len(df.index) - 1])
            highestPrice = currentPrice
            lowestPrice = currentPrice
            first = False
            

        
        # LONG ENTER
        def longEnter(alinacak_miktar):
            order = exchange.create_market_buy_order(symbol, alinacak_miktar)

            
        # LONG EXIT
        def longExit():
            order = exchange.create_market_sell_order(symbol, float(position_info["positionAmt"][len(position_info.index) - 1]), {"reduceOnly": True})


        # SHORT ENTER
        def shortEnter(alincak_miktar):
            order = exchange.create_market_sell_order(symbol, alincak_miktar)

            
        # SHORT EXIT
        def shortExit():
            order = exchange.create_market_buy_order(symbol, (float(position_info["positionAmt"][len(position_info.index) - 1]) * -1), {"reduceOnly": True})


        if inPosition == False:
            priceDeviation = mainPriceDeviation
            safetyOrderSize = mainSafetyOrderSize

        
        # LONG ENTER
        if firstPrice - (firstPrice/100) * priceDeviation >= currentPrice and shortPosition == False and maxSafetyTradesCount>tradeCount and float(free_balance["USDT"]) >= baseOrderSize and (positionSide == 1 or positionSide == 3):
            if tradeCount == 0:
                alinacak_miktar = (baseOrderSize * float(leverage)) / float(df["close"][len(df.index) - 1])
            if tradeCount > 0:
                alinacak_miktar = (safetyOrderSize * float(leverage)) / float(df["close"][len(df.index) - 1])
                safetyOrderSize = safetyOrderSize*safetyOrderVolumeScale

            priceDeviation = priceDeviation * safetyOrderStepScale
            longEnter(alinacak_miktar)
            print("LONG ENTER")
            first = True
            tradeCount = tradeCount + 1
            if tradeCount >= maxSafetyTradesCount:
                lastOrderPrice = currentPrice
            if mail == 1:
                baslik = symbol
                message = "LONG ENTER\n" + "TOTAL MONEY: " + str(balance['total']["USDT"])
                content = f"Subject: {baslik}\n\n{message}"
                mail = SMTP("smtp.gmail.com", 587)
                mail.ehlo()
                mail.starttls()
                mail.login(config.mailAddress, config.password)
                mail.sendmail(config.mailAddress, config.mailAddress, content.encode("utf-8"))
        
        # SHORT ENTER
        if ((firstPrice / 100) * priceDeviation) + firstPrice <= currentPrice and longPosition == False and maxSafetyTradesCount>tradeCount and float(free_balance["USDT"]) >= baseOrderSize and (positionSide == 2 or positionSide == 3): 
            if tradeCount == 0:
                alinacak_miktar = (baseOrderSize * float(leverage)) / float(df["close"][len(df.index) - 1])
            if tradeCount > 0:
                alinacak_miktar = (safetyOrderSize * float(leverage)) / float(df["close"][len(df.index) - 1])
                safetyOrderSize = safetyOrderSize*safetyOrderVolumeScale

            priceDeviation = priceDeviation * safetyOrderStepScale
            shortEnter(alinacak_miktar)
            print("SHORT ENTER")
            first = True
            tradeCount = tradeCount + 1
            if tradeCount >= maxSafetyTradesCount:
                lastOrderPrice = currentPrice
            if mail == 1:
                baslik = symbol
                message = "SHORT ENTER\n" + "TOTAL USDT: " + str(balance['total']["USDT"])
                content = f"Subject: {baslik}\n\n{message}"
                mail = SMTP("smtp.gmail.com", 587)
                mail.ehlo()
                mail.starttls()
                mail.login(config.mailAddress, config.password)
                mail.sendmail(config.mailAddress, config.mailAddress, content.encode("utf-8"))
            
            
        # LONG TAKE PROFIT - CLASSIC
        if takeProfitType == 1 and longPosition and ((float(position_info["entryPrice"][len(position_info.index) - 1])/100)*takeProfit)+float(position_info["entryPrice"][len(position_info.index) - 1]) <= currentPrice and (positionSide == 1 or positionSide == 3):
            print("TAKE PROFIT")
            longExit()
            first = True
            tradeCount = 0
            if mail == 1:
                baslik = symbol
                message = "LONG TAKE PROFIT\n" + "TOTAL USDT: " + str(balance['total']["USDT"])
                content = f"Subject: {baslik}\n\n{message}"
                mail = SMTP("smtp.gmail.com", 587)
                mail.ehlo()
                mail.starttls()
                mail.login(config.mailAddress, config.password)
                mail.sendmail(config.mailAddress, config.mailAddress, content.encode("utf-8"))
            takeProfitCount = takeProfitCount+ 1

        # get highest price
        if currentPrice > highestPrice:
            highestPrice = currentPrice
        else: highestPrice = highestPrice

        # LONG TAKE PROFIT - TRAILING TRIGGER
        if takeProfitType == 2 and longPosition and ((float(position_info["entryPrice"][len(position_info.index) - 1])/100)*takeProfitTrigger)+float(position_info["entryPrice"][len(position_info.index) - 1]) <= currentPrice:
            longTPtrigger = True

        # LONG TAKE PROFIT - TRAILING
        if takeProfitType == 2 and longTPtrigger and longPosition and highestPrice - (highestPrice/100) * takeProfitTrailing >= currentPrice  and (positionSide == 1 or positionSide == 3):
            print("TRAILING TAKE PROFIT")
            longExit()
            longTPtrigger = False
            first = True
            tradeCount = 0
            if mail == 1:
                baslik = symbol
                message = "LONG TRAILING TAKE PROFIT\n" + "TOTAL USDT: " + str(balance['total']["USDT"])
                content = f"Subject: {baslik}\n\n{message}"
                mail = SMTP("smtp.gmail.com", 587)
                mail.ehlo()
                mail.starttls()
                mail.login(config.mailAddress, config.password)
                mail.sendmail(config.mailAddress, config.mailAddress, content.encode("utf-8"))
            takeProfitCount = takeProfitCount+ 1


        # SHORT TAKE PROFIT - CLASSIC
        if takeProfitType == 1 and shortPosition and float(position_info["entryPrice"][len(position_info.index) - 1]) - (float(position_info["entryPrice"][len(position_info.index) - 1])/100) * takeProfit >= currentPrice and (positionSide == 2 or positionSide == 3):
            print("TAKE PROFIT")
            shortExit()
            first = True
            shortTPtrigger = False
            tradeCount = 0
            if mail == 1:
                baslik = symbol
                message = "SHORT TAKE PROFIT\n" + "TOTAL USDT: " + str(balance['total']["USDT"])
                content = f"Subject: {baslik}\n\n{message}"
                mail = SMTP("smtp.gmail.com", 587)
                mail.ehlo()
                mail.starttls()
                mail.login(config.mailAddress, config.password)
                mail.sendmail(config.mailAddress, config.mailAddress, content.encode("utf-8"))
            takeProfitCount = takeProfitCount+ 1


        # get lowest price
        if currentPrice < lowestPrice:
            lowestPrice = currentPrice
        else: lowestPrice = lowestPrice

        # SHORT TAKE PROFIT - TRAILING TRIGGER
        if takeProfitType == 2 and shortPosition and float(position_info["entryPrice"][len(position_info.index) - 1]) - (float(position_info["entryPrice"][len(position_info.index) - 1])/100) * takeProfitTrigger >= currentPrice:
            shortTPtrigger = True
        
        # SHORT TAKE PROFIT - TRAILING
        if takeProfitType == 2 and shortTPtrigger and shortPosition and ((lowestPrice / 100) * stopLossTrailing) + lowestPrice <= currentPrice and (positionSide == 2 or positionSide == 3):
            print("TRAILING STOP LOSS")
            shortExit()
            first = True
            shortTPtrigger = False
            tradeCount = 0
            takeProfitCount = takeProfitCount + 1
            if mail == 1:
                baslik = symbol
                message = "SHORT TRAILING STOP LOSS\n" + "TOTAL USDT: " + str(balance['total']["USDT"])
                content = f"Subject: {baslik}\n\n{message}"
                mail = SMTP("smtp.gmail.com", 587)
                mail.ehlo()
                mail.starttls()
                mail.login(config.mailAddress, config.password)
                mail.sendmail(config.mailAddress, config.mailAddress, content.encode("utf-8"))


        # LONG STOP LOSS - CLASSIC
        if SLselection == 1 and stopLossType == 1 and longPosition  and maxSafetyTradesCount<=tradeCount and lastOrderPrice - (lastOrderPrice/100) * stopLoss >= currentPrice and (positionSide == 1 or positionSide == 3):
            print("STOP LOSS")
            longExit()
            longTPtrigger = False
            first = True
            tradeCount = 0
            if mail == 1:
                baslik = symbol
                message = "LONG STOP LOSS\n" + "TOTAL USDT: " + str(balance['total']["USDT"])
                content = f"Subject: {baslik}\n\n{message}"
                mail = SMTP("smtp.gmail.com", 587)
                mail.ehlo()
                mail.starttls()
                mail.login(config.mailAddress, config.password)
                mail.sendmail(config.mailAddress, config.mailAddress, content.encode("utf-8"))

        # LONG STOP LOSS - TRAILING
        if SLselection == 1 and stopLossType == 2 and longPosition and maxSafetyTradesCount<=tradeCount and highestPrice - (highestPrice/100) * stopLossTrailing >= currentPrice and (positionSide == 1 or positionSide == 3):
            print("TRAILING STOP LOSS")
            longExit()
            longTPtrigger = False
            first = True
            tradeCount = 0
            if mail == 1:
                baslik = symbol
                message = "LONG TRAILING STOP LOSS\n" + "TOTAL USDT: " + str(balance['total']["USDT"])
                content = f"Subject: {baslik}\n\n{message}"
                mail = SMTP("smtp.gmail.com", 587)
                mail.ehlo()
                mail.starttls()
                mail.login(config.mailAddress, config.password)
                mail.sendmail(config.mailAddress, config.mailAddress, content.encode("utf-8"))
        
        # SHORT STOP LOSS - CLASSIC
        if SLselection == 1 and stopLossType == 1 and shortPosition and maxSafetyTradesCount<=tradeCount and ((lastOrderPrice / 100) * stopLoss) + lastOrderPrice <= currentPrice and (positionSide == 2 or positionSide == 3):
            print("STOP LOSS")
            shortExit()
            first = True
            shortTPtrigger = False
            tradeCount = 0
            if mail == 1:
                baslik = symbol
                message = "SHORT STOP LOSS\n" + "TOTAL USDT: " + str(balance['total']["USDT"])
                content = f"Subject: {baslik}\n\n{message}"
                mail = SMTP("smtp.gmail.com", 587)
                mail.ehlo()
                mail.starttls()
                mail.login(config.mailAddress, config.password)
                mail.sendmail(config.mailAddress, config.mailAddress, content.encode("utf-8"))

        # SHORT STOP LOSS- TRAILING
        if SLselection == 1 and stopLossType == 1 and shortPosition and maxSafetyTradesCount<=tradeCount and ((lowestPrice / 100) * stopLoss) + lowestPrice <= currentPrice and (positionSide == 2 or positionSide == 3):
            print("STOP LOSS")
            shortExit()
            first = True
            shortTPtrigger = False
            tradeCount = 0
            if mail == 1:
                baslik = symbol
                message = "SHORT STOP LOSS\n" + "TOTAL USDT: " + str(balance['total']["USDT"])
                content = f"Subject: {baslik}\n\n{message}"
                mail = SMTP("smtp.gmail.com", 587)
                mail.ehlo()
                mail.starttls()
                mail.login(config.mailAddress, config.password)
                mail.sendmail(config.mailAddress, config.mailAddress, content.encode("utf-8"))


        if takeProfitCount == profitAmount:
            exit()

        print("=================================== SETTINGS ===================================")
        print("Pair: ", symbol, " Leverage: ", leverage)
        print("Base Order Size: ", baseOrderSize, " Safety Order Size: ", safetyOrderSize)
        print("Max Safety Trades Count: ", maxSafetyTradesCount, " Price Deviation: %"+str(priceDeviation))
        print("Safety Order Step Scale: ", safetyOrderStepScale, " Safety Order Volume Scale: ", safetyOrderVolumeScale)
        if takeProfitType == 1:
            print("Take Profit Type Is Classic. Take Profit: %"+str(takeProfit))
        if takeProfitType == 2:
            print("Take Profit Type Is Trailing. Trigger: %"+str(takeProfitTrigger), " Take Profit: %"+str(takeProfitTrailing))
        if SLselection == 2:
            print("No Stop Loss")
        if SLselection == 1:
            if stopLossType == 1:
                print("Stop Loss Type Is Classic. Stop Loss: %"+str(stopLoss))
            if stopLossType == 2:
                print("Stop Loss Type Is Trailing. Stop Loss: %"+str(stopLossTrailing))
        if positionSide == 1:
            print("Position Side Only Long")
        if positionSide == 2:
            print("Position Side Only Short")
        if positionSide == 3:
            print("Position Side Long and Short")
        print("After triggering take profit",profitAmount - takeProfitCount,"times, the bot will stop working")
        print("================================= INFORMATIONS =================================")
        if longTPtrigger:
            print("Long Take Profit Triggered")
        if shortTPtrigger:
            print("Short Take Profit Triggered")    
        if longPosition:
            print("In Long Position")
        if shortPosition:
            print("In Short Position")
        if inPosition:
            print("Trade Count: ", tradeCount, " Avarege Price: ", float(position_info["entryPrice"][len(position_info.index) - 1]), " Free Usdt: ", round(float(free_balance["USDT"]),2), " Total USDT: ", round(float(balance['total']["USDT"]),2))
        if inPosition == False: 
            print("Starting Price: ", firstPrice, " Current Price: ", currentPrice, " Total USDT: ", round(float(balance['total']["USDT"]),2))
        print("================================================================================")

    except ccxt.BaseError as Error:
        print ("[ERROR] ", Error )
        continue
