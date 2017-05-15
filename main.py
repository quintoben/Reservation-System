#!/usr/bin/env python

# Copyright 2016 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START imports]
import os
import urllib
import datetime


from google.appengine.api import users
from google.appengine.ext import ndb

import jinja2
import webapp2
import time
from itertools import repeat


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)
# [END imports]


# def validate_date(d):
#     try:
#         datetime.strptime(d, '%Y-%M-%D %H:%M:%S')
#         return True
#     except ValueError:
#         return False

#[User Model]
class User(ndb.Model):
    identity = ndb.StringProperty()
    name = ndb.StringProperty()
    
#[Resource Model]
class Resource(ndb.Model):
    name = ndb.StringProperty()
    tag = ndb.StringProperty(repeated=True,indexed=False)
    start = ndb.DateTimeProperty(indexed=False)
    end = ndb.DateTimeProperty(indexed=False);
    last_made = ndb.DateTimeProperty(auto_now_add=True)
    owner = ndb.StringProperty()
    duration = ndb.StringProperty()
    num = ndb.IntegerProperty()

#[Reservation Model]
class Reservation(ndb.Model):
    name = ndb.StringProperty();
    start = ndb.DateTimeProperty()
    end = ndb.DateTimeProperty();
    userId = ndb.StringProperty()
    made = ndb.DateTimeProperty(auto_now_add=True);
    duration = ndb.StringProperty()
    @classmethod
    def query_reservation(cls, ancestor_key):
        return cls.query(ancestor=ancestor_key).order(-cls.date)
    

# [START main_page]
class MainPage(webapp2.RequestHandler):
    
    def get(self):
        
        user = users.get_current_user()
        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
            user_info = User()
            user_info.identity = user.user_id()
            user_info.name = user.email()
            user_info.put()
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'
        
        #get the user's reservation
        now = datetime.datetime.now()
        reservation_query = Reservation.query(Reservation.userId == user.user_id()).order(-Reservation.made)
#         reservation_query = Reservation.query().order(-Reservation.made)
        result = []
        for res in reservation_query:
            if res.end > now:
                result.append(res)
        
        
        #get all the resources in the system
        all_resource_query = Resource.query().order(-Resource.last_made)
        
        #get resources that the user owns
        own_resource_query = Resource.query(Resource.owner == user.user_id())
        
        template_values = {
            'user': user,
            'reservation_list': result,
#             'reservation_id': urllib.quote_plus(reservation_id),
            'all_resource_list': all_resource_query,
            'own_resource_list': own_resource_query,
            'url': url,
            'url_linktext': url_linktext,
        }
        template = JINJA_ENVIRONMENT.get_template('landing.html')
        self.response.write(template.render(template_values))


class CreateReservation(webapp2.RequestHandler):
    
    def post(self):
        
        reservation = Reservation()
        user = users.get_current_user()
        if user:
            reservation.userId = user.user_id()
        #get start time
        reservation.name = self.request.get('name')
        start_time = self.request.get('start_time')
        start_date_processing = start_time.replace('T', '-').replace(':', '-').split('-')
        valid_start = True
        for v in start_date_processing:
            if v == '':
                valid_start = False
        if valid_start == True:
            start_date_processing = [int(v) for v in start_date_processing]
            start_date_out = datetime.datetime(*start_date_processing)
            reservation.start = start_date_out
        
        
        
        #get end time
        end_time = self.request.get('end_time')
        end_date_processing = end_time.replace('T', '-').replace(':', '-').split('-')
        valid_end = True
        for v in end_date_processing:
            if v == '':
                valid_end = False
        
        if valid_end == True:
            end_date_processing = [int(v) for v in end_date_processing]
            end_date_out = datetime.datetime(*end_date_processing)
            reservation.end = end_date_out
        
        if valid_start and valid_end:
        
            resource = Resource.query(reservation.name == Resource.name).get()
            
            if reservation.start < resource.start or reservation.end > resource.end:
                self.redirect('/error?error=the time you choose is invalid')
            
            else:
                exsit_reservation = Reservation.query(reservation.name == Reservation.name)
                valid = True
                for res in exsit_reservation:
                    if res.start < reservation.start and res.end > reservation.start:
                        valid = False
                    if res.start < reservation.end and res.end > reservation.end:
                        valid = False
                if valid == False:
                    self.redirect('/error?error=the time you choose overlay with other reservation')
                else:
                    #store the data to ndb
                    duration = reservation.end - reservation.start
                    reservation.duration = str(duration)
                    reservation.put()
                    resource.num = resource.num + 1
                    resource.put()
                    time.sleep(0.1)
                    self.redirect('/')
        
        else:
            self.redirect('/error?error=the time you choose is invalid')
            
    

class CreatePage(webapp2.RequestHandler):
    
    def get(self):
        
        user = users.get_current_user()
        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'
        
        template_values = {
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
        }
        template = JINJA_ENVIRONMENT.get_template('create.html')
        self.response.write(template.render(template_values))

class CreateResource(webapp2.RequestHandler):
    
    def post(self):
        
        resource = Resource()
        error = ''
        user = users.get_current_user()
        if user:
            resource.owner = user.user_id()
        #get start time
        resource.name = self.request.get('name')
        if resource.name == '':
            error = 'please enter the resource name'
        
        start_time = self.request.get('start_time')
        start_date_processing = start_time.replace('T', '-').replace(':', '-').split('-')
        valid_start = True
        for v in start_date_processing:
            if v == '':
                valid_start = False
        if valid_start==True:
            start_date_processing = [int(v) for v in start_date_processing]
            start_date_out = datetime.datetime(*start_date_processing)
            resource.start = start_date_out
#             if validate_date(start_date_out) == False:
#                 error = 'please enter the correct resource start time'
        else:
            error = 'please enter the correct resource start time'
        
        #get end time
        end_time = self.request.get('end_time')
        end_date_processing = end_time.replace('T', '-').replace(':', '-').split('-')
        
        valid_end = True
        for v in end_date_processing:
            if v=='':
                valid_end = False
        if valid_end==True:
            end_date_processing = [int(v) for v in end_date_processing]
            end_date_out = datetime.datetime(*end_date_processing)
            resource.end = end_date_out
#             if validate_date(end_date_out) == False:
#                 error = 'please enter the correct resource end time'
        else:
            error = 'please enter the correct resource end time'
        

        tags = str(self.request.get('tags'))
        tag_list = tags.split(";")
        resource.tag = tag_list
        
        if valid_start and valid_end:
            duration = end_date_out - start_date_out
            if end_date_out < start_date_out:
                error = 'resource\'s end date is later than start day'
        if error != '':
            self.redirect('/error?error='+error)
        else:
            resource.duration = str(duration)
            resource.num = 0
        
            #store the data to ndb
            resource.put()
            
            time.sleep(0.1)
            self.redirect('/')

class ShowResourceFilterByTag(webapp2.RequestHandler):
    
    def get(self):
        tag = self.request.get('tag')
        resource_query = Resource.query()
        resource_list = []
        for res in resource_query:
            for  res_tag in res.tag:
                if(res_tag == tag):
                    resource_list.append(res)
        
        
        user = users.get_current_user()
        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'
        
        
        template_values = {
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
            'resource_list': resource_list,
            'tag_name': tag,
        }
        template = JINJA_ENVIRONMENT.get_template('res_filter_by_tag.html')
        self.response.write(template.render(template_values))

class ShowResource(webapp2.RequestHandler):
    
    def get(self):
        resource_name = self.request.get('resource')
        resource_query = Resource.query(resource_name == Resource.name).get()
        now = datetime.datetime.now()
        reservation_query = Reservation.query(Reservation.name == resource_name)
        query = reservation_query.filter(Reservation.end > now)
        
        dict = {}
        for res in query:
            user_info =  User.query(res.userId == User.identity).get()
            dict[res.userId] = user_info.name
        
        user = users.get_current_user()
        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'
        
        
        template_values = {
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
            'resource': resource_query,
            'reservation_list': query,
            'user_info': dict
        }
        
        if user.user_id() == resource_query.owner:
            tag_list = resource_query.tag
            tag_string = ''
            for tag in tag_list:
                tag_string = tag_string + str(tag) + ";"    
            tag_string = tag_string[:-1]
            start = str(resource_query.start)
            end = str(resource_query.end)
            start = start.replace(' ', 'T')
            end = end.replace(' ', 'T')
            template_values['tag'] = tag_string
            template_values['own'] = user.user_id()
            template_values['start'] = start
            template_values['end'] = end
        
        template = JINJA_ENVIRONMENT.get_template('show_resource.html')
        self.response.write(template.render(template_values))
        
class UpdateResource(webapp2.RequestHandler):
    
    def post(self):

        user = users.get_current_user()
        error = ''
        
        #get start time
        resource_name = self.request.get('resource_name')
        new_name = self.request.get('name')
        
        resource = Resource.query(resource_name == Resource.name).get()
        resource.name = new_name
        if resource.name == '':
            error = 'please enter the resource name'
        
        start_time = self.request.get('start_time')
        start_date_processing = start_time.replace('T', '-').replace(':', '-').split('-')
        valid_start = True
        for v in start_date_processing:
            if v == '':
                valid_start = False
        if valid_start==True:
            start_date_processing = [int(v) for v in start_date_processing]
            start_date_out = datetime.datetime(*start_date_processing)
            resource.start = start_date_out
            
        else:
            error = 'please enter the correct resource start time'
        
        #get end time
        end_time = self.request.get('end_time')
        end_date_processing = end_time.replace('T', '-').replace(':', '-').split('-')
        valid_end = True
        for v in end_date_processing:
            if v=='':
                valid_end = False
        if valid_end==True:
            end_date_processing = [int(v) for v in end_date_processing]
            end_date_out = datetime.datetime(*end_date_processing)
            resource.end = end_date_out
        else:
            error = 'please enter the correct resource end time'

        tags = str(self.request.get('tags'))
        tag_list = tags.split(";")
        resource.tag = tag_list
        
        if valid_start and valid_end:
            duration = end_date_out - start_date_out
            if end_date_out < start_date_out:
                error = 'resource\'s end date is later than start day'
        if error != '':
            self.redirect('/error?error='+error)
        else:
            if user:
                resource.owner = user.user_id()
            #store the data to ndb
            resource.duration = str(duration)
            resource.put()
            time.sleep(0.1)
            self.redirect('/')
        
class Delete(webapp2.RequestHandler):
    
    def get(self):
        reservation_key = ndb.Key(urlsafe=self.request.get('name'))
        reservation = Reservation.query(reservation_key == Reservation.key).get()
        reservation.key.delete()
        resource = Resource.query(reservation.name == Resource.name).get()
        resource.num = resource.num - 1
        resource.put()
        time.sleep(0.1)
        self.redirect('/')

class RSS(webapp2.RequestHandler):
    
    def get(self):
        resource_name = self.request.get('name')
        resource_query = Resource.query(resource_name == Resource.name).get()
        reservation_query = Reservation.query(Reservation.name == resource_name)
        template_values = {
            'resource': resource_query,
            'reservation_list': reservation_query
        }
        self.response.headers['Content-Type'] = 'application/rss+xml'
        template = JINJA_ENVIRONMENT.get_template('rss.xml')
        self.response.write(template.render(template_values))
        
class Error(webapp2.RequestHandler):
    
    def get(self):
        error = self.request.get('error')
        template_values = {
            'error': error
        }
        template = JINJA_ENVIRONMENT.get_template('error.html')
        self.response.write(template.render(template_values))

# [START app]
app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/create',CreatePage),
    ('/create_resource',CreateResource),
    ('/tag',ShowResourceFilterByTag),
    ('/resource',ShowResource),
    ('/update_resource',UpdateResource),
    ('/create_reservation',CreateReservation),
    ('/delete',Delete),
    ('/rss',RSS),
    ('/error',Error),
], debug=True)
# [END app]
