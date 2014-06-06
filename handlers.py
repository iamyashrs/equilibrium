# -*- coding: utf-8 -*-
import os
import json
import datetime
import logging
import secrets
import urllib
import collections

import webapp2
from webapp2_extras import auth, sessions, jinja2
from jinja2.runtime import TemplateNotFound
from django.utils.html import strip_tags
from urlparse import urlparse

from simpleauth import SimpleAuthHandler
from google.appengine.ext import ndb
from google.appengine.api import urlfetch
from google.appengine.api import mail
from google.appengine.api import users
from webapp2_extras.appengine.auth.models import User

from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import images
from google.appengine.api import search
from urlparse import parse_qs


project_key = ndb.Key('Projects', 'default_projects')
firms_key = ndb.Key('Firms', 'default_firms')
comments_key = ndb.Key('Comments', 'default_comments')
user_key = ndb.Key('User', 'default_user')
notification_key = ndb.Key('Notification', 'default_notification')

_INDEX_NAME_FIRMS = 'firms'

custom_search_key = 'search key'
custom_search_cx = 'cx'


class Firms(ndb.Model):
    admin = ndb.KeyProperty(kind='User')
    admin_id = ndb.IntegerProperty()
    members = ndb.StringProperty(repeated=True)
    picture = ndb.StringProperty()
    link = ndb.StringProperty()
    desc = ndb.StringProperty()
    logo = ndb.BlobKeyProperty()
    title = ndb.StringProperty()
    pos = ndb.GeoPtProperty(default=ndb.GeoPt(28.635308, 77.224960))
    privacy = ndb.IntegerProperty(default=0)
    date = ndb.DateTimeProperty(auto_now_add=True)


class Projects(ndb.Model):
    author = ndb.KeyProperty(kind='User')
    author_id = ndb.IntegerProperty()
    firm = ndb.KeyProperty(kind='Firms')
    firm_id = ndb.IntegerProperty()
    title = ndb.StringProperty()
    content = ndb.StringProperty()
    deadline = ndb.DateTimeProperty()
    date = ndb.DateTimeProperty(auto_now_add=True)


class Comments(ndb.Model):
    author = ndb.KeyProperty(kind='User')
    firm = ndb.KeyProperty(kind='Firms')
    project = ndb.KeyProperty(kind='Projects')
    comment = ndb.StringProperty()
    project_id = ndb.IntegerProperty()
    date = ndb.DateTimeProperty(auto_now_add=True)


class Notification(ndb.Model):
    author = ndb.KeyProperty(kind='User')
    body_html = ndb.StringProperty()
    id = ndb.IntegerProperty()
    href = ndb.StringProperty()
    time = ndb.DateTimeProperty(auto_now_add=True)
    users = ndb.StringProperty(repeated=True)


class BaseRequestHandler(webapp2.RequestHandler):
    def dispatch(self):
        # Get a session store for this request.
        self.session_store = sessions.get_store(request=self.request)
        try:
            # Dispatch the request.
            webapp2.RequestHandler.dispatch(self)
        finally:
            # Save all sessions.
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def jinja2(self):
        """Returns a Jinja2 renderer cached in the app registry"""
        return jinja2.get_jinja2(app=self.app)

    @webapp2.cached_property
    def session(self):
        """Returns a session using the default cookie key"""
        return self.session_store.get_session()

    @webapp2.cached_property
    def auth(self):
        return auth.get_auth()

    @webapp2.cached_property
    def current_user(self):
        """Returns currently logged in user"""
        user_dict = self.auth.get_user_by_session()
        return self.auth.store.user_model.get_by_id(user_dict['user_id'])

    @webapp2.cached_property
    def logged_in(self):
        """Returns true if a user is currently logged in, false otherwise"""
        return self.auth.get_user_by_session() is not None

    def render(self, template_name, template_vars={}):
        # Preset values for the template
        values = {
            'url_for': self.uri_for,
            'logged_in': self.logged_in,
            'flashes': self.session.get_flashes()
        }

        # Add manually supplied template values
        values.update(template_vars)

        # read the template or 404.html
        try:
            self.response.write(self.jinja2.render_template(template_name, **values))
        except TemplateNotFound:
            self.abort(404)

    def head(self, *args):
        """Head is used by Twitter. If not there the tweet button shows 0"""
        pass


class CommentAdd(BaseRequestHandler):
    def post(self):
        firm_id = int(self.request.get('firm_id'))
        project_id = int(self.request.get('project_id'))

        firm = Firms.get_by_id(firm_id, parent=firms_key)
        project = Projects.get_by_id(project_id, parent=project_key)

        comment = Comments(parent=comments_key)
        comment.author = self.current_user.key
        comment.firm = firm.key
        comment.comment = self.request.get('comment')
        comment.project = project.key
        comment.project_id = project_id
        comment.put()

        notification = Notification(parent=notification_key)
        notification.author = self.current_user.key
        notification.body_html = "<a href=\"./profile?pro_id=" + str(self.current_user.key.id()) \
                                 + "\">" + self.current_user.name + "</a> has commented on your project in " \
                                 + "<a href=\"./projects?firm_id=" + str(firm.key.id()) \
                                 + "\">" + firm.title + "</a> .."
        notification.href = "./projects?firm_id=" + str(firm.key.id()) + "#row" + str(project.key.id())
        notification.id = comment.key.id()
        notification.users.append(project.author.get().email)
        notification.put()

        if firm_id:
            self.redirect('/projects?firm_id=' + str(firm_id) + '#row' + str(project_id))
        else:
            self.redirect('/')


class ProjectAdd(BaseRequestHandler):
    def post(self):
        firm_id = int(self.request.get('firm_id'))
        firm = Firms.get_by_id(firm_id, parent=firms_key)

        projects = Projects(parent=project_key)
        projects.author = self.current_user.key
        projects.author_id = int(self.current_user.key.id())
        projects.firm = firm.key
        projects.firm_id = firm_id
        projects.content = self.request.get('content')
        projects.title = self.request.get('title')
        projects.deadline = datetime.datetime.strptime(self.request.get('datetime'), '%m/%d/%Y %H:%M %p')
        projects.put()

        notification = Notification(parent=notification_key)
        notification.author = self.current_user.key
        notification.body_html = "<a href=\"./profile?pro_id=" + str(self.current_user.key.id()) \
                                 + "\">" + self.current_user.name + "</a> has created a new project " \
                                 + self.request.get('title') + " in " \
                                 + "<a href=\"./projects?firm_id=" + str(firm.key.id()) \
                                 + "\">" + firm.title + "</a> .."
        notification.href = "./projects?firm_id=" + str(firm.key.id())
        notification.id = projects.key.id()
        for member in firm.members:
            notification.users.append(member)
        notification.put()

        self.redirect('/projects?firm_id=' + str(firm_id))


class firms(BaseRequestHandler):
    def post(self):
        if self.request.get('title'):
            title = self.request.get('title')

            if title:
                #google images search
                title1 = urllib.quote_plus(title)
                url = 'https://www.googleapis.com/customsearch/v1?key=' + custom_search_key + '&cx=' + custom_search_cx + '&searchType=image&fileType=jpg&imgSize=large&imgType=news&num=1&alt=json&q=' + title1
                result = urlfetch.fetch(url)
                jsonr = json.loads(result.content)
                picture = jsonr['items'][0]['link']
                link = jsonr['items'][0]['displayLink']
                desc1 = jsonr['items'][0]['title']
                desc = urllib.unquote_plus(desc1)


                #wikipedia description
                urlw = "https://en.wikipedia.org//w/api.php?action=query&prop=extracts&format=json&exsentences=1&exlimit=1&exsectionformat=plain&titles=" + title1
                resultw = urlfetch.fetch(urlw)
                jsonrw = json.loads(resultw.content)
                d = jsonrw['query']['pages'].keys()
                x = d[0]
                try:
                    desciption = jsonrw['query']['pages'][x]['extract']
                except:
                    desciption = ""

                if desciption:
                    desc = strip_tags(desciption)

            else:
                picture = self.current_user.avatar_url
                link = self.current_user.link
                desc = "No data."
        else:
            self.render('error.html', {
                'user': self.current_user,
            })

        firmss = Firms(parent=firms_key)
        firmss.admin = self.current_user.key
        firmss.admin_id = self.current_user.key.id()
        firmss.members = [self.current_user.email]
        firmss.link = link
        firmss.picture = picture
        firmss.title = title
        firmss.desc = desc
        firmss.put()

        id = firmss.key.id()
        search.Index(name=_INDEX_NAME_FIRMS).put(CreateFirmDoc(str(id), self.current_user, title, "null", desc, link))

        self.redirect('/firm?firm_id=' + str(firmss.key.id()))

    def get(self):
        upload_url = blobstore.create_upload_url('/editfirm')
        firm_id = 0
        try:
            firm_id = int(self.request.get('firm_id'))
        except:
            self.abort(404)
        firmed = Firms.get_by_id(firm_id, parent=firms_key)
        if firmed.logo:
            image_url = images.get_serving_url(firmed.logo, 75)
        else:
            image_url = "/img/Hinder-red.png"

        if (firm_id != 0) and self.logged_in:
            self.render('firm.html', {
                'title': 'Edit Firm Settings - ' + firmed.title,
                'user': self.current_user,
                'upload_url': upload_url,
                'image_url': image_url,
                'firm': firmed,
                'firm_id': firm_id
            })
        else:
            self.abort(404)


class EditFirm(BaseRequestHandler, blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        desc = self.request.get('desc')
        desc = (desc[:75] + '..') if len(desc) > 75 else desc

        title = self.request.get('title')
        title = (title[:60] + '..') if len(title) > 75 else title

        link = self.request.get('link')
        parts = urlparse(link)
        if not parts.scheme or not parts.netloc:
            self.abort(404)

        firm_id = int(self.request.get('firm_id'))
        firm = Firms.get_by_id(firm_id, parent=firms_key)
        logo = self.get_uploads('logo')

        if logo:
            blob_info = logo[0]
            if firm.logo:
                blobstore.delete(firm.logo)
            firm.logo = blob_info.key()
            logo = blob_info.key()
        else:
            logo = firm.logo

        firm.link = link
        firm.picture = self.request.get('picture')
        firm.title = title
        firm.privacy = int(self.request.get('type'))
        firm.desc = desc
        firm.pos = ndb.GeoPt(self.request.get('lat'), self.request.get('lng'))
        firm.put()

        notification = Notification(parent=notification_key)
        notification.author = self.current_user.key
        notification.body_html = "<a href=\"./profile?pro_id=" + str(self.current_user.key.id()) \
                                 + "\">" + self.current_user.name + "</a> updated " \
                                 + "<a href=\"./projects?firm_id=" + str(firm.key.id()) \
                                 + "\">" + firm.title + "</a> Details..."
        notification.href = "./projects?firm_id=" + str(firm.key.id())
        notification.id = firm.key.id()
        for member in firm.members:
            notification.users.append(member)
        notification.put()


        doc_index = search.Index(name=_INDEX_NAME_FIRMS)
        if doc_index.get(doc_id=str(firm.key.id())):
            doc_index.delete(document_ids=str(firm.key.id()))

        search.Index(name=_INDEX_NAME_FIRMS).put(CreateFirmDoc(str(firm_id),
        self.current_user, title, str(logo), desc, link))

        self.redirect('/')


class add_firm(BaseRequestHandler):
    def post(self):
        if self.request.get('title'):
            title = self.request.get('title')
        else:
            title = "No Title"
        if self.request.get('link'):
            link = self.request.get('link')
        else:
            link = "No link"
        if self.request.get('desc'):
            desc = self.request.get('desc')
        else:
            desc = "No Description!"

        if self.logged_in:
            self.render('add_firm.html', {
                'user': self.current_user,
                'title': title,
                'link': link,
                'desc': desc
            })
        else:
            self.render('add_firm.html', {
                'title': title,
                'link': link,
                'desc': desc,
            })


class DeleteFirm(BaseRequestHandler):
    def get(self):
        firm_id = 0
        try:
            firm_id = int(self.request.get('firm_id'))
        except:
            self.abort(404)
        firmed = Firms.get_by_id(firm_id, parent=firms_key)

        if (firm_id != 0) and self.logged_in:
            self.render('delete.html', {
                'title': 'Delete Firm',
                'user': self.current_user,
                'firm': firmed,
                'firm_id': firm_id
            })
        else:
            self.abort(404)


    def post(self):
        logging.debug('Deleting the event!: %s' % self.request.get('event_id'))
        firm_id = 0
        try:
            firm_id = int(self.request.get('firm_id'))
        except:
            self.abort(404)
        firmed = Firms.get_by_id(firm_id, parent=firms_key)
        projects = Projects.query(Projects.firm_id == firm_id, ancestor=project_key)
        comments = Comments.query(ancestor=comments_key)

        for project in projects:
            for comment in comments:
                if comment.project == project.key.id():
                    comment.key.delete()
            project.key.delete()

        doc_index = search.Index(name=_INDEX_NAME_FIRMS)
        if doc_index.get(doc_id=str(firmed.key.id())):
            doc_index.delete(document_ids=str(firmed.key.id()))

        firmed.key.delete()
        self.redirect('/')


class AddFirmMember(BaseRequestHandler):
    def post(self):
        firm_id = self.request.get('firm_id')
        email = self.request.get('member_email')
        firm_id1 = int(self.request.get('firm_id'))
        firm = Firms.get_by_id(firm_id1, parent=firms_key)

        if email in firm.members:
            self.abort(404)
        else:
            firm.members.append(email)
            firm.put()

        notification = Notification(parent=notification_key)
        notification.author = self.current_user.key
        notification.body_html = "<a href=\"./profile?pro_id=" + str(self.current_user.key.id()) \
                                 + "\">" + self.current_user.name + "</a> added a new member " + \
                                 self.request.get('member_email') + " to " \
                                 + "<a href=\"./projects?firm_id=" + str(firm.key.id()) \
                                 + "\">" + firm.title + "</a>."
        notification.href = "./projects?firm_id=" + str(firm.key.id())
        notification.id = firm.key.id()
        for member in firm.members:
            notification.users.append(member)
        notification.put()

        if firm_id:
            self.redirect('/projects?firm_id=' + firm_id + '#row')
        else:
            self.redirect('/')


class RootHandler(BaseRequestHandler):
    def get(self):
        """Handles default langing page"""
        # Projects

        if self.logged_in:
            firms = Firms.query(ancestor=firms_key).order(-Firms.date)
            email = self.current_user.email
            foundFirm = False
            firmed = []
            for firm in firms:
                if email in firm.members:
                    firmed.append(firm)
                    foundFirm = True

            #projects = Projects.query(ancestor=project_key).order(-Projects.deadline)
            found = False
            if self.logged_in:
                projectsme = Projects.query(Projects.author_id == self.current_user.key.id(),
                                            ancestor=project_key).order(
                    -Projects.deadline)
                for project in projectsme:
                    found = True
            else:
                projectsme = None

            comments = Comments.query(ancestor=comments_key).order(Comments.date)
            notifications = Notification.query(ancestor=notification_key).order(-Notification.time).fetch(5)
            notification = []
            for notify in notifications:
                if email in notify.users and notify.author.get().email != self.current_user.email:
                    notification.append(notify)
            count = len(notification)

            self.render('home.html', {
                'title': 'Equilibrium',
                'notifications': notification,
                'count': count,
                'firms': firmed,
                'user': self.current_user,
                'greetings': projectsme,
                'comments': comments,
                'found': found,
                'foundFirm': foundFirm
            })
        else:
            self.render('hot.html')


class About(BaseRequestHandler):
    def get(self):
        if self.logged_in:
            self.render('about.html', {
                'title': 'Equilibrium - Work made easy.',
                'user': self.current_user
            })
        else:
            self.render('about.html', {
                'title': 'Equilibrium - Work made easy.'
            })


class DeleteProject(BaseRequestHandler):
    def post(self):
        project_id = 0
        try:
            project_id = int(self.request.get('project_id'))
        except:
            self.abort(404)
        project = Projects.get_by_id(project_id, parent=project_key)
        comments = Comments.query(Comments.project_id == project_id, ancestor=comments_key)
        notifications = Notification.query(Notification.id == project_id, ancestor=notification_key)

        for notice in notifications:
            notice.key.delete()

        for comment in comments:
            comment.key.delete()

        project.key.delete()
        self.redirect('/')


class DeleteComment(BaseRequestHandler):
    def post(self):
        comment_id = 0
        try:
            comment_id = int(self.request.get('comment_id'))
        except:
            self.abort(404)
        comment = Comments.get_by_id(comment_id, parent=comments_key)

        notifications = Notification.query(Notification.id == comment_id, ancestor=notification_key)

        for notice in notifications:
            notice.key.delete()

        comment.key.delete()
        self.redirect('/')


class DeleteMember(BaseRequestHandler):
    def post(self):
        logging.debug('Deleting the member in !: %s' % self.request.get('firm_id'))
        firm_id = 0
        member = ''
        try:
            member = self.request.get('member')
            firm_id = int(self.request.get('firm_id'))
        except:
            self.abort(404)

        firmed = Firms.get_by_id(firm_id, parent=firms_key)
        if member in firmed.members:
            firmed.members.remove(member)

        firmed.put()
        self.redirect('/')


class Invite(BaseRequestHandler):
    def get(self):
        self.render('invite.html', {
            'title': 'Invite People To Equilibrium - Work made easy.',
            'user': self.current_user,
        })

    def post(self):
        email = self.request.get('email')
        message = mail.EmailMessage()
        message.sender = self.current_user.email
        message.to = email
        message.subject = "Invitation to Equilibrium!"
        message.body = """
            You have been invited to Equilibrium!

            To accept this invitation, click the following link,
            or copy and paste the URL into your browser's address
            bar:

            http://gcdc2013-equilibrium.appspot.com/
        """

        message.send()
        self.redirect('/')


class Privacy(BaseRequestHandler):
    def get(self):
        if self.logged_in:
            self.render('privacy.html', {
                'title': 'Privacy / TOS For Equilibrium',
                'user': self.current_user
            })
        else:
            self.render('privacy.html', {
                'title': 'Privacy / TOS For Equilibrium'
            })


class Features(BaseRequestHandler):
    def get(self):
        if self.logged_in:
            self.render('features.html', {
                'title': 'Features of Equilibrium - Work Made Easy',
                'user': self.current_user
            })
        else:
            self.render('features.html', {
                'title': 'Features of Equilibrium - Work Made Easy',
            })


class Browse(BaseRequestHandler):
    def get(self):
        firms = Firms.query(ancestor=firms_key).order(-Firms.date)

        if self.logged_in:
            self.render('browse.html', {
                'title': 'Browse - Equilibrium',
                'user': self.current_user,
                'images': images.get_serving_url,
                'firms': firms
            })
        else:
            self.abort(404)


def CreateFirmDoc(id, author, title, logo, desc, link):
    if author:
        nickname = author.name
    else:
        nickname = 'anonymous'

    return search.Document(doc_id=id,
                           fields=[search.TextField(name='author', value=nickname),
                                   search.TextField(name='title', value=title),
                                   search.TextField(name='logo', value=logo),
                                   search.TextField(name='desc', value=desc),
                                   search.TextField(name='link', value=link),
                                   search.DateField(name='date', value=datetime.datetime.now().date())])


class Search(BaseRequestHandler):
    def get(self):
        uri = urlparse(self.request.uri)
        query = 'null'
        if uri.query:
            query = parse_qs(uri.query)
            query = query['query'][0]

        if query is not 'null':
            expr_list = [search.SortExpression(
                expression='author', default_value='',
                direction=search.SortExpression.DESCENDING)]

            sort_opts = search.SortOptions(expressions=expr_list)
            query_options = search.QueryOptions(limit=9, sort_options=sort_opts)
            query_obj = search.Query(query_string=query, options=query_options)

            results_firms = search.Index(name=_INDEX_NAME_FIRMS).search(query=query_obj)

            self.render('search.html', {
                'user': self.current_user,
                'title': "Search - Equilibrium",
                'results_firms': results_firms,
                'images': images.get_serving_url,
                'len': results_firms.number_found
            })
        else:
            self.render('search.html', {
                'user': self.current_user,
                'title': "Search - Equilibrium"
            })

    def get(self):
        if self.logged_in:

            firms = Firms.query(ancestor=firms_key).order(-Firms.date)
            email = self.current_user.email
            foundFirm = False
            firmed = []
            for firm in firms:
                if email in firm.members:
                    firmed.append(firm)
                    foundFirm = True

            notifications = Notification.query(ancestor=notification_key).order(-Notification.time).fetch(5)
            notification = []
            for notify in notifications:
                if email in notify.users and notify.author.get().email != self.current_user.email:
                    notification.append(notify)
            count = len(notification)

            #projects = Projects.query(ancestor=project_key).order(-Projects.deadline)
            found = False

            if self.logged_in:
                projectsme = Projects.query(Projects.author_id == self.current_user.key.id(),
                                            ancestor=project_key).order(
                    -Projects.deadline)
                for project in projectsme:
                    found = True
            else:
                projectsme = None

            comments = Comments.query(ancestor=comments_key).order(Comments.date)

            self.render('semantic.html', {
                'title': 'Semantic - Equilibrium',
                'notifications': notification,
                'count': count,
                'user': self.current_user,
                'greetings': projectsme,
                'found': found,
                'foundFirm': foundFirm,
                'comments': comments,
            })
        else:
            self.render('semantic.html', {
                'title': 'Semantic - Equilibrium',
            })


class ProjectsHandler(BaseRequestHandler):
    def get(self):
        """Handles default langing page"""
        # Projects
        firm_id = 0
        try:
            firm_id = int(self.request.get('firm_id'))
        except:
            self.abort(404)

        firmed = Firms.get_by_id(firm_id, parent=firms_key)

        projects = Projects.query(Projects.firm_id == firm_id, ancestor=project_key).order(-Projects.deadline)

        comments = Comments.query(ancestor=comments_key).order(Comments.date)

        found = False
        for project in projects:
            found = True

        if self.logged_in:
            self.render('projects.html', {
                'title': firmed.title + ' on Equilibrium',
                'greetings': projects,
                'comments': comments,
                'user': self.current_user,
                'images': images.get_serving_url,
                'firm_id': firm_id,
                'firm': firmed,
                'found': found
            })
        else:
            self.render('projects.html', {
                'title': firmed.title + 'on Equilibrium',
                'greetings': projects,
                'comments': comments,
                'logo_url': images.get_serving_url(firmed.logo, 75),
                'user': None,
                'firm_id': firm_id,
                'firm': firmed,
                'found': found
            })


class ProfileHandler(BaseRequestHandler):
    def get(self):
        """Handles GET /profile"""
        #projects = Projects.query(Projects.author == self.current_user.key, ancestor=project_key).order(-Projects.deadline)

        comments = Comments.query(ancestor=comments_key).order(Comments.date)

        found = False

        pro_id = 0
        try:
            pro_id = int(self.request.get('pro_id'))
        except:
            self.abort(404)
        profile = self.auth.store.user_model.get_by_id(pro_id)

        projects = Projects.query(Projects.author == profile.key, ancestor=project_key).order(-Projects.deadline)

        firms = Firms.query(ancestor=firms_key).order(-Firms.date)
        email = profile.email
        foundFirm = False
        firmed = []
        for firm in firms:
            if email in firm.members:
                firmed.append(firm)
                foundFirm = True

        for project in projects:
            found = True

        self.render('profile.html', {
            'title': profile.name,
            'get_user': profile,
            'foundFirm': foundFirm,
            'firms': firmed,
            'user': self.current_user,
            'greetings': projects,
            'comments': comments,
            'found': found
        })


class AuthHandler(BaseRequestHandler, SimpleAuthHandler):
    """Authentication handler for OAuth 2.0, 1.0(a) and OpenID."""

    # Enable optional OAuth 2.0 CSRF guard
    OAUTH2_CSRF_STATE = True

    USER_ATTRS = {
        'facebook': {
            'id': lambda id: ('avatar_url',
                              'http://graph.facebook.com/{0}/picture?type=large'.format(id)),
            'name': 'name',
            'link': 'link'
        },
        'google': {
            'picture': 'avatar_url',
            'name': 'name',
            'profile': 'link',
            'email': 'email'
        },
        'windows_live': {
            'avatar_url': 'avatar_url',
            'name': 'name',
            'link': 'link'
        },
        'twitter': {
            'profile_image_url': 'avatar_url',
            'screen_name': 'name',
            'link': 'link'
        },
        'linkedin': {
            'picture-url': 'avatar_url',
            'first-name': 'name',
            'public-profile-url': 'link'
        },
        'linkedin2': {
            'picture-url': 'avatar_url',
            'first-name': 'name',
            'public-profile-url': 'link'
        },
        'foursquare': {
            'photo': lambda photo: ('avatar_url', photo.get('prefix') + '100x100' + photo.get('suffix')),
            'firstName': 'firstName',
            'lastName': 'lastName',
            'contact': lambda contact: ('email', contact.get('email')),
            'id': lambda id: ('link', 'http://foursquare.com/user/{0}'.format(id))
        },
        'openid': {
            'id': lambda id: ('avatar_url', '/img/missing-avatar.png'),
            'nickname': 'name',
            'email': 'link'
        }
    }

    def _on_signin(self, data, auth_info, provider):
        """Callback whenever a new or existing user is logging in.
     data is a user info dictionary.
     auth_info contains access token or oauth token and secret.
    """
        auth_id = '%s:%s' % (provider, data['id'])
        logging.info('Looking for a user with id %s', auth_id)

        user = self.auth.store.user_model.get_by_auth_id(auth_id)
        _attrs = self._to_user_model_attrs(data, self.USER_ATTRS[provider])

        if user:
            logging.info('Found existing user to log in')
            # Existing users might've changed their profile data so we update our
            # local model anyway. This might result in quite inefficient usage
            # of the Datastore, but we do this anyway for demo purposes.
            #
            # In a real app you could compare _attrs with user's properties fetched
            # from the datastore and update local user in case something's changed.
            user.populate(**_attrs)
            user.put()
            self.auth.set_session(
                self.auth.store.user_to_dict(user))

        else:
            # check whether there's a user currently logged in
            # then, create a new user if nobody's signed in,
            # otherwise add this auth_id to currently logged in user.

            if self.logged_in:
                logging.info('Updating currently logged in user')

                u = self.current_user
                u.populate(**_attrs)
                # The following will also do u.put(). Though, in a real app
                # you might want to check the result, which is
                # (boolean, info) tuple where boolean == True indicates success
                # See webapp2_extras.appengine.auth.models.User for details.
                u.add_auth_id(auth_id)

            else:
                logging.info('Creating a brand new user')
                ok, user = self.auth.store.user_model.create_user(auth_id, **_attrs)
                if ok:
                    self.auth.set_session(self.auth.store.user_to_dict(user))

        # Remember auth data during redirect, just for this demo. You wouldn't
        # normally do this.
        self.session.add_flash(data, 'data - from _on_signin(...)')
        self.session.add_flash(auth_info, 'auth_info - from _on_signin(...)')

        # Go to the profile page
        self.redirect('/')

    def logout(self):
        self.auth.unset_session()
        self.redirect('/')

    def handle_exception(self, exception, debug):
        logging.error(exception)
        self.render('error.html', {'exception': exception})

    def _callback_uri_for(self, provider):
        return self.uri_for('auth_callback', provider=provider, _full=True)

    def _get_consumer_info_for(self, provider):
        """Returns a tuple (key, secret) for auth init requests."""
        return secrets.AUTH_CONFIG[provider]

    def _to_user_model_attrs(self, data, attrs_map):
        """Get the needed information from the provider dataset."""
        user_attrs = {}
        for k, v in attrs_map.iteritems():
            attr = (v, data.get(k)) if isinstance(v, str) else v(data.get(k))
            user_attrs.setdefault(*attr)

        return user_attrs
