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

DEFAULT_USER_NAME = 'default_user'
DEFAULT_RESOURCE_NAME = 'default_resource'
DEFAULT_RESERVATION_NAME = 'default_reservation'



def user_key(user_name=DEFAULT_USER_NAME):
    """Constructs a Datastore key for a User entity.

    We use user_name as the key.
    """
    return ndb.Key('User', user_name)

def resource_key(resource_name=DEFAULT_RESOURCE_NAME):
    """Constructs a Datastore key for a Resource entity.

    We use resource_name as the key.
    """
    return ndb.Key('Resource', resource_name)

def reservation_key(reservation_name=DEFAULT_RESERVATION_NAME):
    """Constructs a Datastore key for a Reservation entity.

    We use reservation_name as the key.
    """
    return ndb.Key('Reservation', reservation_name)

#[User Model]
class User(ndb.Model):
    identity = ndb.StringProperty()
    
#[Resource Model]
class Resource(ndb.Model):
    identity = ndb.StringProperty()
    name = ndb.StringProperty()
    tag = ndb.StringProperty(repeated=True,indexed=False)
    start = ndb.DateTimeProperty(indexed=False)
    end = ndb.DateTimeProperty(indexed=False);
    available = ndb.DateTimeProperty(repeated=True,indexed=False)
    last_made = ndb.DateTimeProperty(auto_now_add=True)
    owner =ndb.StringProperty()

#[Reservation Model]
class Reservation(ndb.Model):
    identity = ndb.StringProperty()
    name = ndb.StringProperty();
    start = ndb.DateTimeProperty()
    end = ndb.DateTimeProperty(indexed=False);
    userId = ndb.StringProperty()
    resource = ndb.StructuredProperty(Resource,indexed=False)
    made = ndb.DateTimeProperty(auto_now_add=True);
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
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'
        
        #get the user's reservation
        reservation_query = Reservation.query(Reservation.userId == user.user_id()).order(-Reservation.made)
#         reservation_query = Reservation.query().order(-Reservation.made)

        
        #get all the resources in the system
        all_resource_query = Resource.query().order(-Resource.last_made)
        
        #get resources that the user owns
        own_resource_query = Resource.query(Resource.owner == user.user_id())
        
        template_values = {
            'user': user,
            'reservation_list': reservation_query,
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
        start_date_processing = [int(v) for v in start_date_processing]
        start_date_out = datetime.datetime(*start_date_processing)
        reservation.start = start_date_out
        
        #get end time
        end_time = self.request.get('end_time')
        end_date_processing = end_time.replace('T', '-').replace(':', '-').split('-')
        end_date_processing = [int(v) for v in end_date_processing]
        end_date_out = datetime.datetime(*end_date_processing)
        reservation.end = end_date_out
                
        
        #store the data to ndb
        reservation.put()
        time.sleep(0.1)
        self.redirect('/')
            
    

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
        user = users.get_current_user()
        if user:
            resource.owner = user.user_id()
        #get start time
        resource.name = self.request.get('name')
        start_time = self.request.get('start_time')
        start_date_processing = start_time.replace('T', '-').replace(':', '-').split('-')
        start_date_processing = [int(v) for v in start_date_processing]
        start_date_out = datetime.datetime(*start_date_processing)
        resource.start = start_date_out
        
        #get end time
        end_time = self.request.get('end_time')
        end_date_processing = end_time.replace('T', '-').replace(':', '-').split('-')
        end_date_processing = [int(v) for v in end_date_processing]
        end_date_out = datetime.datetime(*end_date_processing)
        resource.end = end_date_out

        tags = str(self.request.get('tags'))
        tag_list = tags.split(";")
        resource.tag = tag_list
        
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
        reservation_query = Reservation.query(Reservation.name == resource_name).order(Reservation.start)
        
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
            'reservation_list':reservation_query
            
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
        
        #get start time
        resource_name = self.request.get('name')
        resource = Resource.query(resource_name == Resource.name).get()
        resource.name = resource_name
        start_time = self.request.get('start_time')
        start_date_processing = start_time.replace('T', '-').replace(':', '-').split('-')
        start_date_processing = [int(v) for v in start_date_processing]
        start_date_out = datetime.datetime(*start_date_processing)
        resource.start = start_date_out
        
        #get end time
        end_time = self.request.get('end_time')
        end_date_processing = end_time.replace('T', '-').replace(':', '-').split('-')
        end_date_processing = [int(v) for v in end_date_processing]
        end_date_out = datetime.datetime(*end_date_processing)
        resource.end = end_date_out

        tags = str(self.request.get('tags'))
        tag_list = tags.split(";")
        resource.tag = tag_list
        
        if user:
            resource.owner = user.user_id()
        #store the data to ndb
        resource.put()
        time.sleep(0.1)
        self.redirect('/')

# [START app]
app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/create',CreatePage),
    ('/create_resource',CreateResource),
    ('/tag',ShowResourceFilterByTag),
    ('/resource',ShowResource),
    ('/update_resource',UpdateResource),
    ('/create_reservation',CreateReservation),
], debug=True)
# [END app]
