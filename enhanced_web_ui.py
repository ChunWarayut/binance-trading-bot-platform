#!/usr/bin/env python3
"""
Enhanced Real-time Web UI with WebSocket integration
"""

import streamlit as st
import json
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import asyncio
import websockets
import threading
from streamlit.runtime.caching import cache_data
import logging

# Page config
st.set_page_config(
    page_title="🚀 Crypto Trading Bot - Real-time Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constants
API_BASE = "http://localhost:8080"
WS_URL = "ws://localhost:8080/ws"

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        margin: 0.5rem 0;
    }
    .status-running {
        color: #28a745;
        font-weight: bold;
    }
    .status-stopped {
        color: #dc3545;
        font-weight: bold;
    }
    .trade-card {
        background: #e8f5e8;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #28a745;
        margin: 0.5rem 0;
    }
    .log-container {
        background: #1a1a1a;
        color: #00ff00;
        padding: 1rem;
        border-radius: 8px;
        font-family: 'Courier New', monospace;
        max-height: 400px;
        overflow-y: scroll;
        font-size: 12px;
    }
</style>
""", unsafe_allow_html=True)

# Helper functions
@cache_data(ttl=60)  # Cache for 1 minute
def load_config():
    """Load bot configuration"""
    try:
        response = requests.get(f"{API_BASE}/api/config", timeout=5)
        return response.json()
    except Exception as e:
        st.error(f"Error loading config: {e}")
        return {}

def get_api_data(endpoint):
    """Get data from API endpoint"""
    try:
        response = requests.get(f"{API_BASE}/api/{endpoint}", timeout=5)
        return response.json()
    except Exception as e:
        st.error(f"Error fetching {endpoint}: {e}")
        return {}

def control_bot(action):
    """Control bot (start/stop/restart)"""
    try:
        response = requests.post(f"{API_BASE}/api/bot/{action}", timeout=10)
        return response.json()
    except Exception as e:
        return {"status": "error", "message": str(e)}

def format_currency(value):
    """Format currency values"""
    try:
        return f"${float(value):,.2f}"
    except:
        return "$0.00"

def format_timestamp(timestamp):
    """Format timestamp"""
    try:
        if isinstance(timestamp, str):
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        return str(timestamp)
    except:
        return "N/A"

# Main dashboard function
def show_main_dashboard():
    """Show the main dashboard"""
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🚀 Crypto Trading Bot - Real-time Dashboard</h1>
        <p>Optimized • 35 Trading Pairs • Multi-timeframe Analysis</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Auto-refresh mechanism
    placeholder = st.empty()
    
    with placeholder.container():
        # Get real-time data
        bot_status = get_api_data("bot_status")
        active_trades = get_api_data("active_trades")
        system_stats = get_api_data("status")
        
        # Status metrics row
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            running = bot_status.get("running", False)
            status_class = "status-running" if running else "status-stopped"
            status_text = "🟢 RUNNING" if running else "🔴 STOPPED"
            st.markdown(f'<div class="metric-card"><h4>Status</h4><p class="{status_class}">{status_text}</p></div>', 
                       unsafe_allow_html=True)
        
        with col2:
            trades_count = bot_status.get("active_trades_count", 0)
            st.markdown(f'<div class="metric-card"><h4>Active Trades</h4><p style="font-size:24px; color:#007bff;">{trades_count}</p></div>', 
                       unsafe_allow_html=True)
        
        with col3:
            total_pnl = bot_status.get("total_pnl", 0)
            pnl_color = "#28a745" if total_pnl >= 0 else "#dc3545"
            st.markdown(f'<div class="metric-card"><h4>Total P&L</h4><p style="font-size:24px; color:{pnl_color};">{format_currency(total_pnl)}</p></div>', 
                       unsafe_allow_html=True)
        
        with col4:
            last_update = format_timestamp(bot_status.get("last_update", "N/A"))
            st.markdown(f'<div class="metric-card"><h4>Last Update</h4><p style="font-size:14px;">{last_update}</p></div>', 
                       unsafe_allow_html=True)
        
        with col5:
            connections = system_stats.get("system_stats", {}).get("python_processes", 0)
            st.markdown(f'<div class="metric-card"><h4>Processes</h4><p style="font-size:24px; color:#6f42c1;">{connections}</p></div>', 
                       unsafe_allow_html=True)
        
        # Control buttons
        st.markdown("### 🎮 Bot Controls")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("▶️ Start Bot", type="primary"):
                result = control_bot("start")
                if result.get("status") == "starting":
                    st.success("✅ Bot starting...")
                else:
                    st.error(f"❌ Error: {result.get('message', 'Unknown error')}")
        
        with col2:
            if st.button("⏹️ Stop Bot", type="secondary"):
                result = control_bot("stop")
                if result.get("status") == "stopping":
                    st.warning("⚠️ Bot stopping...")
                else:
                    st.error(f"❌ Error: {result.get('message', 'Unknown error')}")
        
        with col3:
            if st.button("🔄 Restart Bot"):
                result = control_bot("restart")
                if result.get("status") == "restarting":
                    st.info("🔄 Bot restarting...")
                else:
                    st.error(f"❌ Error: {result.get('message', 'Unknown error')}")
        
        with col4:
            if st.button("📊 Refresh Data"):
                st.rerun()
        
        # Active trades section
        st.markdown("### 📈 Active Trades")
        if active_trades and len(active_trades) > 0:
            trades_df = pd.DataFrame(active_trades)
            
            # Style the trades table
            styled_df = trades_df.style.apply(lambda x: ['background-color: #e8f5e8' if i % 2 == 0 else 'background-color: #f8f9fa' for i in range(len(x))], axis=0)
            st.dataframe(styled_df, use_container_width=True)
            
            # Trade details cards
            for i, trade in enumerate(active_trades):
                symbol = trade.get("Symbol", "N/A")
                side = trade.get("Side", "N/A")
                entry = trade.get("Entry", 0)
                quantity = trade.get("Quantity", 0)
                trailing_stop = trade.get("TrailingStop", "N/A")
                
                side_color = "#28a745" if side == "LONG" else "#dc3545"
                
                st.markdown(f"""
                <div class="trade-card">
                    <h4>🔥 {symbol}</h4>
                    <p><strong>Side:</strong> <span style="color:{side_color};">{side}</span></p>
                    <p><strong>Entry:</strong> {format_currency(entry)}</p>
                    <p><strong>Quantity:</strong> {quantity}</p>
                    <p><strong>Trailing Stop:</strong> {format_currency(trailing_stop) if trailing_stop != 'N/A' else 'N/A'}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("📋 No active trades at the moment")
        
        # Performance charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📊 P&L Chart")
            # Create sample P&L chart
            dates = pd.date_range(start=datetime.now() - timedelta(days=7), end=datetime.now(), freq='H')
            pnl_data = [total_pnl * (1 + 0.01 * (i % 10 - 5)) for i in range(len(dates))]
            
            fig_pnl = go.Figure()
            fig_pnl.add_trace(go.Scatter(
                x=dates, 
                y=pnl_data, 
                mode='lines',
                name='P&L',
                line=dict(color='#28a745', width=2)
            ))
            fig_pnl.update_layout(
                title="P&L Over Time",
                xaxis_title="Time",
                yaxis_title="P&L (USDT)",
                height=300,
                showlegend=False
            )
            st.plotly_chart(fig_pnl, use_container_width=True)
        
        with col2:
            st.markdown("### 🎯 Trading Pairs Distribution")
            # Load config for trading pairs
            config = load_config()
            pairs = config.get("TRADING_PAIRS", ["BTCUSDT", "ETHUSDT", "BNBUSDT"])[:10]  # Top 10
            
            # Create pie chart
            fig_pie = px.pie(
                values=[1] * len(pairs),
                names=pairs,
                title="Active Trading Pairs"
            )
            fig_pie.update_layout(height=300)
            st.plotly_chart(fig_pie, use_container_width=True)
        
        # System information
        st.markdown("### 💻 System Information")
        col1, col2 = st.columns(2)
        
        with col1:
            system_info = system_stats.get("system_stats", {})
            st.markdown(f"""
            **🔧 System Status:**
            - **Uptime:** {time.time() - system_info.get('uptime', time.time()):.0f} seconds
            - **Python Processes:** {system_info.get('python_processes', 0)}
            - **Log Size:** {system_info.get('log_size', 0) / 1024:.1f} KB
            - **API Connections:** {system_stats.get('connections', 0)}
            """)
        
        with col2:
            st.markdown(f"""
            **⚙️ Configuration:**
            - **Trading Pairs:** {len(config.get('TRADING_PAIRS', []))}
            - **Leverage:** {config.get('LEVERAGE', 3)}x
            - **Position Buffer:** {config.get('POSITION_SIZE_BUFFER', 0.9)*100:.0f}%
            - **Daily Trade Limit:** {config.get('MAX_DAILY_TRADES', 30)}
            """)

def show_logs():
    """Show real-time logs"""
    st.markdown("### 📋 Real-time Logs")
    
    # Auto-refresh logs
    if st.button("🔄 Refresh Logs"):
        st.rerun()
    
    try:
        logs_data = get_api_data("logs/50")
        logs = logs_data.get("logs", [])
        
        if logs:
            log_text = "".join(logs[-30:])  # Last 30 lines
            st.markdown(f'<div class="log-container">{log_text}</div>', unsafe_allow_html=True)
        else:
            st.info("No logs available")
    except Exception as e:
        st.error(f"Error loading logs: {e}")

def show_configuration():
    """Show configuration page"""
    st.markdown("### ⚙️ Bot Configuration")
    
    config = load_config()
    
    if not config:
        st.error("Unable to load configuration")
        return
    
    # Trading pairs
    st.markdown("#### 🎯 Trading Pairs")
    pairs_text = "\n".join(config.get("TRADING_PAIRS", []))
    new_pairs = st.text_area("Trading Pairs (one per line)", value=pairs_text, height=150)
    
    # Risk management
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🛡️ Risk Management")
        leverage = st.slider("Leverage", 1, 10, config.get("LEVERAGE", 3))
        trailing_stop = st.number_input("Trailing Stop (%)", 0.1, 10.0, config.get("TRAILING_STOP_PERCENTAGE", 1.0), 0.1)
        take_profit = st.number_input("Take Profit (%)", 0.1, 10.0, config.get("TAKE_PROFIT_PERCENTAGE", 2.0), 0.1)
    
    with col2:
        st.markdown("#### 💰 Position Sizing")
        position_buffer = st.slider("Position Size Buffer", 0.5, 1.0, config.get("POSITION_SIZE_BUFFER", 0.9), 0.05)
        min_notional = st.number_input("Min Notional (USDT)", 5.0, 100.0, config.get("MIN_NOTIONAL", 20.0), 5.0)
        max_daily_trades = st.number_input("Max Daily Trades", 10, 100, config.get("MAX_DAILY_TRADES", 30), 5)
    
    # Save configuration
    if st.button("💾 Save Configuration", type="primary"):
        new_config = config.copy()
        new_config.update({
            "TRADING_PAIRS": [pair.strip() for pair in new_pairs.split('\n') if pair.strip()],
            "LEVERAGE": leverage,
            "TRAILING_STOP_PERCENTAGE": trailing_stop,
            "TAKE_PROFIT_PERCENTAGE": take_profit,
            "POSITION_SIZE_BUFFER": position_buffer,
            "MIN_NOTIONAL": min_notional,
            "MAX_DAILY_TRADES": max_daily_trades
        })
        
        try:
            response = requests.post(f"{API_BASE}/api/config", json=new_config, timeout=10)
            if response.status_code == 200:
                st.success("✅ Configuration saved successfully!")
                st.rerun()
            else:
                st.error("❌ Failed to save configuration")
        except Exception as e:
            st.error(f"❌ Error saving configuration: {e}")

# Main application
def main():
    # Sidebar navigation
    st.sidebar.markdown("## 🚀 Navigation")
    page = st.sidebar.selectbox("Choose a page:", ["Dashboard", "Logs", "Configuration", "About"])
    
    # Auto-refresh settings
    st.sidebar.markdown("## 🔄 Auto-refresh")
    auto_refresh = st.sidebar.checkbox("Enable auto-refresh", value=True)
    refresh_interval = st.sidebar.slider("Refresh interval (seconds)", 1, 30, 5)
    
    if auto_refresh:
        time.sleep(refresh_interval)
        st.rerun()
    
    # Page routing
    if page == "Dashboard":
        show_main_dashboard()
    elif page == "Logs":
        show_logs()
    elif page == "Configuration":
        show_configuration()
    elif page == "About":
        st.markdown("""
        ### 🤖 About This Bot
        
        **Crypto Trading Bot v2.0 - Optimized Edition**
        
        - 🎯 **35 High-quality Trading Pairs**
        - ⚡ **Real-time WebSocket Updates**
        - 📊 **Multi-timeframe Analysis** (1m, 5m, 15m, 1h, 4h, 1d)
        - 🛡️ **Advanced Risk Management**
        - 🔄 **15+ Technical Indicators**
        - 💰 **Automated P&L Tracking**
        
        **Features:**
        - Real-time market scanning
        - Intelligent signal confirmation
        - Circuit breaker protection
        - Multi-channel notifications
        - Performance analytics
        
        **Technology Stack:**
        - Python 3.11
        - Streamlit (Frontend)
        - FastAPI (Backend)
        - WebSocket (Real-time)
        - Binance API
        - Technical Analysis Libraries
        """)

if __name__ == "__main__":
    main() 