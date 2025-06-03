import logging
import threading
from app import app
from bot import start_bot

if __name__ == "__main__":
    # Start the Telegram bot in a separate thread
    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()
    
    logging.info("Starting Flask application on port 5000")
    logging.info("Starting Telegram bot in background thread")
    
    # Start Flask app
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
