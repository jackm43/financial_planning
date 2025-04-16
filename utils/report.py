import json
import argparse
from datetime import datetime, timedelta
import calendar
from collections import defaultdict
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

def load_json_file(filepath):
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {filepath}: {str(e)}")
        return None

def format_currency(value, pos):
    return f"${value:.2f}"

def get_month_date_range(year, month):
    start_date = datetime(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    end_date = datetime(year, month, last_day)
    return start_date, end_date

def filter_transactions_by_date(transactions, start_date, end_date):
    filtered = []
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')
    for tx in transactions:
        tx_date = tx.get('attributes', {}).get('settledAt', '').split('T')[0]
        if start_str <= tx_date <= end_str:
            filtered.append(tx)
    return filtered

def get_transaction_type(transaction):
    if 'transferAccount' in transaction.get('relationships', {}):
        return 'transfer'
    amount = float(transaction.get('attributes', {}).get('amount', {}).get('value', '0'))
    if amount < 0:
        return 'expense'
    else:
        return 'income'

def generate_monthly_summary(transactions, year, month):
    start_date, end_date = get_month_date_range(year, month)
    monthly_transactions = filter_transactions_by_date(transactions, start_date, end_date)
    summary = {
        'period': f"{year}-{month:02d}",
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'total_transactions': len(monthly_transactions),
        'total_income': 0,
        'total_expenses': 0,
        'net_cashflow': 0,
        'income_by_category': defaultdict(float),
        'expenses_by_category': defaultdict(float),
        'transactions_by_account': defaultdict(int),
        'volume_by_account': defaultdict(float)
    }
    for tx in monthly_transactions:
        tx_type = get_transaction_type(tx)
        amount = float(tx.get('attributes', {}).get('amount', {}).get('value', '0'))
        category = tx.get('attributes', {}).get('category', 'uncategorized')
        account_name = tx.get('accountDetails', {}).get('displayName', 'Unknown Account')
        if tx_type == 'income':
            summary['total_income'] += amount
            summary['income_by_category'][category] += amount
        elif tx_type == 'expense':
            summary['total_expenses'] += abs(amount)
            summary['expenses_by_category'][category] += abs(amount)
        summary['transactions_by_account'][account_name] += 1
        summary['volume_by_account'][account_name] += abs(amount)
    summary['net_cashflow'] = summary['total_income'] - summary['total_expenses']
    return summary

def generate_monthly_report(transactions, year, month):
    summary = generate_monthly_summary(transactions, year, month)
    print(f"\n===== Monthly Financial Report: {summary['period']} =====")
    print(f"Period: {summary['start_date']} to {summary['end_date']}")
    print(f"Total Transactions: {summary['total_transactions']}")
    print(f"Total Income: ${summary['total_income']:.2f}")
    print(f"Total Expenses: ${summary['total_expenses']:.2f}")
    print(f"Net Cash Flow: ${summary['net_cashflow']:.2f}")
    print("\nIncome by Category:")
    for category, amount in sorted(summary['income_by_category'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {category}: ${amount:.2f}")
    print("\nExpenses by Category:")
    for category, amount in sorted(summary['expenses_by_category'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {category}: ${amount:.2f}")
    print("\nTransactions by Account:")
    for account, count in sorted(summary['transactions_by_account'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {account}: {count} transactions, ${summary['volume_by_account'][account]:.2f}")
    return summary

def plot_category_breakdown(summary, chart_type='expenses'):
    if chart_type == 'expenses':
        data = summary['expenses_by_category']
        title = f"Expense Breakdown - {summary['period']}"
    else:
        data = summary['income_by_category']
        title = f"Income Breakdown - {summary['period']}"
    sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)
    if len(sorted_data) > 7:
        top_categories = sorted_data[:6]
        other_amount = sum(amount for _, amount in sorted_data[6:])
        if other_amount > 0:
            categories = [cat for cat, _ in top_categories] + ['Other']
            amounts = [amount for _, amount in top_categories] + [other_amount]
        else:
            categories = [cat for cat, _ in top_categories]
            amounts = [amount for _, amount in top_categories]
    else:
        categories = [cat for cat, _ in sorted_data]
        amounts = [amount for _, amount in sorted_data]
    plt.figure(figsize=(10, 6))
    plt.pie(amounts, labels=categories, autopct='%1.1f%%', startangle=90)
    plt.axis('equal')
    plt.title(title)
    plt.tight_layout()
    filename = f"{chart_type}_breakdown_{summary['period']}.png"
    plt.savefig(filename)
    print(f"Saved chart to {filename}")
    plt.close()

def plot_monthly_trend(summaries):
    periods = [s['period'] for s in summaries]
    incomes = [s['total_income'] for s in summaries]
    expenses = [s['total_expenses'] for s in summaries]
    net_flows = [s['net_cashflow'] for s in summaries]
    plt.figure(figsize=(12, 6))
    x = range(len(periods))
    width = 0.35
    plt.bar([i - width/2 for i in x], incomes, width, label='Income')
    plt.bar([i + width/2 for i in x], expenses, width, label='Expenses')
    plt.plot(x, net_flows, 'go-', label='Net Cash Flow')
    plt.xlabel('Month')
    plt.ylabel('Amount ($)')
    plt.title('Monthly Income vs. Expenses')
    plt.xticks(x, periods)
    plt.legend()
    plt.gca().yaxis.set_major_formatter(FuncFormatter(format_currency))
    filename = "monthly_trend.png"
    plt.savefig(filename)
    print(f"Saved trend chart to {filename}")
    plt.close()

def generate_annual_report(transactions, year):
    print(f"\n===== Annual Financial Report: {year} =====")
    monthly_summaries = []
    for month in range(1, 13):
        summary = generate_monthly_summary(transactions, year, month)
        monthly_summaries.append(summary)
        print(f"\nMonth: {month:02d}/{year}")
        print(f"  Income: ${summary['total_income']:.2f}")
        print(f"  Expenses: ${summary['total_expenses']:.2f}")
        print(f"  Net Cash Flow: ${summary['net_cashflow']:.2f}")
    annual_income = sum(s['total_income'] for s in monthly_summaries)
    annual_expenses = sum(s['total_expenses'] for s in monthly_summaries)
    annual_net = annual_income - annual_expenses
    print(f"\nAnnual Summary:")
    print(f"  Total Income: ${annual_income:.2f}")
    print(f"  Total Expenses: ${annual_expenses:.2f}")
    print(f"  Net Cash Flow: ${annual_net:.2f}")
    plot_monthly_trend(monthly_summaries)
    return monthly_summaries

def main():
    transaction_data = load_json_file('combined_transactions.json')
    if not transaction_data:
        print("Error: Could not load transaction data")
        return
    transactions = transaction_data.get('data', [])
    current_year = datetime.now().year
    current_month = datetime.now().month
    summaries = generate_annual_report(transactions, current_year)
    summary = generate_monthly_report(transactions, current_year, current_month)
    plot_category_breakdown(summary, 'expenses')
    plot_category_breakdown(summary, 'income')

if __name__ == "__main__":
    main()