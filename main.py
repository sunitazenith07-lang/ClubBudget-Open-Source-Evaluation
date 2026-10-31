import argparse

from fixtures import sample_rules, sample_transactions
from service import DEFAULT_REPEAT_THRESHOLD, calculate_points, flag_repeat_transactions


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description='RewardBook offline demo')
    parser.add_argument('--threshold', type=int, default=DEFAULT_REPEAT_THRESHOLD,
                        help='alert above this many matching transactions (default: %(default)s)')
    args = parser.parse_args(argv)
    if args.threshold < 1:
        parser.error('--threshold must be 1 or more')
    return args


if __name__=='__main__':
    args=parse_args()
    rules=sample_rules(); print('Points example:',calculate_points(259900,rules['points_per_100_rupees'],rules['bonus_percent'],rules['cap_points']))
    print('Repeat warnings:',flag_repeat_transactions(sample_transactions(),args.threshold))
