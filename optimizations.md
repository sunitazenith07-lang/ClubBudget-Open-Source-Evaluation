optimizations.md - Required submission

I am a first-year student who recently finished learning the basics of Python. While fixing the project, I also looked at whether the code could be made easier to read and whether some unnecessary work could be avoided.

1. Baseline and objective

The main things I wanted to improve were correctness, input checking, readability, and avoiding repeated work where possible.

The starter code always made a deep copy of the account in apply_reward_event and continued processing even when an event_id had already been used. The points calculation also used floating-point division with round(amount_paise / 10000), which caused incorrect results for some amounts.

I also noticed that service.py had several statements written on the same line using semicolons. This made the code harder for me to read and debug.

The original test run had 92 failing tests. Most of the problems were related to missing input validation, the points rounding logic, and duplicate event handling.

2. Options I considered

Option 1 was to keep deepcopy(account), but add early checks for invalid and duplicate events. I also used integer division with // and a shared is_valid_int helper.

The main advantage of this approach is that the original account dictionary is not changed accidentally. This is important because tests such as test_input_account_not_mutated and test_event_processing_does_not_mutate_input_account check for this.

Another advantage is that the code is easier for me to understand and it passed all 205 tests.

The downside is that deepcopy copies the whole account every time the function is called. If an account had thousands of transactions, this could use more memory and take more time.

Option 2 was to avoid deepcopy and only copy the parts of the account that are going to change. This could be faster and use less memory for large accounts.

However, this approach is easier to get wrong. If I forgot to copy one nested dictionary or list, the original account could be changed by accident. Because avoiding mutation was an important requirement, I decided not to use this approach.

3. Changes implemented

I chose the first option because correctness and keeping the input account unchanged were more important for this project.

I replaced round(amount_paise / 10000) with amount_paise // 10000 so the calculation uses complete ₹100 blocks without floating-point rounding.

I also added early return checks in calculate_points, apply_reward_event, and flag_repeat_transactions. This means invalid inputs or duplicate events can be stopped before the rest of the function does unnecessary work.

I changed service.py so that statements are written on separate lines instead of putting several statements together with semicolons. This makes the code easier to follow.

The tests in tests/test_contract.py and tests/test_acceptance_matrix.py check that these changes work correctly. In total, all 205 tests passed, including the tests for preventing changes to the input account.

I did not measure the actual execution speed because the main purpose of my changes was to fix the behaviour, handle invalid inputs safely, and make the code easier to understand.

4. Trade-offs

Using deepcopy(account) does use some extra memory and takes some extra time because the complete account is copied. However, it also makes it much safer because the original account cannot be accidentally changed while processing an event.

Another trade-off is checking whether an event_id is already in processed_event_ids. Since processed_event_ids is a Python list, checking if an item is already there takes O(N) time, where N is the number of processed events.

I kept it as a list because the existing project and tests expect processed_event_ids to be a list. For example, the tests check that it equals ['E1'].

5. Further improvements

If the project later had accounts with tens of thousands of events, duplicate event checking could become slower.

One possible improvement would be to keep a set along with the existing processed_event_ids list. The list could still be used where the project needs it, while the set could make duplicate checks much faster because set lookups are normally O(1).

I would only make this change if the project actually became large enough for the performance difference to matter. For the current project, keeping the simpler list-based approach is enough.