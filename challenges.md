# challenges.md - COMPULSORY submission

This file is mandatory and worth 5 marks. Describe your actual experience honestly. Do not invent difficulties to fill the page.

## 1. Challenge or confusing behaviour

The hardest part was making sure refunds didn't get processed twice, keeping the correct math for partial refunds , and making sure refund amounts didn't go over the allowed limit. The original code stopped duplicate transactions, but it was still wrongly adding event IDs every time an event was replayed.

## 2. Evidence

A test failed because it expected the list to only have the event once .

A test failed because invalid or too-large refunds shouldn't alter the account balance.

A test checked if the refund amounts stayed within safe limits.

## 3. What I tried

1. Ran the test command (python -m pytest -q), which showed 45 test failures to start with

2. Tested event replays by hand to confirm where duplicate event IDs were being added.

## 4. Resolution

Added a quick check at the start of the code to exit early if an event ID had already been processed.

Fixed the math for calculating proportional refunds using the total refunded amount so far.

## 5. Proof and regression prevention

All 214 tests now pass successfully, including all the replay and refund limit tests.

## 6. Unresolved challenge or next step

There are no failing tests left and everything is working correctly. We could add more documentation or extra tests later, but there are no major blockers remaining.

If you did not encounter a major blocker, say so honestly and document the hardest edge case you deliberately tested and what it taught you. Do not manufacture a story.