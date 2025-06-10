from google.adk.agents import Agent
from typing import Dict, Any, List
from datetime import datetime, timedelta
from ...tools.database import db

def calculate_summary_stats(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate summary statistics for reimbursement data.
    
    Args:
        data (List[Dict[str, Any]]): The reimbursement data to analyze.
        
    Returns:
        Dict[str, Any]: Summary statistics including totals, averages, and distributions.
    """
    total_amount = sum(float(request["amount"]) for request in data)
    avg_amount = total_amount / len(data) if data else 0
    
    # Calculate category distribution
    category_dist = {}
    for request in data:
        category = request["category"]
        amount = float(request["amount"])
        if category not in category_dist:
            category_dist[category] = 0
        category_dist[category] += amount
    
    # Calculate organization distribution
    org_dist = {}
    for request in data:
        org = request["user_info"]["user_org"]
        amount = float(request["amount"])
        if org not in org_dist:
            org_dist[org] = 0
        org_dist[org] += amount
    
    return {
        "total_amount": total_amount,
        "average_amount": avg_amount,
        "total_requests": len(data),
        "category_distribution": category_dist,
        "organization_distribution": org_dist
    }

def generate_time_series(data: List[Dict[str, Any]], period: str = "daily") -> Dict[str, Any]:
    """Generate time series data for visualization.
    
    Args:
        data (List[Dict[str, Any]]): The reimbursement data to analyze.
        period (str): The time period for aggregation ("daily", "weekly", "monthly").
        
    Returns:
        Dict[str, Any]: Time series data for visualization.
    """
    # Group data by time period
    time_series = {}
    for request in data:
        timestamp = datetime.fromisoformat(request["timestamp"])
        if period == "daily":
            key = timestamp.date().isoformat()
        elif period == "weekly":
            # Get the start of the week (Monday)
            start_of_week = timestamp - timedelta(days=timestamp.weekday())
            key = start_of_week.date().isoformat()
        else:  # monthly
            key = timestamp.strftime("%Y-%m")
        
        if key not in time_series:
            time_series[key] = {
                "amount": 0,
                "count": 0,
                "categories": {}
            }
        
        time_series[key]["amount"] += float(request["amount"])
        time_series[key]["count"] += 1
        
        # Track category distribution
        category = request["category"]
        if category not in time_series[key]["categories"]:
            time_series[key]["categories"][category] = 0
        time_series[key]["categories"][category] += float(request["amount"])
    
    return {
        "period": period,
        "time_series": time_series
    }

def generate_report(report_params: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a reimbursement report based on specified parameters.
    
    Args:
        report_params (Dict[str, Any]): Report parameters including:
            - report_type: Type of report ("summary", "time_series", "budget")
            - filters: Optional filters for the data
            - time_period: Time period for time series reports
            
    Returns:
        Dict[str, Any]: The generated report.
    """
    report_type = report_params.get("report_type", "summary")
    filters = report_params.get("filters", {})
    time_period = report_params.get("time_period", "daily")
    
    try:
        # Build Firestore query
        query = db.db.collection('reimbursement_requests')
        
        # Apply filters
        if filters:
            if "user_id" in filters:
                query = query.where("user_info.user_id", "==", filters["user_id"])
            if "category" in filters:
                query = query.where("category", "==", filters["category"])
            if "organization" in filters:
                query = query.where("user_info.user_org", "==", filters["organization"])
            if "date_range" in filters:
                start_date = datetime.fromisoformat(filters["date_range"]["start"])
                end_date = datetime.fromisoformat(filters["date_range"]["end"])
                query = query.where("timestamp", ">=", start_date.isoformat())
                query = query.where("timestamp", "<=", end_date.isoformat())
            if "amount_range" in filters:
                query = query.where("amount", ">=", filters["amount_range"]["min"])
                query = query.where("amount", "<=", filters["amount_range"]["max"])
        
        # Execute query and get results
        results = query.stream()
        filtered_data = [doc.to_dict() for doc in results]
        
        # Generate report based on type
        if report_type == "summary":
            return {
                "status": "success",
                "report_type": "summary",
                "data": calculate_summary_stats(filtered_data)
            }
        elif report_type == "time_series":
            return {
                "status": "success",
                "report_type": "time_series",
                "data": generate_time_series(filtered_data, time_period)
            }
        elif report_type == "budget":
            # Calculate budget utilization
            summary = calculate_summary_stats(filtered_data)
            budget_limits = {
                "travel": 100000,    # $100,000 per quarter
                "meals": 50000,      # $50,000 per quarter
                "supplies": 75000,   # $75,000 per quarter
                "other": 25000       # $25,000 per quarter
            }
            
            utilization = {
                category: {
                    "used": amount,
                    "limit": budget_limits[category],
                    "percentage": (amount / budget_limits[category]) * 100
                }
                for category, amount in summary["category_distribution"].items()
            }
            
            return {
                "status": "success",
                "report_type": "budget",
                "data": {
                    "utilization": utilization,
                    "summary": summary
                }
            }
        else:
            return {
                "status": "error",
                "message": f"Unknown report type: {report_type}"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error generating report: {str(e)}"
        }

# Define the reporting agent
reporting_agent = Agent(
    name="report_generator",
    description="Agent for generating reimbursement reports and analytics",
    model="gemini-2.0-flash",
    instruction=(
        "You are a reporting agent. Your responsibilities include:\n"
        "1. Generating summary statistics\n"
        "2. Creating time series analysis\n"
        "3. Tracking budget utilization\n"
        "4. Providing filtered reports\n\n"
        "Report types:\n"
        "- Summary: Overall statistics and distributions\n"
        "- Time Series: Trend analysis over time\n"
        "- Budget: Category-wise budget utilization\n\n"
        "Filtering options:\n"
        "- By user, category, organization\n"
        "- By date range\n"
        "- By amount range"
    )
) 