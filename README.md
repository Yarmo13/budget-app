# Personal Budget Tracker

A comprehensive web-based budgeting application that helps you track expenses, learn spending patterns, and manage your budget effectively.

## Features

### Core Functionality
- **Daily Expense Tracking**: Quick and easy expense logging with categories and descriptions
- **30-Day Learning Period**: Automatically tracks spending patterns for the first month
- **Smart Budget Suggestions**: AI-powered budget recommendations based on your actual spending
- **Real-time Budget Monitoring**: Visual progress bars and alerts for budget limits
- **Interactive Visualizations**: Charts and graphs showing spending trends and patterns

### Key Capabilities
- Track expenses across 10 predefined categories (Groceries, Dining Out, Transportation, etc.)
- View spending history with date range filters
- Automatic spending analysis and insights after 30-day learning period
- Customizable monthly budgets per category
- Color-coded budget status (safe, warning, exceeded)
- Mobile-responsive design for on-the-go tracking

## Technology Stack

- **Backend**: Python Flask
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Charts**: Chart.js for data visualization

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Setup Instructions

1. **Navigate to the project directory**:
   ```bash
   cd budget-app
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python3 -m venv venv
   ```

3. **Activate the virtual environment**:
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the application**:
   ```bash
   python app.py
   ```

6. **Access the application**:
   Open your web browser and go to: `http://localhost:5000`

## Usage Guide

### First-Time Setup

1. **Learning Period (Days 1-30)**:
   - Add your daily expenses without worrying about budgets
   - The app tracks all spending to establish baseline patterns
   - A banner shows how many days remain in the learning period

2. **After 30 Days**:
   - Navigate to the "Budget Setup" tab
   - Review the spending analysis and insights
   - Click "Use Suggested Budget" or manually set your own limits
   - Save your budget

### Daily Use

**Adding an Expense** (takes less than 30 seconds):
1. Go to "Daily Expenses" tab
2. Select date (defaults to today)
3. Choose category from dropdown
4. Enter amount
5. Add optional description
6. Click "Add Expense"

**Viewing Dashboard**:
- See total budget, spent, and remaining amounts
- Monitor each category's progress with visual bars
- Color indicators: Green (safe), Orange (warning at 80%), Red (exceeded)

**Analyzing Trends**:
- Visit "Visualizations" tab
- View monthly spending trends over time
- See category breakdowns with pie charts
- Compare budget vs. actual spending

## File Structure

```
budget-app/
├── app.py                  # Flask application and API routes
├── database.py             # Database models and configuration
├── requirements.txt        # Python dependencies
├── budget.db              # SQLite database (created on first run)
├── static/
│   ├── css/
│   │   └── style.css      # Application styling
│   └── js/
│       └── app.js         # Frontend JavaScript logic
└── templates/
    └── index.html         # Main HTML template
```

## Database Schema

### Tables

**expenses**:
- `id`: Primary key
- `date`: Expense date
- `category`: Expense category
- `amount`: Dollar amount
- `description`: Optional description
- `created_at`: Timestamp

**budgets**:
- `id`: Primary key
- `category`: Category name (unique)
- `monthly_limit`: Budget limit
- `created_at`: Created timestamp
- `updated_at`: Last updated timestamp

**settings**:
- `id`: Primary key
- `key`: Setting key (e.g., 'start_date')
- `value`: Setting value
- `created_at`: Created timestamp
- `updated_at`: Last updated timestamp

## API Endpoints

- `GET /` - Main application page
- `GET/POST /api/expenses` - List/create expenses
- `DELETE /api/expenses/<id>` - Delete expense
- `GET /api/learning-period/status` - Check learning period status
- `GET /api/learning-period/analysis` - Get spending analysis
- `GET/POST /api/budgets` - Get/set budgets
- `GET /api/dashboard` - Dashboard data
- `GET /api/visualizations/monthly-trends` - Monthly trends data
- `GET /api/visualizations/category-breakdown` - Category breakdown
- `GET /api/visualizations/budget-vs-actual` - Budget comparison

## Tips for Best Results

1. **Log expenses daily** for accurate tracking
2. **Be consistent** with category selection
3. **Complete the full 30-day learning period** before setting budgets
4. **Review insights** to identify spending patterns
5. **Adjust budgets** as needed based on real spending habits
6. **Use descriptions** to remember what expenses were for

## Troubleshooting

**Database errors**:
- Delete `budget.db` and restart the app to reset the database

**Port already in use**:
- Change the port in `app.py`: `app.run(debug=True, port=5001)`

**Charts not displaying**:
- Ensure you have an internet connection (Chart.js loads from CDN)
- Check browser console for JavaScript errors

## Future Enhancements

Potential features for future versions:
- Income tracking
- Recurring expense automation
- Export to CSV/PDF
- Multi-user support
- Savings goals
- Bill reminders
- Receipt photo uploads

## License

This project is provided as-is for personal use.

## Support

For issues or questions, please refer to the code comments or modify the application to suit your needs.
