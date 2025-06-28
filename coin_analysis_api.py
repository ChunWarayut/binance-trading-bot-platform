from flask import Flask, jsonify, request
from trading_bot import TradingBot
import asyncio
import json
from datetime import datetime
import config

app = Flask(__name__)
bot = None

def get_bot():
    global bot
    if bot is None:
        bot = TradingBot()
    return bot

@app.route('/api/coin-analysis', methods=['GET'])
def get_coin_analysis():
    """ดึงผลการวิเคราะห์เหรียญทั้งหมด"""
    try:
        bot_instance = get_bot()
        
        # ใช้ asyncio.run เพื่อเรียก async function
        async def get_analysis():
            return await bot_instance.analyze_coins()
        
        analyses = asyncio.run(get_analysis())
        
        # Format response
        formatted_analyses = {}
        for symbol, analysis in analyses.items():
            formatted_analyses[symbol] = {
                'symbol': analysis['symbol'],
                'current_price': analysis['current_price'],
                'order_size_category': analysis['categories']['order_size'],
                'leverage_category': analysis['categories']['leverage'],
                'position_size_multiplier': analysis['recommendations']['position_size_multiplier'],
                'recommended_leverage': analysis['recommendations']['leverage']['recommended'],
                'notes': analysis['recommendations']['notes'],
                'weighted_metrics': {
                    'volatility': analysis['weighted_metrics']['volatility'],
                    'liquidity_score': analysis['weighted_metrics']['liquidity_score'],
                    'avg_volume': analysis['weighted_metrics']['volume_profile']['avg_volume'],
                    'trend_strength': analysis['weighted_metrics']['trend_strength']
                },
                'timeframe_analysis': {
                    'volatility': analysis['timeframe_analysis']['volatility'],
                    'liquidity_score': analysis['timeframe_analysis']['liquidity_score'],
                    'trend_strength': analysis['timeframe_analysis']['trend_strength']
                }
            }
        
        return jsonify({
            'status': 'success',
            'data': formatted_analyses,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/coin-analysis/<symbol>', methods=['GET'])
def get_single_coin_analysis(symbol):
    """ดึงผลการวิเคราะห์เหรียญเฉพาะ"""
    try:
        bot_instance = get_bot()
        
        async def get_analysis():
            return await bot_instance.get_coin_recommendations(symbol)
        
        analysis = asyncio.run(get_analysis())
        
        if not analysis:
            return jsonify({
                'status': 'error',
                'message': f'ไม่พบข้อมูลการวิเคราะห์สำหรับ {symbol}',
                'timestamp': datetime.now().isoformat()
            }), 404
        
        formatted_analysis = {
            'symbol': analysis['symbol'],
            'current_price': analysis['current_price'],
            'order_size_category': analysis['categories']['order_size'],
            'leverage_category': analysis['categories']['leverage'],
            'position_size_multiplier': analysis['recommendations']['position_size_multiplier'],
            'recommended_leverage': analysis['recommendations']['leverage']['recommended'],
            'notes': analysis['recommendations']['notes'],
            'weighted_metrics': {
                'volatility': analysis['weighted_metrics']['volatility'],
                'liquidity_score': analysis['weighted_metrics']['liquidity_score'],
                'avg_volume': analysis['weighted_metrics']['volume_profile']['avg_volume'],
                'trend_strength': analysis['weighted_metrics']['trend_strength']
            },
            'timeframe_analysis': {
                'volatility': analysis['timeframe_analysis']['volatility'],
                'liquidity_score': analysis['timeframe_analysis']['liquidity_score'],
                'trend_strength': analysis['timeframe_analysis']['trend_strength']
            }
        }
        
        return jsonify({
            'status': 'success',
            'data': formatted_analysis,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/coin-analysis/summary', methods=['GET'])
def get_analysis_summary():
    """ดึงรายงานสรุปการวิเคราะห์"""
    try:
        bot_instance = get_bot()
        
        async def get_summary():
            analyses = await bot_instance.analyze_coins()
            return bot_instance.coin_analyzer.get_summary_report(analyses)
        
        summary = asyncio.run(get_summary())
        
        return jsonify({
            'status': 'success',
            'data': {
                'summary': summary,
                'trading_pairs': config.TRADING_PAIRS
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/coin-analysis/recommendations', methods=['GET'])
def get_recommendations():
    """ดึงคำแนะนำเฉพาะ"""
    try:
        bot_instance = get_bot()
        
        async def get_recommendations():
            analyses = await bot_instance.analyze_coins()
            
            # จัดกลุ่มเหรียญตามคำแนะนำ
            large_orders = []
            medium_orders = []
            small_orders = []
            
            high_leverage = []
            medium_leverage = []
            low_leverage = []
            
            for symbol, analysis in analyses.items():
                order_size = analysis['categories']['order_size']
                leverage = analysis['categories']['leverage']
                
                if order_size == "LARGE":
                    large_orders.append(symbol)
                elif order_size == "MEDIUM":
                    medium_orders.append(symbol)
                else:
                    small_orders.append(symbol)
                
                if leverage == "HIGH":
                    high_leverage.append(symbol)
                elif leverage == "MEDIUM":
                    medium_leverage.append(symbol)
                else:
                    low_leverage.append(symbol)
            
            return {
                'order_size_recommendations': {
                    'large': large_orders,
                    'medium': medium_orders,
                    'small': small_orders
                },
                'leverage_recommendations': {
                    'high': high_leverage,
                    'medium': medium_leverage,
                    'low': low_leverage
                }
            }
        
        recommendations = asyncio.run(get_recommendations())
        
        return jsonify({
            'status': 'success',
            'data': recommendations,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True) 