from fixtures import sample_rules, sample_transactions
from service import calculate_points, flag_repeat_transactions

if __name__=='__main__':
    rules=sample_rules(); print('Points example:',calculate_points(259900,rules['points_per_100_rupees'],rules['bonus_percent'],rules['cap_points']))
    print('Repeat warnings:',flag_repeat_transactions(sample_transactions()))
