# optimizations.md

This was a practice run completed with AI assistance and I did not measure performance, so I am not claiming any speed improvements.

## 1. Baseline and objective
My main focus was making the code correct and easier to understand. I worked on issues such as float division with round(), repeated use of setdefault, and missing input validation. Performance wasn’t really an issue with this dataset, as the entire test suite runs in less than a second.

## 2. Options considered
Here’s a more natural version that explains the decisions without sounding overly formal:

Using a set for processed_event_ids: A set would make checking duplicate events faster (O(1) instead of O(n)). However, I kept the existing list because the model and tests expect a list, and sets are not directly JSON-serialisable or ordered. Maintaining both a list and a set would also mean storing the same information twice.

Using integer-based calculations: I replaced float division and round() with integer floor division (//). This avoids rounding issues, works correctly with large paise values, and follows the required calculation.

Using cumulative refund calculations: Instead of calculating reversed points separately for every refund, I used the cumulative refunded amount. This prevents rounding differences when a purchase is refunded in multiple parts.

Raising exceptions for invalid inputs: I considered this approach but decided against it. The expected behaviour is to safely ignore invalid events rather than crash the program because of one incorrect record.

## 3. Changes implemented
I created a reusable _is_int helper and used it across all three functions to avoid repeating type checks and to make sure boolean values are not accidentally accepted as integers.

I kept the original starter code structure and made small, focused changes instead of rewriting the entire file. This also made the changes easier to understand and review.

I added early return out checks for missing IDs, duplicate events, and invalid amounts. These checks happen before modifying the account, so rejected events cannot leave behind partial changes.

I removed the unnecessary max(1, ...) check from the refund formula because the validation already ensures that the original purchase amount is positive before processing a refund.

Finally, I ran the complete test suite again, and all 242 tests passed successfully.

## 4. Trade-offs
Using early returns makes the function a little longer, but I kept this approach because each validation check is clearly visible and easier to follow. The code also uses deepcopy for every event, which takes time proportional to the account size. I kept it because the tests require the original account to remain unchanged.

## 5. Further improvements
In the future, I would like to make a few more improvements to the code:

Add named constants, such as PAISE_PER_100_RUPEES = 10000, and create a small helper function for ledger entries to avoid repeating the same values and code.

If the number of accounts and events grows, consider using a private set of event IDs for faster duplicate checks while keeping the original list unchanged.

Use timeit to measure execution time by replaying the dataset multiple times before and after the changes, so any performance improvement can be verified rather than assumed.

Return a clear rejection reason whenever an event is ignored, making it easier to understand why a transaction was not processed.