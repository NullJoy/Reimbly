"""Constants used across the Reimbly application."""

# Case Status Constants
CASE_STATUS = {
    'SUBMITTED': 'submitted',
    'PENDING_APPROVAL': 'pending_approval',
    'APPROVED': 'approved',
    'REJECTED': 'rejected'
}

# Case Categories
CASE_CATEGORIES = {
    'TRAVEL': 'travel',
    'MEALS': 'meals',
    'SUPPLIES': 'supplies',
    'OTHER': 'other'
}

# Amount Thresholds
AMOUNT_THRESHOLDS = {
    'LOW': 1000,
    'MEDIUM': 5000,
    'HIGH': 10000
}

# Required Documentation by Category
REQUIRED_DOCUMENTATION = {
    'travel': ['receipt', 'itinerary'],
    'meals': ['receipt'],
    'supplies': ['receipt', 'invoice'],
    'other': ['receipt', 'justification']
}

# Category Amount Limits
CATEGORY_LIMITS = {
    'travel': 10000,    # $10,000 per trip
    'meals': 100,       # $100 per meal
    'supplies': 1000,   # $1,000 per order
    'other': 5000       # $5,000 per request
} 