from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from sqlalchemy import func, extract
from database import get_session, Expense, Budget, Settings
import json

app = Flask(__name__)

# Predefined categories
CATEGORIES = [
    'Groceries',
    'Dining Out',
    'Transportation',
    'Entertainment',
    'Utilities',
    'Shopping',
    'Healthcare',
    'Housing',
    'Insurance',
    'Other'
]

def get_or_create_start_date():
    """Get or create the start date for the learning period."""
    session = get_session()
    try:
        setting = session.query(Settings).filter_by(key='start_date').first()
        if not setting:
            setting = Settings(key='start_date', value=datetime.now().strftime('%Y-%m-%d'))
            session.add(setting)
            session.commit()
        return datetime.strptime(setting.value, '%Y-%m-%d').date()
    finally:
        session.close()

def is_learning_period_complete():
    """Check if 30-day learning period is complete."""
    start_date = get_or_create_start_date()
    days_elapsed = (datetime.now().date() - start_date).days
    return days_elapsed >= 30

def get_learning_period_days():
    """Get number of days elapsed in learning period."""
    start_date = get_or_create_start_date()
    days_elapsed = (datetime.now().date() - start_date).days
    return min(days_elapsed, 30)

@app.route('/')
def index():
    return render_template('index.html', categories=CATEGORIES)

@app.route('/api/expenses', methods=['GET', 'POST'])
def expenses():
    session = get_session()
    try:
        if request.method == 'POST':
            data = request.json
            expense = Expense(
                date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
                category=data['category'],
                amount=float(data['amount']),
                description=data.get('description', '')
            )
            session.add(expense)
            session.commit()
            return jsonify({'success': True, 'id': expense.id})

        else:  # GET
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')

            query = session.query(Expense)

            if start_date:
                query = query.filter(Expense.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
            if end_date:
                query = query.filter(Expense.date <= datetime.strptime(end_date, '%Y-%m-%d').date())

            expenses = query.order_by(Expense.date.desc()).all()

            return jsonify([{
                'id': e.id,
                'date': e.date.strftime('%Y-%m-%d'),
                'category': e.category,
                'amount': e.amount,
                'description': e.description
            } for e in expenses])
    finally:
        session.close()

@app.route('/api/expenses/<int:expense_id>', methods=['DELETE'])
def delete_expense(expense_id):
    session = get_session()
    try:
        expense = session.query(Expense).filter_by(id=expense_id).first()
        if expense:
            session.delete(expense)
            session.commit()
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Expense not found'}), 404
    finally:
        session.close()

@app.route('/api/learning-period/status')
def learning_period_status():
    """Get learning period status."""
    start_date = get_or_create_start_date()
    days_elapsed = get_learning_period_days()
    is_complete = is_learning_period_complete()

    return jsonify({
        'start_date': start_date.strftime('%Y-%m-%d'),
        'days_elapsed': days_elapsed,
        'days_remaining': max(0, 30 - days_elapsed),
        'is_complete': is_complete
    })

@app.route('/api/learning-period/analysis')
def learning_period_analysis():
    """Analyze spending patterns from learning period."""
    session = get_session()
    try:
        start_date = get_or_create_start_date()
        end_date = start_date + timedelta(days=30)

        # Get expenses from learning period
        expenses = session.query(Expense).filter(
            Expense.date >= start_date,
            Expense.date < end_date
        ).all()

        # Calculate totals by category
        category_totals = {}
        for expense in expenses:
            if expense.category not in category_totals:
                category_totals[expense.category] = 0
            category_totals[expense.category] += expense.amount

        # Calculate suggested budgets (using actual spending)
        suggested_budgets = {}
        for category, total in category_totals.items():
            suggested_budgets[category] = round(total, 2)

        total_spending = sum(category_totals.values())

        return jsonify({
            'total_spending': round(total_spending, 2),
            'category_totals': category_totals,
            'suggested_budgets': suggested_budgets,
            'insights': generate_insights(category_totals, total_spending)
        })
    finally:
        session.close()

def generate_insights(category_totals, total_spending):
    """Generate spending insights."""
    insights = []

    if not category_totals:
        return ['No spending data available yet.']

    # Find highest spending category
    max_category = max(category_totals, key=category_totals.get)
    max_amount = category_totals[max_category]
    max_percentage = (max_amount / total_spending * 100) if total_spending > 0 else 0

    insights.append(f"Your highest spending category is {max_category} (${max_amount:.2f}, {max_percentage:.1f}% of total)")

    # Daily average
    daily_avg = total_spending / 30
    insights.append(f"Your average daily spending is ${daily_avg:.2f}")

    # Monthly projection
    monthly_projection = total_spending
    insights.append(f"Your monthly spending is ${monthly_projection:.2f}")

    return insights

@app.route('/api/budgets', methods=['GET', 'POST'])
def budgets():
    session = get_session()
    try:
        if request.method == 'POST':
            data = request.json

            # Delete existing budgets and create new ones
            session.query(Budget).delete()

            for category, limit in data.items():
                budget = Budget(category=category, monthly_limit=float(limit))
                session.add(budget)

            session.commit()
            return jsonify({'success': True})

        else:  # GET
            budgets = session.query(Budget).all()
            return jsonify({b.category: b.monthly_limit for b in budgets})
    finally:
        session.close()

@app.route('/api/dashboard')
def dashboard():
    """Get dashboard data with current month spending vs budget."""
    session = get_session()
    try:
        # Get current month date range
        now = datetime.now()
        start_of_month = now.replace(day=1).date()
        if now.month == 12:
            end_of_month = now.replace(year=now.year + 1, month=1, day=1).date()
        else:
            end_of_month = now.replace(month=now.month + 1, day=1).date()

        # Get budgets
        budgets = session.query(Budget).all()
        budget_dict = {b.category: b.monthly_limit for b in budgets}

        # Get current month expenses by category
        expenses = session.query(
            Expense.category,
            func.sum(Expense.amount).label('total')
        ).filter(
            Expense.date >= start_of_month,
            Expense.date < end_of_month
        ).group_by(Expense.category).all()

        spending_dict = {e.category: float(e.total) for e in expenses}

        # Combine budget and spending data
        dashboard_data = []
        total_budget = 0
        total_spent = 0

        for category, limit in budget_dict.items():
            spent = spending_dict.get(category, 0)
            percentage = (spent / limit * 100) if limit > 0 else 0

            status = 'safe'
            if percentage >= 100:
                status = 'exceeded'
            elif percentage >= 80:
                status = 'warning'

            dashboard_data.append({
                'category': category,
                'budget': limit,
                'spent': spent,
                'remaining': max(0, limit - spent),
                'percentage': round(percentage, 1),
                'status': status
            })

            total_budget += limit
            total_spent += spent

        # Add categories with spending but no budget
        for category, spent in spending_dict.items():
            if category not in budget_dict:
                dashboard_data.append({
                    'category': category,
                    'budget': 0,
                    'spent': spent,
                    'remaining': 0,
                    'percentage': 0,
                    'status': 'no_budget'
                })
                total_spent += spent

        return jsonify({
            'categories': dashboard_data,
            'total_budget': total_budget,
            'total_spent': total_spent,
            'total_remaining': max(0, total_budget - total_spent),
            'is_learning_period': not is_learning_period_complete()
        })
    finally:
        session.close()

@app.route('/api/visualizations/monthly-trends')
def monthly_trends():
    """Get monthly spending trends for the last 12 months."""
    session = get_session()
    try:
        # Get last 12 months
        end_date = datetime.now().date()
        start_date = end_date - relativedelta(months=12)

        # Query expenses grouped by month
        expenses = session.query(
            extract('year', Expense.date).label('year'),
            extract('month', Expense.date).label('month'),
            func.sum(Expense.amount).label('total')
        ).filter(
            Expense.date >= start_date
        ).group_by('year', 'month').order_by('year', 'month').all()

        # Format data
        monthly_data = []
        for exp in expenses:
            month_str = f"{int(exp.year)}-{int(exp.month):02d}"
            monthly_data.append({
                'month': month_str,
                'total': float(exp.total)
            })

        return jsonify(monthly_data)
    finally:
        session.close()

@app.route('/api/visualizations/category-breakdown')
def category_breakdown():
    """Get category breakdown for specified period."""
    session = get_session()
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        query = session.query(
            Expense.category,
            func.sum(Expense.amount).label('total')
        )

        if start_date:
            query = query.filter(Expense.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
        if end_date:
            query = query.filter(Expense.date <= datetime.strptime(end_date, '%Y-%m-%d').date())

        expenses = query.group_by(Expense.category).all()

        return jsonify([{
            'category': e.category,
            'total': float(e.total)
        } for e in expenses])
    finally:
        session.close()

@app.route('/api/visualizations/budget-vs-actual')
def budget_vs_actual():
    """Get budget vs actual spending comparison."""
    session = get_session()
    try:
        # Get current month
        now = datetime.now()
        start_of_month = now.replace(day=1).date()

        # Get budgets
        budgets = session.query(Budget).all()
        budget_dict = {b.category: b.monthly_limit for b in budgets}

        # Get current month spending
        expenses = session.query(
            Expense.category,
            func.sum(Expense.amount).label('total')
        ).filter(
            Expense.date >= start_of_month
        ).group_by(Expense.category).all()

        spending_dict = {e.category: float(e.total) for e in expenses}

        # Combine data
        comparison = []
        for category in set(list(budget_dict.keys()) + list(spending_dict.keys())):
            comparison.append({
                'category': category,
                'budget': budget_dict.get(category, 0),
                'actual': spending_dict.get(category, 0)
            })

        return jsonify(comparison)
    finally:
        session.close()

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
