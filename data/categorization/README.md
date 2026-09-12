# Labeled Transaction Dataset for ML Categorization (Task 3.1)

**Total Samples**: 720

**Target Domain**: Indian Retail Banking (UPI, NEFT, RTGS, IMPS, ACH, POS, ATM, NetBanking)

## Category Distribution

| Category | Sample Count | Sample Narrations |
|---|---|---|
| Dining | 60 | `UPI/CR/412345678901/swiggy@icici/Swiggy Order/UPI`<br>`UPI-SWIGGY-swiggy@icici-412345678901` |
| Entertainment | 60 | `UPI/DR/112233445566/bookmyshow@icici/PVR Cinema Tickets`<br>`POS PVR CINEMAS ORION MALL RAJAJINAGAR` |
| Groceries | 60 | `UPI/DR/418291029381/blinkit@kotak/Blinkit Delivery`<br>`UPI-ZEPTO-zepto@hdfc-882718291823` |
| Medical | 60 | `UPI/DR/890123456789/apollopharmacy@hdfcbank/Apollo Medicines`<br>`UPI/DR/102938475610/pharmeasy@icici/Online Pharmacy Medicine` |
| Miscellaneous | 60 | `ANNUAL SMS ALERT CHARGES Q1`<br>`DEBIT CARD ANNUAL MAINTENANCE CHARGES` |
| Rent | 60 | `NEFT-N123456789-RENT APRIL 2025-LANDLORD SANJAY`<br>`UPI/DR/418291029381/houseowner@okhdfcbank/Monthly House Rent` |
| Salary Credit | 60 | `ACH/CREDIT/TCS LIMITED/SALARY CREDIT JUNE 2025`<br>`NEFT/CMS/INFOSYS LTD/SALARY FOR MAY 2025/CMS0019283` |
| Self-Transfer | 60 | `TRANSFER TO OWN ACCOUNT 501009876543 HDFC`<br>`TRANSFER FROM SAVINGS A/C TO ZERO BALANCE 9876` |
| Shopping | 60 | `UPI/DR/123498765432/amazonpay@icici/Amazon Seller Retail`<br>`ECOM PUR/AMAZON PAY INDIA/SEATTLE/02-05-2025` |
| Subscriptions | 60 | `UPI/DR/778899001122/netflix@citibank/Monthly Sub`<br>`ECOM/NETFLIX.COM/MONTHLY SUBSCRIPTION/MUMBAI` |
| Transport | 60 | `UPI/412891283912/Uber India/uber@axis/Payment`<br>`UPI/DR/304958671203/ola@axisbank/Ola Cabs Ride Fare` |
| Utilities | 60 | `UPI/DR/223344556677/tatapower@billdesk/Electricity Bill`<br>`UPI/DR/445566778899/bescom@billdesk/Bescom Bangalore Power` |

## Reproduction

Regenerate the dataset at any time:

```bash
uv run python data/categorization/generate_labeled_dataset.py
```
