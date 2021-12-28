from flask import session, redirect, url_for, render_template, request
from . import main
from flask import Blueprint, request, jsonify, make_response, Response
from services.Users.Enquirer.models import *
from services.Users.Member.models import *
from os import environ, path
from dotenv import load_dotenv
import sys, os
# from . import login_manager
from flask_login import current_user, login_required, logout_user
from flask_jwt_extended import jwt_required , get_jwt_identity
import requests,json
import datetime
from sqlalchemy import desc
from .models import *
import sqlalchemy as sa
from sqlalchemy import func
from app import db
from sqlalchemy import create_engine

chats_uploads_url = 'http://164.90.186.255/Openarc/chats/uploads/'


basedir = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', '..'))
load_dotenv(path.join(basedir, '.env'))

engine = create_engine('mysql+pymysql://root:root@localhost/openarc_chats_db', pool_recycle=3600)
conn = engine.connect()



#######################################GET INBOX DATA############################
@main.route('/inboxData/<user_id>', methods=['GET'])
def getinboxData(user_id):
    try:
        current_user = user_id
        print('current_user',current_user)
        user_instance = User.query.get(current_user)
        result = conn.execute('''
           SELECT group_concat(chats_history.message) 
            FROM chats_history 
            WHERE sent_by = 6 or sent_to = 6
            GROUP BY sent_to , sent_by
            ORDER BY MAX(id) DESC
                    ''').fetchall()
        print('result',result)
        # received_result = conn.execute('''
        #    SELECT group_concat(chats_history.message) 
        #     FROM chats_history 
        #     WHERE sent_to = 6
        #     GROUP BY sent_to , sent_by
        #     ORDER BY MAX(id) DESC
        #             ''').fetchall()
        # print('received_result',received_result)
        # sent_to_users = []
        # for msg in sent_messages:
        #     user_id = 
    except Exception as e:
        #catch error and print line number where error occurs
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in getting inbox data at line number',lNumber,'error is:',e)
        return make_response(jsonify({"error":"Error in messages"}),400)
#################################################################################

@main.route('/availableUsers/', methods=['POST'])
def getAvailableUsers():
    try:
        post_data = request.get_json()
        users_list = []
        user_dict = {}
        current_user = post_data['current_user']
        if ((current_user == None) or (current_user == '')):
            return make_response(jsonify({"error":"current_user id is required"}),400)
        users_available = Session.query.all()
        for data in users_available:
            if str(data.user) != str(current_user):
                user_dict['session_id'] = data.session_id
                user_dict['user_id'] = data.user
                users_list.append(user_dict.copy())
        return make_response(jsonify({"available_users":users_list}),200)
    except Exception as e:
        #catch error and print line number where error occurs
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in getting available_users at line number',lNumber,'error is:',e)
        return make_response(jsonify({"error":"Error in messages"}),400)


@main.route('/chatMessages/<user_id>', methods=['POST'])
def getMessages(user_id):
    try:
        print('here you go>>',user_id)
        can_send = False
        current_user = user_id
        messages_list = []
        message_dict = {'message':'',"time":"","sent_or_received":""}
        user_instance = User.query.get(current_user)
        if user_instance is None:
            return make_response(jsonify({"error":"No such user exists with sent user id"}),400)
        sender_name = user_instance.name
        post_data = request.get_json(force = True)
        if post_data is None:
            return make_response(jsonify({"error":"Please send valid data"}),400)
        receiver = post_data['sent_to']
        if ((receiver == None) or (receiver == '')):
            return make_response(jsonify({"error":"receiver id is required"}),400)
        receiver_instance = User.query.get(receiver)
        if receiver_instance is None:
            return make_response(jsonify({"error":"No such user exists with sent user id"}),400)
        receiver_name = receiver_instance.name
        sent_to = receiver
        sent_messages = ChatHistory.query.filter_by(sent_by=current_user).filter_by(sent_to=sent_to)
        received_messages = ChatHistory.query.filter_by(sent_by=sent_to).filter_by(sent_to=current_user)
        q3 = sent_messages.union(received_messages)
        for message in q3:
            if str(message.sent_by) == str(current_user):
                message_direction = 'sent'
            else:
                message_direction = 'received'
                can_send = True 
            msg = message.message
            time = message.created_at
            try:
                if message.document == '':
                    document_sent = ''
                else:
                    document_sent = chats_uploads_url+message.document
            except Exception as e:
                document_sent = ''
            message_dict['document_name'] = document_sent
            message_dict['document_string'] = document_sent
            message_dict['message'] = msg
            message_dict['time'] = time
            message_dict['sender'] = sender_name
            message_dict['receiver'] = receiver_name
            message_dict['sent_or_received'] = message_direction
            messages_list.append(message_dict.copy())
            messages_list.sort(key = lambda x:x['time'])
        return make_response(jsonify({"messages":messages_list,'can_send_message':can_send}),200)
    except Exception as e:
        #catch error and print line number where error occurs
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in getting user messages at line number',lNumber,'error is:',e)
        return make_response(jsonify({"error":str(e)}),400)



@main.route('/allUserChats/<user_id>', methods=['GET'])
def allUserChats(user_id):
    try:
        current_user = user_id
        print('current_user',current_user)
        messages_list = []
        message_dict = {}
        user_instance = User.query.get(current_user)
        print('user_instance',user_instance)
        user_type = user_instance.user_type
        if user_type == 'member':
            try:
                member_name = user_instance.name
            except Exception as e:
                return make_response(jsonify({"error":'No user found'}),400)
            sent_messages = ChatHistory.query.filter_by(sent_by=current_user)
            received_messages = ChatHistory.query.filter_by(sent_to=current_user)
            q3 = sent_messages.union(received_messages)
            members_users_list = []
            for msg in q3:
                print ('msg',msg,user_type)
                sent_to = msg.sent_to
                sent_by = msg.sent_by
                if sent_to not in members_users_list:
                    members_users_list.append(sent_to)
                if sent_by not in members_users_list:
                    members_users_list.append(sent_by)
            print('members_users_list--',members_users_list) 
            for user in members_users_list:
                if int(user) == int(current_user):
                     pass
                usr_instance = User.query.get(user)
                try:
                    profile_exists = bool(Profile.query.filter_by(user_id=user).first())
                    if profile_exists:
                        profile_instance = Profile.query.filter_by(user_id=user)
                        for profile in profile_instance:
                                profile_pic = profile.profile_pic
                    else:
                        enq_profile_exists = bool(EnquirerProfile.query.filter_by(enquirer_id=user).first())
                        if enq_profile_exists:
                            profile_instance = EnquirerProfile.query.filter_by(enquirer_id=user)
                            for profile in profile_instance:
                                profile_pic = profile.company_logo
                        else:
                            profile_pic = ''
                except Exception as e:
                    print('in Exception pic not found',e)
                print('user',user,'current_user',current_user)
                ########Current user = user####
                if (int(current_user) == int(user)):
                    sent_messages = ChatHistory.query.filter_by(sent_by=current_user)
                    received_messages = ChatHistory.query.filter_by(sent_to=current_user)
                    user_messages = sent_messages.union(received_messages).order_by(ChatHistory.created_at)
                    # print('equal',user_messages)
                    last_obj = user_messages[-1]
                    # print('last_obj',last_obj)
                    if str(last_obj.sent_by) == str(current_user):
                        message_direction = 'sent'
                        for msg in user_messages:
                            sent_to_id = msg.sent_to
                            sent_to_instance = User.query.get(sent_to_id)
                            sent_to = sent_to_instance.name
                            sent_by_id = current_user
                            sent_by = member_name
                            try:
                                profile_exists = bool(Profile.query.filter_by(user_id=sent_to_id).first())
                                if profile_exists:
                                    profile_instance = Profile.query.filter_by(user_id=sent_to_id)
                                    for profile in profile_instance:
                                            profile_pic = profile.profile_pic
                                else:
                                    enq_profile_exists = bool(EnquirerProfile.query.filter_by(enquirer_id=sent_to_id).first())
                                    if enq_profile_exists:
                                        profile_instance = EnquirerProfile.query.filter_by(enquirer_id=sent_to_id)
                                        for profile in profile_instance:
                                            profile_pic = profile.company_logo
                                    else:
                                        profile_pic = ''
                            except Exception as e:
                                print('in Exception pic not found',e)
                    else:
                        message_direction = 'received'
                        for msg in user_messages: 
                            sent_to_id = current_user
                            sent_by_id = msg.sent_by
                            sent_by_instance = User.query.get(sent_by_id)
                            sent_by = sent_by_instance.name
                            sent_to = member_name
                            try:
                                profile_exists = bool(Profile.query.filter_by(user_id=sent_by_id).first())
                                if profile_exists:
                                    profile_instance = Profile.query.filter_by(user_id=sent_by_id)
                                    for profile in profile_instance:
                                            profile_pic = profile.profile_pic
                                else:
                                    enq_profile_exists = bool(EnquirerProfile.query.filter_by(enquirer_id=sent_by_id).first())
                                    if enq_profile_exists:
                                        profile_instance = EnquirerProfile.query.filter_by(enquirer_id=sent_by_id)
                                        for profile in profile_instance:
                                            profile_pic = profile.company_logo
                                    else:
                                        profile_pic = ''
                            except Exception as e:
                                print('in Exception pic not found',e)
                else:
                    sent_messages = ChatHistory.query.filter_by(sent_by=current_user).filter_by(sent_to=user)
                    received_messages = ChatHistory.query.filter_by(sent_to=current_user).filter_by(sent_by=user)
                    user_messages = sent_messages.union(received_messages).order_by(ChatHistory.created_at)
                    try:
                        last_obj = user_messages[-1]
                        print('last_obj',last_obj)
                        if str(last_obj.sent_by) == str(current_user):
                            message_direction = 'sent'
                            sent_to_id = user
                            sent_by_id = current_user
                            sent_by = member_name
                            sent_to = usr_instance.name
                            try:
                                profile_exists = bool(Profile.query.filter_by(user_id=sent_to_id).first())
                                if profile_exists:
                                    profile_instance = Profile.query.filter_by(user_id=sent_to_id)
                                    for profile in profile_instance:
                                            profile_pic = profile.profile_pic
                                else:
                                    enq_profile_exists = bool(EnquirerProfile.query.filter_by(enquirer_id=sent_to_id).first())
                                    if enq_profile_exists:
                                        profile_instance = EnquirerProfile.query.filter_by(enquirer_id=sent_to_id)
                                        for profile in profile_instance:
                                            profile_pic = profile.company_logo
                                    else:
                                        profile_pic = ''
                            except Exception as e:
                                print('in Exception pic not found',e)
                        else:
                            sent_to = member_name
                            sent_by = usr_instance.name
                            sent_by_id = user
                            sent_to_id = current_user
                            message_direction = 'received' 
                            try:
                                profile_exists = bool(Profile.query.filter_by(user_id=sent_by_id).first())
                                if profile_exists:
                                    profile_instance = Profile.query.filter_by(user_id=sent_by_id)
                                    for profile in profile_instance:
                                            profile_pic = profile.profile_pic
                                else:
                                    enq_profile_exists = bool(EnquirerProfile.query.filter_by(enquirer_id=sent_by_id).first())
                                    if enq_profile_exists:
                                        profile_instance = EnquirerProfile.query.filter_by(enquirer_id=sent_by_id)
                                        for profile in profile_instance:
                                            profile_pic = profile.company_logo
                                    else:
                                        profile_pic = ''
                            except Exception as e:
                                print('in Exception pic not found',e)
                    except Exception as e:
                        print('error in last_obj',e)
                        obj = user_messages
                        for msg in obj:
                            print('msg',msg)
                            if str(msg.sent_by) == str(current_user):
                                message_direction = 'sent'
                                sent_to_id = user
                                sent_by_id = current_user
                                sent_by = member_name
                                sent_to = usr_instance.name
                                try:
                                    profile_exists = bool(Profile.query.filter_by(user_id=sent_to_id).first())
                                    if profile_exists:
                                        profile_instance = Profile.query.filter_by(user_id=sent_to_id)
                                        for profile in profile_instance:
                                                profile_pic = profile.profile_pic
                                    else:
                                        enq_profile_exists = bool(EnquirerProfile.query.filter_by(enquirer_id=sent_to_id).first())
                                        if enq_profile_exists:
                                            profile_instance = EnquirerProfile.query.filter_by(enquirer_id=sent_to_id)
                                            for profile in profile_instance:
                                                profile_pic = profile.company_logo
                                        else:
                                            profile_pic = ''
                                except Exception as e:
                                    print('in Exception pic not found',e)
                            else:
                                sent_to = member_name
                                sent_by = usr_instance.name
                                sent_by_id = user
                                sent_to_id = current_user
                                message_direction = 'received'
                                try:
                                    profile_exists = bool(Profile.query.filter_by(user_id=sent_by_id).first())
                                    if profile_exists:
                                        profile_instance = Profile.query.filter_by(user_id=sent_by_id)
                                        for profile in profile_instance:
                                                profile_pic = profile.profile_pic
                                    else:
                                        enq_profile_exists = bool(EnquirerProfile.query.filter_by(enquirer_id=sent_by_id).first())
                                        if enq_profile_exists:
                                            profile_instance = EnquirerProfile.query.filter_by(enquirer_id=sent_by_id)
                                            for profile in profile_instance:
                                                profile_pic = profile.company_logo
                                        else:
                                            profile_pic = ''
                                except Exception as e:
                                    print('in Exception pic not found',e) 
                    message_dict['message'] = last_obj.message
                    message_dict['profile_pic'] = profile_pic
                    message_dict['time'] = last_obj.created_at
                    message_dict['sent_to_id'] = sent_to_id
                    message_dict['direction'] = message_direction
                    message_dict['sent_by'] = sent_by
                    message_dict['sent_to'] = sent_to
                    message_dict['sent_by_id'] = sent_by_id
                    messages_list.append(message_dict.copy())
                    messages_list.sort(key = lambda x:x['time'])
        else:
            try:
                enquirer_name = user_instance.name
            except Exception as e:
                return make_response(jsonify({"error":'No user found'}),400)
            sent_messages = ChatHistory.query.filter_by(sent_by=current_user)
            received_messages = ChatHistory.query.filter_by(sent_to=current_user)
            q3 = sent_messages.union(received_messages)
            users_list = []
            for msg in q3:
                print ('msg',msg,user_type)
                sent_to = msg.sent_to
                sent_by = msg.sent_by
                if sent_to not in users_list:
                    users_list.append(sent_to)
                if sent_by not in users_list:
                    users_list.append(sent_by)
            print('users_list--',users_list) 
            for user in users_list:
                usr_instance = User.query.get(user)
                print('usr_instance-------',usr_instance)
                if usr_instance is None:
                    pass
                else:
                    try:
                        profile_exists = bool(Profile.query.filter_by(user_id=user).first())
                        if profile_exists:
                            profile_instance = Profile.query.filter_by(user_id=user)
                            for profile in profile_instance:
                                    profile_pic = profile.profile_pic
                        else:
                            enq_profile_exists = bool(EnquirerProfile.query.filter_by(enquirer_id=user).first())
                            if enq_profile_exists:
                                profile_instance = EnquirerProfile.query.filter_by(enquirer_id=user)
                                for profile in profile_instance:
                                    profile_pic = profile.profile_pic
                            else:
                                profile_pic = ''
                    except Exception as e:
                        print('in Exception pic not found',e)
                    print('user',user,'current_user',current_user)
                    if (int(current_user) == int(user)):
                        sent_messages = ChatHistory.query.filter_by(sent_by=current_user)
                        received_messages = ChatHistory.query.filter_by(sent_to=current_user)
                        user_messages = sent_messages.union(received_messages).order_by(ChatHistory.created_at)
                        # print('equal',user_messages)
                        last_obj = user_messages[-1]
                        # print('last_obj',last_obj)
                        if str(last_obj.sent_by) == str(current_user):
                            message_direction = 'sent'
                            for msg in user_messages:
                                sent_to_id = msg.sent_to
                                sent_to_instance = User.query.get(sent_to_id)
                                sent_to = sent_to_instance.name
                                sent_by_id = current_user
                                sent_by = enquirer_name
                                try:
                                    profile_exists = bool(Profile.query.filter_by(user_id=sent_to_id).first())
                                    if profile_exists:
                                        profile_instance = Profile.query.filter_by(user_id=sent_to_id)
                                        for profile in profile_instance:
                                                profile_pic = profile.profile_pic
                                    else:
                                        enq_profile_exists = bool(EnquirerProfile.query.filter_by(enquirer_id=sent_to_id).first())
                                        if enq_profile_exists:
                                            profile_instance = EnquirerProfile.query.filter_by(enquirer_id=sent_to_id)
                                            for profile in profile_instance:
                                                profile_pic = profile.profile_pic
                                        else:
                                            profile_pic = ''
                                except Exception as e:
                                    print('in Exception pic not found',e)
                        else:
                            message_direction = 'received'
                            for msg in user_messages: 
                                sent_to_id = current_user
                                sent_by_id = msg.sent_by
                                sent_by_instance = User.query.get(sent_by_id)
                                if sent_by_instance == None:
                                    sent_by = ''
                                else:
                                    sent_by = sent_by_instance.name
                                sent_to = enquirer_name
                                try:
                                    profile_exists = bool(Profile.query.filter_by(user_id=sent_by_id).first())
                                    if profile_exists:
                                        profile_instance = Profile.query.filter_by(user_id=sent_by_id)
                                        for profile in profile_instance:
                                                profile_pic = profile.profile_pic
                                    else:
                                        enq_profile_exists = bool(EnquirerProfile.query.filter_by(enquirer_id=sent_by_id).first())
                                        if enq_profile_exists:
                                            profile_instance = EnquirerProfile.query.filter_by(enquirer_id=sent_by_id)
                                            for profile in profile_instance:
                                                profile_pic = profile.profile_pic
                                        else:
                                            profile_pic = ''
                                except Exception as e:
                                    print('in Exception pic not found',e)
                    else:
                        sent_messages = ChatHistory.query.filter_by(sent_by=current_user).filter_by(sent_to=user)
                        received_messages = ChatHistory.query.filter_by(sent_to=current_user).filter_by(sent_by=user)
                        user_messages = sent_messages.union(received_messages).order_by(ChatHistory.created_at)
                        # last_obj = user_messages[-1]
                        # print('last_obj',last_obj.id,'user',user)
                        # if str(last_obj.sent_by) == str(current_user):
                        #     message_direction = 'sent'
                        #     sent_to_id = user
                        #     sent_by_id = current_user
                        #     sent_by = enquirer_name
                        #     sent_to = usr_instance.name
                        # else:
                        #     sent_to = enquirer_name
                        #     sent_by = usr_instance.name
                        #     sent_by_id = user
                        #     sent_to_id = current_user
                        #     message_direction = 'received'
                        try:
                            last_obj = user_messages[-1]
                            print('last_obj',last_obj)
                            if str(last_obj.sent_by) == str(current_user):
                                message_direction = 'sent'
                                sent_to_id = user
                                sent_by_id = current_user
                                sent_by = enquirer_name
                                sent_to = usr_instance.name
                            else:
                                sent_to = enquirer_name
                                sent_by = usr_instance.name
                                sent_by_id = user
                                sent_to_id = current_user
                                message_direction = 'received' 
                        except Exception as e:
                            print('error in last_obj',e)
                            obj = user_messages
                            for msg in obj:
                                print('msg',msg)
                                if str(msg.sent_by) == str(current_user):
                                    message_direction = 'sent'
                                    sent_to_id = user
                                    sent_by_id = current_user
                                    sent_by = enquirer_name
                                    sent_to = usr_instance.name
                                else:
                                    sent_to = enquirer_name
                                    sent_by = usr_instance.name
                                    sent_by_id = user
                                    sent_to_id = current_user
                                    message_direction = 'received' 
                        message_dict['message'] = last_obj.message
                        message_dict['profile_pic'] = profile_pic
                        message_dict['time'] = last_obj.created_at
                        message_dict['sent_to_id'] = sent_to_id
                        message_dict['direction'] = message_direction
                        message_dict['sent_by'] = sent_by
                        message_dict['sent_to'] = sent_to
                        message_dict['sent_by_id'] = sent_by_id
                        messages_list.append(message_dict.copy())
                        messages_list.sort(key = lambda x:x['time'])
        print('messages_list',messages_list)
        db.session.remove()
        return make_response(jsonify({"messages":messages_list}),200)
    except Exception as e:
        #catch error and print line number where error occurs
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in getting user messagesat line number',lNumber,'error is:',e)
        return make_response(jsonify({"error":str(e)}),400)



@main.route('/chat')
def chat():
    """Chat room. The user's name and room must be stored in
    the session."""
    name = session.get('name', '')
    room = session.get('room', '')
    # if name == '' or room == '':
    #     return redirect(url_for('.index'))
    return render_template('chat.html', name=name, room=room)
