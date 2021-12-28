#################################################PROFILE CRUD ROUTES#########################################
# @main_bp.route("/availabilityDates/", methods=['PUT'])
# @jwt_required
# def availabilityDates():
#     try:
#         unavailability_array = []
#         current_user = get_jwt_identity()
#         user_instance = User.query.get(current_user)
#         if user_instance.user_type == 'member':
#             pass
#         else:
#             return make_response(jsonify({"error": "Function only allowed for Member"}),400)
#         post_data = request.get_json()
#         unavailable_dates = post_data['unavailable_dates']
#         profile_data = Profile.query.filter_by(user_id=current_user)
#         for profile in profile_data:
#             profile_id = profile.id 
#         get_profile = Profile.query.get(profile_id)
#         # check if already exists then remove 
#         dates_array = get_profile.unavailability
#         print('dates_array',dates_array)
#         if not dates_array:
#             unavailability_array.append(unavailable_dates)
#             get_profile.unavailability = str(unavailability_array)
#         else:
#             if unavailable_dates in dates_array:
#                 unavailability_array = ast.literal_eval(dates_array)
#                 unavailability_array.remove(unavailable_dates)
#             else:
#                 unavailability_array = ast.literal_eval(dates_array) 
#                 unavailability_array.append(unavailable_dates)
#         get_profile.unavailability = str(unavailability_array)
#         # ends here
#         db.session.add(get_profile)
#         db.session.commit()  # Create Enquirer profile
#         current_profile = Profile.query.filter_by(user_id=current_user).first()
#         unavailable_dates = ast.literal_eval(current_profile.unavailability)
#         return make_response(jsonify({"success": "Availability update successfull","unavailable_dates":unavailable_dates}),200)
#     except Exception as e:
#         exc_type, exc_obj, exc_tb = sys.exc_info()
#         fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
#         lNumber = exc_tb.tb_lineno
#         print('Error occurs in availabilityDates at line number',lNumber,'error is:',e)
#         return make_response(jsonify({"error": str(e)}),400)

# #Add Documents
# @main_bp.route("/addDocuments/", methods=['PUT'])
# @jwt_required
# def addDocuments():
#     """Add Member Profile."""
#     current_user = get_jwt_identity()
#     user_instance = User.query.get(current_user)
#     if user_instance.user_type == 'member':
#         pass
#     else:
#         return make_response(jsonify({"error": "Function only allowed for member"}),400)
#     profile_exists = bool(Profile.query.filter_by(user_id=current_user).first())
#     if not profile_exists:
#         return Response("{'error':'No such profile exists'}", status=400)
#     try:
#         get_profile = Profile.query.filter_by(user_id=current_user).first()
#         files_list = []
#         post_data = request.get_json()
#         document_string = post_data.get('document_string')
#         doc_name = post_data.get('document_name')
#         path_to_image = destination_uploads+'/'+doc_name
#         with open(path_to_image, "wb") as fh:
#             fh.write(base64.b64decode(document_string))
#         document_name = doc_name
#         files_list.append(document_name)
#         print('files_list',files_list)
#         get_profile.documents = str(files_list)
#         db.session.add(get_profile)
#         db.session.commit()
#         profile_schema = ProfileSchema(many=False)
#         profile = profile_schema.dump(get_profile)
#         profile['documents'] = ast.literal_eval(get_profile.documents)
#         profile['unavailable_dates'] = ast.literal_eval(get_profile.unavailability)
#         return make_response(jsonify({"success":"Documents upload successfull","profile": profile}))
#     except Exception as e:
#         exc_type, exc_obj, exc_tb = sys.exc_info()
#         lNumber = exc_tb.tb_lineno
#         print('error in documents at line',lNumber,'error>>',e)

# #Add Documents
# @main_bp.route("/addSummary/", methods=['PUT'])
# @jwt_required
# def addSummary():
#     """Add Member Summary."""
#     current_user = get_jwt_identity()
#     user_instance = User.query.get(current_user)
#     if user_instance.user_type == 'member':
#         pass
#     else:
#         return make_response(jsonify({"error": "Function only allowed for member"}),400)
#     profile_exists = bool(Profile.query.filter_by(user_id=current_user).first())
#     if not profile_exists:
#         return Response("{'error':'No such profile exists'}", status=400)
#     try:
#         get_profile = Profile.query.filter_by(user_id=current_user).first()
#         post_data = request.get_json()
#         summary = post_data.get('summary')
#         get_profile.summary = str(summary)
#         db.session.add(get_profile)
#         db.session.commit()
#         profile_schema = ProfileSchema(many=False)
#         profile = profile_schema.dump(get_profile)
#         profile['documents'] = ast.literal_eval(get_profile.documents)
#         profile['unavailable_dates'] = ast.literal_eval(get_profile.unavailability)
#         return make_response(jsonify({"success":"Summary Added Successfully","profile": profile}))
#     except Exception as e:
#         exc_type, exc_obj, exc_tb = sys.exc_info()
#         lNumber = exc_tb.tb_lineno
#         print('error in summary at line',lNumber,'error>>',e)

# #Add Documents
# @main_bp.route("/pinLocation/", methods=['PUT'])
# @jwt_required
# def pinLocation():
#     """Add Member Location."""
#     current_user = get_jwt_identity()
#     user_instance = User.query.get(current_user)
#     if user_instance.user_type == 'member':
#         pass
#     else:
#         return make_response(jsonify({"error": "Function only allowed for member"}),400)
#     profile_exists = bool(Profile.query.filter_by(user_id=current_user).first())
#     if not profile_exists:
#         return Response("{'error':'No such profile exists'}", status=400)
#     try:
#         get_profile = Profile.query.filter_by(user_id=current_user).first()
#         post_data = request.get_json()
#         latitude = post_data.get('latitude')
#         longitude = post_data.get('longitude')
#         pin_location = str(latitude)+','+str(longitude)
#         get_profile.pin_location = pin_location
#         db.session.add(get_profile)
#         db.session.commit()
#         profile_schema = ProfileSchema(many=False)
#         profile = profile_schema.dump(get_profile)
#         profile['documents'] = ast.literal_eval(get_profile.documents)
#         profile['unavailable_dates'] = ast.literal_eval(get_profile.unavailability)
#         return make_response(jsonify({"success":"Pin Location Updated Successfully","profile": profile}))
#     except Exception as e:
#         exc_type, exc_obj, exc_tb = sys.exc_info()
#         lNumber = exc_tb.tb_lineno
#         print('error in pin location at line',lNumber,'error>>',e)

################################################REVIEWS CRUD###############################################
# #READ All Reviews
# @main_bp.route('/reviews/', methods = ['GET'])
# def getReviews():
#     get_reviews = Reviews.query.all()
#     reviews_list = []
#     review_dict = {'id':'','review_text':'','stars':'','given_by':'','given_to':''}
#     for review in get_reviews:
#         member_instance = User.query.get(review.given_by)
#         enquirer_instance = User.query.get(review.given_to)
#         review_dict['id']=review.id
#         review_dict['review_text']=review.review_text
#         review_dict['stars']=review.stars
#         review_dict['given_by']=member_instance.email
#         review_dict['given_to']=enquirer_instance.email
#         reviews_list.append(review_dict.copy())
#     return make_response(jsonify({"reviews": reviews_list}))

# #READ REVIEWS BY USER ID
# @main_bp.route('/reviews/<user_id>/', methods = ['GET'])
# def getUserReviews(user_id):
#     try:
#         reviews_list = []
#         review_dict = {}
#         reviews_exist = bool(Reviews.query.filter_by(given_to=user_id).first())
#         if not reviews_exist:
#         #     reviews_dict = {'id':'','text':'','stars':0,'description':'','given_by':'',
#         # 'profile_pic':''}
#         #     reviews_list.append(reviews_dict)
#             return make_response(jsonify({"reviews": reviews_list}))
#         get_reviews = Reviews.query.filter_by(given_to=user_id)
#         for review in get_reviews:
#             given_by = review.given_by
#             user_instance = User.query.get(user_id)
#             user_type = user_instance.user_type
#             if user_type == 'member':
#                 profile_instance = EnquirerProfile.query.filter_by(enquirer_id = given_by).first()
#                 try:
#                     profile_pic = profile_instance.profile_pic
#                     profile_pic_path = enquirer_uploads+profile_pic
#                 except Exception as e:
#                    profile_pic_path = ''
#             if user_type == 'enquirer':
#                 profile_instance = Profile.query.filter_by(user_id = given_by).first()
#                 try:
#                     profile_pic = profile_instance.profile_pic
#                     profile_pic_path = member_uploads+profile_pic
#                 except Exception as e:
#                     profile_pic_path = ''
#             review_dict['id']=review.id
#             review_dict['text']=review.review_text
#             review_dict['stars']=review.stars
#             review_dict['given_by']=user_instance.name
#             review_dict['description']=review.review_description
#             review_dict['profile_pic']=profile_pic_path
#             reviews_list.append(review_dict.copy())
#         return make_response(jsonify({"reviews": reviews_list}))
#     except Exception as e:
#         #catch error and print line number where error occurs
#         exc_type, exc_obj, exc_tb = sys.exc_info()
#         fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
#         lNumber = exc_tb.tb_lineno
#         print('Error occurs in get user review at line number',lNumber,'error is:',e)
#         return make_response(jsonify({"error": str(e)}),400)


# #UPDATE
# @main_bp.route("/review/<id>/", methods=['PUT'])
# @jwt_required
# def updateReview(id):
#     try:
#         current_user = get_jwt_identity()
#         post_data = request.get_json()
#         get_review = Reviews.query.get(id)
#         if get_review == None:
#             return make_response(jsonify({"error": "No such review exists"}),400)
#         if(str(get_review.given_by) != str(current_user)):
#             return make_response(jsonify({"error": "You are not allowed to edit this review"}),400)
#         if post_data.get('text'):
#             get_review.review_text = post_data['text']
#         if post_data.get('stars'):
#             get_review.stars= post_data['stars'] 
#         if post_data.get('user_id'):
#             get_review.user_id= post_data['user_id']  
#         db.session.add(get_review)
#         db.session.commit()
#         review_schema = ReviewsSchema(only=['id','review_text','stars','given_to','given_by'])
#         review = review_schema.dump(get_review)
#         return make_response(jsonify({"success":"Update successfull","review": review}))
#     except Exception as e:
#         #catch error and print line number where error occurs
#         exc_type, exc_obj, exc_tb = sys.exc_info()
#         fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
#         lNumber = exc_tb.tb_lineno
#         print('Error occurs in update review at line number',lNumber,'error is:',e)
#         return make_response(jsonify({"error": str(e)}),400)

# #DELETE
# @main_bp.route('/review/<id>/', methods = ['DELETE'])
# @jwt_required
# def deleteReview(id):
#     current_user = get_jwt_identity()
#     get_profile = Reviews.query.get(id)
#     if get_profile == None:
#         return Response("{'error':'No such review exists'}", status=400)
#     if(str(get_profile.given_by) != str(current_user)):
#             return make_response(jsonify({"error": "You are not allowed to delete this review"}),400)
#     db.session.delete(get_profile)
#     db.session.commit()
#     return make_response(jsonify({"success":"Delete successfull"}),200)
######################################################################################################

################################################Users#################################################

#GET ALL USERS
@main_bp.route('/users/', methods = ['GET'])
def getUsers():
    get_users = User.query.all()
    user_schema = UserSchema(many=True)
    users = user_schema.dump(get_users)
    return make_response(jsonify({"users": users}))


#GET ALL Members
@main_bp.route('/members/', methods = ['GET'])
def getMembers():
    get_users = User.query.filter_by(user_type='member')
    user_schema = UserSchema(many=True)
    users = user_schema.dump(get_users)
    return make_response(jsonify({"users": users}))

#READ BY Member ID
@main_bp.route('/user/<id>', methods = ['GET'])
def getUserById(id):
    get_user = User.query.filter_by(id=id).filter_by(user_type='member').first()
    if get_user == None:
        return make_response(jsonify({"member": "[]"}),400)
    user_schema = UserSchema(many=False)
    user = user_schema.dump(get_user)
    return make_response(jsonify({"member": user}),200)

######################################################################################################
# #READ BY CATEGORY
# @jobs_main_bp.route('/categoryJobs/<category>', methods = ['GET'])
# def getJobByCategory(category):
#     try:
#         job_list = []
#         job_dict = {}
#         get_jobs = Jobs.query.filter_by(job_category=category).filter_by(is_draft=False)
#         print(get_jobs)
#         for job in get_jobs:
#             employer  = job.posted_by
#             profile_instance = EnquirerProfile.query.filter_by(enquirer_id=employer).first()
#             try:
#                 company_name = profile_instance.company_name
#             except Exception as e:
#                 company_name = ''
#             job_dict['id'] = job.id
#             job_dict['job_title'] = job.job_title
#             job_dict['job_category'] = job.job_category
#             job_dict['budget'] = job.budget 
#             job_dict['location'] = job.location
#             job_dict['city'] = job.city
#             job_dict['bidding_started'] = job.bidding_started
#             job_dict['company_name'] = company_name
#             start_date = job.shift_start_date
#             today_date = date.today()
#             delta = start_date - today_date
#             days_remaining = delta.days
#             job_dict['remaining_days'] = days_remaining
#             job_list.append(job_dict.copy())
#         return make_response(jsonify({"jobs": job_list}))
#     except Exception as e:
#         exc_type, exc_obj, exc_tb = sys.exc_info()
#         fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
#         lNumber = exc_tb.tb_lineno
#         print('Error occurs in category jobs at line number',lNumber,'error is:',e)
#         return make_response(jsonify({"error":str(e)}),400)


# #READ BY DISTANCE
# @jobs_main_bp.route('/filterJobs', methods = ['GET'])
# @jwt_required
# def getFilteredJobs():
#     try:
#         current_user = get_jwt_identity()
#         user_instance = User.query.get(current_user)
#         if user_instance.user_type == 'member':
#             pass
#         else:
#             return make_response(jsonify({"error": "Function only allowed for Member"}),400)
#         profile_instance = Profile.query.filter_by(user_id=current_user)
#         for profile in profile_instance:
#             user_city = profile.city
#         source = user_city
#         get_jobs = Jobs.query.all()
#         ten_mile_jobs_list = []
#         twenty_mile_jobs_list = []
#         fifty_mile_jobs_list = []
#         hundred_mile_jobs_list = []
#         night_shift_jobs = []
#         day_shift_jobs = []
#         job_dict = {}
#         miles_list = [10,20,50,100]
#         km_list = [x*1.6 for x in miles_list]
#         for job in get_jobs:
#             job_city = job.city
#             dest = job_city
#             #API to get distance betwen two cities
#             r = requests.get(str(distance_matrix_url+'origins='+source+'&destinations='+dest+'&key='+'AIzaSyAbOQGYshvI_FCLYFaCWhYsXN5-x1T3ENk'))  
#             response = r.json()
#             try:
#                 city_distance = response['rows'][0]['elements'][0]['distance']['text']
#                 city_distance_km = city_distance.split(' ')[0]
#                 if ',' in city_distance_km:
#                     city_distance_km = city_distance_km.replace(',','')
#             except Exception as e:
#                 print('error in city distance',e)
#                 city_distance_km = 0
#             job_dict['id'] = job.id
#             job_dict['job_title'] = job.job_title
#             job_dict['job_category'] = job.job_category
#             job_dict['job_type'] = job.job_type
#             job_dict['budget'] = job.budget 
#             job_dict['job_description'] = job.job_description
#             job_dict['location'] = job.location
#             job_dict['city'] = job.city
#             job_dict['created_at'] = job.created_at
#             job_dict['updated_at'] = job.updated_at
#             job_dict['posted_by'] = job.posted_by
#             job_dict['bidding_started'] = job.bidding_started
#             # job_dict['company_name'] = company_name
#             job_dict['shift_start_date'] = job.shift_start_date
#             job_dict['shift_end_date'] = job.shift_end_date
#             job_dict['shift_start_time'] = job.shift_start_time
#             job_dict['shift_end_time'] = job.shift_end_time
#             start_date = job.shift_start_date
#             today_date = date.today()
#             delta = start_date - today_date
#             days_remaining = delta.days
#             job_dict['remaining_days'] = days_remaining
#             enquirer_profile_instance = EnquirerProfile.query.filter_by(enquirer_id=job.posted_by).first()
#             try:
#                 company_name = enquirer_profile_instance.company_name
#             except Exception as e:
#                 company_name = ''
#             job_dict['company_name'] = company_name
#             if float(city_distance_km) < float(16.0):
#                 ten_mile_jobs_list.append(job_dict.copy())
#             if float(city_distance_km) < float(32.0):
#                 twenty_mile_jobs_list.append(job_dict.copy())
#             if float(city_distance_km) < float(80.0):
#                 fifty_mile_jobs_list.append(job_dict.copy())
#             if float(city_distance_km) < float(160.0):
#                 hundred_mile_jobs_list.append(job_dict.copy())
#             # if ((job.shift == 'Night') or (job.shift == 'night')):
#             #     night_shift_jobs.append(job_dict.copy())
#             # if ((job.shift == 'Day') or (job.shift == 'day')):
#             #     day_shift_jobs.append(job_dict.copy())
#         return make_response(jsonify({"10_mile_jobs_list": ten_mile_jobs_list,"20_mile_jobs_list":
#             twenty_mile_jobs_list,"50_mile_jobs_list":fifty_mile_jobs_list,"100_mile_jobs_list":
#             hundred_mile_jobs_list}))
#     except Exception as e:
#         exc_type, exc_obj, exc_tb = sys.exc_info()
#         fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
#         lNumber = exc_tb.tb_lineno
#         print('Error occurs in filter jobs at line number',lNumber,'error is:',e)
#         return make_response(jsonify({"error":str(e)}),400)

# #Accept a job application
# @jobs_main_bp.route('/acceptApplication/<application_id>', methods = ['POST'])
# @jwt_required
# def acceptApplication(application_id):
#     current_user = get_jwt_identity()
#     user_instance = User.query.get(current_user)
#     if user_instance.user_type == 'enquirer':
#         pass
#     else:
#         return make_response(jsonify({"error": "Function only allowed for enquirer"}),400)
#     application_data = AppliedJobs.query.get(application_id)
#     member_id = application_data.applied_by
#     job_id = application_data.job_id
#     member_data = User.query.get(member_id)
#     member_device_id = member_data.device_id
#     member_email = member_data.email
#     job_profile_data = Jobs.query.get(job_id)
#     job_title = job_profile_data.business_name
#     try:
#         applied_jobs = AppliedJobs.query.filter_by(job_id=job_id)
#     except Exception as e:
#             return make_response(jsonify({"error":"No application for this job yet"}),400)
#     try:
#         if application_data.application_status == AppliedJobStatusEnum.approved:        
#             return make_response(jsonify({"error":"Already Approved"}),400)
#         else:
#             application_data.application_status="approved"
#             try:
#                 local_object = db.session.merge(application_data)
#                 db.session.add(local_object)
#             except Exception as e:
#                 print('error in commit',e)
#                 db.session.add(application_data)
#             db.session.commit()
#             message_title = "Job Application Approved-OpenArc"
#             message_body = 'Your application has been approved for job at'+job_title
#             send_notification(member_device_id, message_title, message_body)
#             subject = "Job Application Rejected-OpenArc"
#             to = member_email
#             body = 'Hello '+to+',\nYour application has been approved for job at\n'+job_title
#             try:
#                 send_email(to, subject, job_title, 'rejected','')
#             except Exception as e:
#                 print('error sending email',e)
#             return make_response(jsonify({"success":"Job application approved successfully"}),200)
#     except Exception as e:
#         print('error in reject menber',e)
#         return make_response(jsonify({"error":"No such application exists"}),400)
# #Time Screen
# @jobs_main_bp.route('/logWorkTime/<application_id>', methods = ['POST'])
# @jwt_required
# def logWorkTime(application_id):
#     response_list = []
#     response_dict = {}
#     current_user = get_jwt_identity()
#     user_instance = User.query.get(current_user)
#     if user_instance.user_type == 'member':
#         pass
#     else:
#         return make_response(jsonify({"error": "Function only allowed for member"}),400)
#     application_instance = AppliedJobs.query.get(application_id)
#     per_hour_rate = application_instance.pay_expected
#     if '$' in per_hour_rate:
#         per_hour_rate = per_hour_rate.replace('$','')
#     if '£' in per_hour_rate:
#         per_hour_rate = per_hour_rate.replace('£','')
#     job_id = application_instance.job_id
#     job_details = Jobs.query.get(job_id)
#     post_data = request.get_json()
#     print('post_data',post_data)
#     date = post_data['date']
#     start_time = post_data['start_time']
#     end_time = post_data['end_time']
#     hours = post_data['hours']
#     after_hours = post_data['after_hours']
#     review_message = post_data['review_message']
#     stars = post_data['stars']
#     after_hours_reason = post_data['after_hours_reason']
#     after_hours_amount = ((33/100)*int(per_hour_rate))*int(after_hours)
#     amount = per_hour_rate
#     print('after_hours_amount',after_hours_amount)
#     if application_instance.is_active:
#         pass
#     else:
#         application_instance.is_active == True
#     log_instance_exists = bool(StartedJobLogs.query.filter_by(application_id = application_id).filter_by(date=date).first())
#     if log_instance_exists:
#         log_instance = StartedJobLogs.query.filter_by(application_id = application_id).filter_by(date=date).first()
#         log_instance.date = date,
#         log_instance.start_time = start_time,
#         log_instance.end_time = end_time,
#         log_instance.hours = hours,
#         log_instance.after_hours = after_hours,
#         log_instance.after_hours_reason = after_hours_reason,
#         log_instance.member_review = review_message,
#         log_instance.member_stars = stars,
#         log_instance.amount = int(per_hour_rate)*int(hours),
#         log_instance.after_hours_amount = after_hours_amount,
#         log_instance.work_status = 'submitted',
#         log_instance.member_status = 'inactive',
#         log_instance.application_id = application_id,
#     else:
#         log_instance = StartedJobLogs(
#             date = date,
#             start_time = start_time,
#             end_time = end_time,
#             hours = hours,
#             after_hours = after_hours,
#             after_hours_reason = after_hours_reason,
#             member_review = review_message,
#             member_stars = stars,
#             amount = int(per_hour_rate)*int(hours),
#             after_hours_amount = after_hours_amount,
#             work_status = 'submitted',
#             member_status = 'inactive',
#             application_id = application_id,
#             )
#     try:
#         local_object = db.session.merge(application_instance)
#         db.session.add(local_object)
#     except Exception as e:
#         print('error in commit',e)
#         db.session.add(application_instance)
#     try:
#         local_object = db.session.merge(log_instance)
#         db.session.add(local_object)
#     except Exception as e:
#         print('error in commit',e)
#         db.session.add(log_instance)
#     db.session.commit()
#     url = '/memberTimeScreen/'+str(application_id)
#     return redirect(url)


#Employer Time Screen
@jobs_main_bp.route('/employerTimeScreen/<application_id>', methods = ['GET'])
@jwt_required
def employerTimeScreen(application_id):
    current_user = get_jwt_identity()
    user_instance = User.query.get(current_user)
    if user_instance.user_type == 'enquirer':
        pass
    else:
        return make_response(jsonify({"error": "Function only allowed for enquirer"}),400)
    if request.method=='GET':
        response_list = []
        response_dict = {}
        application_instance = AppliedJobs.query.get(application_id)
        per_hour_rate = application_instance.pay_expected
        if '$' in per_hour_rate:
            per_hour_rate = per_hour_rate.replace('$','£')
        if '£' not in per_hour_rate:
            per_hour_rate = '£'+per_hour_rate+'/hr'
        job_id = application_instance.job_id
        job_details = Jobs.query.get(job_id)
        job_title = job_details.job_title
        member_id = application_instance.applied_by
        member_instance = User.query.get(member_id)
        member_name = member_instance.name
        member_profile_instance = Profile.query.filter_by(user_id=member_id).first()
        try:
            profile_pic = member_profile_instance.profile_pic
        except Exception as e:
            profile_pic = ''
        reviews = 5
        shift_start_date = job_details.shift_start_date
        shift_end_date = job_details.shift_end_date
        delta = shift_end_date - shift_start_date
        days_count = delta.days
        print('days_count',days_count)
        log_instance = StartedJobLogs.query.filter_by(application_id=application_id).filter_by(date=datetime.date.today()).first()
        if log_instance:
            print('log_instance')
            user_status = log_instance.member_status
        else:
            user_status = 'inactive'
        days_data_list = []
        day_data_dict = {}
        for i in range(days_count + 1):
            day = shift_start_date + timedelta(days=i)
            print(day)
            log_details = StartedJobLogs.query.filter_by(application_id=application_id).filter_by(date=day).first()
            if log_details != None:
                day_data_dict['start_time'] = str(log_details.start_time)
                day_data_dict['end_time'] = str(log_details.end_time)
                day_data_dict['hours'] = log_details.hours
                day_data_dict['after_hours'] = log_details.after_hours
                day_data_dict['after_hours_reason'] = log_details.after_hours_reason
                day_data_dict['member_review'] = log_details.member_review
                day_data_dict['member_stars'] = log_details.member_stars
                day_data_dict['date'] = log_details.date
                day_data_dict['work_status'] = log_details.work_status
                days_data_list.append(day_data_dict.copy())
        response_dict['application_id'] = application_id
        response_dict['member_id'] = member_id
        response_dict['job_title'] = job_title
        response_dict['member_name'] = member_name
        response_dict['profile_pic'] = profile_pic
        response_dict['reviews'] = reviews
        response_dict['days_count'] = days_count
        response_dict['per_hour_rate'] = per_hour_rate
        response_dict['shift_start_date'] = shift_start_date
        response_dict['shift_end_date'] = shift_end_date
        response_dict['user_status'] = user_status
        response_list.append(response_dict)
        return make_response(jsonify({"response":response_list,'dates_data':days_data_list}),200)

#Accept Member Time Log
@jobs_main_bp.route('/acceptTimeLog/', methods = ['POST'])
@jwt_required
def acceptTimeLog():
    try:
        current_user = get_jwt_identity()
        user_instance = User.query.get(current_user)
        if user_instance.user_type == 'enquirer':
            pass
        else:
            return make_response(jsonify({"error": "Function only allowed for enquirer"}),400)
        post_data = request.get_json()
        print('post_data',post_data)
        application_id = post_data['application_id']
        date = post_data['date']
        employer_review = post_data['review_message']
        employer_stars = post_data['review_stars']
        work_status = 'accepted'
        print('date>>',datetime.date.today())
        log_instance_exists = bool(StartedJobLogs.query.filter_by(application_id = application_id).first())
        if log_instance_exists:
            log_instance = StartedJobLogs.query.filter_by(application_id = application_id).filter_by(date=date).first()
            log_instance.employer_review = employer_review
            log_instance.employer_stars = employer_stars
            log_instance.work_status = work_status
        else:
            return make_response(jsonify({"error":"No work started yet"}),400)
        try:
            local_object = db.session.merge(log_instance)
            db.session.add(local_object)
        except Exception as e:
            print('error in commit',e)
            db.session.add(log_instance)
        db.session.commit()
        url = '/employerTimeScreen/'+str(application_id)
        return redirect(url)
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in accept time log at line ',lNumber,'error is:',e)
        return make_response(jsonify({"error":str(e)}),400)

# #Start a Job
# @jobs_main_bp.route('/clockIn/<application_id>', methods = ['POST'])
# @jwt_required
# def clockIn(application_id):
#     current_user = get_jwt_identity()
#     user_instance = User.query.get(current_user)
#     if user_instance.user_type == 'member':
#         pass
#     else:
#         return make_response(jsonify({"error": "Function only allowed for member"}),400)
#     user_data = User.query.get(current_user)
#     user_type = user_data.user_type
#     user_email = user_data.email
#     application_data = AppliedJobs.query.get(application_id)
#     if(application_data.is_funded == False):
#         return make_response(jsonify({"error": "Payment is not secured yet"}),400)
#     if application_data.is_active:
#         pass
#     else:
#         application_data.is_active == True
#     job_id = application_data.job_id
#     job_profile_data = Jobs.query.get(job_id)
#     job_title = job_profile_data.job_title
#     try:
#         job_log_exists = StartedJobLogs.query.filter(StartedJobLogs.date.contains(datetime.now().date()))
#         for log in job_log_exists:
#             if(log.application_id == application_id):
#                 if ((str(log.start_time) == '00:00:00') or (log.start_time == ' ')):
#                     pass
#                 else:
#                     return make_response(jsonify({"error":"Already started"}),400)
#         job_log = StartedJobLogs(
#                 application_id = application_id,
#                 end_time = ''
#             )
#         try:
#             local_object = db.session.merge(job_log)
#             db.session.add(local_object)
#         except Exception as e:
#             print('error in commit',e)
#             db.session.add(job_log)
#         try:
#             local_object = db.session.merge(application_data)
#             db.session.add(local_object)
#         except Exception as e:
#             print('error in commit',e)
#             db.session.add(application_data)
#         db.session.commit()
#         # db.session.close()
#         subject = "Shift started-OpenArc"
#         to = user_email
#         body = 'Hello '+to+',\n Work started on job titled\n'+job_title
#         try:
#             send_email(to, subject, job_title, '', 'started')
#         except Exception as e:
#             print('error sending email',e)
#         return make_response(jsonify({"success":"Shift started successfully"}),200)
#     except Exception as e:
#         exc_type, exc_obj, exc_tb = sys.exc_info()
#         fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
#         lNumber = exc_tb.tb_lineno
#         print('error in start job member at line',lNumber,'error is',e)
#         return make_response(jsonify({"error":str(e)}),400)



# #Stop a Job
# @jobs_main_bp.route('/clockOut/<application_id>', methods = ['POST'])
# @jwt_required
# def clockOut(application_id):
#     current_user = get_jwt_identity()
#     user_instance = User.query.get(current_user)
#     if user_instance.user_type == 'member':
#         pass
#     else:
#         return make_response(jsonify({"error": "Function only allowed for member"}),400)
#     user_data = User.query.get(current_user)
#     user_type = user_data.user_type
#     user_email = user_data.email
#     application_data = AppliedJobs.query.get(application_id)
#     application_data.is_active = True
#     job_id = application_data.job_id
#     job_profile_data = Jobs.query.get(job_id)
#     job_title = job_profile_data.job_title
#     # application_details = AppliedJobs.query.filter_by(id=application_id).first()
#     per_hour_rate = application_data.pay_expected
#     if '$' in per_hour_rate:
#         hourly_rate = per_hour_rate.replace('$','')
#     else:
#         hourly_rate = per_hour_rate
#     try:
#         today = datetime.now().strftime("%Y-%m-%d")
#         job_log_exists = StartedJobLogs.query.filter(StartedJobLogs.date.contains(today))
#         for log in job_log_exists:
#             print('log',log.id)
#             if(str(log.application_id) == str(application_id)):
#                 if ((str(log.end_time) == '00:00:00') or (log.end_time == ' ')):
#                     log_id = log.id
#                     log_instance = StartedJobLogs.query.get(log_id)
#                     now = datetime.now()
#                     log_instance.end_time = now.strftime("%H:%M:%S")
#                     start_time = log.start_time
#                     end_time = datetime.time(datetime.now())
#                     FMT = '%H:%M'
#                     tdelta = datetime.combine(date.today(), end_time) - datetime.combine(date.today(), start_time)
#                     shift_hours = int(tdelta.seconds/3600)
#                     log.hours = shift_hours
#                     log.amount = int(shift_hours)*int(hourly_rate)
#                     try:
#                         print('in try')
#                         log_object = db.session.merge(log_instance)
#                         db.session.add(log_object)
#                     except Exception as e:
#                         print('error in commit',e)
#                         db.session.add(log_instance)
#                     db.session.commit()
#                     db.session.close()
#                 else:
#                     return make_response(jsonify({"error":"Already Stopped"}),400)
#         subject = "Shift Completed-OpenArc"
#         to = user_email
#         body = 'Hello '+to+',\n Work stopped on job titled\n'+job_title
#         try:
#             send_email(to, subject, job_title, '', 'stopped')
#         except Exception as e:
#             print('error sending email',e)
#         return make_response(jsonify({"success":"Shift Completed successfully"}),200)
#     except Exception as e:
#         exc_type, exc_obj, exc_tb = sys.exc_info()
#         fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
#         lNumber = exc_tb.tb_lineno
#         print('error in  clock out data at line',lNumber,'error is',e)
#         return make_response(jsonify({"error":str(e)}),400)

# #Get Clock Screen Data
# @jobs_main_bp.route('/clockScreen/<application_id>', methods = ['GET'])
# @jwt_required
# def clockScreen(application_id):
#     try:
#         from datetime import datetime, date
#         today = datetime.now()
#         application_details = AppliedJobs.query.filter_by(id=application_id).first()
#         per_hour_rate = application_details.pay_expected
#         if '$' in per_hour_rate:
#             hourly_rate = per_hour_rate.replace('$','')
#         if '£' in per_hour_rate:
#             hourly_rate = per_hour_rate.replace('£','')
#         else:
#             hourly_rate = per_hour_rate
#         job_logs_exist = bool(StartedJobLogs.query.filter_by(application_id = application_id).filter(StartedJobLogs.date <= today).first())
#         print('job_logs_exist',job_logs_exist)
#         if job_logs_exist:
#             job_logs = StartedJobLogs.query.filter_by(application_id = application_id).filter_by(amount_paid=False)
#             hours_list = []
#             amount_list = []
#             for log in job_logs:
#                 shift_hours = log.hours
#                 amount = log.amount
#                 hours_list.append(int(shift_hours))
#                 amount_list.append(int(amount))
#             # print('hours_list',hours_list)
#             total_hours = sum(hours_list)
#             earned_money = sum(amount_list)
#         else:
#             total_hours = ''
#             earned_money = ''
#         # ###Payment####
#         # application_instance_exists = bool(AppliedJobs.query.filter_by(applied_by=current_user.id).filter_by(is_completed=True).first()) 
#         # payment_list = []
#         # payment_dict = {'date':'','amount':''}
#         # if application_instance_exists:
#         #     application_instance = AppliedJobs.query.filter_by(applied_by=current_user).filter_by(is_completed=True).first()
#         #     payment_dict['date'] = application_instance.completed_on
#         #     payment_dict['amount'] = application_instance.payment_received
#         #     payment_list.append(payment_dict.copy())
#         # else:
#         #     payment_list.append(payment_dict)
#         ############Invoices#################
#         invoices_details = StartedJobLogs.query.filter_by(application_id = application_id)
#         invoices_list = []
#         invoice_dict = {}
#         if invoices_details:
#             for invoice in invoices_details:
#                 invoice_dict['id'] = invoice.id
#                 invoice_dict['amount'] = invoice.amount
#                 invoice_dict['hours'] = invoice.hours
#                 invoice_dict['date'] = invoice.date
#                 amount_paid = invoice.amount_paid
#                 if amount_paid == True:
#                     payment_status = 'Paid'
#                 else:
#                     payment_status = 'Pending'
#                 invoice_dict['status'] = payment_status
#                 invoices_list.append(invoice_dict.copy())
#         return make_response(jsonify({"earned_money":earned_money,
#                 "total_hours":total_hours, 'invoices':invoices_list}))
#     except Exception as e:
#         exc_type, exc_obj, exc_tb = sys.exc_info()
#         fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
#         lNumber = exc_tb.tb_lineno
#         print('error in getting clock screen data at line',lNumber,'error is',e)
#         return make_response(jsonify({"error":str(e)}),400)


#REQUEST PAYMENT
@jobs_main_bp.route("/requestPayment/<application_id>", methods=['POST'])
@jwt_required
def requestPayment(application_id):
    try:
        current_user = get_jwt_identity()
        user_instance = User.query.get(current_user)
        if user_instance.user_type == 'member':
            pass
        else:
            return make_response(jsonify({"error": "Function only allowed for member"}),400)
        job_log_instance = StartedJobLogs.query.filter_by(application_id=application_id).filter_by(amount_paid=False).first()
        job_log_instance.payment_requested = True
        try:
            log_object = db.session.merge(job_log_instance)
            db.session.add(log_object)
        except Exception as e:
            print('error in commit',e)
            db.session.add(job_log_instance)
        db.session.commit()
        db.session.close()
        return make_response(jsonify({"success":"Payment Request Submitted successfully"}),200)
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('error in request_payment',lNumber,'error is',e)
        return make_response(jsonify({"error":str(e)}),400)

#approvePayment
@jobs_main_bp.route("/invoiceDetails/", methods=['POST'])
def invoiceDetails():
    try:
        post_data = request.get_json()
        member_id = post_data['member_id']
        job_id = post_data['job_id']
        if ((member_id == None) or (member_id == '')):
                return make_response(jsonify({"error":"member_id is required"}),400)
        if ((job_id == None) or (job_id == '')):
                return make_response(jsonify({"error":"job_id is required"}),400)
        job_instance = Jobs.query.get(job_id)
        job_type = job_instance.payment_type
        application_instance = AppliedJobs.query.filter_by(applied_by=member_id).filter_by(job_id=job_id).first()
        # if application_instance.payment_status =='pending':
        application_id = application_instance.id
        # job_log_instance = StartedJobLogs.query.filter_by(application_id=application_id).first()
        # start_time = job_log_instance.start_time
        # end_time = job_log_instance.end_time
        # time_diff = datetime.combine(date.today(), end_time) - datetime.combine(date.today(), start_time)
        # print('diff',time_diff,type(time_diff))
        ##################
        # pay_per_hour = application_instance.pay_expected
        # if '$' in pay_per_hour:
        #     hourly_rate = pay_per_hour.replace('$','')
        ##########
        if job_type == 'fixed':
            job_budget =  application_instance.pay_expected
            if('-' in job_budget):
                budget_amount_list = job_budget.split('-')
                amount_str = str(budget_amount_list[1])
                monthly_rate = amount_str.replace('$','')
            elif '$' in job_budget:
                monthly_rate = pay_per_hour.replace('$','')
            else:
                pass
            final_rate = monthly_rate
            print('final_rate monthly',final_rate)
            taxes = 0
            return make_response(jsonify({"application_id":application_id,
                "taxes":taxes, 'total':final_rate}))
        if job_type == 'hourly':
            pay_per_hour = application_instance.pay_expected
            if('-' in pay_per_hour):
                budget_amount_list = pay_per_hour.split('-')
                amount_str = str(budget_amount_list[1])
                hourly_rate = amount_str.replace('$','')
            elif '$' in pay_per_hour:
                hourly_rate = pay_per_hour.replace('$','')
            else:
                pass
            print('hourly_rate hourly',hourly_rate)
            # hours, remainder = divmod(time_diff.seconds, 3600)
            # minutes, seconds = divmod(remainder, 60)
            calculated_hours = 8
            per_minute_amount = int(hourly_rate)/60
            print('per_minute_amount',per_minute_amount)
            # calculated_minutes = minutes
            hours_amount = int(calculated_hours)*int(hourly_rate)
            # minutes_amount = minutes*per_minute_amount
            # payable_amount = int(hours_amount+minutes_amount)
            taxes = 0
            return make_response(jsonify({"application_id":application_id,"pay_per_hour": hourly_rate, 'no_of_hours': calculated_hours,
                "taxes":taxes, 'total':hours_amount}))
        # else:
        #     return make_response(jsonify({"error":"job is not completed yet"}),400)
    except Exception as e:
        #catch error and print line number where error occurs
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in getting invoice details at line number',lNumber,'error is:',e)
        return make_response(jsonify({"error": str(e)}),400)

#Approve PAYMENT
@jobs_main_bp.route("/approvePayment/", methods=['POST'])
@jwt_required
def approvePayment():
    try:
        current_user = get_jwt_identity()
        post_data = request.get_json()
        amount = post_data['amount']
        # description = post_data['payment_description']
        # token = post_data['token']
        application_id = post_data['application_id']
        payable_amount = int(amount)*100
        currency='usd',
        if ((amount == None) or (amount == '')):
                return make_response(jsonify({"error":"amount is required"}),400)
        # if ((token == None) or (token == '')):
        #         return make_response(jsonify({"error":"token is required"}),400)
        # charge = stripe.Charge.create(
        #   amount=payable_amount,
        #   currency='usd',
        #   description=description,
        #   source=token,
        # )
        get_application = AppliedJobs.query.get(application_id)
        if get_application.payment_status == 'paid':
            return make_response(jsonify({"error":"Already paid"}),400)
        get_application.payment_status = 'paid'
        get_application.payment_received = amount
        get_application.is_completed = True
        get_application.completed_on = datetime.datetime.now()
        db.session.add(get_application)
        db.session.commit() 
        return make_response(jsonify({"status":"success","message": "payment succesfull"}),200)
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('error at approve payment at line',lNumber,'error is',e)
        return make_response(jsonify({"error":str(e)}),400)

#Get Member Total Earnings
@jobs_main_bp.route('/memberDashboard/', methods = ['GET'])
@jwt_required
def getMemberDashboard():
    try:
        current_user = get_jwt_identity()
        user_instance = User.query.get(current_user)
        if user_instance.user_type == 'member':
            pass
        else:
            return make_response(jsonify({"error": "Function only allowed for member"}),400)
        Weekly_earnings_list = []
        Monthly_earnings_list = []
        Yearly_earnings_list = []
        present_job_list = []
        present_job_dict = {'job_id':'','application_id':'','company_name':'','job_title':'','city':'','shift_time':''}
        past_jobs_list = []
        past_job_dict = {'job_id':'','company_name':'','job_title':'','city':''}
        #####Present Job####
        present_job_exist = bool(AppliedJobs.query.filter_by(applied_by=current_user).filter_by(is_active=True).first())
        if present_job_exist:
            present_job = AppliedJobs.query.filter_by(applied_by=current_user).filter_by(is_active=True).first()
            present_job_dict['application_id'] = present_job.id
            present_job_dict['job_id'] = present_job.job_id
            job_detail = Jobs.query.get(present_job.job_id)
            #Time Calculation
            shift_start_time = job_detail.shift_start_time
            shift_end_time = job_detail.shift_end_time
            start_time = convert24(shift_start_time)
            end_time = convert24(shift_end_time)
            if 'AM' or 'PM' in start_time:
                start_time_final = start_time.replace('AM','')
                start_time_final = start_time.replace('PM','')
            if 'AM' or 'PM' in end_time:
                end_time_final = end_time.replace('AM','')
                end_time_final = end_time.replace('PM','')
            FMT = '%H:%M'
            tdelta = datetime.strptime(end_time_final, FMT) - datetime.strptime(start_time_final, FMT)
            shift_hours = tdelta.seconds/3600
            print('shift_hours',int(shift_hours))
            #Weekly shifts calculation
            shift_start_date = job_detail.shift_start_date
            shift_end_date = job_detail.shift_end_date
            delta = shift_end_date - shift_start_date
            shifts_count = delta.days
            print('shifts_count',shifts_count)
            job_title = job_detail.job_title
            job_city = job_detail.city
            shift_start_time = job_detail.shift_start_time
            posted_by = job_detail.posted_by
            company_details = EnquirerProfile.query.filter_by(enquirer_id=posted_by).first()
            try:
                company_name = company_details.company_name
            except Exception as e:
                company_name = ''
            present_job_dict['company_name'] = company_name
            present_job_dict['job_title'] = job_title
            present_job_dict['city'] = job_city
            present_job_dict['shift_time'] = shift_start_time
            present_job_list.append(present_job_dict.copy())
        else:
            present_job_list.append(present_job_list)
        ###Past Jobs#####
        completed_jobs_exist = bool(AppliedJobs.query.filter_by(applied_by=current_user).filter_by(is_completed=True).first())
        if completed_jobs_exist:
            completed_jobs = AppliedJobs.query.filter_by(applied_by=current_user).filter_by(is_completed=True)
            for job in completed_jobs:
                past_job_dict['job_id'] = job.job_id
                job_details = Jobs.query.get(job.job_id)
                job_title = job_details.job_title
                job_city = job_details.city
                posted_by = job_details.posted_by
                company_details = EnquirerProfile.query.filter_by(enquirer_id=posted_by).first()
                try:
                    company_name = company_details.company_name
                except Exception as e:
                    company_name = ''
                past_job_dict['company_name'] = company_name
                past_job_dict['job_title'] = job_title
                past_job_dict['city'] = job_city
                past_jobs_list.append(past_job_dict.copy())
        else:
            past_jobs_list.append(past_job_dict)
        #for week
        today = datetime.now().date()
        year, week_num, day_of_week = today.isocalendar()
        day_of_week = day_of_week
        start = today - timedelta(days=day_of_week)
        end = start + timedelta(days=6)
        week_start_date = start
        week_end_date = end
        start_date = str(week_start_date)
        end_date = str(week_end_date)
        start_date_value = datetime.strptime(start_date, "%Y-%m-%d")
        end_date_value = datetime.strptime(end_date, "%Y-%m-%d")
        print('week dates',start_date_value, end_date_value)
        application_data = AppliedJobs.query.filter(AppliedJobs.applied_by == current_user).filter(AppliedJobs.completed_on <= end_date_value).filter(AppliedJobs.completed_on >= start_date_value).filter(AppliedJobs.is_completed==True)
        for data in application_data:
            payment = data.payment_received
            Weekly_earnings_list.append(int(payment))
        weekly_earning = sum(Weekly_earnings_list)
        #for month
        today = datetime.now().date()
        start = today
        end = start - timedelta(days=30)
        month_start_date = start
        month_end_date = end
        start_date = str(month_start_date)
        end_date = str(month_end_date)
        start_date_value = datetime.strptime(start_date, "%Y-%m-%d")
        end_date_value = datetime.strptime(end_date, "%Y-%m-%d")
        print('month dates',start_date_value, end_date_value)
        application_data = AppliedJobs.query.filter(AppliedJobs.applied_by == current_user).filter(AppliedJobs.completed_on >= end_date_value).filter(AppliedJobs.completed_on <= start_date_value).filter(AppliedJobs.is_completed==True)
        for data in application_data:
            payment = data.payment_received
            Monthly_earnings_list.append(int(payment))
        monthly_earning = sum(Monthly_earnings_list)
        #for year
        today = datetime.now().date()
        start = today
        end = start - timedelta(days=365)
        year_start_date = start
        year_end_date = end
        start_date = str(year_start_date)
        end_date = str(year_end_date)
        start_date_value = datetime.strptime(start_date, "%Y-%m-%d")
        end_date_value = datetime.strptime(end_date, "%Y-%m-%d")
        print('year dates',start_date_value, end_date_value)
        application_data = AppliedJobs.query.filter(AppliedJobs.applied_by == current_user).filter(AppliedJobs.completed_on >= end_date_value).filter(AppliedJobs.completed_on <= start_date_value).filter(AppliedJobs.is_completed==True)
        for data in application_data:
            payment = data.payment_received
            Yearly_earnings_list.append(int(payment))
        yearly_earning = sum(Yearly_earnings_list)
        return make_response(jsonify({"weekly_earning": weekly_earning,'monthly_earning':
            monthly_earning,'yearly_earning':yearly_earning,'past_jobs':past_jobs_list,
            'present_job':present_job_list,'shift_hours':shift_hours,'shifts_count':shifts_count}))
    except Exception as e:
        #catch error and print line number where error occurs
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in memebr earnings at line number',lNumber,'error is:',e)
        return make_response(jsonify({"error": str(e)}),400)

# #READ AN EMPLOYER JOBS
# @jobs_main_bp.route('/allEmployerJobs/', methods = ['GET'])
# @jwt_required
# def getJobs():
#     try:
#         all_jobs_list = []
#         all_job_dict = {}
#         active_jobs_list = []
#         active_job_dict = {}
#         completed_jobs_list = []
#         completed_job_dict = {}
#         drafts_list = []
#         drafts_dict = {}
#         current_user = get_jwt_identity()
#         user_instance = User.query.get(current_user)
#         if user_instance.user_type == 'enquirer':
#             pass
#         else:
#             return make_response(jsonify({"error": "Function only allowed for Enquirer"}),400)
#         user_profile_instance = EnquirerProfile.query.filter_by(enquirer_id=current_user).first()
#         try:
#             company_name = user_profile_instance.company_name
#         except Exception as e:
#             company_name = ''
#         #All Jobs
#         all_jobs = Jobs.query.filter_by(posted_by=current_user).filter_by(is_draft=False)
#         for job in all_jobs:
#             all_job_dict['id'] = job.id
#             all_job_dict['job_title'] = job.job_title
#             all_job_dict['budget'] = job.budget 
#             all_job_dict['location'] = job.location
#             all_job_dict['city'] = job.city
#             all_job_dict['company_name'] = company_name
#             start_date = job.shift_start_date
#             today_date = date.today()
#             delta = start_date - today_date
#             days_remaining = delta.days
#             all_job_dict['remaining_days'] = days_remaining
#             applied_jobs_instance = bool(AppliedJobs.query.filter_by(job_id=job.id).first())
#             if applied_jobs_instance:
#                 applicants_count = AppliedJobs.query.filter_by(job_id=job.id).count()
#             else:
#                 applicants_count = 0
#             all_job_dict['applicants_count'] = applicants_count
#             all_jobs_list.append(all_job_dict.copy())
#         #Drafts Jobs
#         all_drafts = Jobs.query.filter_by(posted_by=current_user).filter_by(is_draft=True)
#         for job in all_drafts:
#             drafts_dict['id'] = job.id
#             drafts_dict['job_title'] = job.job_title
#             drafts_dict['budget'] = job.budget 
#             drafts_dict['location'] = job.location
#             drafts_dict['city'] = job.city
#             drafts_dict['company_name'] = company_name
#             start_date = job.shift_start_date
#             today_date = date.today()
#             delta = start_date - today_date
#             days_remaining = delta.days
#             drafts_dict['remaining_days'] = days_remaining
#             applied_jobs_instance = bool(AppliedJobs.query.filter_by(job_id=job.id).first())
#             if applied_jobs_instance:
#                 applicants_count = AppliedJobs.query.filter_by(job_id=job.id).count()
#             else:
#                 applicants_count = 0
#             drafts_dict['applicants_count'] = applicants_count
#             drafts_list.append(drafts_dict.copy())
#         #Active Jobs
#         all_jobs = Jobs.query.filter_by(posted_by=current_user).filter_by(is_draft=False)
#         for job in all_jobs:
#             job_id = job.id
#             members_list = []
#             member_dict = {'member_name':'','profile_pic':''}
#             applied_job_instance = bool(AppliedJobs.query.filter_by(job_id=job.id).first())
#             if applied_job_instance:
#                 applied_jobs = AppliedJobs.query.filter_by(job_id=job.id)
#                 for application in applied_jobs:
#                     is_active = application.is_active
#                     if is_active:
#                         active_job_dict['id'] = job.id
#                         active_job_dict['job_title'] = job.job_title
#                         active_job_dict['budget'] = job.budget 
#                         active_job_dict['location'] = job.location
#                         active_job_dict['city'] = job.city
#                         active_job_dict['company_name'] = company_name
#                         start_date = job.shift_start_date
#                         today_date = date.today()
#                         delta = start_date - today_date
#                         days_remaining = delta.days
#                         active_job_dict['remaining_days'] = days_remaining
#                         applicants_count = AppliedJobs.query.filter_by(job_id=job.id).count()
#                         # for i in range(0,applicants_count):
#                         #     applicant_id = application.applied_by
#                         #     user = User.query.get(applicant_id)
#                         #     user_name = user.name
#                         #     member_profile_instance = bool(Profile.query.filter_by(user_id=applicant_id).first())
#                         #     if member_profile_instance:
#                         #         member_profile = Profile.query.filter_by(user_id=applicant_id).first()
#                         #         profile_pic = member_profile.profile_pic
#                         #     else:
#                         #         profile_pic = ''
#                         #     member_dict['member_name'] = user_name
#                         #     member_dict['profile_pic'] = profile_pic
#                         #     members_list.append(member_dict.copy())
#                         active_job_dict['applicants_count'] = applicants_count
#                         # active_job_dict['applicants'] = members_list
#                         active_jobs_list.append(active_job_dict.copy())
#         #Completed Jobs
#         all_jobs = Jobs.query.filter_by(posted_by=current_user).filter_by(is_draft=False)
#         for job in all_jobs:
#             job_id = job.id
#             applied_job_instance = bool(AppliedJobs.query.filter_by(job_id=job.id).first())
#             if applied_job_instance:
#                 applied_jobs = AppliedJobs.query.filter_by(job_id=job.id)
#                 for application in applied_jobs:
#                     is_completed = application.is_completed
#                     if is_completed:
#                         completed_job_dict['id'] = job.id
#                         completed_job_dict['job_title'] = job.job_title
#                         completed_job_dict['budget'] = job.budget 
#                         completed_job_dict['location'] = job.location
#                         completed_job_dict['city'] = job.city
#                         completed_job_dict['company_name'] = company_name
#                         start_date = job.shift_start_date
#                         today_date = date.today()
#                         delta = start_date - today_date
#                         days_remaining = delta.days
#                         #completed_job_dict['remaining_days'] = days_remaining
#                         completed_jobs_list.append(completed_job_dict.copy())
#         active_jobs_list = [dict(t) for t in {tuple(d.items()) for d in active_jobs_list}]
#         return make_response(jsonify({'all_jobs':all_jobs_list,'drafts':drafts_list,'active_jobs':active_jobs_list,'completed_jobs':completed_jobs_list}),200)
#     except Exception as e:
#         exc_type, exc_obj, exc_tb = sys.exc_info()
#         fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
#         lNumber = exc_tb.tb_lineno
#         print('Error occurs in getting  job details for employer at line number',lNumber,'error is:',e)
#         return make_response(jsonify({"error":str(e)}),400)



# #READ Complaints For a Member
# @jobs_main_bp.route('/getMemberComplaints', methods = ['GET'])
# @jwt_required
# def getMemberComplaints():
#     current_user = get_jwt_identity()
#     get_complaints = Complaints.query.filter_by(member_id=current_user).filter_by(status='active')
#     complaints_list = []
#     complaints_dict = {'id':'','description':'','submitted_by':'','status':'', 'created_on':''}
#     for complaint in get_complaints:
#         enquirer_instance = User.query.get(complaint.submitted_by)
#         complaints_dict['id']=complaint.id
#         complaints_dict['description']=complaint.description
#         complaints_dict['status']=complaint.status
#         complaints_dict['submitted_by']=enquirer_instance.email
#         complaints_dict['created_on']=complaint.created_at
#         complaints_list.append(complaints_dict.copy())
#     return make_response(jsonify({"complaints": complaints_list}))

#Resolve a complaint
@jobs_main_bp.route('/resolveDispute/', methods = ['POST'])
@jwt_required
def resolveComplaint():
    try:
        current_user = get_jwt_identity()
        user_instance = User.query.get(current_user)
        # if user_instance.user_type == 'enquirer':
        #         pass
        # else:
        #     return make_response(jsonify({"error": "Function only allowed for enquirer"}),400)
        post_data = request.get_json()
        dispute_id = post_data['dispute_id']
        if dispute_id== '':
            return make_response(jsonify({"error": "dispute_id is required"}))
        dispute_instance = Disputes.query.get(dispute_id)
        dispute_instance.status = 'resolved'
        try:
            local_object = db.session.merge(dispute_instance)
            db.session.add(local_object)
        except Exception as e:
            print('error in commit',e)
            db.session.add(dispute_instance)
        db.session.commit()
        return make_response(jsonify({"success": "complaint resolved successfully"}))
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in resolve complaint at line number',lNumber,'error is:',e)

#DELETE
@jobs_main_bp.route('/dispute/<id>/', methods = ['DELETE'])
@jwt_required
def deleteComplaint(id):
    current_user = get_jwt_identity()
    get_complaint = Complaints.query.get(id)
    if get_complaint == None:
        return Response("{'error':'No such complaint exists'}", status=400)
    if(str(get_complaint.submitted_by) != str(current_user)):
            return make_response(jsonify({"error": "You are not allowed to delete this complaint"}),400)
    db.session.delete(get_complaint)
    db.session.commit()
    return make_response(jsonify({"success":"Delete successfull"}),200)