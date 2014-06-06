# -*- coding: utf-8 -*-
import sys
from secrets import SESSION_KEY

from webapp2 import WSGIApplication, Route

# inject './lib' dir in the path so that we can simply do "import ndb" 
# or whatever there's in the app lib dir.
if 'lib' not in sys.path:
    sys.path[0:0] = ['lib']

# webapp2 config
app_config = {
    'webapp2_extras.sessions': {
        'cookie_name': '_simpleauth_sess',
        'secret_key': SESSION_KEY
    },
    'webapp2_extras.auth': {
        'user_attributes': []
    }
}

# Map URLs to handlers
routes = [
    Route('/', handler='handlers.RootHandler', name='home'),
    Route('/semantic', handler='handlers.Semantic', name='Semantic'),
    Route('/add', handler='handlers.ProjectAdd'),
    Route('/firm', handler='handlers.firms'),
    Route('/delete_firm', handler='handlers.DeleteFirm'),
    Route('/delete_project', handler='handlers.DeleteProject'),
    Route('/delete_comment', handler='handlers.DeleteComment'),
    Route('/delete_member', handler='handlers.DeleteMember'),
    Route('/about', handler='handlers.About'),
    Route('/invite', handler='handlers.Invite'),
    Route('/privacy', handler='handlers.Privacy'),
    Route('/google0e3609a4a19b9bdc.html', handler='handlers.VerifyGoogle'),
    Route('/features', handler='handlers.Features'),
    Route('/browse', handler='handlers.Browse'),
    Route('/search', handler='handlers.Search'),
    Route('/chrome', handler='handlers.Chrome'),
    Route('/editfirm', handler='handlers.EditFirm'),
    Route('/addfirm', handler='handlers.firms'),
    Route('/add_firm_new', handler='handlers.add_firm'),
    Route('/cadd', handler='handlers.CommentAdd'),
    Route('/add_member', handler='handlers.AddFirmMember'),
    Route('/projects', handler='handlers.ProjectsHandler', name='projects'),
    Route('/profile', handler='handlers.ProfileHandler', name='profile'),

    Route('/logout', handler='handlers.AuthHandler:logout', name='logout'),
    Route('/<Firms>', handler='handlers.projects', name='firms'),
    Route('/auth/<provider>',
          handler='handlers.AuthHandler:_simple_auth', name='auth_login'),
    Route('/auth/<provider>/callback',
          handler='handlers.AuthHandler:_auth_callback', name='auth_callback')
]

app = WSGIApplication(routes, config=app_config, debug=True)
