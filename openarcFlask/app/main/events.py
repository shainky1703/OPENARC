from flask import session
from flask_socketio import emit, join_room, leave_room
from .. import socketio
from app.main.models import *
import sys, os
from sqlalchemy import desc
import base64, re
from werkzeug.utils import secure_filename

chats_uploads = '/var/www/html/Openarc/chats/uploads'
chats_uploads_url = 'http://164.90.186.255/Openarc/chats/uploads/'

@socketio.on('joined', namespace='/chat')
def handle_joined(data):
    # print('request',user)
    """Sent by clients when they enter a room.
    A status message is broadcast to all people in the room."""
    print('joined called---')
    print(session)
    current_user = data['user']
    room = data['room']
    join_room(room)
    try:
        session_inst = Session.query.filter_by(user = current_user)
        if session_inst:
            for obj in session_inst:
                id = obj.id
            get_session = Session.query.get(id)
            print('--get_session-',get_session)
            get_session.session_id = room  
            db.session.add(get_session)
            db.session.commit()
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in joined event at line number',lNumber,'error is:',e)
        session_obj = Session(
            user = current_user,
            session_id = room
        )
        db.session.add(session_obj)
        db.session.commit()
    emit('status', {'msg': 'user' + str(current_user) +' has entered the room.'}, room=room)


@socketio.on('text', namespace='/chat')
def handle_text(data):
    """Sent by a client when the user entered a new message.
    The message is sent to all people in the room."""
    try:
        print('in message')
        current_user = data['user']
        print(current_user)
        sent_by = current_user
        sent_by_instance = User.query.get(current_user)
        sent_to = data['send_to']
        if ((sent_to == 0) or (sent_to == '0')):
            print('error in emit',e)
        sent_to_instance = User.query.get(sent_to)
        print('sent_to',sent_to)
        try:
            message = data['msg']
        except Exception as e:
            print('no message found')
            message = ''
        try:
            print('in document chat')
            document_string = data['document_string']
            doc_name = data['document_name']
            path_to_doc = chats_uploads+'/'+doc_name
            with open(path_to_doc, "wb") as fh:
                fh.write(base64.b64decode(document_string))
            document_name = doc_name
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            lNumber = exc_tb.tb_lineno
            print('error in upload chat document at line',lNumber,'eror>>',e)
            document_name = ''
        try:
            user_room = Session.query.get(sent_to)
            room_id = user_room.session_id
        except Exception as e:
            room_id = '1'
            print('no user is available on other side')
        chat_instance = ChatHistory(
            document = document_name,
            message = message,
            sent_by = sent_by,
            sent_to = sent_to
            )
        db.session.add(chat_instance)
        db.session.commit()
        room_list = [current_user,room_id]
        messages_list = []
        message_dict = {'message':'',"time":"","sent_or_received":""}
        sent_messages = ChatHistory.query.filter_by(sent_by=current_user).filter_by(sent_to=sent_to)
        received_messages = ChatHistory.query.filter_by(sent_by=sent_to).filter_by(sent_to=current_user)
        q3 = sent_messages.union(received_messages)
        for data in q3:
            if str(data.sent_by) == str(current_user):
                message_direction = 'sent'
            else:
                message_direction = 'received'
            try:
                print('data.document',data.document)
                if data.document == '':
                    document_sent = ''
                else:
                    document_sent = chats_uploads_url+data.document
            except Exception as e:
                document_sent = ''
            message_dict['document_name'] = document_sent
            message_dict['document_string'] = document_sent 
            message_dict['message'] = data.message
            message_dict['sender'] = sent_by_instance.name
            message_dict['receiver'] = sent_to_instance.name
            message_dict['sent_or_received'] = message_direction
            message_dict['time'] = str(data.created_at)
            messages_list.append(message_dict.copy())
            messages_list.sort(key = lambda x:x['time'])
            print('messages_list',messages_list)
        try:
            for room in room_list:
                print('room',room)
                emit('status', {'chat_history': messages_list}, room=str(room))
        except Exception as e:
            print('error in emit',e)
        # emit('message', {'msg': 'user'+str(current_user) + ':' + data['msg']}, room=room_id)
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in sending text event at line number',lNumber,'error is:',e)


