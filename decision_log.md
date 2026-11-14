# Decision Log – T117-PS-043

## 1. Programming Language
Decision: Python was selected for implementation.
Reason: Python supports data processing, CSV handling, date and time operations, and object-oriented programming.

## 2. Data Models
Decision: Dataclasses represent Station, SmartCard, Journey, MetroEvent, and Transaction.
Reason: Dataclasses provide a clear structure for project data.

## 3. Fare Calculation
Decision: Decimal is used for monetary calculations.
Reason: It avoids common floating-point precision issues.

## 4. Zone-Based Pricing
Decision: The number of zones crossed is calculated using the absolute difference between entry and exit zones.
Reason: This provides the basis for distance-based fares.

## 5. Fare Adjustments
Decision: The fare engine applies card-type discounts, smart-card discounts, peak or off-peak adjustments, and a city supplement.
Reason: Separating fare logic makes it easier to maintain and test.

## 6. Peak-Hour Rules
Decision: Peak hours are 8:00–10:00 AM and 5:00–8:00 PM, excluding Sundays and configured holidays.
Reason: This allows fares to vary according to travel time.

## 7. Journey Penalties
Decision: A ₹50 penalty applies when a journey exceeds 90 minutes for distances up to two zones, or 120 minutes for longer distances.
Reason: This provides a time-based overstay penalty.

## 8. Daily Spending Cap
Decision: A ₹150 daily fare cap is applied to STANDARD cards.
Reason: This limits daily fare deductions for standard card users.

## 9. Tourist Passes
Decision: Tourist passes support 1-day and 3-day validity periods.
Reason: This provides time-limited travel options.

## 10. Automatic Reload
Decision: Automatic reload adds ₹500 when an eligible card balance falls below ₹100. A ₹5 fee is charged, with a maximum of two reloads per day.
Reason: This helps maintain sufficient card balance.

## 11. CSV Data Storage
Decision: CSV files are used for input data and generated reports.
Reason: CSV files are simple to inspect and work with spreadsheet applications.

## 12. Testing
Decision: Pytest is used for automated testing.
Reason: Automated tests verify module behavior.

## 13. Project Structure
Decision: The project is divided into modules for models, fare calculations, event processing, card services, data loading, and report generation.
Reason: Modular organization improves readability, maintainability, and testing.

---
Note: These decisions describe the implemented project design and are not a substitute for the official problem statement.
