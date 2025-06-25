import streamlit as st
import json
import subprocess
import os
from datetime import datetime
import pandas as pd
from streamlit_autorefresh import st_autorefresh
import io
import requests

API_BASE = "http://status-api:8080/api"

def load_config():
    try:
        with open('bot_config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("bot_config.json not found!")
        return {}

def save_config(config):
    try:
        with open('bot_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        st.error(f"Error saving config: {e}")
        return False

def get_bot_status():
    try:
        r = requests.get(f"{API_BASE}/bot_status", timeout=2)
        return r.json()
    except Exception:
        return {"running": False, "active_trades_count": 0, "total_pnl": 0.0, "last_update": "-"}

def get_active_trades():
    try:
        r = requests.get(f"{API_BASE}/active_trades", timeout=2)
        return r.json()
    except Exception:
        return []

def get_trade_history():
    try:
        r = requests.get(f"{API_BASE}/trade_history", timeout=2)
        return r.json()
    except Exception:
        return []

def bot_control(action):
    try:
        r = requests.post(f"{API_BASE}/{action}_bot", timeout=5)
        return r.json().get("status", "error")
    except Exception as e:
        return f"error: {e}"

def main():
    st.set_page_config(
        page_title="Crypto Trading Bot Dashboard",
        page_icon="🤖",
        layout="wide"
    )
    
    st.title("🤖 Crypto Trading Bot Dashboard")
    
    # Sidebar for navigation
    page = st.sidebar.selectbox("Navigation", ["Dashboard", "Configuration", "Logs", "About"])
    
    if page == "Dashboard":
        show_dashboard()
    elif page == "Configuration":
        show_configuration()
    elif page == "Logs":
        show_logs()
    elif page == "About":
        show_about()

def show_dashboard():
    # Auto-refresh every 5 seconds
    st_autorefresh(interval=5000, key="dashboardrefresh")
    st.header("📊 Bot Status")
    
    # Bot status
    bot_status = get_bot_status()
    active_trades = get_active_trades()
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Status", "🟢 Running" if bot_status.get("running") else "🔴 Stopped")
    with col2:
        st.metric("Active Trades", bot_status.get("active_trades_count", 0))
    with col3:
        st.metric("Total P&L", f"${bot_status.get('total_pnl', 0.0):.2f}")
    with col4:
        st.metric("Last Update", bot_status.get("last_update", "-"))
    
    # Bot control buttons
    st.subheader("🎮 Bot Control")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("▶️ Start Bot"):
            status = bot_control("start")
            st.info(f"Start Bot: {status}")
    
    with col2:
        if st.button("⏹️ Stop Bot"):
            status = bot_control("stop")
            st.warning(f"Stop Bot: {status}")
    
    with col3:
        if st.button("🔄 Restart Bot"):
            status = bot_control("restart")
            st.info(f"Restart Bot: {status}")
    
    # Active trades table
    st.subheader("📈 Active Trades")
    if active_trades:
        df = pd.DataFrame(active_trades)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No active trades")
    
    # Recent activity (real trade history)
    st.subheader("📋 Recent Activity")
    try:
        history = get_trade_history()
        if history:
            activity_df = pd.DataFrame(history)
            # Filter widgets
            col1, col2, col3 = st.columns([2,2,2])
            with col1:
                search = st.text_input("🔍 Search", "")
            with col2:
                event_types = ["All"] + sorted(activity_df["event"].dropna().unique().tolist())
                event_filter = st.selectbox("Event Type", event_types)
            with col3:
                symbols = ["All"] + sorted(activity_df["symbol"].dropna().unique().tolist())
                symbol_filter = st.selectbox("Symbol", symbols)
            # Apply filters
            filtered_df = activity_df
            if event_filter != "All":
                filtered_df = filtered_df[filtered_df["event"] == event_filter]
            if symbol_filter != "All":
                filtered_df = filtered_df[filtered_df["symbol"] == symbol_filter]
            if search:
                mask = filtered_df.apply(lambda row: search.lower() in str(row).lower(), axis=1)
                filtered_df = filtered_df[mask]
            # Show latest first
            filtered_df = filtered_df[::-1]
            # Export button
            csv = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"trade_history_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime='text/csv'
            )
            # Show table
            st.dataframe(filtered_df, use_container_width=True)
        else:
            st.info("No recent activity.")
    except Exception:
        st.info("No recent activity.")

def show_configuration():
    st.header("⚙️ Bot Configuration")
    
    # Load current config
    config = load_config()
    
    # Trading pairs
    st.subheader("Trading Pairs")
    pairs_input = st.text_area(
        "Trading Pairs (one per line)",
        value="\n".join(config.get("TRADING_PAIRS", [])),
        height=100,
        help="Enter one trading pair per line (e.g., ETHUSDT, BTCUSDT)"
    )
    
    # Risk management
    st.subheader("Risk Management")
    col1, col2 = st.columns(2)
    with col1:
        leverage = st.slider("Leverage", 1, 10, config.get("LEVERAGE", 3), help="Trading leverage (1-10x)")
        trailing_stop = st.number_input("Trailing Stop (%)", 0.1, 10.0, config.get("TRAILING_STOP_PERCENTAGE", 1.0), 0.1, help="Trailing stop percentage")
    with col2:
        take_profit = st.number_input("Take Profit (%)", 0.1, 10.0, config.get("TAKE_PROFIT_PERCENTAGE", 2.0), 0.1, help="Take profit percentage")
        min_notional = st.number_input("Min Notional (USDT)", 5.0, 100.0, config.get("MIN_NOTIONAL", 20.0), 5.0, help="Minimum order size in USDT")
    
    # Position sizing
    st.subheader("Position Sizing")
    col1, col2 = st.columns(2)
    with col1:
        position_buffer = st.slider("Position Size Buffer", 0.5, 1.0, config.get("POSITION_SIZE_BUFFER", 0.90), 0.05, help="Percentage of available balance to use")
        min_balance = st.number_input("Min Balance Threshold (USDT)", 10.0, 1000.0, config.get("MIN_BALANCE_THRESHOLD", 100.0), 10.0, help="Minimum balance required to start trading")
    with col2:
        small_account_limit = st.slider("Small Account Position Limit", 0.1, 1.0, config.get("SMALL_ACCOUNT_POSITION_LIMIT", 0.50), 0.05, help="Position size limit for small accounts")
    
    # Configuration summary
    st.subheader("📋 Configuration Summary")
    summary_data = {
        "Trading Pairs": len([p.strip() for p in pairs_input.split("\n") if p.strip()]),
        "Leverage": f"{leverage}x",
        "Trailing Stop": f"{trailing_stop}%",
        "Take Profit": f"{take_profit}%",
        "Min Notional": f"${min_notional}",
        "Position Buffer": f"{position_buffer*100}%",
        "Min Balance": f"${min_balance}",
        "Small Account Limit": f"{small_account_limit*100}%"
    }
    
    summary_df = pd.DataFrame(list(summary_data.items()), columns=["Parameter", "Value"])
    st.dataframe(summary_df, use_container_width=True)
    
    # Save button
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("💾 Save Configuration", type="primary"):
            # Parse trading pairs
            pairs = [p.strip() for p in pairs_input.split("\n") if p.strip()]
            
            # Update config
            new_config = {
                "TRADING_PAIRS": pairs,
                "LEVERAGE": leverage,
                "TRAILING_STOP_PERCENTAGE": trailing_stop,
                "TAKE_PROFIT_PERCENTAGE": take_profit,
                "MIN_NOTIONAL": min_notional,
                "MIN_BALANCE_THRESHOLD": min_balance,
                "POSITION_SIZE_BUFFER": position_buffer,
                "SMALL_ACCOUNT_POSITION_LIMIT": small_account_limit
            }
            
            if save_config(new_config):
                st.success("✅ Configuration saved successfully!")
                st.info("🔄 Please restart the bot for changes to take effect.")
    
    with col2:
        if st.button("🔄 Reset to Defaults"):
            default_config = {
                "TRADING_PAIRS": ["ETHUSDT"],
                "LEVERAGE": 3,
                "TRAILING_STOP_PERCENTAGE": 1.0,
                "TAKE_PROFIT_PERCENTAGE": 2.0,
                "MIN_NOTIONAL": 20.0,
                "MIN_BALANCE_THRESHOLD": 100.0,
                "POSITION_SIZE_BUFFER": 0.90,
                "SMALL_ACCOUNT_POSITION_LIMIT": 0.50
            }
            if save_config(default_config):
                st.success("✅ Configuration reset to defaults!")
                st.rerun()

def show_logs():
    st.header("📋 Bot Logs")
    
    # Log file selector
    log_files = []
    if os.path.exists("logs"):
        log_files = [f for f in os.listdir("logs") if f.endswith('.log')]
    
    if log_files:
        log_file = st.selectbox("Select Log File", log_files)
        
        # Read and display logs
        try:
            with open(f"logs/{log_file}", "r") as f:
                logs = f.readlines()
            
            # Show last N lines
            num_lines = st.slider("Number of lines to show", 50, 500, 100)
            recent_logs = logs[-num_lines:]
            
            # Search filter
            search_term = st.text_input("Search logs", "")
            if search_term:
                filtered_logs = [log for log in recent_logs if search_term.lower() in log.lower()]
                st.text_area("Filtered Logs", "".join(filtered_logs), height=400)
            else:
                st.text_area("Recent Logs", "".join(recent_logs), height=400)
            
            # Download button
            st.download_button(
                label="📥 Download Full Log",
                data="".join(logs),
                file_name=f"{log_file}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )
            
            # Log statistics
            st.subheader("📊 Log Statistics")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Lines", len(logs))
            with col2:
                error_count = len([log for log in logs if "ERROR" in log])
                st.metric("Errors", error_count)
            with col3:
                warning_count = len([log for log in logs if "WARNING" in log])
                st.metric("Warnings", warning_count)
                
        except FileNotFoundError:
            st.error("Log file not found")
        except Exception as e:
            st.error(f"Error reading log file: {e}")
    else:
        st.warning("No log files found in logs directory")

def show_about():
    st.header("ℹ️ About")
    
    st.markdown("""
    ## Crypto Trading Bot
    
    A sophisticated cryptocurrency trading bot built with Python and Binance API.
    
    ### Features
    - 🤖 Automated trading with RSI strategy
    - 📊 Real-time market monitoring
    - 🛡️ Risk management with trailing stops
    - 📱 Multi-channel notifications (Telegram, Email, Discord)
    - ⚙️ Easy configuration via Web UI
    - 📈 Comprehensive logging and monitoring
    
    ### Technology Stack
    - **Backend**: Python, Binance API, pandas, pandas-ta
    - **Web UI**: Streamlit
    - **Notifications**: Telegram, Email, Discord
    - **Containerization**: Docker
    
    ### Configuration
    - Trading pairs and parameters can be modified via the Configuration page
    - All settings are stored in `bot_config.json`
    - API keys and sensitive data are stored in environment variables
    
    ### Safety Features
    - Rate limiting to prevent API bans
    - Comprehensive error handling
    - Position size limits for small accounts
    - Trailing stops to limit losses
    
    ### Support
    For issues or questions, please check the logs or contact support.
    """)
    
    # System information
    st.subheader("🔧 System Information")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Python Version", "3.9+")
        st.metric("Streamlit Version", "1.28.0")
    with col2:
        st.metric("Bot Version", "1.0.0")
        st.metric("Last Updated", "2024-01-15")

if __name__ == "__main__":
    main() 