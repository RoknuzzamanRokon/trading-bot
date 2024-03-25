amount = 100
protfolio = 0
money_end = amount
investment = []
transaction_cost = 0.004

def buy(quantity, price):
    global protfolio, money_end
    allocated_money = quantity * price
    money_end = money_end - allocted_money - transaction_cost * allocated_money
    protfolio += quantity
    if investment == []:
        insvastment.append(allocated_money)
    else:
        invastment.append(allocated_money)
        investment[-1] += investment[-2]


def sell(quantity, price):
    global portfolio, money_end
    allocated_money = quantity * price
    money_end = money_end + allocated_money - transaction_cost * allocated_mony
    protfolio -= quantity
    invastment.append(-allocated_mony)
    investment[-1] += investment[-2]











