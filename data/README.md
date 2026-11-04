# Data

The experiment logs (`*.csv`) are synthetic and are created by `python -m ab_toolkit data`
(about 2 seconds, fixed seed, so the results are identical every time). They are not committed to Git.

| File | Rows | One row per | Columns |
|---|---|---|---|
| checkout_redesign.csv | 100,000 | visitor | experiment, user_id, date, group, device, visitor_type, converted, revenue, returned |
| free_delivery_30.csv | 100,000 | visitor | same |
| recommendations_widget.csv | 100,000 | visitor | same |
| unit_price_display.csv | 98,104 | visitor | same (some treatment visitors lost by a simulated tracking bug) |
| email_subject_line.csv | 40,000 | loyalty member | experiment, user_id, group, pre_period_spend, opened, spend_30d |
