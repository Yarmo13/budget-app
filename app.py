from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from sqlalchemy import func, extract
from database import get_session, User, Expense, Budget, Settings, Saving, SavingsGoal
import json
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Predefined categories
CATEGORIES = [
    'Groceries',
    'Dining Out',
    'Transportation',
    'Gas',
    'Entertainment',
    'Utilities',
    'Shopping',
    'Healthcare',
    'Housing',
    'Insurance',
    'Subscriptions',
    'Other'
]

def get_prorated_budget(user_id, year, month, monthly_budget, db_session):
    """Calculate prorated budget based on tracking start date for a specific month."""
    import calendar

    # Get tracking start date from settings
    tracking_setting = db_session.query(Settings).filter_by(
        user_id=user_id,
        key='tracking_start_date'
    ).first()

    if not tracking_setting or not tracking_setting.value:
        # No tracking start date set, return full budget
        return monthly_budget

    tracking_start = datetime.strptime(tracking_setting.value, '%Y-%m-%d').date()

    # Only prorate if tracking started in the same month/year we're calculating
    if tracking_start.year != year or tracking_start.month != month:
        # If tracking started before this month, use full budget
        if tracking_start < datetime(year, month, 1).date():
            return monthly_budget
        # If tracking starts after this month, budget is 0
        else:
            return 0

    # Calculate proration
    days_in_month = calendar.monthrange(year, month)[1]
    tracking_day = tracking_start.day
    days_tracked = days_in_month - tracking_day + 1  # +1 to include the start day

    prorated_budget = (monthly_budget / days_in_month) * days_tracked
    return round(prorated_budget, 2)

def get_current_user():
    """Get the current logged-in user."""
    if 'user_id' not in session:
        return None
    db_session = get_session()
    try:
        return db_session.query(User).filter_by(id=session['user_id']).first()
    finally:
        db_session.close()

def login_required(f):
    """Decorator to require login for routes."""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return render_template('index.html', categories=CATEGORIES)

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    db_session = get_session()
    try:
        user = db_session.query(User).filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            return jsonify({'success': True, 'username': user.username})
        return jsonify({'success': False, 'error': 'Invalid username or password'}), 401
    finally:
        db_session.close()

@app.route('/api/auth/signup', methods=['POST'])
def signup():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'success': False, 'error': 'Username and password required'}), 400

    # Only allow specific usernames and passwords
    ALLOWED_ACCOUNTS = {
        'cole': 'yarmoshuk',
        'natalie': 'pinto'
    }

    # Verify credentials match allowed accounts
    if username not in ALLOWED_ACCOUNTS or password != ALLOWED_ACCOUNTS[username]:
        return jsonify({'success': False, 'error': 'Account creation is restricted'}), 403

    db_session = get_session()
    try:
        # Check if user already exists
        existing_user = db_session.query(User).filter_by(username=username).first()
        if existing_user:
            return jsonify({'success': False, 'error': 'Account already exists. Please log in.'}), 400

        # Create the allowed user
        user = User(username=username)
        user.set_password(password)
        db_session.add(user)
        db_session.commit()

        session['user_id'] = user.id
        session['username'] = user.username
        return jsonify({'success': True, 'username': user.username})
    finally:
        db_session.close()

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/api/auth/me')
def get_current_user_info():
    if 'user_id' in session:
        return jsonify({'logged_in': True, 'username': session.get('username')})
    return jsonify({'logged_in': False})

@app.route('/api/expenses', methods=['GET', 'POST'])
@login_required
def expenses():
    user_id = session['user_id']
    db_session = get_session()
    try:
        if request.method == 'POST':
            data = request.json
            expense = Expense(
                user_id=user_id,
                date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
                category=data['category'],
                amount=float(data['amount']),
                description=data.get('description', '')
            )
            db_session.add(expense)
            db_session.commit()
            return jsonify({'success': True, 'id': expense.id})

        else:  # GET
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')

            query = db_session.query(Expense).filter_by(user_id=user_id)

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
        db_session.close()

@app.route('/api/expenses/<int:expense_id>', methods=['DELETE'])
@login_required
def delete_expense(expense_id):
    user_id = session['user_id']
    db_session = get_session()
    try:
        expense = db_session.query(Expense).filter_by(id=expense_id, user_id=user_id).first()
        if expense:
            db_session.delete(expense)
            db_session.commit()
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Expense not found'}), 404
    finally:
        db_session.close()


@app.route('/api/budgets', methods=['GET', 'POST'])
@login_required
def budgets():
    user_id = session['user_id']
    db_session = get_session()
    try:
        if request.method == 'POST':
            data = request.json

            # Delete existing budgets and create new ones
            db_session.query(Budget).filter_by(user_id=user_id).delete()

            for category, limit in data.items():
                budget = Budget(user_id=user_id, category=category, monthly_limit=float(limit))
                db_session.add(budget)

            db_session.commit()
            return jsonify({'success': True})

        else:  # GET
            budgets = db_session.query(Budget).filter_by(user_id=user_id).all()
            return jsonify({b.category: b.monthly_limit for b in budgets})
    finally:
        db_session.close()

@app.route('/api/dashboard')
@login_required
def dashboard():
    """Get dashboard data with current month spending vs budget."""
    user_id = session['user_id']
    db_session = get_session()
    try:
        # Get current month date range
        now = datetime.now()
        start_of_month = now.replace(day=1).date()
        if now.month == 12:
            end_of_month = now.replace(year=now.year + 1, month=1, day=1).date()
        else:
            end_of_month = now.replace(month=now.month + 1, day=1).date()

        # Get budgets
        budgets = db_session.query(Budget).filter_by(user_id=user_id).all()
        budget_dict = {b.category: b.monthly_limit for b in budgets}

        # Get current month expenses by category
        expenses = db_session.query(
            Expense.category,
            func.sum(Expense.amount).label('total')
        ).filter(
            Expense.user_id == user_id,
            Expense.date >= start_of_month,
            Expense.date < end_of_month
        ).group_by(Expense.category).all()

        spending_dict = {e.category: float(e.total) for e in expenses}

        # Combine budget and spending data
        dashboard_data = []
        total_budget = 0
        total_spent = 0

        for category, limit in budget_dict.items():
            # Get prorated budget for current month
            prorated_limit = get_prorated_budget(user_id, now.year, now.month, limit, db_session)

            spent = spending_dict.get(category, 0)
            percentage = (spent / prorated_limit * 100) if prorated_limit > 0 else 0

            status = 'safe'
            if percentage >= 100:
                status = 'exceeded'
            elif percentage >= 80:
                status = 'warning'

            dashboard_data.append({
                'category': category,
                'budget': prorated_limit,
                'spent': spent,
                'remaining': max(0, prorated_limit - spent),
                'percentage': round(percentage, 1),
                'status': status
            })

            total_budget += prorated_limit
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
            'total_remaining': max(0, total_budget - total_spent)
        })
    finally:
        db_session.close()

@app.route('/api/visualizations/monthly-trends')
@login_required
def monthly_trends():
    """Get monthly spending trends for the last 12 months."""
    user_id = session['user_id']
    db_session = get_session()
    try:
        # Get last 12 months
        end_date = datetime.now().date()
        start_date = end_date - relativedelta(months=12)

        # Query expenses grouped by month
        expenses = db_session.query(
            extract('year', Expense.date).label('year'),
            extract('month', Expense.date).label('month'),
            func.sum(Expense.amount).label('total')
        ).filter(
            Expense.user_id == user_id,
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
        db_session.close()

@app.route('/api/visualizations/category-breakdown')
@login_required
def category_breakdown():
    """Get category breakdown for specified period."""
    user_id = session['user_id']
    db_session = get_session()
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        query = db_session.query(
            Expense.category,
            func.sum(Expense.amount).label('total')
        ).filter(Expense.user_id == user_id)

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
        db_session.close()

@app.route('/api/visualizations/budget-vs-actual')
@login_required
def budget_vs_actual():
    """Get budget vs actual spending comparison."""
    user_id = session['user_id']
    db_session = get_session()
    try:
        # Get current month
        now = datetime.now()
        start_of_month = now.replace(day=1).date()

        # Get budgets
        budgets = db_session.query(Budget).filter_by(user_id=user_id).all()
        budget_dict = {b.category: b.monthly_limit for b in budgets}

        # Get current month spending
        expenses = db_session.query(
            Expense.category,
            func.sum(Expense.amount).label('total')
        ).filter(
            Expense.user_id == user_id,
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
        db_session.close()

@app.route('/api/savings', methods=['GET', 'POST'])
@login_required
def savings():
    user_id = session['user_id']
    db_session = get_session()
    try:
        if request.method == 'POST':
            data = request.json
            saving = Saving(
                user_id=user_id,
                date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
                amount=float(data['amount']),
                description=data.get('description', '')
            )
            db_session.add(saving)
            db_session.commit()
            return jsonify({'success': True, 'id': saving.id})

        else:  # GET
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')

            query = db_session.query(Saving).filter_by(user_id=user_id)

            if start_date:
                query = query.filter(Saving.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
            if end_date:
                query = query.filter(Saving.date <= datetime.strptime(end_date, '%Y-%m-%d').date())

            savings = query.order_by(Saving.date.desc()).all()

            return jsonify([{
                'id': s.id,
                'date': s.date.strftime('%Y-%m-%d'),
                'amount': s.amount,
                'description': s.description
            } for s in savings])
    finally:
        db_session.close()

@app.route('/api/savings/<int:saving_id>', methods=['DELETE'])
@login_required
def delete_saving(saving_id):
    user_id = session['user_id']
    db_session = get_session()
    try:
        saving = db_session.query(Saving).filter_by(id=saving_id, user_id=user_id).first()
        if saving:
            db_session.delete(saving)
            db_session.commit()
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Saving not found'}), 404
    finally:
        db_session.close()

@app.route('/api/savings-goals', methods=['GET', 'POST'])
@login_required
def savings_goals():
    user_id = session['user_id']
    db_session = get_session()
    try:
        if request.method == 'POST':
            data = request.json
            goal = SavingsGoal(
                user_id=user_id,
                name=data['name'],
                target_amount=float(data['target_amount']),
                current_amount=0
            )
            db_session.add(goal)
            db_session.commit()
            return jsonify({'success': True, 'id': goal.id})

        else:  # GET
            # Get archived parameter
            show_archived = request.args.get('archived', 'false').lower() == 'true'

            goals = db_session.query(SavingsGoal).filter_by(
                user_id=user_id,
                is_archived=show_archived
            ).order_by(SavingsGoal.created_at.desc()).all()

            return jsonify([{
                'id': g.id,
                'name': g.name,
                'target_amount': g.target_amount,
                'current_amount': g.current_amount,
                'progress_percentage': round((g.current_amount / g.target_amount * 100) if g.target_amount > 0 else 0, 1),
                'is_archived': g.is_archived,
                'created_at': g.created_at.isoformat() if g.created_at else None,
                'completed_at': g.completed_at.isoformat() if g.completed_at else None
            } for g in goals])
    finally:
        db_session.close()

@app.route('/api/savings-goals/<int:goal_id>/add', methods=['POST'])
@login_required
def add_to_goal(goal_id):
    user_id = session['user_id']
    db_session = get_session()
    try:
        data = request.json
        goal = db_session.query(SavingsGoal).filter_by(id=goal_id, user_id=user_id).first()

        if not goal:
            return jsonify({'success': False, 'error': 'Goal not found'}), 404

        amount = float(data['amount'])
        goal.current_amount += amount

        # Check if goal is completed
        if goal.current_amount >= goal.target_amount and not goal.completed_at:
            goal.completed_at = datetime.utcnow()

        db_session.commit()
        return jsonify({'success': True, 'new_amount': goal.current_amount})
    finally:
        db_session.close()

@app.route('/api/savings-goals/<int:goal_id>/archive', methods=['POST'])
@login_required
def archive_goal(goal_id):
    user_id = session['user_id']
    db_session = get_session()
    try:
        goal = db_session.query(SavingsGoal).filter_by(id=goal_id, user_id=user_id).first()

        if not goal:
            return jsonify({'success': False, 'error': 'Goal not found'}), 404

        goal.is_archived = True
        if not goal.completed_at:
            goal.completed_at = datetime.utcnow()

        db_session.commit()
        return jsonify({'success': True})
    finally:
        db_session.close()

@app.route('/api/savings-goals/<int:goal_id>', methods=['DELETE'])
@login_required
def delete_goal(goal_id):
    user_id = session['user_id']
    db_session = get_session()
    try:
        goal = db_session.query(SavingsGoal).filter_by(id=goal_id, user_id=user_id).first()
        if goal:
            db_session.delete(goal)
            db_session.commit()
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Goal not found'}), 404
    finally:
        db_session.close()

@app.route('/api/settings/tracking-start-date', methods=['GET', 'POST'])
@login_required
def tracking_start_date():
    """Get or set the tracking start date."""
    user_id = session['user_id']
    db_session = get_session()
    try:
        if request.method == 'POST':
            data = request.json
            start_date = data.get('start_date')

            if not start_date:
                return jsonify({'success': False, 'error': 'Start date is required'}), 400

            # Validate date format
            try:
                datetime.strptime(start_date, '%Y-%m-%d')
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid date format'}), 400

            # Check if setting exists
            setting = db_session.query(Settings).filter_by(
                user_id=user_id,
                key='tracking_start_date'
            ).first()

            if setting:
                setting.value = start_date
                setting.updated_at = datetime.utcnow()
            else:
                setting = Settings(
                    user_id=user_id,
                    key='tracking_start_date',
                    value=start_date
                )
                db_session.add(setting)

            db_session.commit()
            return jsonify({'success': True, 'start_date': start_date})

        else:  # GET
            setting = db_session.query(Settings).filter_by(
                user_id=user_id,
                key='tracking_start_date'
            ).first()

            if setting:
                return jsonify({'start_date': setting.value})
            else:
                return jsonify({'start_date': None})
    finally:
        db_session.close()

@app.route('/api/reports/monthly/<year_month>')
@login_required
def monthly_report(year_month):
    """Get detailed monthly report for a specific month (format: YYYY-MM)."""
    user_id = session['user_id']
    db_session = get_session()
    try:
        # Parse year and month
        year, month = map(int, year_month.split('-'))
        start_date = datetime(year, month, 1).date()
        if month == 12:
            end_date = datetime(year + 1, 1, 1).date()
        else:
            end_date = datetime(year, month + 1, 1).date()

        # Get budgets
        budgets = db_session.query(Budget).filter_by(user_id=user_id).all()
        budget_dict = {b.category: b.monthly_limit for b in budgets}

        # Get expenses for the month
        expenses = db_session.query(
            Expense.category,
            func.sum(Expense.amount).label('total'),
            func.count(Expense.id).label('count')
        ).filter(
            Expense.user_id == user_id,
            Expense.date >= start_date,
            Expense.date < end_date
        ).group_by(Expense.category).all()

        spending_dict = {e.category: {'total': float(e.total), 'count': e.count} for e in expenses}

        # Get savings for the month
        savings = db_session.query(
            func.sum(Saving.amount).label('total')
        ).filter(
            Saving.user_id == user_id,
            Saving.date >= start_date,
            Saving.date < end_date
        ).first()

        total_saved = float(savings.total) if savings.total else 0

        # Build category details
        categories = []
        total_spent = 0
        total_budget = 0

        for category in set(list(budget_dict.keys()) + list(spending_dict.keys())):
            budget = budget_dict.get(category, 0)
            # Get prorated budget for the specified month
            prorated_budget = get_prorated_budget(user_id, year, month, budget, db_session)

            spent_data = spending_dict.get(category, {'total': 0, 'count': 0})
            spent = spent_data['total']
            count = spent_data['count']

            difference = prorated_budget - spent
            percentage = (spent / prorated_budget * 100) if prorated_budget > 0 else 0

            status = 'under'
            if prorated_budget == 0:
                status = 'no_budget'
            elif spent > prorated_budget:
                status = 'over'
            elif percentage >= 80:
                status = 'warning'

            categories.append({
                'category': category,
                'budget': prorated_budget,
                'spent': spent,
                'difference': difference,
                'percentage': round(percentage, 1),
                'transaction_count': count,
                'status': status
            })

            total_spent += spent
            total_budget += prorated_budget

        return jsonify({
            'month': year_month,
            'total_budget': total_budget,
            'total_spent': total_spent,
            'total_saved': total_saved,
            'total_difference': total_budget - total_spent,
            'categories': sorted(categories, key=lambda x: x['spent'], reverse=True)
        })
    finally:
        db_session.close()

@app.route('/api/reports/available-months')
@login_required
def available_months():
    """Get list of months that have expense data."""
    user_id = session['user_id']
    db_session = get_session()
    try:
        months = db_session.query(
            extract('year', Expense.date).label('year'),
            extract('month', Expense.date).label('month')
        ).filter(
            Expense.user_id == user_id
        ).distinct().order_by('year', 'month').all()

        return jsonify([
            f"{int(m.year)}-{int(m.month):02d}"
            for m in months
        ])
    finally:
        db_session.close()

if __name__ == '__main__':
    import os
    # Ensure required accounts exist on startup
    from init_accounts import ensure_accounts_exist
    ensure_accounts_exist()

    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
