#!/bin/env python
from app import create_app, socketio
from flask_socketio import SocketIO
import eventlet

eventlet.monkey_patch()

app = create_app(debug=True)

if __name__ == '__main__':
    socketio = SocketIO(app, cors_allowed_origins='*',message_queue='redis://',always_connect=True, async_mode='eventlet')
    socketio.run(app, host="0.0.0.0", port=5004)
