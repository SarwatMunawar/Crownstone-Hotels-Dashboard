# Crownstone Hotels UK - Streamlit Analytics Dashboard

This package contains cleaned data extracts, a multi-page Streamlit dashboard, an analytical summary and a PDF report.

## Dashboard pages
1. Executive Overview
2. Revenue & Channels
3. Operations & Cost
4. Guest Experience
5. Workforce
6. Booking Funnel & Insights

## Filters
Hotel, City, Region, Channel Group, Booking Source, Booking Status, Loyalty Tier, Room Type and Booking Date.

All KPI cards and charts recalculate from the active filters.

## Run
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Modelling note
The uploaded workbook is a hotel operations dataset, not a recruitment dataset. The process funnel is therefore a booking lifecycle funnel rather than a recruitment funnel.

The Legacy OTA table is cleaned as a staging dataset but is not appended to the booking fact until canonical keys and duplicate checks are resolved.
