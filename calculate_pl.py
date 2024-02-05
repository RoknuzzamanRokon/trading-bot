pp = 1.0
lp = 1.0
amount = 42000
print(f"Actual value: {amount}")
def profit_amount(ia, pp):
    try:
        ia = float(ia) 
        profit_percentage_amount = (pp / 100) * ia
        total_profit_amount = ia + profit_percentage_amount
        return total_profit_amount
    except ValueError:
        print(f'Error converting ia to float in profit_amount')
        return None

def loss_amount(ia, lp):
    try:
        ia = float(ia) 
        loss_percentage_amount = (lp / 100) * ia
        total_loss_amount = ia - loss_percentage_amount
        return total_loss_amount
    except ValueError:
        print(f'Error converting ia to float in loss_amount')
        return None
    
profit = profit_amount(amount, pp=pp )
loss = loss_amount(amount, lp=lp)

total_increment = profit - loss
print(f"profit sell {profit}")
print(f"Loss sell {loss}")
print(f"Total increment value: {total_increment}")
