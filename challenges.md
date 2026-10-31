# Challenges and debugging evidence

## Scope of this record
The original author's debugging experience was not provided. This is an AI-assisted review of observable defects and checks, not a fabricated first-person account of obstacles.

## Tricky boundary: cumulative partial refunds
A 100,000-paise purchase awards 10 points. Refunding 60,000 reverses 6; a subsequent 50,000 refund must be rejected because the cumulative total would exceed the purchase. `test_multiple_partial_refunds_cannot_exceed_purchase` passes and leaves refunded paise at 60,000 and balance at 4. The guard runs before updating totals. Refund replay is independently covered by `test_refund_event_once`.

## Calculation and replay evidence
The reconstructed starter returned 2 for 19,999 paise at one point per 100 rupees; `test_points_use_floor` now passes with 1. A cap of zero previously returned 5 for 50,000 paise and now returns 0. Purchase replays formerly changed state or duplicated processed IDs; the acceptance matrix now passes all 20 replay cases.

## Review correction
The fourth commit removed the reversed-points assertion from the existing partial-refund test. Documentation preparation restored that assertion; the suite still passes. This protects transaction audit state as well as the balance.

## Verification obstacles
The default Windows Python launcher was unavailable. The bundled Python 3.12.14 runtime ran the demo, but initially lacked pytest. Dependencies were installed into ignored `.venv/test-deps`, then the suite ran successfully. The starter baseline was reproduced from a Git archive without changing the working branch.

## Remaining limits
No original pre-change test log was supplied. Visible tests do not prove every malformed account structure is safe. For example, unhashable identifiers are outside current validation. Accounts are assumed to follow `models.new_account`; concurrency and persistence are outside this offline service. No timing benchmark was run.
