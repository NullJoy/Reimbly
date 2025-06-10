"""
Dashboard routes for FastAPI
"""

from fastapi import APIRouter, WebSocket, HTTPException, Query
from fastapi.responses import HTMLResponse, FileResponse
from typing import Optional, Literal
from datetime import datetime
from .agent import dashboard_agent
from .websocket import websocket_manager
from pathlib import Path

router = APIRouter()

@router.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard(
    theme: Literal["light", "dark", "corporate"] = "light",
    layout: Literal["grid", "list", "compact"] = "grid",
    show_pending: bool = True,
    show_approved: bool = True,
    show_rejected: bool = True,
    show_charts: bool = True,
    show_activity: bool = True,
    max_requests: int = Query(50, ge=1, le=1000),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """
    Get the dashboard HTML with customization options.
    
    Args:
        theme: Dashboard theme (light, dark, corporate)
        layout: Dashboard layout (grid, list, compact)
        show_pending: Whether to show pending requests
        show_approved: Whether to show approved requests
        show_rejected: Whether to show rejected requests
        show_charts: Whether to show charts
        show_activity: Whether to show recent activity
        max_requests: Maximum number of requests to show (1-1000)
        start_date: Start date for filtering (YYYY-MM-DD)
        end_date: End date for filtering (YYYY-MM-DD)
    """
    try:
        # Validate dates if provided
        date_range = None
        if start_date or end_date:
            if not (start_date and end_date):
                raise HTTPException(
                    status_code=400,
                    detail="Both start_date and end_date must be provided for date filtering"
                )
            try:
                datetime.strptime(start_date, '%Y-%m-%d')
                datetime.strptime(end_date, '%Y-%m-%d')
                date_range = {'start': start_date, 'end': end_date}
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid date format. Use YYYY-MM-DD"
                )
        
        return dashboard_agent.generate_dashboard_html(
            theme=theme,
            layout=layout,
            show_pending=show_pending,
            show_approved=show_approved,
            show_rejected=show_rejected,
            show_charts=show_charts,
            show_activity=show_activity,
            max_requests=max_requests,
            date_range=date_range
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard/save")
async def save_dashboard(
    output_path: Optional[str] = None,
    theme: Literal["light", "dark", "corporate"] = "light",
    layout: Literal["grid", "list", "compact"] = "grid",
    show_pending: bool = True,
    show_approved: bool = True,
    show_rejected: bool = True,
    show_charts: bool = True,
    show_activity: bool = True,
    max_requests: int = Query(50, ge=1, le=1000),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """
    Save dashboard HTML to file with customization options.
    
    Args:
        output_path: Optional custom path to save the dashboard
        theme: Dashboard theme (light, dark, corporate)
        layout: Dashboard layout (grid, list, compact)
        show_pending: Whether to show pending requests
        show_approved: Whether to show approved requests
        show_rejected: Whether to show rejected requests
        show_charts: Whether to show charts
        show_activity: Whether to show recent activity
        max_requests: Maximum number of requests to show (1-1000)
        start_date: Start date for filtering (YYYY-MM-DD)
        end_date: End date for filtering (YYYY-MM-DD)
    """
    try:
        # Validate dates if provided
        date_range = None
        if start_date or end_date:
            if not (start_date and end_date):
                raise HTTPException(
                    status_code=400,
                    detail="Both start_date and end_date must be provided for date filtering"
                )
            try:
                datetime.strptime(start_date, '%Y-%m-%d')
                datetime.strptime(end_date, '%Y-%m-%d')
                date_range = {'start': start_date, 'end': end_date}
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid date format. Use YYYY-MM-DD"
                )
        
        saved_path = dashboard_agent.save_dashboard(
            output_path=output_path,
            theme=theme,
            layout=layout,
            show_pending=show_pending,
            show_approved=show_approved,
            show_rejected=show_rejected,
            show_charts=show_charts,
            show_activity=show_activity,
            max_requests=max_requests,
            date_range=date_range
        )
        
        return {
            "status": "success",
            "message": "Dashboard saved successfully",
            "path": saved_path
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard/file")
async def get_dashboard_file():
    """
    Get the saved dashboard file.
    Returns the most recently saved dashboard HTML file.
    """
    try:
        file_path = Path("output/dashboard.html")
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Dashboard file not found")
        return FileResponse(
            file_path,
            media_type="text/html",
            filename="dashboard.html"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.websocket("/ws/dashboard")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time dashboard updates."""
    await websocket_manager.connect(websocket)
    try:
        while True:
            # Keep the connection alive
            await websocket.receive_text()
    except Exception:
        await websocket_manager.disconnect(websocket) 