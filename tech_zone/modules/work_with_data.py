from decimal import Decimal
from bot.tech_zone.modules.database_admin import table_select, table_update


def work_volume_calculation(trade_percent='0', trade_volume='0', trade_commission='0', current_trade_id=None):
    balance = table_select('balance')
    print(f'balance = {balance}')
    if float(balance) <= 0:
        return 'баланс пуст'

    base_work_volume = Decimal(balance) * Decimal(12.5) // 100 * 100

    current_work_volume = table_select('volume')
    try:
        Decimal(current_work_volume)
    except ArithmeticError:
        table_update('volume', base_work_volume)
        current_work_volume = table_select('volume')

    results = table_select('results')
    try:
        Decimal(results)
    except ArithmeticError:
        table_update('results', '0')

    day_results = table_select('day_results')
    try:
        Decimal(day_results)
    except ArithmeticError:
        table_update('day_results', '0')

    print('check done')

    change_volume = (Decimal(trade_volume) * (100 + Decimal(trade_percent)) / 100) - Decimal(trade_commission)
    new_balance = Decimal(balance) + change_volume - Decimal(trade_volume)

    if Decimal(trade_percent) == 0:
        table_update('volume', int(base_work_volume))
        table_update('day_results', '0')
        table_update('results', '0')

        current_work_volume = table_select('volume')
        return current_work_volume

    else:
        table_update('balance', round(new_balance, 3))
        table_update('results', round(Decimal(results) + Decimal(trade_percent) - Decimal(trade_commission) / Decimal(trade_volume) * 100, 3))
        table_update('day_results', round(Decimal(day_results) + Decimal(trade_percent), 3))
        table_update('previous_trade_id', current_trade_id)

        day_results = table_select('day_results')

        if Decimal(day_results) < -1.5:
            table_update('volume', int(base_work_volume))
            table_update('day_results', '0')
            table_update('results', '0')
            return 'просадка превышена'
        else:
            results = table_select('results')

            if Decimal(results) < -0.5:
                table_update('volume', int(current_work_volume) - 100)
                table_update('results', '0')

            elif Decimal(results) > 1:
                table_update('volume', int(current_work_volume) + 100)
                table_update('results', '0')

            current_work_volume = table_select('volume')
            results = table_select('results')

            if results == '0':
                return current_work_volume
            else:
                return current_work_volume


def main():
    work_volume_calculation()


if __name__ == '__main__':
    main()